## **Deployment Guide**

### **Pre-requisites**

To deploy this solution accelerator, ensure you have access to an [Azure subscription](https://azure.microsoft.com/free/) with the necessary permissions to create **resource groups and resources**. Follow the steps in  [Azure Account Set Up](./AzureAccountSetUp.md) 

Check the [Azure Products by Region](https://azure.microsoft.com/en-us/explore/global-infrastructure/products-by-region/?products=all&regions=all) page and select a **region** where the following services are available:  

- Azure AI Foundry 
- Azure OpenAI Service  
- GPT Model Capacity

> ⚠️ **Region-Specific Deployment Constraints:**  
> This application is currently supported only in the following Azure regions. Please ensure you select one of these regions during deployment to avoid failures:
>
> - Australia East  
> - East US    
> - East US 2  
> - France Central  
> - Japan East  
> - Norway East  
> - South India  
> - Sweden Central  
> - UK South  
> - West US 
> - West US 3

### ⚠️ Important: Check Azure OpenAI Quota Availability  

➡️ To ensure sufficient quota is available in your subscription, please follow **[Quota check instructions guide](../docs/quota_check.md)** before you deploy the solution.

## Deployment Options & Steps

### Sandbox or WAF Aligned Deployment Options

The [`infra`](../infra) folder contains the [`main.bicep`](../infra/main.bicep) Bicep script, which defines all Azure infrastructure components for this solution.

When running `azd up`, you’ll now be prompted to choose between a **WAF-aligned configuration** and a **sandbox configuration** using a simple selection:

- A **sandbox environment** — ideal for development and proof-of-concept scenarios, with minimal security and cost controls for rapid iteration.

- A **production deployments environment**, which applies a [Well-Architected Framework (WAF) aligned](https://learn.microsoft.com/en-us/azure/well-architected/) configuration. This option enables additional Azure best practices for reliability, security, cost optimization, operational excellence, and performance efficiency, such as:
  - Enhanced network security (e.g., Network protection with private endpoints)
  - Stricter access controls and managed identities
  - Logging, monitoring, and diagnostics enabled by default
  - Resource tagging and cost management recommendations

**How to choose your deployment configuration:**

When prompted during `azd up`:

![useWAFAlignedArchitecture](images/macae_waf_prompt.png)

- Select **`true`** to deploy a **WAF-aligned, production-ready environment**  
- Select **`false`** to deploy a **lightweight sandbox/dev environment**
  
> [!TIP]
> Always review and adjust parameter values (such as region, capacity, security settings and log analytics workspace configuration) to match your organization’s requirements before deploying. For production, ensure you have sufficient quota and follow the principle of least privilege for all identities and role assignments.

### Deployment Steps 

Pick from the options below to see step-by-step instructions for: GitHub Codespaces, VS Code Dev Containers, Local Environments, and Bicep deployments.

| [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/microsoft/Modernize-your-Code-Solution-Accelerator) | [![Open in Dev Containers](https://img.shields.io/static/v1?style=for-the-badge&label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/microsoft/Modernize-your-Code-Solution-Accelerator) |
|---|---|

<details>
  <summary><b>Deploy in GitHub Codespaces</b></summary>

### GitHub Codespaces

You can run this solution using GitHub Codespaces. The button will open a web-based VS Code instance in your browser:

1. Open the solution accelerator (this may take several minutes):

    [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/microsoft/Modernize-your-Code-Solution-Accelerator)
2. Accept the default values on the create Codespaces page
3. Open a terminal window if it is not already open
4. Continue with the [deploying steps](#deploying-with-azd)

</details>

<details>
  <summary><b>Deploy in VS Code</b></summary>

 ### VS Code Dev Containers

You can run this solution in VS Code Dev Containers, which will open the project in your local VS Code using the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers):

1. Start Docker Desktop (install it if not already installed)
2. Open the project:

    [![Open in Dev Containers](https://img.shields.io/static/v1?style=for-the-badge&label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/microsoft/Modernize-your-Code-Solution-Accelerator)


3. In the VS Code window that opens, once the project files show up (this may take several minutes), open a terminal window.
4. Continue with the [deploying steps](#deploying-with-azd)

</details>

<details>
  <summary><b>Deploy in your local environment</b></summary>

 ### Local environment

If you're not using one of the above options for opening the project, then you'll need to:

1. Make sure the following tools are installed:

    * [Azure Developer CLI (azd)](https://aka.ms/install-azd)
    * [Python 3.9+](https://www.python.org/downloads/)
    * [Docker Desktop](https://www.docker.com/products/docker-desktop/)
    * [Git](https://git-scm.com/downloads)

2. Download the project code:

    ```shell
    azd init -t microsoft/Modernize-your-Code-Solution-Accelerator/
    ```

3. Open the project folder in your terminal or editor.

4. Continue with the [deploying steps](#deploying-with-azd).

</details>

<br/>

Consider the following settings during your deployment to modify specific settings:

 <details>
<Summary><b>Configurable Deployment Settings</b></Summary>

When you start the deployment, most parameters will have **default values**, but you can update the following settings by following the steps [here](../docs/CustomizingAzdParameters.md):  

| **Setting**                       | **Description**                                                                                      | **Default value**         |
|----------------------------------|------------------------------------------------------------------------------------------------------|----------------------------|
| **Azure Region**                 | The region where resources will be created.                                                         | East US                   |
| **Resource Prefix**              | Prefix for all resources created by this template. This prefix will be used to create unique names for all resources. The prefix must be unique within the resource group. | azdtemp                   |
| **AI Location**                  | Location for all AI services resources. This location can be different from the resource group location. | japaneast                 |
| **Capacity**                     | Configure capacity for **gpt-4o**.                                                                   | 200                        |
| **Model Deployment Type**        | Change the Model Deployment Type (allowed values: Standard, GlobalStandard).                        | GlobalStandard             |
| **Model Name**                   | Set the Model Name (allowed values: gpt-4o).                                                        | gpt-4o                     |
| **Model Version**                | Set the Azure model version (allowed values: 2024-08-06).                                           | 2024-08-06                 |
| **Image Tag**                    | Set the Image tag (allowed values: latest, dev, hotfix).                                            | latest                     |
| **Existing Log analytics workspace** | To reuse the existing Log analytics workspace Id.                                                | `<Existing Workspace Id>` |


This accelerator can be configured to  use authentication. 

* To use authentication the installer must have the rights to create and register an application identity in their Azure environment.
After installation is complete, follow the directions in the [App Authentication](../docs/AddAuthentication.md) document to enable authentication.
* Note: If you enable authentication, all processing history and current processing will be performed for your specific user. Without authentication, all batch history from the tool will be visible to all users.

 </details>

<details>
<Summary><b> Quota Recommendations </b></Summary> 
  
By default, the **GPT model capacity** in deployment is set to **5k tokens**.  
> **We recommend increasing the capacity to 200k tokens for optimal performance.** 

To adjust quota settings, follow these [steps](../docs/AzureGPTQuotaSettings.md)

</details>

<details>

  <summary><b>Reusing an Existing Log Analytics Workspace</b></summary>

  Guide to get your [Existing Workspace ID](/docs/re-use-log-analytics.md)

</details>

### Deploying with AZD

Once you've opened the project in [Codespaces](#github-codespaces) or in [Dev Containers](#vs-code-dev-containers) or [locally](#local-environment), you can deploy it to Azure following the following steps. 

To change the azd parameters from the default values, follow the steps [here](../docs/CustomizingAzdParameters.md). 


1. Login to Azure:

    ```shell
    azd auth login
    ```

    #### Note: To authenticate with Azure Developer CLI (`azd`) to a specific tenant, use the previous command with your **Tenant ID**:

    ```sh
    azd auth login --tenant-id <tenant-id>
   ```

2. Provide an `azd` environment name (like "cmsaapp")

   ```sh
   azd env new <cmsaapp>
   ```

3. Provision and deploy all the resources:

    ```shell
    azd up
    ```
    
4. Select a subscription from your Azure account, and select a location which has quota for all the resources. 
    * This deployment will take *6-9 minutes* to provision the resources in your account and set up the solution with sample data. 
    * If you get an error or timeout with deployment, changing the location can help, as there may be availability constraints for the resources.

5. Once the deployment has completed successfully, open the [Azure Portal](https://portal.azure.com/), go to the deployed resource group, find the container app with "frontend" in the name, and get the app URL from `Application URI`.

6. You can now delete the resources by running `azd down`, when you have finished trying out the application. 

<h2>
Additional Steps
</h2>

1. **Deleting Resources After a Failed Deployment**

     Follow steps in [Delete Resource Group](../docs/DeleteResourceGroup.md) If your deployment fails and you need to clean up the resources.

1. **Add App Authentication**
   
    If you chose to enable authentication for the deployment, follow the steps in [App Authentication](../docs/AddAuthentication.md)

## Running the application

To help you get started, sample Informix queries have been included in the data/informix/functions and data/informix/simple directories. You can choose to upload these files to test the application.
