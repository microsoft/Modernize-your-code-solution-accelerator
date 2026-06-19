metadata name = 'Modernize Your Code Solution Accelerator'
metadata description = '''CSA CTO Gold Standard Solution Accelerator for Modernize Your Code.
'''
targetScope = 'resourceGroup'

@allowed([
  'bicep'
  'avm'
  'avm-waf'
])
@description('Required. Deployment flavor selector.')
param deploymentFlavor string = 'avm'

@minLength(3)
@maxLength(16)
@description('Required. A unique application/solution name for all resources in this deployment. This should be 3-16 characters long.')
param solutionName string

@maxLength(5)
@description('Optional. A unique token for the solution. This is used to ensure resource names are unique for global resources. Defaults to a 5-character substring of the unique string generated from the subscription ID, resource group name, and solution name.')
param solutionUniqueToken string = substring(uniqueString(subscription().id, resourceGroup().name, solutionName), 0, 5)

@minLength(3)
@metadata({ azd: { type: 'location' } })
@description('Optional. Azure region for all services. Defaults to the resource group location.')
param location string = resourceGroup().location

@allowed([
  'australiaeast'
  'eastus'
  'eastus2'
  'francecentral'
  'japaneast'
  'norwayeast'
  'southindia'
  'swedencentral'
  'uksouth'
  'westus'
  'westus3'
])
@metadata({
  azd: {
    type: 'location'
    usageName: [
      'OpenAI.GlobalStandard.gpt-4o, 150'
    ]
  }
})
@description('Required. Location for all AI service resources. This location can be different from the resource group location.')
param azureAiServiceLocation string

@description('Optional. AI model deployment token capacity. Defaults to 150K tokens per minute.')
param gptDeploymentCapacity int = 150

@description('Optional. Enable monitoring for the resources. This will enable Application Insights and Log Analytics. Defaults to false.')
param enableMonitoring bool = false

@description('Optional. Enable scaling for the container apps. Defaults to false.')
param enableScalability bool = false

@description('Optional. Enable redundancy for applicable resources. Defaults to false.')
param enableRedundancy bool = false

@description('Optional. The secondary location for the Cosmos DB account if redundancy is enabled.')
param secondaryLocation string?

@description('Optional. Enable private networking for the resources. Set to true to enable private networking. Defaults to false.')
param enablePrivateNetworking bool = false

@description('Optional. Size of the Jumpbox Virtual Machine when created. Set to custom value if enablePrivateNetworking is true.')
param vmSize string?

@description('Optional. Admin username for the Jumpbox Virtual Machine. Set to custom value if enablePrivateNetworking is true.')
@secure()
param vmAdminUsername string?

@description('Optional. Admin password for the Jumpbox Virtual Machine. Set to custom value if enablePrivateNetworking is true.')
@secure()
param vmAdminPassword string?

