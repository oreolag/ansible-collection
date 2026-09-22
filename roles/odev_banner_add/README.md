# Oreol banner

Copy `odev_banner.sh` from beside your inventory to the remote server with
executable permissions (`0755`), matching the old `odev-banner-add` task.

In `mgmt/group_vars/all.yml`, set the existing destination directory:

```yaml
banner:
  remote_path: /opt
```

Keep the script at `mgmt/odev_banner.sh`. With the updated collection installed,
run from `mgmt`:

```bash
./ansible-play.sh odev_banner_add <inventory_group>
```

This installs `/opt/odev_banner.sh` with the configuration above. It does not run
the script or configure it to appear automatically at login. The existing runner
supplies the inventory and `oreol_target`; privilege escalation settings come
from your inventory.
