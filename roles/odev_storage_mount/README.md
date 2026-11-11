# odev_storage_mount

Mount NFS shares directly on Ubuntu/Debian VMs and physical servers. No Incus
host-specific configuration is performed; containers are rejected.

Run from the management repository after updating the installed collection:

```bash
./ansible-play.sh odev_storage_mount 'odev-development-01:odev-development-02'
```

The role reads `cmdb/<inventory short hostname>.yml` beside the inventory. A
missing file, omitted `storage` section or empty `storage.mounts` does nothing:
no package installation, mount changes or fact-gathering connection is needed.
Malformed configuration fails rather than being silently skipped.

```yaml
storage:
  mounts:
    - server: odev-storage-01
      share: scratch
      mount_path: /scratch
      state: present
```

Assignments resolve against `cmdb/storage.yml`. State is mandatory on both
shares and mounts. Present mounts require present shares. Duplicate paths,
unknown/duplicate servers, unknown shares, unsupported types and invalid paths
fail before package or mount changes on the machine. An actual hostname check
prevents applying another machine's configuration. Existing live and fstab
entries must match the declared NFS source; unrelated filesystems are not
replaced or unmounted. Keep old source details until an absent mount is removed.

Present installs `nfs-common` and mounts with `rw,hard,_netdev,vers=4`, persisting
in `/etc/fstab`. NFS permission/UID/GID policy still determines write access.
Absent unmounts normally (busy mounts fail), then removes the fstab entry using
`absent_from_fstab`. It preserves the directory and shared contents. No force
unmount or deletion is used. Omitting an assignment leaves existing mounts
unchanged. Changing a source at the same path requires explicit removal first.

Server exports must be configured first. For retirement, run client unmounts
before withdrawing exports. Use `odev_storage_present` for server exports and
`odev_storage_mount` for clients. These are two explicit playbooks with no wrapper. Never retire
an export while clients still use it. The server may be absent in the catalogue
state during client removal, but retain its endpoint and share path.

Verify on a client:

```bash
findmnt /scratch
grep ' /scratch ' /etc/fstab
ls -la /scratch
```

A shared test file readable from both VMs verifies end-to-end access. This role
does not create user directories, quotas or grant write permissions. In check
mode, existing mounts are inspected and module changes are predicted; mounts
are not actually attached. Check mode cannot verify NFS connectivity.
