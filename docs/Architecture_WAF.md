# WAF-Aligned Solution Architecture

This document describes the architecture and key features of the WAF-aligned (Well-Architected Framework) deployment option for the Modernize Your Code Solution Accelerator.

![WAF-Aligned Architecture Diagram](../docs/images/read_me/solArchitectureWAF.png)

## Overview
The WAF-aligned deployment is hardened architecture following Azure Well-Architected Framework pillars:
- Security
- Reliability
- Performance Efficiency
- Cost Optimization
- Operational Excellence

## Key Features
- **Private Networking:**
  - Critical resources are accessible only via private endpoints within a Virtual Network (VNet).
  - Private DNS zones and virtual network links ensure secure, internal name resolution.
- **Monitoring & Diagnostics:**
  - Log Analytics Workspace and Application Insights are enabled for observability and troubleshooting.
- **Scaling & Redundancy:**
  - Resources can be configured for high availability and geo-redundancy.
- **Role-Based Access Control (RBAC):**
  - Managed identities and least-privilege access for secure automation and resource access.
- **Parameterization:**
  - All WAF features are controlled via parameters in `main.waf.bicepparam` for easy customization.

## Architecture Components
- **Virtual Network (VNet):** Isolates all solution resources.
- **Private Endpoints:** Securely connect to Azure PaaS services (AI foundry, AI Services, Azure Storage, Cosmos DB, Key Vault), from within VNET. 
- **Private DNS Zones:** Provide internal DNS resolution for private endpoints.
- **Jumpbox/Bastion Host:** Secure admin access to the VNet.
- **Monitoring:** Centralized logging and application insights.
- **App Services/Container Apps:** Deployed within the VNet, with private access to dependencies.

## Deployment
- Use the `main.waf.bicepparam` parameter file to enable all WAF features.
- Deploy with:
  ```sh
  cp infra/main.waf.bicepparam infra/main.bicepparam
  azd up
  ```

## Customization
- Adjust parameters in `main.waf.bicepparam` to fit your organization's requirements (e.g., enable/disable redundancy, monitoring, private networking).

## References
- [Azure Well-Architected Framework](https://learn.microsoft.com/azure/architecture/framework/)
- [Parameter file example](../infra/main.waf.bicepparam)
- [Main deployment Bicep](../infra/main.bicep)

