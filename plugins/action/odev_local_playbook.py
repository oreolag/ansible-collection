"""Call MGMT's ansible-play.sh for a controller checkout, with live output."""

import json
import os
from pathlib import Path
import subprocess
import sys

from ansible import context
from ansible.errors import AnsibleActionFail
from ansible.plugins.action import ActionBase
from ansible.utils.display import Display


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


def playbook_arguments(argv, original_playbooks, playbook, hosts, wrapper):
    # Preserve inventory, extra vars, SSH, Vault, tags, check/diff and other options
    # exactly as supplied, using the same wrapper as cli_install_macos.sh.
    if len(original_playbooks) != 1 or argv.count(original_playbooks[0]) != 1:
        raise ValueError("odev_install_local requires a single outer playbook invocation.")
    arguments = list(argv)
    arguments.remove(original_playbooks[0])
    # Insert before -- if present, so these remain options rather than filenames.
    position = arguments.index("--") if "--" in arguments else len(arguments)
    arguments[position:position] = [
        "--limit", hosts, "--extra-vars",
        json.dumps({"cli": {"local_path": str(Path(playbook).parent)}}),
    ]
    return [wrapper, playbook, hosts, *arguments]


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
            mgmt_path = os.environ.get("OMGMT_PATH")
            if not mgmt_path:
                raise ValueError("Run odev_install_local through omgmt so OMGMT_PATH identifies its ansible-play.sh.")
            wrapper = Path(mgmt_path) / "ansible-play.sh"
            if not wrapper.is_file() or not os.access(wrapper, os.X_OK):
                raise ValueError("MGMT's executable ansible-play.sh was not found: %s" % wrapper)
            selected = task_vars["ansible_play_hosts_all"]
            # One wrapper invocation serves all selected hosts. Do not silently
            # choose one checkout when their inventory variables disagree.
            for host in selected:
                other_path = task_vars["hostvars"][host].get("cli", {}).get("local_path", "")
                if checkout_playbook(other_path) != playbook:
                    raise ValueError("All selected hosts must use the same cli.local_path.")
            for option in ("ask_pass", "become_ask_pass", "ask_vault_pass"):
                if context.CLIARGS.get(option):
                    raise ValueError("odev_install_local needs noninteractive credentials; use inventory variables or password files instead of password prompts.")
            arguments = playbook_arguments(
                sys.argv[1:], context.CLIARGS.get("args", ()),
                playbook, ",".join(selected), str(wrapper),
            )
        except (ValueError, KeyError) as error:
            raise AnsibleActionFail(str(error)) from error

        if self._task.args.get("validate_only", False):
            result.update(changed=False, playbook=playbook)
            return result

        # The wrapper execs ansible-playbook just like cli_install_macos.sh.
        # Relay each line immediately; do not turn its output into a debug array.
        display = Display()
        with subprocess.Popen(
            arguments, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, bufsize=1,
            env=dict(os.environ, PYTHONUNBUFFERED="1"),
        ) as process:
            for line in process.stdout:
                if not self._task.no_log:
                    display.display(line.rstrip("\r\n"))
            rc = process.wait()
        result.update(
            changed=not self._task.check_mode, rc=rc, failed=rc != 0,
        )
        if rc:
            result["msg"] = "The local CLI installation failed in ansible-play.sh; see the live output above."
        return result
