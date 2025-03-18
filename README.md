# Modernize your code solution accelerator

MENU: [**USER STORY**](#user-story) \| [**QUICK DEPLOY**](#quick-deploy) \| [**SUPPORTING DOCUMENTATION**](#supporting-documents) \|  [**CUSTOMER TRUTH**](#customer-truth)

<h2><img src="./docs/images/read_me/userStory.png" width="64">
<br/>
User story
</h2>

### Overview

Welcome to the *Modernize your code* solution accelerator, designed to help customers transition their SQL queries to new environments quickly and efficiently. This accelerator is particularly useful for organizations modernizing their data estates, as it simplifies the process of translating SQL queries from various dialects.

When dealing with legacy code, users often face significant challenges, including the absence of proper documentation, loss of knowledge of outdated languages, and missing business logic that explains functional requirements.

The *Modernize your code* solution accelerator allows users to specify a group of SQL queries and the target SQL dialect for translation. It then initiates a batch process where each query is translated using a group of Large Language Model (LLM) agents. This automation not only saves time but also ensures accuracy and consistency in query translation.

### Technical Key features

<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".\docs\images\read_me\keyFeaturesDark.png">
  <source media="(prefers-color-scheme: light)" srcset=".\docs\images\read_me\keyFeaturesLight.png">
  <img src=".\docs\images\read_me\keyFeaturesLight.png" alt="KeyFeatures">
</picture>

</br>
</br>

Below is an image of the solution accelerator:

<img src="./docs/images/read_me/webappHero.png" alt="image" style="max-width: 100%;">

</br>

### Use case / scenario

Companies maintaining and modernizing their data estates often face large migration projects. They may have volumes of files in various dialects, which need to be translated into a modern alternative. Some of the challenges they face include:

<ul><li>Difficulty analyzing and maintaining legacy systems due to missing documentation</li>
<li>Time-consuming process to manually update legacy code and extract missing business logic</li>
<li>High risk of errors from manual translations, which can lead to incorrect query results and data integrity issues</li>
<li>Lack of available knowledge and expertise for legacy languages creates additional effort, cost, and reliance on niche skills</li></ul>

By using the *Modernize your code* solution accelerator, users can automate this process, ensuring that all queries are accurately translated and ready for use in the new modern environment.

For an in-depth look at the applicability of using multiple agents for this code modernization use case, please see the [supporting AI Research paper](./documentation/modernize_report.pdf).

The sample data used in this repository is synthetic and generated using Azure Open AI service. The data is intended for use as sample data only.

### Solution architecture

<img src="./docs/images/read_me/solArchitecture.png" alt="image" style="max-width: 100%;">

<br/>

### Agentic architecture

<img src="./docs/images/read_me/agentArchitecture.png" alt="image" style="max-width: 100%;">

<br/>

This diagram double-clicks into the agentic framework for the code conversion process. The conversion uses an agentic approach with each agent playing a specialized role in the process. The system gets a list of SQL files which are targeted for conversion. 

**Step 1:** The system loops through the list of SQL files, converting each file, starting by passing the SQL to the Migrator agent. This agent will create several candidate SQL files that should be equivalent. It does this to ensure that the system acknowledges that most of these queries could be converted in a number of different ways. *Note that the processing time can vary depending on OpenAI and cloud services.*

**Step 2:** The Picker agent then examines these various possibilities and picks the one it believes is best using criteria such as simplicity, clarity of syntax, etc.

**Step 3:** This query is sent to the Syntax checker agent which, using a command line tool designed to validate SQL syntax, checks to make sure the query should run without error.
- **Step 3n:** If the Syntax checker agent finds potential errors, it then in Step 3n sends the query to a Fixer agent which will attempt to fix the problem. The Fixer agent then sends the fixed query back to the Syntax checker agent again. If there are still errors, the Syntax checker agent sends back to the Fixer agent to make another attempt. This iteration continues until, either there are no errors found, or a max number of allowed iterations is reached. If the max number is hit, error logs are generated for that query and stored in its Cosmos DB metadata. 

**Step 4:** Once the SQL is found to run without errors, it is sent for a final check to the Semantic checker agent. This agent makes sure that the query in the new syntax will have the same logical effects as the old query, with no extra effects. It can find edge cases which don’t apply to most scenarios, so, if it finds an issue, this issue is sent to the query logs, and the query is generated and the file will be present in storage, but its state will be listed as “warning”.  If no semantic issues are found, the query is generated and placed into Azure storage with a state of success.

<h2><img src="./docs/images/read_me/quickDeploy.png" width="64">
<br/>
QUICK DEPLOY
</h2>


| [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/microsoft/Modernize-your-Code-Solution-Accelerator) | [![Open in Dev Containers](https://img.shields.io/static/v1?style=for-the-badge&label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/microsoft/Modernize-your-Code-Solution-Accelerator) | [![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fmarktayl1%2Ftestdeploy%2Frefs%2Fheads%2Fmain%2FCodeGenDeploy.json) |
|---|---|---|

### **Prerequisites**

To deploy this solution accelerator, ensure you have access to an [Azure subscription](https://azure.microsoft.com/free/) with the necessary permissions to create **resource groups and resources**. Follow the steps in  [Azure Account Set Up](./docs/AzureAccountSetUp.md) 

Check the [Azure Products by Region](https://azure.microsoft.com/en-us/explore/global-infrastructure/products-by-region/?products=all&regions=all) page and select a **region** where the following services are available:  

- Azure AI Foundry 
- Azure OpenAI Service 
- Azure AI Search
- Azure AI Content Understanding
- Embedding Deployment Capacity  
- GPT Model Capacity
- [Azure Semantic Search](./docs/AzureSemanticSearchRegion.md)  

Here are some example regions where the services are available: East US, East US2, Australia East, UK South, France Central.

This accelerator can be deployed with or without authentication. 

* To install with authentication requires that the installer have the rights to create and register an application identity in their Azure environment.
This is controlled through the Authorization field in the installation form. If you do not have this permission, or are not sure, you can start with the no authorization option to view and experiment with the accelerator.
* Note: If you install with authentication, all processing history and current processing will be performed for your specific user. If you deploy without authentication, all batch history from the tool will be visible to all users.
 
### **Configurable Deployment Settings**  

When you start the deployment, most parameters will have **default values**, but you can update the following settings:  

| **Setting** | **Description** |  **Default value** |
|------------|----------------|  ------------|
| **Azure Region** | The region where resources will be created. | East US| 
| **Resource Prefix** | Prefix for all resources created by this template. This prefix will be used to create unique names for all resources. The prefix must be unique within the resource group. |  ? |
| **Authorization** | Authorization requires permission to create an app identity in the subscription. See readme for details |  false |
| **Ai Location** | Location for all Ai services resources. This location can be different from the resource group location |  ? |
| **Capacity** | Configure capacity for **GPT models**. |  5k |

### [Optional] Quota Recommendations  
By default, the **GPT model capacity** in deployment is set to **5k tokens**.  
> **We recommend increasing the capacity to 30k tokens for optimal performance.** 

To adjust quota settings, follow these [steps](./docs/AzureGPTQuotaSettings.md)  

**⚠️ Warning:**  **Insufficient quota can cause application errors.** Please ensure you have the recommended capacity or request for additional capacity before deploying this solution. 

### Deployment Options
Pick from the options below to see step-by-step instructions for: GitHub Codespaces, VS Code Dev Containers, Local Environments, and Bicep deployments.

<details>
  <summary><b>Deploy with Bicep/ARM template</b></summary>

### Bicep

   Click the following deployment button to create the required resources for this accelerator directly in your Azure Subscription.

   [![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fmarktayl1%2Ftestdeploy%2Frefs%2Fheads%2Fmain%2FCodeGenDeploy.json)

</details>

### Deploying

Once you've opened the project in [Codespaces](#github-codespaces) or in [Dev Containers](#vs-code-dev-containers) or [locally](#local-environment), you can deploy it to Azure following the following steps. 

To change the azd parameters from the default values, follow the steps [here](./docs/CustomizingAzdParameters.md). 


1. Login to Azure:

    ```shell
    azd auth login
    ```

    #### To authenticate with Azure Developer CLI (`azd`), use the following command with your **Tenant ID**:

    ```sh
    azd auth login --tenant-id <tenant-id>
   ```

2. Provision and deploy all the resources:

    ```shell
    azd up
    ```

3. Provide an `azd` environment name (like "ckmapp")
4. Select a subscription from your Azure account, and select a location which has quota for all the resources. 
    * This deployment will take *7-10 minutes* to provision the resources in your account and set up the solution with sample data. 
    * If you get an error or timeout with deployment, changing the location can help, as there may be availability constraints for the resources.

5. Once the deployment has completed successfully, open the [Azure Portal](https://portal.azure.com/), go to the deployed resource group, find the App Service and get the app URL from `Default domain`.

6. You can now delete the resources by running `azd down`, when you have finished trying out the application. 

<h2>
Additional Steps
</h2>

1. **Add App Authentication**
   
    If you chose to enable authentication for the deployment, follow the steps in [App Authentication](./docs/AddAuthentication.md)

1. **Deleting Resources After a Failed Deployment**

     Follow steps in [Delete Resource Group](./docs/DeleteResourceGroup.md) If your deployment fails and you need to clean up the resources.

## Sample Questions

To help you get started, here are some **Sample Questions** you can ask in the app:

- < Add how to run here >

These questions serve as a great starting point to explore insights from the data.

<h2>
Responsible AI Transparency FAQ 
</h2>

Please refer to [Transparency FAQ](./TRANSPARENCY_FAQ.md) for responsible AI transparency details of this solution accelerator.

<h2><img src="./docs/images/read_me/supportingDocuments.png" width="64" style="max-width: 100%;">
</br>
  Supporting Documentation
</h2>

### Costs

Pricing varies per region and usage, so it isn't possible to predict exact costs for your usage.
The majority of the Azure resources used in this infrastructure are on usage-based pricing tiers.
However, Azure Container Registry has a fixed cost per registry per day.

You can try the [Azure pricing calculator](https://azure.microsoft.com/en-us/pricing/calculator) for the resources:

* Azure AI Foundry: Free tier. [Pricing](https://azure.microsoft.com/pricing/details/ai-studio/)
* Azure Storage Account: Standard tier, LRS. Pricing is based on storage and operations. [Pricing](https://azure.microsoft.com/pricing/details/storage/blobs/)
* Azure Key Vault: Standard tier. Pricing is based on the number of operations. [Pricing](https://azure.microsoft.com/pricing/details/key-vault/)
* Azure AI Services: S0 tier, defaults to gpt-4o-mini and text-embedding-ada-002 models. Pricing is based on token count. [Pricing](https://azure.microsoft.com/pricing/details/cognitive-services/)
* Azure Container App: Consumption tier with 0.5 CPU, 1GiB memory/storage. Pricing is based on resource allocation, and each month allows for a certain amount of free usage. [Pricing](https://azure.microsoft.com/pricing/details/container-apps/)
* Azure Container Registry: Basic tier. [Pricing](https://azure.microsoft.com/pricing/details/container-registry/)
* Log analytics: Pay-as-you-go tier. Costs based on data ingested. [Pricing](https://azure.microsoft.com/pricing/details/monitor/)
* Azure Cosmos DB: [Pricing](https://azure.microsoft.com/en-us/pricing/details/cosmos-db/autoscale-provisioned/)

⚠️ To avoid unnecessary costs, remember to take down your app if it's no longer in use,
either by deleting the resource group in the Portal or running `azd down`.

### Security guidelines

This template uses Azure Key Vault to store all connections to communicate between resources.

This template also uses [Managed Identity](https://learn.microsoft.com/entra/identity/managed-identities-azure-resources/overview) for local development and deployment.

To ensure continued best practices in your own repository, we recommend that anyone creating solutions based on our templates ensure that the [Github secret scanning](https://docs.github.com/code-security/secret-scanning/about-secret-scanning) setting is enabled.

You may want to consider additional security measures, such as:

* Enabling Microsoft Defender for Cloud to [secure your Azure resources](https://learn.microsoft.com/azure/security-center/defender-for-cloud).
* Protecting the Azure Container Apps instance with a [firewall](https://learn.microsoft.com/azure/container-apps/waf-app-gateway) and/or [Virtual Network](https://learn.microsoft.com/azure/container-apps/networking?tabs=workload-profiles-env%2Cazure-cli).

**Additional resources**

- [Azure AI Foundry documentation](https://learn.microsoft.com/en-us/azure/ai-studio/)
- [Semantic Kernel Agent Framework](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/?pivots=programming-language-python)
- [Azure Cosmos DB Documentation](https://learn.microsoft.com/en-us/azure/cosmos-db/)
- [Azure OpenAI Service - Documentation, quickstarts, API reference - Azure AI services | Microsoft Learn](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/use-your-data)
- [Azure Container Apps documentation](https://learn.microsoft.com/en-us/azure/container-apps/)


## Disclaimers

To the extent that the Software includes components or code used in or derived from Microsoft products or services, including without limitation Microsoft Azure Services (collectively, “Microsoft Products and Services”), you must also comply with the Product Terms applicable to such Microsoft Products and Services. You acknowledge and agree that the license governing the Software does not grant you a license or other right to use Microsoft Products and Services. Nothing in the license or this ReadMe file will serve to supersede, amend, terminate or modify any terms in the Product Terms for any Microsoft Products and Services. 

You must also comply with all domestic and international export laws and regulations that apply to the Software, which include restrictions on destinations, end users, and end use. For further information on export restrictions, visit https://aka.ms/exporting. 

You acknowledge that the Software and Microsoft Products and Services (1) are not designed, intended or made available as a medical device(s), and (2) are not designed or intended to be a substitute for professional medical advice, diagnosis, treatment, or judgment and should not be used to replace or as a substitute for professional medical advice, diagnosis, treatment, or judgment. Customer is solely responsible for displaying and/or obtaining appropriate consents, warnings, disclaimers, and acknowledgements to end users of Customer’s implementation of the Online Services. 

You acknowledge the Software is not subject to SOC 1 and SOC 2 compliance audits. No Microsoft technology, nor any of its component technologies, including the Software, is intended or made available as a substitute for the professional advice, opinion, or judgement of a certified financial services professional. Do not use the Software to replace, substitute, or provide professional financial advice or judgment.  

BY ACCESSING OR USING THE SOFTWARE, YOU ACKNOWLEDGE THAT THE SOFTWARE IS NOT DESIGNED OR INTENDED TO SUPPORT ANY USE IN WHICH A SERVICE INTERRUPTION, DEFECT, ERROR, OR OTHER FAILURE OF THE SOFTWARE COULD RESULT IN THE DEATH OR SERIOUS BODILY INJURY OF ANY PERSON OR IN PHYSICAL OR ENVIRONMENTAL DAMAGE (COLLECTIVELY, “HIGH-RISK USE”), AND THAT YOU WILL ENSURE THAT, IN THE EVENT OF ANY INTERRUPTION, DEFECT, ERROR, OR OTHER FAILURE OF THE SOFTWARE, THE SAFETY OF PEOPLE, PROPERTY, AND THE ENVIRONMENT ARE NOT REDUCED BELOW A LEVEL THAT IS REASONABLY, APPROPRIATE, AND LEGAL, WHETHER IN GENERAL OR IN A SPECIFIC INDUSTRY. BY ACCESSING THE SOFTWARE, YOU FURTHER ACKNOWLEDGE THAT YOUR HIGH-RISK USE OF THE SOFTWARE IS AT YOUR OWN RISK.  
