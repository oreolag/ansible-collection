# cmdb_network_setup

Configures persistent NetworkManager Ethernet connections from the host CMDB already
deployed on the target server. Requires NetworkManager and `nmcli` already
installed and running on the target. It does not switch network managers.

```bash
./ansible-play.sh cmdb_network_setup <inventory_group> --check --diff
./ansible-play.sh cmdb_network_setup <inventory_group>
```

## Defaults

```yaml
cmdb_network_setup_file: "{{ cmdb.remote_path | default('/opt') }}/{{ inventory_hostname_short }}.yml"
cmdb_network_setup_device_types: [endata]
```

The default reads `/opt/<inventory_hostname_short>.yml`, or the base directory
configured in `cmdb.remote_path`, matching `cmdb_copy`. The role checks that the
remote file exists before reading it. Deploy an up-to-date CMDB first:

```bash
./ansible-play.sh cmdb_copy <inventory_group>
```

Override the remote file path when the inventory alias does not match the CMDB filename.
Add `enmgmt` to the device types only when you intend to configure management
interfaces. Applying network changes may interrupt access through those interfaces.

## CMDB format

The role reads `devices.endata[].uplinks` and optionally `devices.enmgmt[].access`.
Device and port `id` values are explicit IDs, not list positions. For example:

```yaml
devices:
  endata:
    - id: 1
      ports: 1
      uplinks:
        - id: 0
          name: enp1s0f0np0
          mac: '02:00:00:04:00:01'
          ip_address: '10.0.4.10'
          ip_mask: 24
```

`name`, `mac`, `ip_address` and an IPv4 prefix length `ip_mask` are required for
configured ports. Ports with no address and no mask are left untouched; incomplete
address pairs fail validation. Missing device categories are skipped. The `ports`
count is not used for iteration. All selected port data is validated before any
connection is changed.

Connections retain the old naming convention: `<host>-<category><device-id>p<port-id>`.
They bind by MAC, use static IPv4, disable IPv6 and enable autoconnect. Existing
profiles are updated without deleting them. Activation runs only for new, changed
or inactive profiles, and failures are reported. Unlisted profiles are not removed.
Gateway, DNS, routing and switch configuration are outside this role's scope.

The role reads the deployed YAML directly; no CLI installation or Python CMDB
helper is needed. It does not copy or update the CMDB itself. This role uses `community.general.nmcli`,
which is declared as a collection dependency.
