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

## Install in your cluster repository

Create your own cluster repository containing its inventory, CMDB, and Ansible configuration. You do not need to clone this collection separately.

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

Add this setting to your cluster's `ansible.cfg` under `[defaults]`:

```ini
[defaults]
collections_path = ./collections
```

Add `/collections/` to your cluster's `.gitignore`, since this directory contains installed dependencies.

To refresh the installed copy after changes are pushed to `main`:

```bash
ansible-galaxy collection install -r requirements.yml -p ./collections --force
```

Local, unpushed changes to the source repository are not included. For reproducible installations, replace `main` with a published release tag or a specific commit.
