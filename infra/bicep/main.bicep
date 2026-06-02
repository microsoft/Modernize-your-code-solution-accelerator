metadata name = 'Modernize Your Code Solution Accelerator - Bicep Flavor'
metadata description = 'Thin bicep flavor wrapper that preserves the flavor-specific entrypoint and delegates to the shared implementation.'
targetScope = 'resourceGroup'

@allowed([
  'bicep'
  'avm'
  'avm-waf'
])
@description('Deployment flavor selector. This wrapper is intended for bicep flavor routing.')
param deploymentFlavor string = 'bicep'

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
@description('Optional. Set the Image tag.')
param imageTag string = 'latest_2025-11-10_599'

@description('Optional. Azure Container Registry endpoint.')
param containerRegistryEndpoint string = 'cmsacontainerreg.azurecr.io'

@minLength(1)
@description('Optional. Version of the GPT model to deploy. Defaults to 2024-08-06.')
param gptModelVersion string = '2024-08-06'

@description('Optional. Use this parameter to use an existing AI project resource ID. Defaults to empty string.')
param existingFoundryProjectResourceId string = ''

@description('Optional. Use this parameter to use an existing Log Analytics workspace resource ID. Defaults to empty string.')
param existingLogAnalyticsWorkspaceId string = ''

@description('Optional. Tag, Created by user name. Defaults to user principal name or object ID.')
param createdBy string = contains(deployer(), 'userPrincipalName') ? split(deployer().userPrincipalName, '@')[0] : deployer().objectId

module implementation '../avm/main.bicep' = {
  name: take('module.bicep.shared.${solutionName}', 64)
  params: {
    deploymentFlavor: deploymentFlavor
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
    imageTag: imageTag
    containerRegistryEndpoint: containerRegistryEndpoint
    gptModelVersion: gptModelVersion
    existingFoundryProjectResourceId: existingFoundryProjectResourceId
    existingLogAnalyticsWorkspaceId: existingLogAnalyticsWorkspaceId
    createdBy: createdBy
  }
}

output resourceGroupName string = implementation.outputs.resourceGroupName
output WEB_APP_URL string = implementation.outputs.WEB_APP_URL
output COSMOSDB_ENDPOINT string = implementation.outputs.COSMOSDB_ENDPOINT
output AZURE_BLOB_ACCOUNT_NAME string = implementation.outputs.AZURE_BLOB_ACCOUNT_NAME
output AZURE_BLOB_ENDPOINT string = implementation.outputs.AZURE_BLOB_ENDPOINT
output AZURE_AI_AGENT_PROJECT_NAME string = implementation.outputs.AZURE_AI_AGENT_PROJECT_NAME
output AZURE_AI_AGENT_ENDPOINT string = implementation.outputs.AZURE_AI_AGENT_ENDPOINT
output AZURE_AI_AGENT_PROJECT_CONNECTION_STRING string = implementation.outputs.AZURE_AI_AGENT_PROJECT_CONNECTION_STRING
output AZURE_AI_AGENT_RESOURCE_GROUP_NAME string = implementation.outputs.AZURE_AI_AGENT_RESOURCE_GROUP_NAME
output AZURE_AI_AGENT_SUBSCRIPTION_ID string = implementation.outputs.AZURE_AI_AGENT_SUBSCRIPTION_ID
output AI_PROJECT_ENDPOINT string = implementation.outputs.AI_PROJECT_ENDPOINT
output AZURE_CLIENT_ID string = implementation.outputs.AZURE_CLIENT_ID
output AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME string = implementation.outputs.AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME
output AZURE_BLOB_CONTAINER_NAME string = implementation.outputs.AZURE_BLOB_CONTAINER_NAME
output COSMOSDB_DATABASE string = implementation.outputs.COSMOSDB_DATABASE
output COSMOSDB_BATCH_CONTAINER string = implementation.outputs.COSMOSDB_BATCH_CONTAINER
output COSMOSDB_FILE_CONTAINER string = implementation.outputs.COSMOSDB_FILE_CONTAINER
output COSMOSDB_LOG_CONTAINER string = implementation.outputs.COSMOSDB_LOG_CONTAINER
output APPLICATIONINSIGHTS_CONNECTION_STRING string = implementation.outputs.APPLICATIONINSIGHTS_CONNECTION_STRING
output MIGRATOR_AGENT_MODEL_DEPLOY string = implementation.outputs.MIGRATOR_AGENT_MODEL_DEPLOY
output PICKER_AGENT_MODEL_DEPLOY string = implementation.outputs.PICKER_AGENT_MODEL_DEPLOY
output FIXER_AGENT_MODEL_DEPLOY string = implementation.outputs.FIXER_AGENT_MODEL_DEPLOY
output SEMANTIC_VERIFIER_AGENT_MODEL_DEPLOY string = implementation.outputs.SEMANTIC_VERIFIER_AGENT_MODEL_DEPLOY
output SYNTAX_CHECKER_AGENT_MODEL_DEPLOY string = implementation.outputs.SYNTAX_CHECKER_AGENT_MODEL_DEPLOY
output DEPLOYMENT_FLAVOR string = implementation.outputs.DEPLOYMENT_FLAVOR
