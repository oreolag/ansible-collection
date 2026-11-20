# gh_update

Updates an already installed GitHub CLI (`gh`) package to the latest version
available from the host's configured APT repositories on Ubuntu or Debian.
The role refreshes the APT cache on each run and leaves machines without the
package uninstalled.

Install GitHub CLI and configure its package repository first using your existing
installation workflow. This role does not configure repositories, change GitHub
authentication, or reboot the host. An up-to-date package produces no package
changes on repeat runs.

After installing the updated collection in your administration environment, run:

```bash
./ansible-play.sh gh_update <inventory_group>
```

Add `--check --diff` to preview the update without applying it. No GitHub token
is required.
