# odev_install

Downloads and runs the Oreol CLI installer as root on each target Ubuntu server.
The download sends `Cache-Control: no-cache`. The temporary script is removed
on success or failure. The script download is retried up to three times after
failure. Check mode skips the download and execution.

The installer runs asynchronously, with completion polled every 15 seconds and a
bounded runtime. Output is saved to `/var/log/odev-install.log` (root-only), and
its exit status to `/var/log/odev-install.exit`. These files are overwritten on
each run. Follow progress on a target with:

```bash
sudo tail -f /var/log/odev-install.log
```

After completion, `sudo cat /var/log/odev-install.exit` reports `0` for success
or the installer's nonzero exit code. If the process is killed or times out,
the status file may be absent; inspect the log and Ansible result. Existing CLI
files alone do not prove completion. Do not start overlapping installations on
the same host. Polling still requires SSH connectivity.

Dependency downloads inside the installer are not retried by this role, and a
failed installer is not automatically rerun.

## Defaults

```yaml
odev_install_url: https://oreol.ch/cli/install.sh
odev_install_timeout: 3600
```

Run through mgmt:

```bash
./ansible-play.sh odev_install <inventory_group>
```

Every run executes the installer again and reports a change. Installation behavior
is controlled by the downloaded script. The CLI installer also installs the mgmt
plugin and Tailscale; this role does not enroll the machine in a tailnet.
