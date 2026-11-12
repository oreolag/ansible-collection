"""Read-only preflight tests. Never delete real accounts, groups or services."""
import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
ROLE = ROOT / 'roles/odev_uninstall'
spec = importlib.util.spec_from_file_location('uninstall_preflight', ROLE/'files/preflight.py')
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)

class UninstallPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='odev-uninstall-', dir='/tmp')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = {'prefix':'/opt', 'hostname':'storage-01', 'booking_catalogue':''}
        self.groups = [SimpleNamespace(gr_name=name, gr_gid=200000+i) for i,name in enumerate(preflight.GROUPS)]
        self.users = [SimpleNamespace(pw_name='alice', pw_gid=1000)]

    def write(self, path, content):
        p = self.root/path.lstrip('/')
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return p

    def inspect(self):
        return preflight.inspect(self.config, root=self.root, group_entries=self.groups, passwd_entries=self.users)

    def test_safe_storage_host_has_exact_bounded_removal_plan(self):
        result = self.inspect()
        self.assertEqual(result['errors'], [])
        self.assertEqual(set(result['groups']), set(preflight.GROUPS))
        for path in ['/opt/odev','/opt/odev_login.sh','/etc/sudoers.d/odev-users']:
            self.assertIn(path, result['remove_paths'])
        for retained in ['/exports','/home','/opt/mgmt','/opt/cmdb','/opt/booking.yml','/var/lib/odev-booking','/etc/exports','/etc/fstab','/etc/ssh','/var/lib/tailscale']:
            self.assertFalse(any(retained==p or retained.startswith(p+'/') for p in result['remove_paths']), retained)
        self.assertIn('odev-booking-expiry.timer',result['units'])
        self.assertNotIn('nfs-kernel-server.service',result['units'])

    def test_declared_booking_server_and_managed_host_are_blocked(self):
        for server in [{'name':'storage-01'}, {'name':'booking-01','managed_servers':['storage-01']}]:
            self.config['booking_catalogue'] = yaml.safe_dump({'servers':[server]})
            self.assertTrue(any('Booking still depends' in e for e in self.inspect()['errors']))

    def test_installed_custom_booking_inventory_is_checked(self):
        self.write('/opt/odev/vars.yml','paths:\n  booking: /etc/custom-booking.yml\n')
        self.write('/etc/custom-booking.yml','servers:\n  - name: storage-01\n')
        self.assertTrue(any('Booking still depends' in e for e in self.inspect()['errors']))

    def test_malformed_catalogue_fails_closed(self):
        self.config['booking_catalogue'] = 'servers: ['
        self.assertTrue(self.inspect()['errors'])

    def test_pam_endpoint_and_forced_lookup_commands_are_blocked(self):
        cases=[('/etc/pam.d/sshd','# BEGIN ODEV BOOKING ADMISSION\n'),('/etc/odev/booking-access/endpoint.json','{}'),('/var/lib/odev-booking-check/.ssh/authorized_keys','restrict,command="/opt/odev/booking/access.py --serve node" key\n')]
        for path,content in cases:
            with self.subTest(path=path):
                p=self.write(path,content)
                self.assertTrue(self.inspect()['errors'])
                p.unlink()

    def test_primary_group_use_is_blocked_and_account_is_preserved(self):
        self.users.append(SimpleNamespace(pw_name='login-user',pw_gid=self.groups[0].gr_gid))
        result=self.inspect()
        self.assertTrue(any('primary group of login-user' in e for e in result['errors']))
        self.assertEqual(self.users[-1].pw_name,'login-user')

    def test_retained_group_owned_file_is_blocked_but_cli_artifacts_are_allowed(self):
        retained=self.write('/exports/scratch/alice/data','preserve')
        cli=self.write('/opt/odev/cli-file','code')
        original=os.lstat
        target_gid=self.groups[0].gr_gid
        def fake_stat(path,*args,**kwargs):
            actual=original(path,*args,**kwargs)
            if Path(path) in (retained,cli):
                values=list(actual);values[5]=target_gid
                return os.stat_result(values)
            return actual
        with patch.object(preflight.os,'lstat',side_effect=fake_stat):
            result=self.inspect()
            self.assertTrue(any('/exports/scratch/alice/data' in e for e in result['errors']))
            retained.unlink()
            self.assertEqual(self.inspect()['errors'],[])
        self.assertEqual(cli.read_text(),'code')

    def test_unreadable_filesystem_fails_closed(self):
        def walk(root, **kwargs):
            kwargs['onerror'](PermissionError('cannot read retained storage'))
            return iter([])
        with patch.object(preflight.os,'walk',side_effect=walk):
            self.assertTrue(any('Cannot inspect filesystem' in e for e in self.inspect()['errors']))

    def test_absent_installation_and_groups_are_rerunnable(self):
        self.groups=[]
        self.assertEqual(self.inspect()['errors'],[])
        self.assertEqual(self.inspect()['groups'],[])

    def test_unsafe_prefix_and_symlink_installation_are_blocked(self):
        for prefix in ['/','/opt/../home','relative']:
            self.config['prefix']=prefix
            self.assertTrue(self.inspect()['errors'])
        self.config['prefix']='/opt'
        (self.root/'opt').mkdir()
        (self.root/'opt/odev').symlink_to(self.root/'retained')
        self.assertTrue(any('symlink' in e for e in self.inspect()['errors']))

    def test_task_order_checks_before_removal_and_deletes_groups_last(self):
        tasks=yaml.safe_load((ROLE/'tasks/main.yml').read_text())
        guard=next(i for i,t in enumerate(tasks) if t['name'].startswith('Refuse uninstall'))
        destructive=[i for i,t in enumerate(tasks) if any(m in t for m in ('ansible.builtin.systemd_service','ansible.builtin.file','ansible.builtin.group','ansible.builtin.lineinfile'))]
        self.assertTrue(all(i>guard for i in destructive))
        self.assertEqual(tasks[-1]['ansible.builtin.group']['state'],'absent')
        self.assertFalse(any('ansible.builtin.user' in t for t in tasks))
        self.assertFalse(any('ansible.builtin.apt' in t for t in tasks))

if __name__=='__main__':
    unittest.main()
