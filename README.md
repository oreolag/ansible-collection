<p align="right">
<a href="https://oreol.ch">Oreol</a> <a href="https://github.com/oreolag/cli">CLI</a>
</p>

<!-- <p align="center" style="margin-bottom: 0px;">
  <img src="https://github.com/oreolag/ansible-collection/blob/main/ansible_logo-removebg.png"
       align="center" style="width: 350px; height: auto;">
</p> -->

<h1 align="center">
  Oreol Ansible Collection
  <p align="center">
   <!--  <a href="https://galaxy.ansible.com/ui/repo/published/oreol/mgmt/"><img src="https://img.shields.io/ansible/collection/d/oreol/mgmt" alt="Ansible Collection Downloads" /></a> -->
    <a href="https://github.com/oreolag/ansible-collection/releases"><img src="https://img.shields.io/github/v/release/oreolag/ansible-collection" alt="Latest release" /></a>
    <a href="https://github.com/oreolag/ansible-collection/blob/main/LICENSE"><img src="https://img.shields.io/github/license/oreolag/ansible-collection" alt="License" /></a>
    <a href="https://github.com/oreolag/ansible-collection/graphs/contributors"><img src="https://img.shields.io/github/contributors/oreolag/ansible-collection?color=blue" alt="Contributors" /></a>
    <a href="https://github.com/oreolag/ansible-collection/stargazers"><img src="https://img.shields.io/github/stars/oreolag/ansible-collection?style=flat" alt="GitHub stars" /></a>
  </p>
</h1>

Reusable Ansible playbooks and roles for configuring and managing Linux and Oreol co-managed heterogeneous computing clusters. Apply shared automation across your hosts while keeping each cluster’s inventory, variables, and CMDB in its own repository.

## Install the collection

```bash
ansible-galaxy collection install oreol.mgmt
```

### Update the collection

```bash
ansible-galaxy collection install oreol.mgmt --upgrade
```

## Citation

[![ACM](https://img.shields.io/badge/ACM-10.1145%2F3805700-green)](https://doi.org/10.1145/3805700)

If you use Oreol Ansible Collection in your research, development, or publications, please cite the following reference:

```bibtex
@article{moya2026hacc,
  author    = {Javier Moya and Matthias Gabathuler and Mario Ruiz and Gustavo Alonso},
  title     = {A Development Platform for Managed Heterogeneous Accelerated Compute Clusters: A Case Study on ETH Zurich’s AMD HACC},
  journal   = {ACM Transactions on Reconfigurable Technology and Systems},
  year      = {2026},
  doi       = {10.1145/3805700},
  url       = {https://doi.org/10.1145/3805700}
}
```
