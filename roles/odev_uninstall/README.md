# odev_uninstall

Remove the CLI and its system integration from selected Linux machines. This is
a generic collection role/playbook, independent of Incus and storage roles.

```bash
./ansible-play.sh odev_uninstall odev_storage_servers --check
./ansible-play.sh odev_uninstall odev_storage_servers
```

Use root or an administrator with sudo access independent of the CLI sudoers
rules. Current SSH sessions may retain old PATH/environment values; open a new
session after uninstall. The role is rerunnable. It never uninstalls packages.

## Removed

- `/opt/odev`, `/opt/odev_login.sh` and `/opt/odev_banner.sh`.
- CLI PATH/login files in `/etc/profile.d`, the exact installed ODEV_PATH line
  in `/etc/bash.bashrc`, and the `odev` bash completion file.
- CLI sudoers files `odev-users`, `odev-developers` and `odev-admins`.
- Booking daemon, expiry service/timer and old configuration service/timer units
  installed by the CLI. Stop/disable them before deleting unit files.
- Unused booking-access configuration and booking runtime directory.
- The three groups `odev-users`, `odev-developers`, `odev-admins`, including their
  supplementary memberships. Accounts themselves are not removed.

`odev_uninstall_prefix` defaults to `/opt`; it controls only known CLI paths
beneath that directory. The prefix directory itself is never removed. Symlinked
CLI installations are refused for inspection. CLI-owned paths are treated as
installation artifacts; preserve any custom work inside them before uninstall.

## Preserved

Login accounts and primary groups, home directories, user SSH keys and peer SSH
configuration, Tailscale, management sudo policy, NFS packages/services/exports,
shared directories/data, mounts/fstab, `/opt/mgmt`, CMDB files, booking inventories,
booking databases and booking service accounts/groups remain. No recursive
ownership changes or automatic user/GID renumbering occur.

## Read-only checks before removal

- Refuse if controller or installed booking inventory still lists this host as
  a booking server or managed booking host.
- Refuse if PAM admission, a booking endpoint or forced booking-lookup SSH command
  still depends on the CLI. Decommission that booking integration separately.
- Refuse if a group to be removed is any account's primary group.
- Refuse if any retained path is owned by a group to be removed. The ownership
  scan includes home and shared filesystems; only known removal paths and virtual
  `/proc`, `/sys`, `/dev` trees are excluded. Inaccessible paths cause failure,
  not an assumption that removal is safe. Large filesystems may take time to scan.

These checks run in check mode too. No removal starts on the host until they
pass. The role stops rather than silently keeping groups when a dependency is
found; resolve the reported path/account explicitly and rerun. Booking service
accounts stay because they may own retained databases, but unused supplementary
membership in the deleted odev groups disappears with group deletion.

This role is a correction/retirement operation; it is not a fresh-install step.
