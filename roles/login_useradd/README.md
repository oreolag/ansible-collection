# Login users

Create users marked `state: present` in `users.login` only when a matching, non-empty public-key
file exists. Create their home directories, set `/bin/bash` as their shell, and
install their SSH public keys. Existing authorized
keys are preserved, and users omitted from the list are not removed.

## Requirements

Linux hosts with Bash installed. Run with root privileges, either by connecting
as root or using privilege escalation. The collection depends on `ansible.posix`
for its `authorized_key` module.

## Variables and keys

Add `login` to the existing `users` mapping in your administration repository's
`group_vars/all/users.yml`:

```yaml
users:
  login:
    - name: example_user
      state: present
    - name: former_user
      state: absent
```

An absent or empty `users.login` list performs no work.

Put each user's public key in `keys/<username>.pub` beside the
inventory file, for example `mgmt/keys/example_user.pub`. Files are read on the
controller using `inventory_dir`, not from the installed collection. Missing or
empty key files for present entries cause the user to be reported and skipped: neither the account
nor its SSH keys are changed. Whitespace-only files are also treated as empty.

## Usage

After installing the updated collection in `mgmt`, use its existing runner:

```bash
./collections-update.sh
./ansible-play.sh login_useradd minix
```

The runner supplies the inventory, host limit, and required `oreol_target`.
Connection and privilege escalation settings come from your inventory.

Or invoke the collection playbook directly:

```bash
ansible-playbook oreol.mgmt.login_useradd -i hosts -e oreol_target=minix
```

The role can also be used in a larger playbook:

```yaml
---
- name: Configure login users
  hosts: managed_hosts
  become: true
  roles:
    - oreol.mgmt.login_useradd
```

## Removing users

This same role deletes accounts marked `state: absent` in `users.login`, including
their home directories and mail spools. No public key is required for deletion.
Files owned by these users elsewhere are not automatically removed.
Removing a name or public-key file from this role's inputs does not revoke
existing access.

## License

MIT, as specified in the collection's LICENSE file.

Entries require `name` and an explicit `state`; plain usernames are not supported.
The role processes both states in one run. See `defaults/main.yml` for examples.
