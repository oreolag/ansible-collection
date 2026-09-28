# Copy CMDB data

Copy CMDB files using the original `cmdb-copy` workflow, clearing the destination first.
Keep the source `cmdb/` directory beside your inventory in `mgmt`, including a
`<inventory_hostname_short>.yml` file for each target host.

Set the destination in `group_vars/all.yml`:

```yaml
cmdb:
  remote_path: /opt
```

With the updated collection installed, run from `mgmt`:

```bash
./ansible-play.sh cmdb_copy <inventory_group>
```

The role deletes `/opt/cmdb` and all its contents, recreates it, copies the full
CMDB directory there, removes the
current host's file from that directory, and copies that file to
`/opt/<inventory_hostname_short>.yml` instead. A missing source file fails the
copy, as in the original implementation. Files outside `/opt/cmdb` are not purged.

The runner supplies the inventory and `oreol_target`. Privilege escalation
settings come from your inventory. The source paths use `inventory_dir` so the
data comes from `mgmt`, rather than the installed collection.
