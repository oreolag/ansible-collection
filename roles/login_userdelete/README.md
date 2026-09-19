# Delete login users

Delete accounts listed in `users.login_deleted`, including their home directories
and mail spools. This preserves the original `login-userdelete` behavior.
Files owned by these users elsewhere on the server are not automatically removed.

## Variables

Add `login_deleted` to the existing `users` mapping in your administration
repository's `group_vars/all.yml`:

```yaml
users:
  login_deleted:
    - former_user
```

An absent or empty list performs no work. No matching public-key file is required.
Remove these usernames from `users.login` to prevent a later `login_useradd` run
from recreating them. Also remove them from any group membership lists.

## Usage

With the updated collection installed, run from `mgmt`:

```bash
./ansible-play.sh login_userdelete <inventory_group>
```

The existing runner supplies the inventory, host limit, and `oreol_target`.
Run with root privileges; connection and privilege escalation settings come from
your inventory. This deletes accounts and their home directories, rather than
just removing one SSH key from an account.

Or invoke the collection playbook directly:

```bash
ansible-playbook oreol.mgmt.login_userdelete -i hosts -e oreol_target=managed_hosts
```

Removing a name from `users.login` or deleting its public-key file alone does not
delete the remote account. Only names explicitly listed in `users.login_deleted`
are selected for deletion.

## License

MIT, as specified in the collection's LICENSE file.
