# odev_install

Downloads and runs the Oreol CLI installer as root on each target Ubuntu server.
The download sends `Cache-Control: no-cache`. The temporary script is removed
on success or failure. Check mode skips the download and execution.

## Defaults

```yaml
odev_install_url: https://oreol.ch/cli/install.sh
```

Run through mgmt:

```bash
./ansible-play.sh odev_install <inventory_group>
```

Every run executes the installer again and reports a change. Installation behavior
is controlled by the downloaded script. The CLI installer also installs the mgmt
plugin and Tailscale; this role does not enroll the machine in a tailnet.
