# Update Ubuntu

Update Ubuntu packages and firmware, following the original
`nvidia-dgxspark-update` workflow. Run from `mgmt`:

```bash
./ansible-play.sh ubuntu_update <inventory_group>
```

The role completes interrupted package configuration, refreshes APT, upgrades
packages, checks for and installs available firmware updates, and reboots if
packages or firmware changed. Firmware updates are always included.

Requires Ubuntu, root privileges, and `fwupdmgr` with configured firmware remotes.
This updates packages within the configured release; it does not upgrade Ubuntu
to a new release. Firmware check errors stop the run; exit code 2 means there
is nothing to update.
