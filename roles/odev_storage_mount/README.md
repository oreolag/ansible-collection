# odev_storage_mount

Mount named NFS shares on Ubuntu/Debian VMs or physical servers. Containers are
rejected. This role is independent of Incus and does not change Tailscale SSH.

```bash
./ansible-play.sh odev_storage_mount incus_instances
```

Read `cmdb/<inventory short hostname>.yml` beside the inventory:

```yaml
storage:
  mounts:
    - server: odev-storage-01
      share: scratch
      state: present
    - server: odev-storage-01
      share: scratch_2
      state: present
```

The storage catalogue contains a server-level `path` and a list of named shares;
see `../odev_storage_present/README.md`. Given `path: /exports`, the source is
`10.42.30.172:/exports/scratch` and the destination is `/scratch` automatically.
Users see `/scratch/<username>`, not `/scratch/scratch/<username>`. No
`mount_path` is accepted. Different servers' shares with the same name collide
at the client and are rejected; they cannot both mount at `/scratch`.

Missing machine CMDB files, omitted storage sections and empty mount lists are
skipped without packages or mount changes. Malformed assignments, duplicate
paths, unknown/duplicate references, unsupported types and present mounts of
absent shares fail before changes. The real hostname is verified. Existing live
and fstab entries must match the declared source; unrelated filesystems are
never replaced or unmounted. Retain the old endpoint details until removal.

Before attaching present mounts, verify present `users.login` accounts have the
same UID/primary GID on client and storage servers. Accounts must already exist,
and the management inventory must include their servers. The identity check
uses the storage role's shared read-only tasks; it never changes accounts.

Present installs `nfs-common`, mounts with `rw,hard,_netdev,vers=4` and persists
in `/etc/fstab`. Absent unmounts normally and removes the fstab entry, preserving
directories and shared contents. Busy mounts fail; there is no forced unmount.
Omitting an assignment leaves existing mounts unchanged. State is required.

Configure exports first with `odev_storage_present`; unmount clients before
withdrawing exports. These are two explicit playbooks, without an install
wrapper. No quotas or user creation are performed by this role. Private user
directories are created by `odev_storage_present` from `users.login`.

Verify as a regular user after installing the updated collection and migrating
the CMDB schema:

```bash
findmnt /scratch
grep ' /scratch ' /etc/fstab
cd /scratch/"$USER"
touch test-file
```

The user directory must be writable by its owner and inaccessible to other
ordinary users. Check mode inspects existing mounts and predicts changes, but
does not actually attach shares or verify NFS connectivity.
