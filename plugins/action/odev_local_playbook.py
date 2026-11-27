"""Run a controller checkout's full playbook with the caller's CLI options."""

import os
from pathlib import Path
import subprocess
import sys

from ansible import context
from ansible.errors import AnsibleActionFail
from ansible.plugins.action import ActionBase


def checkout_playbook(local_path):
    if not isinstance(local_path, str) or not local_path.strip():
        raise ValueError("Set a nonempty cli.local_path in the cluster's group_vars/all/main.yml.")
    checkout = Path(local_path)
    if not checkout.is_absolute() or not checkout.is_dir():
        raise ValueError("cli.local_path must be an existing absolute directory on the controller: %s" % local_path)
    playbook = checkout / "install.yml"
    if not playbook.is_file():
        raise ValueError("Local CLI installation playbook not found on the controller: %s" % playbook)
    return str(playbook)


def playbook_arguments(argv, original_playbooks, playbook, hostname):
    # Preserve inventory, extra vars, SSH, Vault, tags, check/diff and other options
    # exactly as supplied. Only replace the outer playbook and narrow its limit.
    if len(original_playbooks) != 1 or argv.count(original_playbooks[0]) != 1:
        raise ValueError("odev_install_local requires a single outer playbook invocation.")
    arguments = list(argv)
    arguments[arguments.index(original_playbooks[0])] = playbook
    # Insert before -- if present, so these remain options rather than filenames.
    position = arguments.index("--") if "--" in arguments else len(arguments)
    arguments[position:position] = ["--limit", hostname]
    return arguments


class ActionModule(ActionBase):
    TRANSFERS_FILES = False
    _supports_check_mode = True
    _supports_async = False
    _requires_connection = False

    def run(self, tmp=None, task_vars=None):
        result = super().run(tmp, task_vars)
        task_vars = task_vars or {}
        try:
            playbook = checkout_playbook(self._task.args.get("local_path"))
            for option in ("ask_pass", "become_ask_pass", "ask_vault_pass"):
                if context.CLIARGS.get(option):
                    raise ValueError("odev_install_local needs noninteractive credentials; use inventory variables or password files instead of password prompts.")
            arguments = playbook_arguments(
                sys.argv[1:], context.CLIARGS.get("args", ()),
                playbook, task_vars["inventory_hostname"],
            )
        except (ValueError, KeyError) as error:
            raise AnsibleActionFail(str(error)) from error

        if self._task.args.get("validate_only", False):
            result.update(changed=False, playbook=playbook)
            return result

        completed = subprocess.run(
            [sys.executable, "-m", "ansible.cli.playbook", *arguments],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, env=os.environ.copy(),
        )
        result.update(
            changed=not self._task.check_mode, rc=completed.returncode,
            stdout=completed.stdout, stdout_lines=completed.stdout.splitlines(),
            stderr=completed.stderr, stderr_lines=completed.stderr.splitlines(),
            failed=completed.returncode != 0,
        )
        if completed.returncode:
            result["msg"] = "The local CLI installation playbook failed; see stdout and stderr."
        return result
