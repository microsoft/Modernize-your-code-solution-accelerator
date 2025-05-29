# Deployment Plan

The deployment code will be in the **infra** folder. The **modules** subfolder contains reusable, parameterized modules. There are two main deployment files: `main.bicep` (for quick, cost-effective solution exploration and demos) and `main.waf.bicep` (for production-grade, WAF-secured deployments). Both leverage the same modules, but with different parameters and security/networking posture.

- **main.bicep**: Lightweight deployment for rapid prototyping, demos, and decision making. Minimal networking/security for speed and cost.
- **main.waf.bicep**: Production-ready deployment. Creates a Virtual Network with subnets, private endpoints for all solution resources (e.g., Azure AI Foundry, Storage, Cosmos DB, Key Vault), Bastion Host, and all networking/security resources recommended by WAF Security Guidelines. Uses Azure Verified Modules (AVM) where appropriate. See [Microsoft Azure Well-Architected Framework (WAF) Security design principles](https://learn.microsoft.com/en-us/azure/well-architected/security/principles) and [Azure Verified Modules (AVM)](https://azure.github.io/Azure-Verified-Modules/).

If you are new to AVM BICEP implementation, refer to [AVM Bicep Quickstart Guide](https://azure.github.io/Azure-Verified-Modules/usage/quickstart/bicep/).

**All modules are parameterized for maximum reusability and maintainability. Use outputs from modules to wire dependencies (e.g., VNet/subnet IDs, resource IDs).**

Below is an example deployment design. The Group (module) Name column shows how to group code in BICEP modules.

**Solution Components** 

| Component Name                            | Notes                                   | Subnet            |
| ----------------------------------------- | ------------------------------------------------------------ | ----------------- |
| Log Analytics Workspace | monitoring **(global, not subnet) |  |
| Application Insights | app-insights **(global, not subnet)** |  |
| Container Apps Environment                | Shared by two apps                 | app             |
| Frontend Container App                    |                      | app            |
| Backend Container App                     |                      | app               |
| NSG for App Subnet                        | nsg                                                          | app               |
| AI Hub                                    | ai-foundry / **private end point**                          | ai                |
| AI Project                                | ai-foundry / **private end point**                          | ai                |
| AI Services                               | ai-foundry / **private end point**                          | ai                |
| NSG for AI Subnet                         | nsg                                                          | ai                |
| Managed Identity (RG, etc)   | identity                                                     |               |
| Key Vault                                 | keyvault / **private end point**                            | data         |
| Cosmos DB                                 | cosmos-db/ **private end point**       | data              |
| Storage Account Front End                 | storage / **private end point**       | data          |
| Storage Account Back End                  | storage / **private end point**  | data          |
| NSG for Data Subnet                       | nsg                                                          | data              |
| Bastion Host                              | bastion                                                      | bastion           |
| NSG for Bastion                           | nsg                                                          | bastion           |
| JumpBox VM                                | (your-jumpbox-module)                                        | jumpbox           |
| NSG for JumpBox                           | nsg                                                          | jumpbox           |
| Route Table                               | routeTable                                                   | (associated subnets) |
| Private Endpoints                         | privateEndpoint                                              | respective subnet |
| Private DNS Zone                          | privateDnsZone                                               | vnet              |



### **Example Subnet/NSG Table**

| Subnet   | NSG Rules (Inbound)                                 | NSG Rules (Outbound)        |
|----------|-----------------------------------------------------|-----------------------------|
| web      | 80/443 from internet or allowed IPs                 | To app, internet            |
| app      | From web subnet only                                | To data, PaaS               |
| ai       | From app subnet only                                | To data, PaaS               |
| data     | From app/ai/private endpoints                       | To PaaS, as needed          |
| jumpbox  | RDP/SSH from allowed IPs or Bastion                 | To internet, as needed      |
| bastion  | Platform-managed (Bastion Host only, no direct NSG) | To VMs for RDP/SSH          |

## **Monitoring & Logging**
- Enable diagnostic logs for all resources, send to Log Analytics Workspace.
- Enable Application Insights for all app components.

## **DDoS Protection**
- Enable at the VNet level for public-facing workloads.

## **Route Tables (UDRs)**
- Optional, but recommended for advanced routing (e.g., force tunneling through Azure Firewall if used).

## Azure Bastion Host

**Function:**

- Azure Bastion is a managed PaaS service that provides secure RDP/SSH connectivity to your VMs directly from the Azure Portal, without exposing public IP addresses on those VMs.

**How to Use:**

- Deploy Bastion Host in a dedicated subnet (must be named `bastion` or `AzureBastionSubnet`).
- When you need to access a VM (like a JumpBox or any other VM) for admin purposes, use the “Connect” button in the Azure Portal and select “Bastion.”
- Your session runs over SSL in the browser—no public IP, no direct RDP/SSH from the internet.

**Best Practice:**

- Use Bastion Host for all admin access to VMs in your VNet.
- Never assign public IPs to your VMs.

## JumpBox VM

**Function:**

- A JumpBox (or Jump Host) is a hardened VM (often Linux or Windows) that acts as a single entry point for admin access to other VMs or resources in your private network.
- It is typically used for scenarios where you need to run custom tools, scripts, or have a persistent admin environment.

**How to Use:**

- Deploy the JumpBox VM in its own subnet (e.g., `jumpbox`).
- Access the JumpBox via Bastion Host (never via public IP).
- From the JumpBox, you can SSH/RDP to other VMs, run scripts, or use it as a staging point for troubleshooting.

**Best Practice:**

- The JumpBox should have minimal software, be tightly controlled, and monitored.
- Use NSGs to restrict access to/from the JumpBox subnet.
- Use Bastion Host to access the JumpBox, not a public IP.

## Deployment Considerations

### Add Networking Components
- **Network Security Group (NSG):** Protects subnets and controls inbound/outbound traffic. One NSG per subnet is recommended.
- **Bastion Host:** Provides secure RDP/SSH access to VMs without exposing public IPs.
- **Route Table:** Custom route tables for advanced routing scenarios (optional, but recommended for segmented networks).
- **Private Endpoints:** For secure, private connectivity to PaaS services (Key Vault, Storage, Cosmos DB, etc.), add private endpoints in the relevant subnets. Use a dedicated PrivateEndpointSubnet for easier management.
- **Private DNS Zone:** Required for name resolution of private endpoints, ensuring resources in your VNet can resolve the private DNS names of Azure PaaS services to their private IP addresses.

### Security & Best Practices
- Use Managed Identity for all services that support it.
- Store secrets and connection strings in Key Vault; never hardcode credentials.
- Enable diagnostic logging for all resources (send to Log Analytics Workspace).
- Apply NSGs to each subnet with least-privilege rules.
- Use Bastion Host for secure admin access.
- Consider DDoS Protection for the VNet if required.
- Use Private Endpoints for PaaS services to avoid public exposure.
- For all PaaS resources with private endpoints, set public network access to 'Deny'.
- Enable soft delete and purge protection on Key Vault and Storage Accounts.

---

**For more information, see:**
- [Microsoft Azure Well-Architected Framework (WAF) Security design principles](https://learn.microsoft.com/en-us/azure/well-architected/security/principles)
- [Azure Verified Modules (AVM)](https://azure.github.io/Azure-Verified-Modules/)
- [AVM Bicep Quickstart Guide](https://azure.github.io/Azure-Verified-Modules/usage/quickstart/bicep/)
- [Azure Application Gateway documentation](https://learn.microsoft.com/en-us/azure/application-gateway/overview)
- [Azure Bastion documentation](https://learn.microsoft.com/en-us/azure/bastion/bastion-overview)
- [Azure Private Endpoint documentation](https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-overview)
- [Azure Firewall documentation](https://learn.microsoft.com/en-us/azure/firewall/overview)
- [Azure DDoS Protection documentation](https://learn.microsoft.com/en-us/azure/ddos-protection/ddos-protection-overview)
- [Azure Key Vault documentation](https://learn.microsoft.com/en-us/azure/key-vault/general/overview)
- [Azure Cosmos DB documentation](https://learn.microsoft.com/en-us/azure/cosmos-db/introduction)
- [Azure Storage documentation](https://learn.microsoft.com/en-us/azure/storage/common/storage-introduction)

