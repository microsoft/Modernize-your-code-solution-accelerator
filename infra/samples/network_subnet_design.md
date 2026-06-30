# Network Subnet Design Guide

This guide explains how to use the sample Bicep program `network-subnet-design.bicep` to create and test your own Azure network design using reusable modules. The sample is designed to be a standalone test harness and a reference for integrating your network design into the solution.

## Purpose and Approach

- **Sample File:** `infra/samples/network-subnet-design.bicep`
- **Reusable Modules:** All code in `infra/samples/network` is designed to be reusable. You should not need to modify code in the modules folder.
- **Custom Network File:** For your own solution, create a `network.bicep` in `infra/modules/` that represents your specific network design, using the modules as building blocks.

## How to Use the Sample

- The sample demonstrates how to deploy a virtual network, subnets, NSGs, Azure Bastion Host, and Jumpbox VM using parameters and reusable modules.
- The sample is parameterized, so you can easily adjust subnet names, address spaces, NSG rules, and delegations.
- You can design and validate your network design with `infra/samples/network-subnet-design.bicep`, then integrate the code by creating `infra/modules/network.bicep` with your tested design (network-subnet-design.bicep). 

## Key Features in the Sample

- **Parameterization:**
  - `resourcesName`, `location`, `addressPrefixes`, `subnets`, `bastionConfiguration`, and `jumpboxConfiguration` are all parameterized for flexibility.
- **Subnet Design:**
  - Subnets are defined with clear address ranges and optional NSGs and delegations.
  - Example subnets: `peps`, `web`, `app`, `ai`, `data`, and a dedicated subnet for Jumpbox.
- **Security:**
  - Each subnet can have its own NSG with custom rules.
  - Example: The `web` subnet allows HTTPS inbound from anywhere; the `app` subnet allows traffic from the `web` subnet, etc.
- **Bastion and Jumpbox:**
  - Optional Azure Bastion Host and Jumpbox VM are included for secure management access.

## Example Workflow

1. **Review the Sample:**
   - Open `infra/samples/network-subnet-design.bicep` and read the comments at the top for context and usage.
2. **Customize Parameters:**
   - Adjust the subnet array, address prefixes, NSG rules, and other parameters to match your requirements.
3. **Deploy the Sample:**
   - Use Azure Developer CLI (`azd`) or Azure CLI to deploy the sample and validate your design.
4. **Integrate into Your Solution:**
   - Once validated, create your own `network.bicep` in `infra/modules/` using the tested design (network-subnet-design.bicep).
   - **Key Integration Steps:**
     - Remove any standalone calls to `virtualNetwork.bicep`, `bastionHost`, and `jumpboxVM` modules from main.bicep file
     - Replace them with a single call to `infra/modules/network.bicep` (netwly created network design bicep)
   - This approach uses the tested, reusable modules without code duplication.
   - Test your integrated solution with `infra/main.bicep`. 

## Example Directory Structure

```
infra/
  samples/
    network/
      ... (reusable modules)
  modules/
    network.bicep   # <--Create your own custom network design
  samples/
    network-subnet-design.bicep  # <-- reference
```

## Best Practices

- Keep your customizations in your own `network.bicep` minimal and focused on your solution’s needs.
- Reuse modules as much as possible to reduce duplication and improve maintainability.
- Clearly document subnet address ranges, NSG rules, and any special configuration in comments.
- Validate your design with Azure best practices for security, scalability, and manageability.