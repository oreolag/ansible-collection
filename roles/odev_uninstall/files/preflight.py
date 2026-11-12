#!/usr/bin/env python3
"""Read-only uninstall checks and an exact list of CLI-owned removal paths."""
import grp
import json
import os
from pathlib import Path
import pwd
import sys

GROUPS = ("odev-users", "odev-developers", "odev-admins")
UNITS = ("odev-booking-expiry.timer", "odev-booking-expiry.service",
         "odev-booking-config.timer", "odev-booking-config.service",
         "odev-booking.service")

def inspect(config, root=Path("/"), group_entries=None, passwd_entries=None):
    errors = []
    prefix = config.get("prefix", "/opt")
    if not isinstance(prefix, str) or not prefix.startswith("/") or prefix == "/" or os.path.normpath(prefix) != prefix:
        return {"errors": ["CLI prefix must be a normalized absolute directory other than /."]}
    cli = prefix + "/odev"
    def local(path):
        return root / path.lstrip("/")
    paths = [cli, prefix + "/odev_login.sh", prefix + "/odev_banner.sh",
             "/etc/profile.d/odev.sh", "/etc/profile.d/odev_login.sh",
             "/usr/share/bash-completion/completions/odev",
             "/etc/odev/booking-access", "/run/odev-booking"]
    paths += ["/etc/sudoers.d/" + name for name in GROUPS]
    paths += ["/etc/systemd/system/" + name for name in UNITS]
    if local(cli).is_symlink():
        errors.append("CLI installation is a symlink; inspect its target before uninstalling.")
    hostname = config["hostname"]
    sources = [("controller cmdb/booking.yml", config.get("booking_catalogue", ""))]
    inventory_paths = {prefix + "/booking.yml"}
    try:
        import yaml
        cli_vars = local(cli + "/vars.yml")
        if cli_vars.exists():
            settings = yaml.safe_load(cli_vars.read_text()) or {}
            inventory_paths.add(settings.get("paths", {}).get("booking", prefix + "/booking.yml"))
        for path in inventory_paths:
            if not isinstance(path, str) or not path.startswith("/"):
                errors.append("Installed booking inventory path is not absolute.")
            elif local(path).exists():
                sources.append((path, local(path).read_text()))
        for label, content in sources:
            if not content.strip():
                continue
            catalogue = yaml.safe_load(content)
            if not isinstance(catalogue, dict) or not isinstance(catalogue.get("servers"), list):
                errors.append("Invalid booking catalogue: " + label)
                continue
            for server in catalogue["servers"]:
                if server["name"] == hostname or hostname in server.get("managed_servers", []):
                    errors.append("Booking still depends on this machine in " + label + "; decommission booking first.")
    except ImportError:
        # Never guess whether an unreadable booking configuration is safe.
        if any(local(p).exists() for p in inventory_paths) or local(cli + "/vars.yml").exists() or config.get("booking_catalogue", "").strip():
            errors.append("python3-yaml is needed to verify booking dependencies before uninstall.")
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        errors.append("Cannot verify booking configuration: " + str(error))
    except Exception as error:
        errors.append("Cannot parse booking configuration: " + str(error))
    try:
        pam = local("/etc/pam.d/sshd")
        if pam.exists():
            text = pam.read_text()
            if "ODEV BOOKING ADMISSION" in text or any("/booking/access.py" in line for line in text.splitlines() if not line.lstrip().startswith("#")):
                errors.append("OpenSSH PAM booking enforcement is still configured; remove enforcement before uninstall.")
        if local("/etc/odev/booking-access/endpoint.json").exists():
            errors.append("Booking lookup endpoint is still configured; decommission booking access first.")
        keys = local("/var/lib/odev-booking-check/.ssh/authorized_keys")
        if keys.exists() and any("/booking/access.py" in line for line in keys.read_text().splitlines() if not line.lstrip().startswith("#")):
            errors.append("Booking lookup SSH commands still reference the CLI; revoke them first.")
    except OSError as error:
        errors.append("Cannot verify booking enforcement: " + str(error))
    groups = [g for g in (grp.getgrall() if group_entries is None else group_entries) if g.gr_name in GROUPS]
    users = pwd.getpwall() if passwd_entries is None else passwd_entries
    gids = {g.gr_gid: g.gr_name for g in groups}
    for user in users:
        if user.pw_gid in gids:
            errors.append("Group " + gids[user.pw_gid] + " is the primary group of " + user.pw_name + "; reassign it explicitly first.")
    if not errors and gids:
        excluded = paths + ["/proc", "/sys", "/dev"]
        def managed(path):
            return any(path == entry or path.startswith(entry + "/") for entry in excluded)
        def scan_error(error):
            errors.append("Cannot inspect filesystem ownership: " + str(error))
        for directory, directories, files in os.walk(root, topdown=True, followlinks=False, onerror=scan_error):
            logical = "/" + str(Path(directory).relative_to(root))
            if logical == "/.":
                logical = ""
            for name in list(directories) + files:
                path = logical.rstrip("/") + "/" + name
                if managed(path):
                    if name in directories:
                        directories.remove(name)
                    continue
                try:
                    group = gids.get(os.lstat(Path(directory) / name).st_gid)
                    if group:
                        errors.append("Group " + group + " owns retained path " + path + "; reassign ownership explicitly first.")
                except FileNotFoundError:
                    pass  # A transient file vanished during the read-only scan.
                except OSError as error:
                    scan_error(error)
                if len(errors) >= 20:
                    break
            if errors:
                break
    return {"errors": errors, "remove_paths": paths, "groups": [g.gr_name for g in groups], "units": list(UNITS)}

if __name__ == "__main__":
    try:
        result = inspect(json.load(sys.stdin))
    except Exception as error:
        result = {"errors": ["Uninstall preflight could not complete: " + str(error)]}
    print(json.dumps(result))
