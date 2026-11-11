# odev_storage_present

Configure a declared Linux storage server using its share types in the CMDB.
Version one supports only `type: nfs` and rejects other types before making
changes. NFS tasks live in `tasks/nfs.yml`.

Configure a declared Linux NFS storage server (Ubuntu/Debian package and service
names). This role is independent of Incus. The collection reads configuration from the calling inventory’s `cmdb` directory.
Run from your management repository after updating its installed collection:

```bash
./ansible-play.sh odev_storage_present odev-storage-01
```

The playbook accepts mixed inventory groups. Machines not listed as storage
servers in `cmdb/storage.yml` are skipped without gathering facts, connecting to
them or changing packages/services. An empty `servers: []` skips all targets.
Duplicate matching declarations fail before any server changes. Declared servers
still undergo configuration, actual hostname and storage-IP validation before
changes. Unsupported types, invalid states and contradictory client assignments
fail rather than being skipped. The same selection behavior applies when the
role is invoked directly.

```bash
./ansible-play.sh odev_storage_present incus_instances
./ansible-play.sh odev_storage_mount incus_instances
```

Both storage playbooks can use ordinary SSH over Tailscale addresses. They do
not disable Tailscale SSH. The OpenSSH-only management route used for booking
enforcement is not required by storage. Connectivity and sudo access are still
required on machines with applicable declarations.

Client access is derived from each `cmdb/*.yml` file's `storage.mounts`. Only
machines referencing the server and share with `state: present` are authorized.
Every assignment requires `state: present` or `state: absent`. Absent assignments
are excluded from exports; shares with no present clients are not exported.
Applying this server role reconciles export authorization; client unmounting
is handled by the separate `odev_storage_mount` role. Shared data is
never deleted by changing an assignment state. Version one uses the
first management interface's first access IPv4 (`devices.enmgmt[0].access[0]`).
These addresses must be the actual source addresses clients use to reach NFS.
The inventory must provide a working SSH management connection to the server.
Keep its connection address consistent with `cmdb/storage.yml` and use a stable
storage service IP. Provisioning and address reservations are cluster-specific.

The role installs `nfs-kernel-server`, creates export directories, writes
`/etc/exports.d/odev.exports`, enables the service and reloads exports when changed.
Existing exports outside this file are preserved. Options are
`rw,sync,no_subtree_check,root_squash`; the export is not open to all hosts.
The playbook displays `exportfs -v` after applying changes.

## Verify on the storage server

Connect from your management machine:

```bash
ssh -J javier@minix-ngc-de-javier javier@10.42.30.172
```

Then check:

```bash
systemctl is-active nfs-kernel-server
sudo exportfs -v
cat /proc/fs/nfsd/versions
sudo ss -lnt 'sport = :2049'
```

Expect an active service, `/exports/scratch` exported to the assigned client IPs,
NFSv4 enabled (`+4`, possibly `+4.1` and `+4.2`), and a TCP listener on port 2049.
A fresh read-only mount on an authorized Linux VM/physical client is the end-to-end
test (requires `nfs-common` on that client):

```bash
sudo mkdir -p /mnt/nfs-check
sudo mount -t nfs -o ro,vers=4 10.42.30.172:/exports/scratch /mnt/nfs-check
findmnt /mnt/nfs-check
ls -la /mnt/nfs-check
sudo umount /mnt/nfs-check
```

This is a temporary verification mount, not the eventual managed `/scratch` mount.
Unprivileged containers require a different attachment mechanism; do not use them
for this direct-mount test. Firewall policy must permit authorized clients to
reach TCP 2049. This role does not change firewall rules.

## Version one scope

Directories are root-owned with mode 0755, allowing read verification without
world-writable storage. User directories, consistent UID/GID values and write
permissions are separate work. No quotas, client mounts, disk formatting or data
volume are configured. Until a data volume is attached, the export uses the
server's existing root filesystem and deleting the VM deletes that data.
The role does not delete exported data when configuration changes.

## Playbook structure and share lifecycle

Use two explicit playbooks, each calling its matching role:

```bash
./ansible-play.sh odev_storage_present odev-storage-01
./ansible-play.sh odev_storage_mount 'odev-development-01:odev-development-02'
```

There is no storage installation wrapper. Configure server exports before
mounting clients; unmount clients before withdrawing exports.

Every share requires explicit `state: present` or `state: absent`:

```yaml
servers:
  - name: storage-01
    ip: 192.0.2.10
    shares:
      scratch:
        type: nfs
        export: /exports/scratch
        state: present
```

Present shares are configured and exported to clients with present assignments.
Absent shares are omitted from the managed export file on reconciliation; their
directories and contents are never removed. The NFS service remains installed
and running. All shares must retain a valid type and export path even when absent.
A present client assignment referencing an absent share fails before installation
or export changes. Absent client assignments are not granted export access.

For retirement, mark the client assignments absent and run `odev_storage_mount`
on all affected clients before withdrawing the server export with this playbook.
This server role does not unmount clients. For installation, configure servers
first, then run `odev_storage_mount` on the selected clients. Omitting a server does not remove its existing setup;
targeting an omitted server skips it without changing its existing setup.
