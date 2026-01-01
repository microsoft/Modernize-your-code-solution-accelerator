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

The [`infra`](../infra) folder of the Multi Agent Solution Accelerator contains the [`main.bicep`](../infra/main.bicep) Bicep script, which defines all Azure infrastructure components for this solution.

By default, the `azd up` command uses the [`main.parameters.json`](../infra/main.parameters.json) file to deploy the solution. This file is pre-configured for a **sandbox environment** — ideal for development and proof-of-concept scenarios, with minimal security and cost controls for rapid iteration.

For **production deployments**, the repository also provides [`main.waf.parameters.json`](../infra/main.waf.parameters.json), which applies a [Well-Architected Framework (WAF) aligned](https://learn.microsoft.com/en-us/azure/well-architected/) configuration. This option enables additional Azure best practices for reliability, security, cost optimization, operational excellence, and performance efficiency, such as:

**How to choose your deployment configuration:**

* Use the default `main.parameters.json` file for a **sandbox/dev environment**
* For a **WAF-aligned, production-ready deployment**, copy the contents of `main.waf.parameters.json` into `main.parameters.json` before running `azd up`


> [!TIP]
> Always review and adjust parameter values (such as region, capacity, security settings and log analytics workspace configuration) to match your organization’s requirements before deploying. For production, ensure you have sufficient quota and follow the principle of least privilege for all identities and role assignments.

### Deployment Steps 

Pick from the options below to see step-by-step instructions for: GitHub Codespaces, VS Code Dev Containers, Local Environments, and Bicep deployments.

| [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/microsoft/Modernize-your-Code-Solution-Accelerator) | [![Open in Dev Containers](https://img.shields.io/static/v1?style=for-the-badge&label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/microsoft/Modernize-your-Code-Solution-Accelerator) | [![Open in Visual Studio Code Web](https://img.shields.io/static/v1?style=for-the-badge&label=Visual%20Studio%20Code%20(Web)&message=Open&color=blue&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/azure/?vscode-azure-exp=foundry&agentPayload=eyJiYXNlVXJsIjogImh0dHBzOi8vcmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbS9taWNyb3NvZnQvTW9kZXJuaXplLXlvdXItY29kZS1zb2x1dGlvbi1hY2NlbGVyYXRvci9yZWZzL2hlYWRzL21haW4vaW5mcmEvdnNjb2RlX3dlYiIsICJpbmRleFVybCI6ICIvaW5kZXguanNvbiIsICJ2YXJpYWJsZXMiOiB7ImFnZW50SWQiOiAiIiwgImNvbm5lY3Rpb25TdHJpbmciOiAiIiwgInRocmVhZElkIjogIiIsICJ1c2VyTWVzc2FnZSI6ICIiLCAicGxheWdyb3VuZE5hbWUiOiAiIiwgImxvY2F0aW9uIjogIiIsICJzdWJzY3JpcHRpb25JZCI6ICIiLCAicmVzb3VyY2VJZCI6ICIiLCAicHJvamVjdFJlc291cmNlSWQiOiAiIiwgImVuZHBvaW50IjogIiJ9LCAiY29kZVJvdXRlIjogWyJhaS1wcm9qZWN0cy1zZGsiLCAicHl0aG9uIiwgImRlZmF1bHQtYXp1cmUtYXV0aCIsICJlbmRwb2ludCJdfQ==) |
|---|---|---|

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
  <summary><b>Deploy in VS Code Dev Containers</b></summary>

 ### VS Code Dev Containers

You can run this solution in VS Code Dev Containers, which will open the project in your local VS Code using the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers):

1. Start Docker Desktop (install it if not already installed)
2. Open the project:

    [![Open in Dev Containers](https://img.shields.io/static/v1?style=for-the-badge&label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/microsoft/Modernize-your-Code-Solution-Accelerator)


3. In the VS Code window that opens, once the project files show up (this may take several minutes), open a terminal window.
4. Continue with the [deploying steps](#deploying-with-azd)

</details>

<details>
  <summary><b>Deploy in VS Code Web</b></summary>

 ### VS Code Web

[![Open in Visual Studio Code Web](https://img.shields.io/static/v1?style=for-the-badge&label=Visual%20Studio%20Code%20(Web)&message=Open&color=blue&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/azure/?vscode-azure-exp=foundry&agentPayload=eyJiYXNlVXJsIjogImh0dHBzOi8vcmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbS9taWNyb3NvZnQvTW9kZXJuaXplLXlvdXItY29kZS1zb2x1dGlvbi1hY2NlbGVyYXRvci9yZWZzL2hlYWRzL21haW4vaW5mcmEvdnNjb2RlX3dlYiIsICJpbmRleFVybCI6ICIvaW5kZXguanNvbiIsICJ2YXJpYWJsZXMiOiB7ImFnZW50SWQiOiAiIiwgImNvbm5lY3Rpb25TdHJpbmciOiAiIiwgInRocmVhZElkIjogIiIsICJ1c2VyTWVzc2FnZSI6ICIiLCAicGxheWdyb3VuZE5hbWUiOiAiIiwgImxvY2F0aW9uIjogIiIsICJzdWJzY3JpcHRpb25JZCI6ICIiLCAicmVzb3VyY2VJZCI6ICIiLCAicHJvamVjdFJlc291cmNlSWQiOiAiIiwgImVuZHBvaW50IjogIiJ9LCAiY29kZVJvdXRlIjogWyJhaS1wcm9qZWN0cy1zZGsiLCAicHl0aG9uIiwgImRlZmF1bHQtYXp1cmUtYXV0aCIsICJlbmRwb2ludCJdfQ==)

1. Click the badge above (may take a few minutes to load)
2. Sign in with your Azure account when prompted
3. Select the subscription where you want to deploy the solution
4. Wait for the environment to initialize (includes all deployment tools)
5. Once the solution opens, the **AI Foundry terminal** will automatically start running the following command to install the required dependencies:

    ```shell
    sh install.sh
    ```
    During this process, you’ll be prompted with the message:
    ```
    What would you like to do with these files?
    - Overwrite with versions from template
    - Keep my existing files unchanged
    ```
    Choose “**Overwrite with versions from template**” and provide a unique environment name when prompted.
6. Continue with the [deploying steps](#deploying-with-azd)

</details>

<details>
  <summary><b>Deploy in your local environment</b></summary>

 ### Local environment

If you're not using one of the above options for opening the project, then you'll need to:

1. Make sure the following tools are installed:

    * [Azure Developer CLI (azd)](https://aka.ms/install-azd) <small>(v1.18.0+)</small> - version
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

When you start the deployment, most parameters will have **default values**, but you can update the following settings by following the steps [here](../docs/CustomizingAzdParameters.md)

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
    > **Note:** This solution accelerator requires **Azure Developer CLI (azd) version 1.18.0 or higher**. Please ensure you have the latest version installed before proceeding with deployment. [Download azd here](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd).
  
4. Select a subscription from your Azure account, and select a location which has quota for all the resources. 
    * This deployment will take *6-9 minutes* to provision the resources in your account and set up the solution with sample data. 
    * If you get an error or timeout with deployment, changing the location can help, as there may be availability constraints for the resources.

5. Once the deployment has completed successfully, open the [Azure Portal](https://portal.azure.com/), go to the deployed resource group, find the container app with "frontend" in the name, and get the app URL from `Application URI`.

6. You can now delete the resources by running `azd down`, when you have finished trying out the application.
   > **Note:** If you deployed with `enableRedundancy=true` and Log Analytics workspace replication is enabled, you must first disable replication before running `azd down` else resource group delete will fail. Follow the steps in [Handling Log Analytics Workspace Deletion with Replication Enabled](./LogAnalyticsReplicationDisable.md), wait until replication returns `false`, then run `azd down`.

### Deploy your local changes

To deploy your local changes rename the below files.

Rename `azure.yaml` to `azure_original.yaml` and `azure_custom.yaml` to `azure.yaml`.

Go to `infra` directory

Rename `main.bicep` to `main_original.bicep` and `main_custom.bicep` to `main.bicep`. Continue with the [deploying steps](https://github.com/microsoft/Modernize-your-code-solution-accelerator/blob/main/docs/DeploymentGuide.md#deploying-with-azd).

### 🛠️ Troubleshooting
 If you encounter any issues during the deployment process, please refer [troubleshooting](../docs/TroubleShootingSteps.md) document for detailed steps and solutions.

<h2>
Additional Steps
</h2>

1. **Deleting Resources After a Failed Deployment**

     Follow steps in [Delete Resource Group](../docs/DeleteResourceGroup.md) If your deployment fails and you need to clean up the resources.

1. **Add App Authentication**
   
    If you chose to enable authentication for the deployment, follow the steps in [App Authentication](../docs/AddAuthentication.md)

## Running the application

To help you get started, here's the [Sample Workflow](./SampleWorkflow.md) you can follow to try it out.

## Environment configuration for local development & debugging
> Set APP_ENV in your .env file to control Azure authentication. Use dev to enable to use Azure CLI credential, Prod to enable Managed Identity (for production). **Ensure you're logged in via az login when using dev in local**.

1. Navigate to the `src\backend` folder.
2. Create a `.env` file based on the `.env.sample` file.
3. Fill in the `.env` file using the deployment output or by checking the Azure Portal under "Deployments" in your resource group.
4. Alternatively, if resources were
   provisioned using `azd provision` or `azd up`, a `.env` file is automatically generated in the `.azure/<env-name>/.env`
   file. To get your `<env-name>` run `azd env list` to see which env is default.
5. Ensure that `APP_ENV` is set to "**dev**" in your `.env` file.
