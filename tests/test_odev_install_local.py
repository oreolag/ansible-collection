"""Exercise the local installer with disposable inventories and harmless plays."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'odev_local_playbook', ROOT / 'plugins/action/odev_local_playbook.py')
plugin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plugin)


class LocalInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='odev-local-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        collection = self.root / 'ansible_collections/oreol/mgmt'
        collection.parent.mkdir(parents=True)
        collection.symlink_to(ROOT, target_is_directory=True)
        self.checkout = self.root / 'CLI checkout with spaces'
        self.checkout.mkdir()
        self.marker = self.root / 'selected'
        self.inventory = self.root / 'hosts'
        self.inventory.write_text('[servers]\nselected ansible_connection=local\nexcluded ansible_connection=local\n')
        self.variables = self.root / 'group_vars/all/main.yml'
        self.variables.parent.mkdir(parents=True)
        self.configure({'cli': {'local_path': str(self.checkout)}})
        # A relative vars_file proves execution uses the checkout's playbook.
        (self.checkout / 'vars.yml').write_text('checkout_marker: developer-source\n')
        (self.checkout / 'install.yml').write_text(yaml.safe_dump([{
            'hosts': 'all', 'gather_facts': False, 'vars_files': ['vars.yml'],
            'tasks': [
                {'ansible.builtin.assert': {'that': [
                    "inventory_hostname == 'selected'", 'main | bool',
                    'src | bool', 'booking | bool',
                    "checkout_marker == 'developer-source'",
                    'cli.local_path == ' + repr(str(self.checkout)),
                ]}},
                {'ansible.builtin.copy': {'content': 'local source', 'dest': str(self.marker)}},
            ],
        }], sort_keys=False))
        config = self.root / 'ansible.cfg'
        config.write_text('[defaults]\nretry_files_enabled = False\n')
        self.env = dict(os.environ, ANSIBLE_COLLECTIONS_PATH=str(self.root),
                        ANSIBLE_CONFIG=str(config), ANSIBLE_NOCOLOR='1')

    def configure(self, values):
        self.variables.write_text(yaml.safe_dump(values))

    def run_play(self, *extra):
        return subprocess.run([
            sys.executable, '-m', 'ansible.cli.playbook',
            'oreol.mgmt.odev_install_local', '-i', str(self.inventory),
            '--limit', 'selected', '-e', 'oreol_target=servers',
            '-e', 'main=true src=true booking=true', *extra,
        ], env=self.env, text=True, capture_output=True, timeout=30)

    def test_inventory_flags_checkout_and_target_are_preserved(self):
        result = self.run_play()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.marker.read_text(), 'local source')
        self.assertNotIn('excluded :', result.stdout)

    def test_check_mode_is_forwarded_and_does_not_write(self):
        result = self.run_play('--check', '--diff')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(self.marker.exists())

    def test_missing_empty_whitespace_and_invalid_paths_fail_before_execution(self):
        for config in ({}, {'cli': {}}, {'cli': {'local_path': ''}},
                       {'cli': {'local_path': '   '}},
                       {'cli': {'local_path': str(self.root / 'missing')}},
                       {'cli': {'local_path': str(self.root)}}):
            with self.subTest(config=config):
                self.configure(config)
                result = self.run_play()
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertFalse(self.marker.exists())

    def test_repo_installation_is_rejected(self):
        result = self.run_play('-e', 'repo=true')
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn('does not support repo=true', result.stdout)
        self.assertFalse(self.marker.exists())

    def test_child_failure_is_propagated(self):
        (self.checkout / 'install.yml').write_text(yaml.safe_dump([{
            'hosts': 'all', 'gather_facts': False,
            'tasks': [{'ansible.builtin.fail': {'msg': 'developer playbook failure'}}],
        }]))
        result = self.run_play()
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn('developer playbook failure', result.stdout)

    def test_all_hosts_validate_before_any_installation(self):
        host_vars = self.root / 'host_vars'
        host_vars.mkdir()
        (host_vars / 'excluded.yml').write_text('cli:\n  local_path: ""\n')
        result = self.run_play('--limit', 'servers')
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse(self.marker.exists())

    def test_arguments_preserve_options_and_narrow_limit(self):
        args = ['wrapper.yml', '-i', 'hosts', '-e', 'main=true', '--check', '--', 'unused']
        forwarded = plugin.playbook_arguments(args, ['wrapper.yml'], '/local/install.yml', 'node')
        self.assertEqual(forwarded, ['/local/install.yml', '-i', 'hosts', '-e',
                                    'main=true', '--check', '--limit', 'node', '--', 'unused'])
        self.assertEqual(args[0], 'wrapper.yml')


if __name__ == '__main__':
    unittest.main()