@description('Optional. Specifies the resource tags for all the resources. Tag "azd-env-name" is automatically added to all resources.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@minLength(1)
@description('Optional. GPT model deployment type. Defaults to GlobalStandard.')
param deploymentType string = 'GlobalStandard'

@minLength(1)
@description('Optional. Name of the GPT model to deploy. Defaults to gpt-4o.')
param gptModelName string = 'gpt-4o'

@minLength(1)
@description('Optional. Image tag for the backend container. Defaults to latest_2025-11-10_599.')
param backendImageTag string = 'latest_2025-11-10_599'

@minLength(1)
@description('Optional. Image tag for the frontend container. Defaults to latest_2025-11-10_599.')
param frontendImageTag string = 'latest_2025-11-10_599'

@description('Optional. Azure Container Registry endpoint.')
param containerRegistryEndpoint string = 'cmsacontainerreg.azurecr.io'

@description('Optional. Enable Microsoft Entra authentication in the frontend. Defaults to false.')
param enableAuth bool = false

@description('Optional. MSAL client ID for frontend authentication.')
param msalAuthClientId string = ''

@description('Optional. MSAL authority URL, for example https://login.microsoftonline.com/<tenant-id>.')
param msalAuthAuthority string = ''

@description('Optional. MSAL redirect URL. Defaults to /.')
param msalRedirectUrl string = '/'

@description('Optional. MSAL post logout redirect URL. Defaults to /.')
param msalPostRedirectUrl string = '/'

@minLength(1)
@description('Optional. Version of the GPT model to deploy. Defaults to 2024-08-06.')
param gptModelVersion string = '2024-08-06'

@description('Optional. Use this parameter to use an existing AI project resource ID. Defaults to empty string.')
param existingFoundryProjectResourceId string = ''

@description('Optional. Use this parameter to use an existing Log Analytics workspace resource ID. Defaults to empty string.')
param existingLogAnalyticsWorkspaceId string = ''

@description('Optional. Tag, Created by user name. Defaults to user principal name or object ID.')
param createdBy string = contains(deployer(), 'userPrincipalName') ? split(deployer().userPrincipalName, '@')[0] : deployer().objectId

var isBicep = deploymentFlavor == 'bicep'
var isAvmWaf = deploymentFlavor == 'avm-waf'

module bicepDeployment './bicep/main.bicep' = if (isBicep) {
  name: take('module.bicep.custom.${solutionName}', 64)
  params: {
    deploymentFlavor: 'bicep'
    solutionName: solutionName
    solutionUniqueToken: solutionUniqueToken
    location: location
    azureAiServiceLocation: azureAiServiceLocation
    gptDeploymentCapacity: gptDeploymentCapacity
    enableMonitoring: enableMonitoring
    enableScalability: enableScalability
    enableRedundancy: enableRedundancy
    secondaryLocation: secondaryLocation
    enablePrivateNetworking: enablePrivateNetworking
    vmSize: vmSize
    vmAdminUsername: vmAdminUsername
    vmAdminPassword: vmAdminPassword
    tags: tags
    enableTelemetry: enableTelemetry
    deploymentType: deploymentType
    gptModelName: gptModelName
    backendImageTag: backendImageTag
    frontendImageTag: frontendImageTag
    containerRegistryEndpoint: containerRegistryEndpoint
    enableAuth: enableAuth
    msalAuthClientId: msalAuthClientId
    msalAuthAuthority: msalAuthAuthority
    msalRedirectUrl: msalRedirectUrl
    msalPostRedirectUrl: msalPostRedirectUrl
    gptModelVersion: gptModelVersion
    existingFoundryProjectResourceId: existingFoundryProjectResourceId
    existingLogAnalyticsWorkspaceId: existingLogAnalyticsWorkspaceId
    createdBy: createdBy
  }
}

module avmDeployment './avm/main.bicep' = if (!isBicep) {
  name: take('module.avm.custom.${solutionName}', 64)
  params: {
    deploymentFlavor: deploymentFlavor
    solutionName: solutionName
    solutionUniqueToken: solutionUniqueToken
    location: location
    azureAiServiceLocation: azureAiServiceLocation
    gptDeploymentCapacity: gptDeploymentCapacity
    enableMonitoring: enableMonitoring || isAvmWaf
    enableScalability: enableScalability || isAvmWaf
    enableRedundancy: enableRedundancy || isAvmWaf
    secondaryLocation: secondaryLocation
    enablePrivateNetworking: enablePrivateNetworking || isAvmWaf
    vmSize: vmSize
    vmAdminUsername: vmAdminUsername
    vmAdminPassword: vmAdminPassword
    tags: tags
    enableTelemetry: enableTelemetry
    deploymentType: deploymentType
    gptModelName: gptModelName
    backendImageTag: backendImageTag
    frontendImageTag: frontendImageTag
    containerRegistryEndpoint: containerRegistryEndpoint
    enableAuth: enableAuth
    msalAuthClientId: msalAuthClientId
    msalAuthAuthority: msalAuthAuthority
    msalRedirectUrl: msalRedirectUrl
    msalPostRedirectUrl: msalPostRedirectUrl
    gptModelVersion: gptModelVersion
    existingFoundryProjectResourceId: existingFoundryProjectResourceId
    existingLogAnalyticsWorkspaceId: existingLogAnalyticsWorkspaceId
    createdBy: createdBy
  }
}

output resourceGroupName string = isBicep ? bicepDeployment!.outputs.resourceGroupName : avmDeployment!.outputs.resourceGroupName
output WEB_APP_URL string = isBicep ? bicepDeployment!.outputs.WEB_APP_URL : avmDeployment!.outputs.WEB_APP_URL
output COSMOSDB_ENDPOINT string = isBicep ? bicepDeployment!.outputs.COSMOSDB_ENDPOINT : avmDeployment!.outputs.COSMOSDB_ENDPOINT
output AZURE_BLOB_ACCOUNT_NAME string = isBicep ? bicepDeployment!.outputs.AZURE_BLOB_ACCOUNT_NAME : avmDeployment!.outputs.AZURE_BLOB_ACCOUNT_NAME
output AZURE_BLOB_ENDPOINT string = isBicep ? bicepDeployment!.outputs.AZURE_BLOB_ENDPOINT : avmDeployment!.outputs.AZURE_BLOB_ENDPOINT
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistryEndpoint
output AZURE_AI_AGENT_PROJECT_CONNECTION_STRING string = isBicep ? bicepDeployment!.outputs.AZURE_AI_AGENT_PROJECT_CONNECTION_STRING : avmDeployment!.outputs.AZURE_AI_AGENT_PROJECT_CONNECTION_STRING
output AZURE_AI_AGENT_PROJECT_NAME string = isBicep ? bicepDeployment!.outputs.AZURE_AI_AGENT_PROJECT_NAME : avmDeployment!.outputs.AZURE_AI_AGENT_PROJECT_NAME
output AZURE_AI_AGENT_ENDPOINT string = isBicep ? bicepDeployment!.outputs.AZURE_AI_AGENT_ENDPOINT : avmDeployment!.outputs.AZURE_AI_AGENT_ENDPOINT
output AZURE_AI_AGENT_RESOURCE_GROUP_NAME string = isBicep ? bicepDeployment!.outputs.AZURE_AI_AGENT_RESOURCE_GROUP_NAME : avmDeployment!.outputs.AZURE_AI_AGENT_RESOURCE_GROUP_NAME
output AZURE_AI_AGENT_SUBSCRIPTION_ID string = isBicep ? bicepDeployment!.outputs.AZURE_AI_AGENT_SUBSCRIPTION_ID : avmDeployment!.outputs.AZURE_AI_AGENT_SUBSCRIPTION_ID
output AI_PROJECT_ENDPOINT string = isBicep ? bicepDeployment!.outputs.AI_PROJECT_ENDPOINT : avmDeployment!.outputs.AI_PROJECT_ENDPOINT
output AZURE_CLIENT_ID string = isBicep ? bicepDeployment!.outputs.AZURE_CLIENT_ID : avmDeployment!.outputs.AZURE_CLIENT_ID
output AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME string = isBicep ? bicepDeployment!.outputs.AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME : avmDeployment!.outputs.AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME
output AZURE_BLOB_CONTAINER_NAME string = isBicep ? bicepDeployment!.outputs.AZURE_BLOB_CONTAINER_NAME : avmDeployment!.outputs.AZURE_BLOB_CONTAINER_NAME
output COSMOSDB_DATABASE string = isBicep ? bicepDeployment!.outputs.COSMOSDB_DATABASE : avmDeployment!.outputs.COSMOSDB_DATABASE
output COSMOSDB_BATCH_CONTAINER string = isBicep ? bicepDeployment!.outputs.COSMOSDB_BATCH_CONTAINER : avmDeployment!.outputs.COSMOSDB_BATCH_CONTAINER
output COSMOSDB_FILE_CONTAINER string = isBicep ? bicepDeployment!.outputs.COSMOSDB_FILE_CONTAINER : avmDeployment!.outputs.COSMOSDB_FILE_CONTAINER
output COSMOSDB_LOG_CONTAINER string = isBicep ? bicepDeployment!.outputs.COSMOSDB_LOG_CONTAINER : avmDeployment!.outputs.COSMOSDB_LOG_CONTAINER
output APPLICATIONINSIGHTS_CONNECTION_STRING string = isBicep ? bicepDeployment!.outputs.APPLICATIONINSIGHTS_CONNECTION_STRING : avmDeployment!.outputs.APPLICATIONINSIGHTS_CONNECTION_STRING
output MIGRATOR_AGENT_MODEL_DEPLOY string = isBicep ? bicepDeployment!.outputs.MIGRATOR_AGENT_MODEL_DEPLOY : avmDeployment!.outputs.MIGRATOR_AGENT_MODEL_DEPLOY
output PICKER_AGENT_MODEL_DEPLOY string = isBicep ? bicepDeployment!.outputs.PICKER_AGENT_MODEL_DEPLOY : avmDeployment!.outputs.PICKER_AGENT_MODEL_DEPLOY
output FIXER_AGENT_MODEL_DEPLOY string = isBicep ? bicepDeployment!.outputs.FIXER_AGENT_MODEL_DEPLOY : avmDeployment!.outputs.FIXER_AGENT_MODEL_DEPLOY
output SEMANTIC_VERIFIER_AGENT_MODEL_DEPLOY string = isBicep ? bicepDeployment!.outputs.SEMANTIC_VERIFIER_AGENT_MODEL_DEPLOY : avmDeployment!.outputs.SEMANTIC_VERIFIER_AGENT_MODEL_DEPLOY
output SYNTAX_CHECKER_AGENT_MODEL_DEPLOY string = isBicep ? bicepDeployment!.outputs.SYNTAX_CHECKER_AGENT_MODEL_DEPLOY : avmDeployment!.outputs.SYNTAX_CHECKER_AGENT_MODEL_DEPLOY
output DEPLOYMENT_FLAVOR string = isBicep ? bicepDeployment!.outputs.DEPLOYMENT_FLAVOR : avmDeployment!.outputs.DEPLOYMENT_FLAVOR
