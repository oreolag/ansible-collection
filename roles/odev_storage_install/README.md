# odev_storage_install

Configure a declared Linux storage server using its share types in the CMDB.
Version one supports only `type: nfs` and rejects other types before making
changes. NFS tasks live in `tasks/nfs.yml`.

Configure a declared Linux NFS storage server (Ubuntu/Debian package and service
names). This role is independent of Incus. The collection reads configuration from the calling inventory’s `cmdb` directory.
Run from your management repository after updating its installed collection:

```bash
./ansible-play.sh odev_storage odev-storage-01
```

The playbook checks every selected inventory name against `cmdb/storage.yml`
before running the role. Undeclared or duplicate server names fail before
installation. The role repeats the authorization check and verifies the actual
hostname and storage IPv4 before making changes. The role also validates shares
and client assignments before installation.

Client access is derived from each `cmdb/*.yml` file's `storage.mounts`. Only
machines referencing the server and share with `state: present` are authorized.
Every assignment requires `state: present` or `state: absent`. Absent assignments
are excluded from exports; shares with no present clients are not exported.
Applying this server role reconciles export authorization; client unmounting
will be handled by the forthcoming `odev_storage_mount` role. Shared data is
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

## Playbook structure

`odev_storage` is the public wrapper playbook. It currently imports
`odev_storage_install`, which applies this role. Server installation can also
be run independently:

```bash
./ansible-play.sh odev_storage_install odev-storage-01
```

The planned client role/playbook is `odev_storage_mount`. It is not implemented
or called yet. When added, the wrapper will orchestrate separate server and
client plays in that order, selecting hosts from their CMDB declarations.
The existing rejection of client targets during installation is preserved;
passing `odev-01` does not configure it as a server or mount storage.
