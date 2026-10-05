# Passwordless sudo group

Create the `passwordless-sudo` group, add existing users from the cluster CMDB variables, and configure its members to run commands through sudo without a password.

## Requirements

Linux hosts with `getent`, `gpasswd`, sudo, and `visudo` installed, and an existing `/etc/sudoers.d` directory included by the system sudo configuration. Run with root privileges, either by connecting as root or using privilege escalation.

## Variables

- `users.passwordless_sudo` (default: empty): a list of `{name, state}` entries for existing users. Missing users are reported and skipped; the role does not create them.

Example cluster inventory variables:

```yaml
users:
  passwordless_sudo:
    - name: example_user
      state: present
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


## Sudo configuration

The role writes `/etc/sudoers.d/passwordless-sudo`, owned by root with mode `0440`, and validates it with `visudo` before installation:

```sudoers
%passwordless-sudo ALL=(ALL) NOPASSWD:ALL
```

## License

MIT, as specified in the collection's LICENSE file.

Entries require `name` and `state: present` or `state: absent`; plain usernames
are not supported. Present adds supplementary membership; absent removes only
that membership, preserving the account and its other groups. Primary group
membership is not managed. Omitted users are preserved.
See `defaults/main.yml` for inventory examples and the empty-list fallback.
