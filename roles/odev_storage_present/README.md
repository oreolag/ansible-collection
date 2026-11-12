# odev_storage_present

Configure NFS services on existing Ubuntu/Debian storage servers, independent of
Incus. Read the catalogue beside the calling inventory:

```yaml
# cmdb/storage.yml
servers:
  - name: odev-storage-01
    ip: 10.42.30.172
    path: /exports
    shares:
      - name: scratch
        type: nfs
        state: present
      - name: scratch_2
        type: nfs
        state: present
```

```bash
./ansible-play.sh odev_storage_present incus_instances
```

Mixed groups are supported. Machines absent from the catalogue are skipped;
empty `servers: []` skips all. Duplicate server/share names, unsupported types,
invalid paths/states and contradictory client assignments fail before changes.
The actual hostname and storage IPv4 are verified before installation.

`path` is a normalized absolute base directory with no trailing slash. Share
names are letters followed by letters, digits, underscores or hyphens. Exports
are derived as `<path>/<share name>`; clients use `/<share name>`. There is no
per-share `export` or per-client `mount_path` configuration.

Client access comes from `storage.mounts` in machine CMDB files. Only present
assignments to present shares are authorized. Each client's first management
access IPv4 (`devices.enmgmt[0].access[0].ip_address`) must be its NFS source IP.
Exports use `rw,sync,no_subtree_check,root_squash` and are managed only in
`/etc/exports.d/odev.exports`. Other exports are preserved.

## Private user directories

Every present share gets one directory per present `users.login` entry. The
share root stays `root:root` mode 0755. For example, `/exports/scratch/jmoya82`
is owned by that existing user's numeric UID/primary GID, with mode 0700.
Through a client mount, the user accesses `/scratch/jmoya82`.

Run `login_useradd` first on storage servers and clients. Storage roles do not
create or renumber accounts. Before directory creation, the role verifies that
present login accounts exist with matching UID and primary GID across the
storage server and every declared present client. These clients must have a
usable management inventory entry (short name preferred, otherwise a unique
FQDN). Stale client CMDB assignments must be removed or marked absent. Identity
checks can contact peers outside the selected target group; all are read-only.
If IDs differ, the role stops before provisioning directories or changing exports.
Never renumber existing users without considering ownership of their files.

Empty/missing `users.login` creates no private directories. Absent users and
shares never cause deletion of stored directories/data. Directory ownership and
mode are reconciled without recursively changing file ownership. Standard NFS
AUTH_SYS assumes trusted client administrators; 0700 isolates ordinary users,
not privileged administrators on authorized clients. No quotas are configured.

## Lifecycle and verification

Run this playbook before `odev_storage_mount`. To retire a share, mark its mounts
absent and unmount all clients first, then mark the share absent and reconcile
exports. Absent shares retain their directory/data; NFS stays installed. Removing
an entry does not identify data for deletion. No wrapper playbook is required.

On the storage server:

```bash
systemctl is-active nfs-kernel-server
sudo exportfs -v
sudo ss -lnt 'sport = :2049'
sudo ls -ld /exports/scratch /exports/scratch/*
```

The service should be active, exports listed for the assigned IPs and TCP 2049
listening. The root filesystem backs these paths until a separate persistent
volume is configured; this role neither formats disks nor configures firewalls.

## Migrating the earlier schema

Add server `path: /exports`; replace the shares mapping with a list containing
`name`, `type` and `state`. Remove each explicit `export` field. Remove client
`mount_path` fields. If the derived paths match the existing paths, the mount
source and destination remain unchanged. The old schema is rejected rather
than silently mapped to a different location. Update the live inventory CMDB
before applying the new collection.
