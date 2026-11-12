"""Exercise private directories and UID/GID guards using local temporary fixtures."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import yaml
from jinja2 import Environment, StrictUndefined

ROOT=Path(__file__).resolve().parents[1]
ROLE=ROOT/'roles/odev_storage_present'

class StorageUsersTests(unittest.TestCase):
    def invoke(self, root, play, variables):
        (root/'play.yml').write_text(yaml.safe_dump(play,sort_keys=False))
        (root/'vars.json').write_text(json.dumps(variables))
        (root/'hosts').write_text('storage-01 ansible_connection=local\npeer-01 ansible_connection=local\n')
        (root/'ansible.cfg').write_text('[defaults]\n')
        return subprocess.run(['ansible-playbook','-i','hosts','play.yml','-e','@vars.json'],cwd=root,env=dict(os.environ,ANSIBLE_CONFIG=str(root/'ansible.cfg'),ANSIBLE_LOCAL_TEMP=str(root/'tmp')),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)

    def identity_case(self, peer_uid=1001, peer_gid=1001):
        with tempfile.TemporaryDirectory(prefix='storage-users-',dir='/tmp') as d:
            root=Path(d)
            for name in ('identities.yml','identity_peer.yml'):
                shutil.copy2(ROLE/'tasks'/name, root/name)
            # Only the peer's read command is replaced; resolution and comparisons
            # are the real tasks. No real accounts or SSH connections are used.
            peer=yaml.safe_load((root/'identity_peer.yml').read_text())
            for task in peer:
                if task['name']=='Read peer login account identities':
                    task['ansible.builtin.command']['argv']=['getent','--peer','{{ item.item.name }}']
            (root/'identity_peer.yml').write_text(yaml.safe_dump(peer,sort_keys=False))
            binary=root/'bin';binary.mkdir()
            getent=binary/'getent'
            getent.write_text('#!/bin/sh\nif [ "$1" = "--peer" ]; then uid=PEER_UID; gid=PEER_GID; else uid=1001; gid=1001; fi\nprintf "%s:x:%s:%s::/home/%s:/bin/bash\\n" "$2" "$uid" "$gid" "$2"\n'.replace('PEER_UID',str(peer_uid)).replace('PEER_GID',str(peer_gid)))
            getent.chmod(0o755)
            # The read commands need no root privilege in this offline fixture.
            peer=yaml.safe_load((root/'identity_peer.yml').read_text())
            for task in peer:
                if task['name']=='Read peer login account identities': task['become']=False
            (root/'identity_peer.yml').write_text(yaml.safe_dump(peer,sort_keys=False))
            play=[{'hosts':'storage-01','gather_facts':False,'environment':{'PATH':str(binary)+os.pathsep+os.environ['PATH']},'tasks':[{'ansible.builtin.include_tasks':'identities.yml'}]}]
            return self.invoke(root,play,{'users':{'login':[{'name':'alice','state':'present'},{'name':'former','state':'absent'}]},'odev_storage_identity_peer_names':['peer-01']})

    def test_matching_numeric_identities(self):
        result=self.identity_case()
        self.assertEqual(result.returncode,0,result.stdout)
        self.assertNotIn('item=former',result.stdout.split('Read existing present login users')[1])

    def test_uid_and_gid_mismatches_fail_without_changes(self):
        for uid,gid in [(1002,1001),(1001,1002)]:
            result=self.identity_case(uid,gid)
            self.assertEqual(result.returncode,2,result.stdout)
            self.assertIn('UID/GID mismatch',result.stdout)
            self.assertIn('changed=0',result.stdout)

    def test_private_directories_for_present_shares_only_and_no_data_deletion(self):
        tasks=yaml.safe_load((ROLE/'tasks/nfs.yml').read_text())
        create=next(t for t in tasks if t['name']=='Create private login user directories on each present share')
        with tempfile.TemporaryDirectory(prefix='storage-directory-',dir='/tmp') as d:
            root=Path(d); base=root/'exports';base.mkdir()
            old=base/'retired/alice';old.mkdir(parents=True);(old/'keep').write_text('data')
            config={'path':str(base),'shares':[{'name':'scratch','state':'present'},{'name':'retired','state':'absent'}]}
            account={'item':{'name':'alice','state':'present'},'stdout':f'alice:x:{os.getuid()}:{os.getgid()}::/home/alice:/bin/bash'}
            play=[{'hosts':'storage-01','gather_facts':False,'tasks':[create]}]
            variables={'odev_storage_present_config':config,'odev_storage_identity_accounts':{'results':[account]}}
            result=self.invoke(root,play,variables)
            self.assertEqual(result.returncode,0,result.stdout)
            directory=base/'scratch/alice'
            self.assertEqual(directory.stat().st_mode & 0o777,0o700)
            self.assertEqual(directory.stat().st_uid,os.getuid())
            self.assertEqual(directory.stat().st_gid,os.getgid())
            self.assertEqual((old/'keep').read_text(),'data')
            result=self.invoke(root,play,variables)
            self.assertEqual(result.returncode,0,result.stdout)
            self.assertIn('changed=0',result.stdout)

    def test_server_resolves_named_client_shares_and_management_host(self):
        with tempfile.TemporaryDirectory(prefix='storage-client-',dir='/tmp') as d:
            root=Path(d)
            client={'storage':{'mounts':[{'server':'storage-01','share':'scratch','state':'present'}]},'devices':{'enmgmt':[{'access':[{'ip_address':'192.0.2.20'}]}]}}
            (root/'client-01.yml').write_text(yaml.safe_dump(client))
            config={'name':'storage-01','path':'/exports','shares':[{'name':'scratch','type':'nfs','state':'present'}]}
            play=[{'hosts':'storage-01','gather_facts':False,'tasks':[{'ansible.builtin.set_fact':{'odev_storage_present_clients':[]}},{'ansible.builtin.include_tasks':str(ROLE/'tasks/client.yml')},{'ansible.builtin.assert':{'that':["odev_storage_present_clients == [{'share':'scratch','ip':'192.0.2.20','host':'client-01'}]"]}}]}]
            variables={'odev_storage_present_config':config,'odev_storage_present_client_file':str(root/'client-01.yml')}
            result=self.invoke(root,play,variables)
            self.assertEqual(result.returncode,0,result.stdout)
            config['shares'][0]['state']='absent'
            result=self.invoke(root,play,variables)
            self.assertEqual(result.returncode,2,result.stdout)
            self.assertIn('changed=0',result.stdout)

    def test_derived_exports_and_absent_share(self):
        template=Environment(undefined=StrictUndefined).from_string((ROLE/'templates/shares.exports.j2').read_text())
        config={'path':'/exports','shares':[{'name':'scratch','state':'present'},{'name':'scratch_2','state':'present'},{'name':'retired','state':'absent'}]}
        clients=[{'share':name,'ip':'192.0.2.20'} for name in ('scratch','scratch_2','retired')]
        output=template.render(odev_storage_present_config=config,odev_storage_present_clients=clients)
        self.assertIn('/exports/scratch 192.0.2.20(',output)
        self.assertIn('/exports/scratch_2 192.0.2.20(',output)
        self.assertNotIn('/exports/retired',output)

if __name__=='__main__': unittest.main()
