# tailscale_update

Updates an already installed Tailscale package to the latest version available
from the host's configured APT repositories on Ubuntu or Debian. Run
`tailscale_install` first to configure the official stable repository and enroll
new machines. Machines without the package are left uninstalled.

The role refreshes the APT cache on each run. It does not change authentication,
Tailscale SSH preferences, repository configuration, or other Tailscale settings,
and it does not reboot the host. Package upgrades may restart `tailscaled` and
briefly interrupt Tailscale connections; run through LAN or your Incus jump
connection.

After installing the updated collection in your administration environment, run:

```bash
./ansible-play.sh tailscale_update <inventory_group>
```

Add `--check --diff` to preview the update without applying it. No Tailscale auth
key is required. An up-to-date package produces no package changes on repeat runs.

The role uses Ansible's [APT module](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/apt_module.html)
with `only_upgrade: true` to avoid installing Tailscale on unenrolled hosts.
