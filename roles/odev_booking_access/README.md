# odev_booking_access

Provision read-only machine credentials for managed servers. Deploy the
booking code and copy the CMDB to the servers before running the role.

```bash
./ansible-play.sh odev_booking_access incus_containers
```

The role reads `cmdb/booking.yml` beside the management inventory, skips
unmanaged hosts, and provisions each managed host for its assigned service.
Set `access.host` to an IP, DNS name or tailnet address that reaches the
service's OpenSSH listener. `access.port` defaults to 22. The service name
must match the short hostname of an inventory entry. The role prefers
matching entries in the selected group when the inventory has aliases.

The management connection supplies the verified OpenSSH Ed25519 host key.
The managed server uses the configured endpoint at runtime and keeps its
private key root-only. The service restricts the key to read-only booking
checks for that managed host. The role expects the default authorized-keys
location and does not configure PAM or enable an SSH listener.

As root on the managed host, run
`python3 /opt/odev/booking/access.py --check jmoya82`.
Exit status 0 means allowed, 1 means no active owned or shared booking, and
2 means the lookup could not be completed.
