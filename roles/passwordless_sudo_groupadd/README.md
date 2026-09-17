# Passwordless sudo group

Create the `passwordless-sudo` group, add existing users from the cluster CMDB variables, and configure its members to run commands through sudo without a password.

## Requirements

Linux hosts with `getent`, `gpasswd`, sudo, and `visudo` installed, and an existing `/etc/sudoers.d` directory included by the system sudo configuration. Run with root privileges, either by connecting as root or using privilege escalation.

## Variables

- `users.passwordless_sudo` (required): a list of existing usernames. Missing users are reported and skipped; the role does not create them.
- `update` (default: `false`): when false, preserve existing group members and add the listed users. When true, clear supplementary group membership first, then add the listed users that exist. An empty list with `update: true` clears supplementary membership.

Example cluster inventory variables:

```yaml
users:
  passwordless_sudo:
    - example_user
update: false
```

## Usage

```yaml
---
- name: Configure passwordless sudo
  hosts: managed_hosts
  become: true
  roles:
    - oreol.mgmt.passwordless_sudo_groupadd
```

Or invoke the collection playbook with your inventory:

```bash
ansible-playbook oreol.mgmt.passwordless_sudo_groupadd -i hosts -e oreol_target=managed_hosts
```

Append `-e update=true` to clear membership before adding CMDB users. The reset is not atomic: a failure after clearing membership can leave the group empty or partially populated.

## Sudo configuration

The role writes `/etc/sudoers.d/passwordless-sudo`, owned by root with mode `0440`, and validates it with `visudo` before installation:

```sudoers
%passwordless-sudo ALL=(ALL) NOPASSWD:ALL
```

## License

MIT, as specified in the collection's LICENSE file.
