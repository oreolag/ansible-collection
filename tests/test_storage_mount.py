"""Offline client CMDB validation: no live mounts or package changes."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
ROLE = ROOT / 'roles/odev_storage_mount'

class StorageMountTests(unittest.TestCase):
    def run_case(self, assignments=None, share_state='present', file_present=True):
        with tempfile.TemporaryDirectory(prefix='mount-test-', dir='/tmp') as d:
            root=Path(d)
            roles=root/'roles'
            shutil.copytree(ROLE, roles/'odev_storage_mount')
            configure=roles/'odev_storage_mount/tasks/configure.yml'
            tasks=yaml.safe_load(configure.read_text())
            # Run the real preflight, replacing only host operations with an
            # assertion that the real resolver produced the expected entries.
            stop=next(i for i,t in enumerate(tasks) if t['name']=='Gather client identity and virtualization facts')
            tasks=tasks[:stop]+[{'name':'Verify resolved assignments','ansible.builtin.assert':{'that':['odev_storage_mount_resolved | length == expected_count',"odev_storage_mount_resolved[0].source == '192.0.2.10:/exports/scratch'"]}}]
            configure.write_text(yaml.safe_dump(tasks,sort_keys=False))
            (root/'cmdb').mkdir()
            if file_present:
                machine={} if assignments is None else {'storage':{'mounts':assignments}}
                (root/'cmdb/client.yml').write_text(yaml.safe_dump(machine))
            catalogue={'servers':[{'name':'storage-01','ip':'192.0.2.10','shares':{'scratch':{'state':share_state,'type':'nfs','export':'/exports/scratch'}}}]}
            (root/'cmdb/storage.yml').write_text(yaml.safe_dump(catalogue))
            (root/'ansible.cfg').write_text('[defaults]\nroles_path=./roles\n')
            # No usable connection: all preflight must run locally without SSH.
            (root/'hosts').write_text('client ansible_connection=local\n')
            (root/'play.yml').write_text('- hosts: all\n  gather_facts: false\n  roles:\n    - odev_storage_mount\n')
            (root/'vars.json').write_text(json.dumps({'expected_count':len(assignments or [])}))
            run=subprocess.run(['ansible-playbook','-i','hosts','play.yml','-e','@vars.json'],cwd=root,env=dict(os.environ,ANSIBLE_CONFIG=str(root/'ansible.cfg'),ANSIBLE_LOCAL_TEMP=str(root/'tmp')),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            return run

    def entry(self, **changes):
        result={'server':'storage-01','share':'scratch','mount_path':'/scratch','state':'present'}
        result.update(changes)
        return result

    def test_no_assignments_do_nothing(self):
        for assignments,file_present in [(None,False),(None,True),([],True)]:
            r=self.run_case(assignments,file_present=file_present)
            self.assertEqual(r.returncode,0,r.stdout)
            self.assertIn('changed=0',r.stdout)

    def test_present_and_absent_resolve(self):
        for mount_state,share_state in [('present','present'),('absent','present'),('absent','absent')]:
            r=self.run_case([self.entry(state=mount_state)],share_state=share_state)
            self.assertEqual(r.returncode,0,r.stdout)

    def test_invalid_configuration_is_rejected(self):
        cases=[([self.entry()], 'absent'),([self.entry(server='unknown')],'present'),([self.entry(share='unknown')],'present'),([self.entry(),self.entry()],'present'),([self.entry(state='invalid')],'present'),([self.entry(mount_path='/')],'present'),([self.entry(mount_path='/scratch/../home')],'present')]
        for mounts,state in cases:
            with self.subTest(mounts=mounts,state=state):
                r=self.run_case(mounts,share_state=state)
                self.assertEqual(r.returncode,2,r.stdout)
                self.assertIn('changed=0',r.stdout)

    def test_removal_preserves_directories(self):
        tasks=yaml.safe_load((ROLE/'tasks/configure.yml').read_text())
        mount_states=[task['ansible.posix.mount']['state'] for task in tasks if 'ansible.posix.mount' in task]
        self.assertEqual(mount_states,['unmounted','absent_from_fstab','mounted'])
        self.assertFalse(any(task.get('ansible.builtin.file',{}).get('state')=='absent' for task in tasks))

if __name__=='__main__': unittest.main()
