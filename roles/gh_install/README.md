# gh_install

Installs GitHub CLI (`gh`) on Ubuntu or Debian from the
[official APT repository](https://github.com/cli/cli/blob/trunk/docs/install_linux.md).
The role installs CA certificates, downloads the repository signing key, configures
the package repository for the host's native Debian architecture, and installs `gh`.

This is a standalone role with no dependency on odev or omgmt. Their installation
flows are unchanged. No GitHub token is required, and the role does not authenticate
users. Run `gh auth login` separately as the intended user if needed.

Existing `gh` installations are kept at their installed version. Use the separate
`gh_update` role to upgrade them. Repeated installation runs make no package changes
when the prerequisites and `gh` are already installed.

After installing the updated collection in your administration environment, run:

```bash
./ansible-play.sh gh_install <inventory_group>
```

Verify on the target with `gh --version`, then repeat the playbook to check
idempotence. Add `--check --diff` to preview configuration changes; on a fresh host,
check mode cannot resolve `gh` from a repository it has not actually added yet.
