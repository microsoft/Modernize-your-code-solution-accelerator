## [Optional]: Customizing resource names 

By default this template will use the environment name as the prefix to prevent naming collisions within Azure. The parameters below show the default values. You only need to run the statements below if you need to change the values. 

> To override any of the parameters, run `azd env set <PARAMETER_NAME> <VALUE>` before running `azd up`. On the first azd command, it will prompt you for the environment name. Be sure to choose 3-20 characters alphanumeric unique name. 

## Parameters

| Name                                   | Type    | Default Value    | Purpose                                                                                              |
| -------------------------------------- | ------- | ---------------- | ---------------------------------------------------------------------------------------------------- |
| `AZURE_ENV_NAME`                       | string  | `azdtemp`        | Used as a prefix for all resource names to ensure uniqueness across environments.                    |
| `AZURE_LOCATION`                       | string  | `eastus2`      | Location of the Azure resources. Controls where the infrastructure will be deployed.                 |
| `AZURE_AISERVICE_LOCATION`                       | string  | `japaneast`      | Set the Azure AI Service Location.                 |
| `AZURE_ENV_MODEL_DEPLOYMENT_TYPE`      | string  | `GlobalStandard` | Change the Model Deployment Type (allowed values: Standard, GlobalStandard).                         |
| `AZURE_ENV_MODEL_NAME`                 | string  | `gpt-4o`         | Set the Model Name (allowed values: gpt-4o).                                                         |
| `AZURE_ENV_MODEL_VERSION`              | string  | `2024-08-06`     | Set the Azure model version (allowed values: 2024-08-06)    |
| `AZURE_ENV_MODEL_CAPACITY`             | integer | `200`            | Set the Model Capacity (choose a number based on available GPT model capacity in your subscription). |
| `AZURE_ENV_LOG_ANALYTICS_WORKSPACE_ID` | string  | Guide to get your [Existing Workspace ID](/docs/re-use-log-analytics.md)     | Set this if you want to reuse an existing Log Analytics Workspace instead of creating a new one.     |
| `AZURE_ENV_IMAGETAG`                   | string  | `latest`         | Set the Image tag Like (allowed values: latest, dev, hotfix)    |
| `AZURE_ENV_JUMPBOX_SIZE`                   | string  | `Standard_DS2_v2`         | Specifies the size of the Jumpbox Virtual Machine. Set a custom value if `enablePrivateNetworking` is `true`.    |
---

## How to Set a Parameter

To customize any of the above values, run the following command **before** `azd up`:

```bash
azd env set <PARAMETER_NAME> <VALUE>
```

Set the Log Analytics Workspace Id if you need to reuse the existing workspace which is already existing
```shell
azd env set AZURE_ENV_LOG_ANALYTICS_WORKSPACE_ID '/subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.OperationalInsights/workspaces/<workspace-name>'
```

**Example:**

```bash
azd env set AZURE_LOCATION westus2
```
