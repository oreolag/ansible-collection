# odev_ssh_access

Enroll existing `odev-users` accounts for non-interactive SSH between the
selected servers. Run this from the management machine using its existing
trusted Ansible connection and privilege escalation.

```bash
ansible-playbook -i hosts oreol.mgmt.odev_ssh_access \
  -e oreol_target=odev
```

Replace `odev` with the inventory group for the complete SSH mesh. Each selected
account comes from `users.odev_users` with `state: present` and must exist and belong to `odev-users` on each selected host. The role
expects the default OpenSSH Ed25519 host key and default known-hosts and
authorized-keys paths. Use resolvable hostnames or addresses from the inventory.

Each account gets a dedicated private key that stays on its server. Peers
authorize the corresponding public key for normal commands as that same
account. Host trust comes from the host public keys read over the management
connection. Existing SSH entries outside the managed blocks are preserved.

Rerun against the complete group when adding servers. Runs replace the managed
peer entries on the selected servers for the selected accounts. To revoke
access from accounts or hosts no longer selected, also remove their managed
entries on those machines.

From an enrolled server, as an enrolled user, test with
`ssh -o BatchMode=yes peer-host true`, then run Ansible using your inventory.
