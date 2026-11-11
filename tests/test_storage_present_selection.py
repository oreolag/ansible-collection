"""Offline mixed-group selection tests; NFS backend is stubbed."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class StorageSelectionTests(unittest.TestCase):
    def run_case(self, servers):
        with tempfile.TemporaryDirectory(prefix='storage-selection-', dir='/tmp') as directory:
            root = Path(directory)
            role = root / 'roles/odev_storage_present'
            shutil.copytree(ROOT / 'roles/odev_storage_present', role)
            (role / 'tasks/nfs.yml').write_text('- name: Record selected backend\n  ansible.builtin.debug:\n    msg: "BACKEND {{ inventory_hostname }}"\n')
            (root / 'cmdb').mkdir()
            (root / 'cmdb/storage.yml').write_text(json.dumps({'servers': servers}))
            # No actual connection is usable: all selection runs locally.
            (root / 'hosts').write_text('storage-01 ansible_host=192.0.2.10\nclient-01 ansible_host=192.0.2.20\n')
            (root / 'ansible.cfg').write_text('[defaults]\nroles_path=./roles\n')
            play = (ROOT / 'playbooks/odev_storage_present.yml').read_text()
            (root / 'play.yml').write_text(play.replace('oreol.mgmt.odev_storage_present', 'odev_storage_present'))
            return subprocess.run(['ansible-playbook', '-i', 'hosts', 'play.yml', '-e', 'oreol_target=all'], cwd=root, env=dict(os.environ, ANSIBLE_CONFIG=str(root/'ansible.cfg'), ANSIBLE_LOCAL_TEMP=str(root/'tmp')), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def server(self, state='present'):
        return {'name':'storage-01','ip':'192.0.2.10','shares':{'scratch':{'type':'nfs','state':state,'export':'/exports/scratch'}}}

    def test_mixed_group_only_dispatches_declared_server(self):
        result = self.run_case([self.server()])
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('BACKEND storage-01', result.stdout)
        self.assertNotIn('BACKEND client-01', result.stdout)
        self.assertIn('unreachable=0', result.stdout)

    def test_empty_catalogue_skips_every_machine(self):
        result = self.run_case([])
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertNotIn('BACKEND ', result.stdout)
        self.assertIn('changed=0', result.stdout)

    def test_duplicate_server_stops_before_dispatch(self):
        result = self.run_case([self.server(), self.server()])
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertNotIn('BACKEND ', result.stdout)
        self.assertIn('changed=0', result.stdout)

    def test_invalid_declared_state_is_not_silently_skipped(self):
        result = self.run_case([self.server('invalid')])
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertNotIn('BACKEND ', result.stdout)
        self.assertIn('changed=0', result.stdout)

if __name__ == '__main__':
    unittest.main()
