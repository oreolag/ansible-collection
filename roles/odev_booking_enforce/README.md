# odev_booking_enforce

Enable the booking account check for new OpenSSH connections on selected
managed hosts. Deploy the booking code and run `odev_booking_access` first.
Run this playbook over a verified OpenSSH management connection as an
`odev-admins` member. Keep an independent console available for recovery.

```bash
./ansible-play.sh odev_booking_enforce incus-01
```

Use an inventory name that reaches OpenSSH directly. The role verifies
the booking lookup, disables Tailscale SSH if enabled, and adds a managed
block to `/etc/pam.d/sshd`. Tailscale networking remains available.
The existing SSH authentication policy still applies. Root and members
of `odev-admins` bypass the booking check.

Use fresh SSH connections for testing. A multiplexed connection can reuse
a session admitted earlier. The check reads the current booking.yml for
each new connection, so unassigning a host releases the booking requirement.
Existing connections continue.

If needed, remove the ODEV BOOKING ADMISSION block from
`/etc/pam.d/sshd` using the console. The role keeps a backup on modification.
