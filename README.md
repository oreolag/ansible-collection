<p align="right">
<a href="https://oreol.ch">Oreol</a> <a href="https://github.com/oreolag/cli">CLI</a>
</p>

<p align="center" style="margin-bottom: 0px;">
  <img src="https://github.com/oreolag/ansible-collection/blob/main/oreol-logo-ansible.svg"
       align="center" style="width: 200px; height: auto;">
</p>

<h1 align="center">
  Ansible Collection
</h1> 

Reusable Ansible playbooks and roles for configuring and managing Linux clusters, maintained by Oreol. Apply shared automation across your hosts while keeping each cluster’s inventory, variables, and CMDB in its own repository.

## Oreol-managed clusters

Organizations that own an Oreol cluster receive a customized repository from Oreol, ready for co-managing their infrastructure in accordance with the management agreement between the parties.

## Other users

You can use this collection with your own cluster. Create a repository for its inventory, shared variables, and CMDB using the following example structure:

```text
my-cluster/
├── README.md
├── .gitignore
├── ansible.cfg
├── requirements.yml
├── hosts
├── group_vars/
│   └── all.yml
└── cmdb/
    ├── node-01.yml
    └── node-02.yml
```

Define your machines and host groups in `hosts`, and shared connection settings and role variables in `group_vars/all.yml`. Store machine-specific CMDB descriptions under `cmdb/`, using your own host names. Ansible loads inventory variables automatically; files under `cmdb/` are read only by operations that explicitly use them.

This is a generic example: all cluster names, host details, and configuration belong in your own repository. You do not need to clone this collection separately.

### Install the collection

Add `requirements.yml` to your cluster repository:

```yaml
---
collections:
  - name: https://github.com/oreolag/ansible-collection.git
    type: git
    version: main
```

With Ansible and Git installed, run this command from the root of your cluster repository:

```bash
ansible-galaxy collection install -r requirements.yml -p ./collections
```

Ansible downloads the collection from GitHub and installs it as `oreol.cluster` under `collections/ansible_collections/oreol/cluster/`. This prepares the automation locally; it does not run any tasks on your hosts.

Configure the inventory and collection location in your cluster's `ansible.cfg`:

```ini
[defaults]
inventory = ./hosts
collections_path = ./collections
```

Add `/collections/` to your cluster's `.gitignore`, since this directory contains installed dependencies.

### Update the collection

To refresh the installed copy after changes are pushed to `main`:

```bash
ansible-galaxy collection install -r requirements.yml -p ./collections --force
```

Local, unpushed changes to the source repository are not included. For reproducible installations, replace `main` with a published release tag or a specific commit.
