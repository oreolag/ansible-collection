# odev-developers group

Create the `odev-developers` group and add existing users from the cluster CMDB variables.

## Requirements

Linux hosts with `getent` and `gpasswd` installed. Run with root privileges, either by connecting as root or using privilege escalation.

## Variables

- `users.odev_developers` (default: empty): a list of `{name, state}` entries for existing users. Missing users are reported and skipped.

Example inventory variables:

```yaml
users:
  odev_developers:
    - name: example_user
      state: present
```

## Usage

```yaml
---
- name: Configure odev-developers group
  hosts: managed_hosts
  become: true
  roles:
    - oreol.mgmt.odev_developers_groupadd
```

Or invoke the collection playbook with your inventory:

```bash
ansible-playbook oreol.mgmt.odev_developers_groupadd -i hosts -e oreol_target=managed_hosts
```

Supply cluster variables through inventory or `-e @vars.yml`, and configure connection and privilege escalation settings in your inventory as needed.


This role does not configure sudo permissions.

## License

MIT, as specified in the collection's LICENSE file.

Entries require `name` and `state: present` or `state: absent`; plain usernames
are not supported. Present adds supplementary membership; absent removes only
that membership, preserving the account and its other groups. Primary group
membership is not managed. Omitted users are preserved.
See `defaults/main.yml` for inventory examples and the empty-list fallback.
