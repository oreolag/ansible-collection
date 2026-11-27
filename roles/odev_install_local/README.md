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

The role contains a normal controller-side shell task that calls MGMT's existing
`ansible-play.sh` once for all selected hosts, like `cli_install_macos.sh`:

```bash
exec ./ansible-play.sh \
  "<cli.local_path>/install.yml" "<selected hosts>" "main,src,booking" \
  -i "<selected cluster inventory>" \
  --extra-vars '{"cli":{"local_path":"<cli.local_path>"}}'
```

The task runs in `OMGMT_PATH`, which omgmt sets to its software directory, using
`delegate_to: localhost`, `become: false`, and `run_once: true`. There is no custom
Python runner. Hosts selected together must share the same checkout and component
flags. One cluster inventory is required.

For an explicit comma-separated component list, use:

```bash
omgmt run playbook --name odev_install_local --hosts <host-or-group> \
  --vars 'odev_install_local_flags=main,src,booking'
```

Otherwise, supported boolean component variables such as `main`, `src`, and
`booking` are converted to the comma-separated flags accepted by ansible-play.sh.
The wrapper supplies the component variables to the checkout's playbook.

The checkout's relative includes and privilege-escalation settings are retained.
Check/diff mode is passed through. Other settings should come from the selected
inventory or Ansible environment; this simplified task does not forward arbitrary
outer command-line options or extra variables. Use noninteractive inventory or
environment-based credentials rather than password prompts.

As with a normal Ansible shell task, output is collected and displayed after the
command finishes. A nonzero exit code fails the role with the command output.
