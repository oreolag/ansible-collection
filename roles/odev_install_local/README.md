# odev_install_local

Runs `install.yml` from a local Oreol CLI checkout on the computer running
Ansible (the controller). The playbook still installs onto the selected remote
hosts. Both the installation logic and source files come from that checkout,
including edits that have not been committed. No release is downloaded by this
wrapper. The stable `odev_install` role is independent and unchanged.

## Configuration

In the selected cluster's `group_vars/all/main.yml`, configure an absolute path
that exists on the controller:

```yaml
cli:
  local_path: /Users/javier/src/github.com/oreolag/cli
```

Missing, empty, or whitespace-only paths fail before running the checkout's
playbook. The directory and its `install.yml` must exist on the controller.
There is no default path or fallback to a remote installation. Every selected
host is validated before installation starts.

## Run through omgmt

After installing the updated collection:

```bash
omgmt run playbook --name odev_install_local \
  --hosts odev-development-01.tailaaf611.ts.net \
  --vars 'main=true src=true booking=true'
```

Use `--cluster <name>` when necessary. Component flags are those supported by
your checkout's `install.yml`; the example matches `cli_install_macos.sh`.
`repo=true` is rejected because it selects a downloaded repository installation
instead of local file installation. Provision prerequisites with `odev_install`
first if your checkout's selected tasks require them.

The role calls MGMT's existing `ansible-play.sh` once for all selected hosts,
following the same approach as `cli_install_macos.sh`:

```bash
"$OMGMT_PATH/ansible-play.sh" \
  "$CLI_LOCAL_PATH/install.yml" "$SELECTED_HOSTS" \
  -i "$CLUSTER_INVENTORY" \
  --extra-vars '{"cli":{"local_path":"<the configured checkout>"}}'
```

Here `CLI_LOCAL_PATH` means the configured `cli.local_path`; it is not a required
environment variable. `omgmt` sets `OMGMT_PATH` to its software directory. The
runner requires that directory's executable `ansible-play.sh`; it does not fall
back to launching Ansible directly. The selected hosts must share one checkout.

The original inventory, component flags (already represented as extra variables
by omgmt), SSH settings, Vault files, tags, and check/diff options are forwarded.
The checkout's relative includes and privilege-escalation settings are retained.
Normal installation output is streamed live, without a final debug array. The
collection's validation tasks and outer play recap still appear. A nonzero wrapper
exit code fails the role.

Invoke a single outer playbook at a time. Interactive password prompts are not
supported by the nested invocation: use inventory credentials or password files.
Do not run this role with a controller connection delegated to a different
machine. Whether selected installation tasks work in check mode is determined
by the checkout's playbook.
