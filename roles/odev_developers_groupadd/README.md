# odev-developers group

Create the `odev-developers` group and add existing users from the cluster CMDB variables.

## Requirements

Linux hosts with `getent` and `gpasswd` installed. Run with root privileges, either by connecting as root or using privilege escalation.

## Variables

- `users.odev_developers` (required): a list of existing usernames. Missing users are reported and skipped.
- `update` (default: `false`): preserve existing group members and add the listed users. When true, clear supplementary group membership first, then add the listed users that exist. An empty list with `update: true` clears supplementary membership.

Example inventory variables:

```yaml
users:
  odev_developers:
    - example_user
update: false
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

Append `-e update=true` to clear membership before adding CMDB users. The reset is not atomic: a failure after clearing membership can leave the group empty or partially populated.

The tasks are copied unchanged from `ansible-playbooks/tasks/odev-developers-groupadd.yml`, including the commented-out sudo configuration. This role does not configure sudo permissions.

## License

MIT, as specified in the collection's LICENSE file.
