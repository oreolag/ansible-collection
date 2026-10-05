# tailscale_install

Installs Tailscale from its official stable APT repository on Ubuntu or Debian,
enables `tailscaled`, and enrolls unauthenticated machines using `tailscale.auth_key`.
Store that variable encrypted with Ansible Vault in your administration repository.

Authenticated machines are not re-enrolled. Stopped connections are brought up.
The auth key is written to a temporary root-only file and removed after enrollment,
including on failure. Secret tasks hide their output. Device approval, if enabled,
must be satisfied separately or through a pre-approved auth key.

Run with mgmt: `./ansible-play.sh tailscale_install <inventory_group>`.
The updated mgmt wrapper prompts for the Vault password automatically unless an
explicit Vault option or `ANSIBLE_VAULT_PASSWORD_FILE` is supplied.

Check mode previews package configuration but does not enroll machines.

## Tailscale SSH

Tailscale SSH is enabled by default on both newly enrolled and existing machines.
The role checks the current preference and uses `tailscale set --ssh=true` only
when needed, preserving other Tailscale preferences.

Set `tailscale_install_ssh: false` in your inventory to disable it.
Your tailnet policy must permit network access and Tailscale SSH for the requested
user. Tailscale SSH handles port 22 on the Tailscale address; OpenSSH on the LAN
address remains available. Enabling it can interrupt existing SSH connections
using the Tailscale address, so apply this via LAN or your Incus jump connection.

See [Tailscale SSH](https://tailscale.com/docs/features/tailscale-ssh).
