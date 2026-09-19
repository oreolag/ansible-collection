# Login users

Create the users listed in `users.login`, with home directories and `/bin/bash`
as their shell. Install their SSH public keys when provided. Existing authorized
keys are preserved, and users omitted from the list are not removed.

## Requirements

Linux hosts with Bash installed. Run with root privileges, either by connecting
as root or using privilege escalation. The collection depends on `ansible.posix`
for its `authorized_key` module.

## Variables and keys

Add `login` to the existing `users` mapping in your administration repository's
`group_vars/all.yml`:

```yaml
users:
  login:
    - example_user
```

An absent or empty `users.login` list performs no work.

Optionally put each user's public key in `keys/<username>.pub` beside the
inventory file, for example `mgmt/keys/example_user.pub`. Files are read on the
controller using `inventory_dir`, not from the installed collection. Missing or
empty key files are skipped; the user is still created.

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

## License

MIT, as specified in the collection's LICENSE file.
