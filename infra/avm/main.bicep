// ========== main.bicep (AVM flavor) ========== //
// Uses Azure Verified Modules (br/public:avm/...) via toolkit wrappers.
targetScope = 'resourceGroup'

// ==============================================================================
// Parameters
// ==============================================================================

// ── Core ──

@minLength(3)
@maxLength(16)
@description('Required. A unique application/solution name for all resources in this deployment.')
param solutionName string = 'containermig'

@maxLength(5)
@description('Optional. A unique text suffix appended to resource names for uniqueness.')
param solutionUniqueText string = substring(uniqueString(subscription().id, resourceGroup().name, solutionName), 0, 5)

@description('Optional. Primary Azure region for resource deployment. Defaults to resource group location.')
param location string = ''

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
      'OpenAI.GlobalStandard.gpt-5.1,500'
    ]
  }
})
@description('Required. Location for AI Foundry and model deployments.')
param azureAiServiceLocation string

@description('Optional. Secondary location for Cosmos DB resources.')
param cosmosLocation string = 'eastus2'

// ── AI Configuration ──

@allowed([
  'Standard'
  'GlobalStandard'
])
@description('Optional. GPT model deployment type.')
param deploymentType string = 'GlobalStandard'

@description('Optional. Name of the GPT model to deploy.')
param gptModelName string = 'gpt-5.1'

@description('Optional. Version of the GPT model.')
param gptModelVersion string = '2025-11-13'

@description('Optional. GPT model deployment capacity (tokens per minute in thousands).')
param gptDeploymentCapacity int = 500

@description('Optional. Name of the embedding model to deploy.')
param embeddingModel string = 'text-embedding-3-large'

@description('Optional. Version of the embedding model.')
param embeddingModelVersion string = '1'

@allowed([
  'Standard'
  'GlobalStandard'
])
@description('Optional. Embedding model deployment type.')
param embeddingDeploymentType string = 'GlobalStandard'

@description('Optional. Embedding model deployment capacity.')
param embeddingDeploymentCapacity int = 500

// ── Container Apps Configuration ──

@description('Optional. The endpoint (excluding https://) of an existing container registry.')
param containerRegistryEndpoint string = 'cmsacontainerreg.azurecr.io'

@description('Optional. The image tag to use for container images.')
param imageTag string = 'latest_2025-11-10_599'

// ── Identity ──

@description('Optional. Resource ID of an existing Foundry project.')
param existingFoundryProjectResourceId string = ''

@description('Optional. Existing Log Analytics Workspace Resource ID.')
param existingLogAnalyticsWorkspaceId string = ''

@description('Optional. The tags to apply to all deployed Azure resources.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@description('Optional. Enable private networking for applicable resources.')
param enablePrivateNetworking bool = false

@description('Optional. Enable monitoring for applicable resources.')
param enableMonitoring bool = false

@secure()
@description('Optional. The user name for the administrator account of the virtual machine. Required by Azure at provisioning time but not used for login when Entra ID is enabled.')
param vmAdminUsername string?

@secure()
@description('Optional. The password for the administrator account of the virtual machine. Auto-generated if not provided. Not used for login when Entra ID is enabled.')
param vmAdminPassword string?

@description('Optional. The size of the virtual machine. Defaults to Standard_D2s_v5.')
param vmSize string = 'Standard_D2s_v5'

// ==============================================================================
// Variables
// ==============================================================================

var solutionLocation = empty(location) ? resourceGroup().location : location

var solutionSuffix = toLower(trim(replace(
  replace(
    replace(replace(replace(replace('${solutionName}${solutionUniqueText}', '-', ''), '_', ''), '.', ''), '/', ''),
    ' ',
    ''
  ),
  '*',
  ''
)))

var deployerInfo = deployer()
var deployingUserPrincipalId = deployerInfo.objectId
var deployingUserPrincipalType = contains(deployerInfo, 'userPrincipalName') ? 'User' : 'ServicePrincipal'

var createdBy = contains(deployerInfo, 'userPrincipalName')
  ? split(deployerInfo.userPrincipalName, '@')[0]
  : deployerInfo.objectId

var existingTags = resourceGroup().tags ?? {}
var useExistingLogAnalytics = !empty(existingLogAnalyticsWorkspaceId)

var aiModelDeployments = [
  {
    name: gptModelName
    model: gptModelName
    sku: {
      name: deploymentType
      capacity: gptDeploymentCapacity
    }
    version: gptModelVersion
    raiPolicyName: 'Microsoft.Default'
  }
  {
    name: embeddingModel
    model: embeddingModel
    sku: {
      name: embeddingDeploymentType
      capacity: embeddingDeploymentCapacity
    }
    version: embeddingModelVersion
    raiPolicyName: 'Microsoft.Default'
  }
]

var cosmosDatabaseName = 'migration_db'
var cosmosContainers = [
  { name: 'processes', partitionKeyPath: '/batch_id' }
  { name: 'agent_telemetry', partitionKeyPath: '/log_id' }
  { name: 'processcontrol', partitionKeyPath: '/_partitionKey' }
  { name: 'files', partitionKeyPath: '/file_id' }
  { name: 'process_statuses', partitionKeyPath: '/_partitionKey' }
]

var processBlobContainerName = 'processes'
var processQueueName = 'processes-queue'

// ========== Resource Group Tag ========== //
resource resourceGroupTags 'Microsoft.Resources/tags@2023-07-01' = {
  name: 'default'
  properties: {
    tags: union(
      existingTags,
      tags,
      {
        TemplateName: 'Container Migration'
        CreatedBy: createdBy
        DeploymentName: deployment().name
        Type: enablePrivateNetworking ? 'WAF' : 'Non-WAF'
        DeploymentFlavor: enablePrivateNetworking ? 'avm-waf' : 'avm'
      }
    )
  }
}

// ========== Monitoring (Log Analytics) ========== //

module log_analytics './modules/monitoring/log-analytics.bicep' = if (!useExistingLogAnalytics) {
  name: take('module.log-analytics.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    location: solutionLocation
    enableTelemetry: enableTelemetry
  }
}

var logAnalyticsWorkspaceResourceId = useExistingLogAnalytics
  ? existingLogAnalyticsWorkspaceId
  : log_analytics!.outputs.resourceId

// ========== AI Foundry and related resources ========== //

module ai_foundry_project './modules/ai/ai-foundry-project.bicep' = if (empty(existingFoundryProjectResourceId)) {
  name: take('module.ai-foundry-project.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    location: azureAiServiceLocation
    enableTelemetry: enableTelemetry
  }
  scope: resourceGroup(resourceGroup().name)
}

// ========== Unified AI Foundry resource name vars ========== //
var useExistingAIProject = !empty(existingFoundryProjectResourceId)
var aiFoundryResourceName = useExistingAIProject ? split(existingFoundryProjectResourceId, '/')[8] : ai_foundry_project!.outputs.name
var aiProjectResourceName = useExistingAIProject ? split(existingFoundryProjectResourceId, '/')[10] : ai_foundry_project!.outputs.projectName
var aiServiceSubscription = useExistingAIProject ? split(existingFoundryProjectResourceId, '/')[2] : subscription().subscriptionId
var aiServiceResourceGroup = useExistingAIProject ? split(existingFoundryProjectResourceId, '/')[4] : resourceGroup().name

module existing_project_setup './modules/ai/existing-project-setup.bicep' = if (useExistingAIProject) {
  name: take('module.existing-project-setup.${solutionName}', 64)
  scope: resourceGroup(aiServiceSubscription, aiServiceResourceGroup)
  params: {
    name: aiFoundryResourceName
    projectName: aiProjectResourceName
  }
}

module foundry_storage_connection './modules/ai/ai-foundry-connection.bicep' = {
  name: take('module.foundry-storage-conn.${solutionName}', 64)
  scope: resourceGroup(aiServiceSubscription, aiServiceResourceGroup)
  params: {
    solutionName: solutionSuffix
    aiServicesAccountName: aiFoundryResourceName
    projectName: aiProjectResourceName
    category: 'AzureBlob'
    target: storage_account.outputs.blobEndpoint
    authType: 'AAD'
    metadata: {
      ResourceId: storage_account.outputs.resourceId
      AccountName: storage_account.outputs.name
      ContainerName: 'default'
    }
  }
}

@batchSize(1)
module model_deployments './modules/ai/ai-foundry-model-deployment.bicep' = [for (deployment, i) in aiModelDeployments: {
  name: take('module.model-deployment-${i}.${solutionName}', 64)
  scope: resourceGroup(aiServiceSubscription, aiServiceResourceGroup)
  params: {
    aiServicesAccountName: aiFoundryResourceName
    deploymentName: deployment.name
    modelName: deployment.model
    modelVersion: deployment.version
    raiPolicyName: deployment.raiPolicyName
    skuName: deployment.sku.name
    skuCapacity: deployment.sku.capacity
  }
}]

var aiFoundryEndpoint = useExistingAIProject ? existing_project_setup!.outputs.cognitiveServicesEndpoint : ai_foundry_project!.outputs.cognitiveServicesEndpoint
var projectEndpoint = useExistingAIProject ? existing_project_setup!.outputs.projectEndpoint : ai_foundry_project!.outputs.projectEndpoint
var aiFoundryResourceId = !useExistingAIProject ? ai_foundry_project!.outputs.resourceId : ''
var aiProjectPrincipalId = useExistingAIProject ? existing_project_setup!.outputs.projectIdentityPrincipalId : ai_foundry_project!.outputs.projectIdentityPrincipalId

// ========== Storage Account module ========== //
module storage_account './modules/data/storage-account.bicep' = {
  name: take('module.storage-account.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    location: solutionLocation
    tags: tags
    containers: [
      { name: 'data', publicAccess: 'None' }
    ]
    enableTelemetry: enableTelemetry
  }
  scope: resourceGroup(resourceGroup().name)
}

// ========== Cosmos DB module ========== //
module cosmosDBModule './modules/data/cosmos-db-nosql.bicep' = {
  name: take('module.cosmos-db.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    name: 'cosmos-${solutionSuffix}'
    location: cosmosLocation
    databaseName: cosmosDatabaseName
    containers: cosmosContainers
    enableTelemetry: enableTelemetry
  }
  scope: resourceGroup(resourceGroup().name)
}

// ========== Container App Environment ========== //
module containerAppEnv './modules/compute/container-app-environment.bicep' = {
  name: take('module.container-app-env.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    location: solutionLocation
    tags: union(existingTags, tags, { TemplateName: 'Container Migration' })
    logAnalyticsWorkspaceResourceId: logAnalyticsWorkspaceResourceId
    enableTelemetry: enableTelemetry
  }
}

// ========== Container Apps ========== //
var backendContainerAppName = take('ca-backend-api-${solutionSuffix}', 32)
var processorContainerAppName = take('ca-processor-${solutionSuffix}', 32)
var frontEndContainerAppName = take('ca-frontend-${solutionSuffix}', 32)

// ========== Backend API Container App ========== //
module ca_backend_api './modules/compute/container-app.bicep' = {
  name: take('module.ca-backend-api.${solutionName}', 64)
  params: {
    name: backendContainerAppName
    location: solutionLocation
    tags: union(existingTags, tags, { TemplateName: 'Container Migration' })
    environmentResourceId: containerAppEnv.outputs.resourceId
    managedIdentities: { systemAssigned: true }
    ingressExternal: true
    ingressTargetPort: 8000
    enableTelemetry: enableTelemetry
    containers: [
      {
        name: 'cmsabackend'
        image: '${containerRegistryEndpoint}/cmsabackend:${imageTag}'
        env: [
          // CosmosDB — names read by config.py
          { name: 'COSMOSDB_ENDPOINT', value: cosmosDBModule.outputs.endpoint }
          { name: 'COSMOSDB_DATABASE', value: cosmosDatabaseName }
          { name: 'COSMOSDB_BATCH_CONTAINER', value: 'processes' }
          { name: 'COSMOSDB_FILE_CONTAINER', value: 'files' }
          { name: 'COSMOSDB_LOG_CONTAINER', value: 'agent_telemetry' }
          // Storage — names read by config.py
          { name: 'AZURE_BLOB_ACCOUNT_NAME', value: storage_account.outputs.name }
          { name: 'AZURE_BLOB_CONTAINER_NAME', value: 'data' }
          // AI Foundry / agents — names read by config.py
          { name: 'AI_PROJECT_ENDPOINT', value: projectEndpoint }
          { name: 'AZURE_AI_AGENT_ENDPOINT', value: projectEndpoint }
          { name: 'AZURE_AI_AGENT_PROJECT_NAME', value: aiProjectResourceName }
          { name: 'AZURE_AI_AGENT_RESOURCE_GROUP_NAME', value: aiServiceResourceGroup }
          { name: 'AZURE_AI_AGENT_SUBSCRIPTION_ID', value: aiServiceSubscription }
          { name: 'AZURE_AI_AGENT_PROJECT_CONNECTION_STRING', value: projectEndpoint }
          { name: 'AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME', value: gptModelName }
          { name: 'MIGRATOR_AGENT_MODEL_DEPLOY', value: gptModelName }
          { name: 'PICKER_AGENT_MODEL_DEPLOY', value: gptModelName }
          { name: 'FIXER_AGENT_MODEL_DEPLOY', value: gptModelName }
          { name: 'SEMANTIC_VERIFIER_AGENT_MODEL_DEPLOY', value: gptModelName }
          { name: 'SYNTAX_CHECKER_AGENT_MODEL_DEPLOY', value: gptModelName }
          // App config
          { name: 'APP_ENV', value: 'Prod' }
        ]
        resources: {
          cpu: json('1')
          memory: '2.0Gi'
        }
      }
    ]
    corsPolicy: {
      allowedOrigins: ['*']
      allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
      allowedHeaders: ['Authorization', 'Content-Type', '*']
    }
    scaleSettings: {
      maxReplicas: 1
      minReplicas: 1
    }
  }
}

// ========== Frontend Container App ========== //
module ca_frontend './modules/compute/container-app.bicep' = {
  name: take('module.ca-frontend.${solutionName}', 64)
  params: {
    name: frontEndContainerAppName
    location: solutionLocation
    tags: union(existingTags, tags, { TemplateName: 'Container Migration' })
    environmentResourceId: containerAppEnv.outputs.resourceId
    managedIdentities: { systemAssigned: true }
    ingressExternal: true
    ingressTargetPort: 3000
    enableTelemetry: enableTelemetry
    containers: [
      {
        name: 'cmsafrontend'
        image: '${containerRegistryEndpoint}/cmsafrontend:${imageTag}'
        env: [
          { name: 'API_URL', value: 'https://${ca_backend_api.outputs.fqdn}' }
          { name: 'APP_ENV', value: 'prod' }
          { name: 'REACT_APP_MSAL_POST_REDIRECT_URL', value: '/' }
          { name: 'REACT_APP_MSAL_REDIRECT_URL', value: '/' }
          { name: 'ALLOWED_ORIGINS', value: 'https://${frontEndContainerAppName}.${containerAppEnv.outputs.defaultDomain}' }
        ]
        resources: {
          cpu: json('1')
          memory: '2.0Gi'
        }
      }
    ]
    scaleSettings: {
      maxReplicas: 1
      minReplicas: 1
    }
  }
}

// ========== Processor Container App ========== //
// NOTE: Processor is not in Code Modernization base; disabled for AVM flavor alignment
module ca_processor './modules/compute/container-app.bicep' = if (false) {
  name: take('module.ca-processor.${solutionName}', 64)
  params: {
    name: processorContainerAppName
    location: solutionLocation
    tags: union(existingTags, tags, { TemplateName: 'Container Migration' })
    environmentResourceId: containerAppEnv.outputs.resourceId
    managedIdentities: { systemAssigned: true }
    ingressExternal: false
    ingressTargetPort: 8080
    ingressAllowInsecure: true
    enableTelemetry: enableTelemetry
    containers: [
      {
        name: 'processor'
        image: '${containerRegistryEndpoint}/processor:${imageTag}'
        env: [
          { name: 'AZURE_OPENAI_ENDPOINT', value: aiFoundryEndpoint }
          { name: 'AZURE_OPENAI_CHAT_DEPLOYMENT_NAME', value: gptModelName }
          { name: 'AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME', value: embeddingModel }
          { name: 'AZURE_OPENAI_API_VERSION', value: '2025-03-01-preview' }
          { name: 'COSMOS_DB_ACCOUNT_URL', value: cosmosDBModule.outputs.endpoint }
          { name: 'COSMOS_DB_DATABASE_NAME', value: cosmosDatabaseName }
          { name: 'COSMOS_DB_CONTAINER_NAME', value: 'agent_telemetry' }
          { name: 'COSMOS_DB_CONTROL_CONTAINER_NAME', value: 'processcontrol' }
          { name: 'COSMOS_DB_PROCESS_CONTAINER', value: 'processes' }
          { name: 'COSMOS_DB_PROCESS_LOG_CONTAINER', value: 'agent_telemetry' }
          { name: 'STORAGE_ACCOUNT_BLOB_URL', value: storage_account.outputs.blobEndpoint }
          { name: 'STORAGE_ACCOUNT_NAME', value: storage_account.outputs.name }
          { name: 'STORAGE_QUEUE_ACCOUNT', value: storage_account.outputs.name }
          { name: 'STORAGE_ACCOUNT_PROCESS_CONTAINER', value: processBlobContainerName }
          { name: 'STORAGE_ACCOUNT_PROCESS_QUEUE', value: processQueueName }
          { name: 'STORAGE_ACCOUNT_QUEUE_URL', value: '${storage_account.outputs.serviceEndpoints.queue}' }
          { name: 'GLOBAL_LLM_SERVICE', value: 'AzureOpenAI' }
          { name: 'CONTROL_API_ENABLED', value: '1' }
          { name: 'CONTROL_API_PORT', value: '8080' }
        ]
        resources: {
          cpu: json('2')
          memory: '4.0Gi'
        }
      }
    ]
    scaleSettings: {
      maxReplicas: 1
      minReplicas: 1
    }
  }
}

// ========== Virtual Network (WAF — private networking) ========== //
module virtualNetwork './modules/networking/virtual-network.bicep' = if (enablePrivateNetworking) {
  name: take('module.virtual-network.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    location: solutionLocation
    addressPrefixes: ['10.0.0.0/20']
    tags: union(existingTags, tags, { TemplateName: 'Container Migration' })
    logAnalyticsWorkspaceId: enableMonitoring ? logAnalyticsWorkspaceResourceId : ''
    resourceSuffix: solutionSuffix
    enableTelemetry: enableTelemetry
  }
}

// ========== Bastion Host (WAF — private networking) ========== //
module bastionHost './modules/networking/bastion-host.bicep' = if (enablePrivateNetworking) {
  name: take('module.bastion-host.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    location: solutionLocation
    tags: union(existingTags, tags, { TemplateName: 'Container Migration' })
    enableTelemetry: enableTelemetry
    virtualNetworkResourceId: virtualNetwork!.outputs.resourceId
    diagnosticSettings: enableMonitoring ? [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }] : null
  }
}

// ========== Jumpbox VM (WAF — private networking) ========== //
// Login is via Microsoft Entra ID through Azure Bastion (not local credentials)
module virtualMachine './modules/compute/virtual-machine.bicep' = if (enablePrivateNetworking) {
  name: take('module.virtual-machine.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    location: solutionLocation
    tags: union(existingTags, tags, { TemplateName: 'Container Migration' })
    enableTelemetry: enableTelemetry
    vmSize: vmSize
    adminUsername: vmAdminUsername ?? 'testvmuser'
    adminPassword: vmAdminPassword ?? 'Vm!${uniqueString(subscription().subscriptionId, solutionName)}${guid(subscription().subscriptionId, solutionName, 'vm-admin-password')}'
    subnetResourceId: virtualNetwork!.outputs.administrationSubnetResourceId
    deployingUserPrincipalId: deployingUserPrincipalId
    deployingUserPrincipalType: deployingUserPrincipalType
    roleAssignments: [
      {
        roleDefinitionIdOrName: '1c0163c0-47e6-4577-8991-ea5c82e286e4' // Virtual Machine Administrator Login
        principalId: deployingUserPrincipalId
        principalType: deployingUserPrincipalType
      }
    ]
    diagnosticSettings: enableMonitoring ? [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }] : null
  }
}

// ========== Role Assignments ========== //
module role_assignments './modules/identity/role-assignments.bicep' = {
  name: take('module.role-assignments.${solutionName}', 64)
  params: {
    solutionName: solutionSuffix
    useExistingAIProject: useExistingAIProject
    existingFoundryProjectResourceId: existingFoundryProjectResourceId
    aiFoundryResourceId: !useExistingAIProject ? aiFoundryResourceId : ''
    aiSearchResourceId: ''
    storageAccountResourceId: storage_account.outputs.resourceId
    aiProjectPrincipalId: aiProjectPrincipalId
    aiSearchPrincipalId: ''
    backendAppServicePrincipalId: ca_backend_api.outputs.principalId
    processorAppServicePrincipalId: '' // Processor not deployed in Code Modernization alignment
    cosmosDbAccountName: cosmosDBModule.outputs.name
  }
  scope: resourceGroup(resourceGroup().name)
}

// ==============================================================================
// Outputs
// ==============================================================================

@description('Solution suffix used for naming resources')
output SOLUTION_NAME string = solutionSuffix

@description('Name of the deployed resource group')
output RESOURCE_GROUP_NAME string = resourceGroup().name

@description('The name of the web app container app.')
output CONTAINER_WEB_APP_NAME string = ca_frontend.outputs.name

@description('The FQDN of the web app container app.')
output CONTAINER_WEB_APP_FQDN string = ca_frontend.outputs.fqdn

@description('The name of the API container app.')
output CONTAINER_API_APP_NAME string = ca_backend_api.outputs.name

@description('The FQDN of the API container app.')
output CONTAINER_API_APP_FQDN string = ca_backend_api.outputs.fqdn

@description('Azure OpenAI service endpoint URL')
output AZURE_OPENAI_ENDPOINT string = aiFoundryEndpoint

@description('GPT model deployment name')
output AZURE_ENV_GPT_MODEL_NAME string = gptModelName

@description('Embedding model deployment name')
output AZURE_ENV_EMBEDDING_DEPLOYMENT_NAME string = embeddingModel

@description('Cosmos DB account name')
output AZURE_COSMOSDB_ACCOUNT string = cosmosDBModule.outputs.name

@description('Cosmos DB database name')
output AZURE_COSMOSDB_DATABASE string = cosmosDatabaseName

@description('The Azure subscription ID.')
output AZURE_SUBSCRIPTION_ID string = subscription().subscriptionId

@description('The Azure resource group name.')
output AZURE_RESOURCE_GROUP string = resourceGroup().name

@description('Azure AI Agent service endpoint URL')
output AZURE_AI_AGENT_ENDPOINT string = projectEndpoint

// Compatibility outputs to preserve base root template contract across flavors.
output resourceGroupName string = resourceGroup().name
output WEB_APP_URL string = 'https://${ca_frontend.outputs.fqdn}'
output COSMOSDB_ENDPOINT string = cosmosDBModule.outputs.endpoint
output AZURE_BLOB_ACCOUNT_NAME string = storage_account.outputs.name
output AZURE_BLOB_ENDPOINT string = storage_account.outputs.blobEndpoint
output AZURE_AI_AGENT_PROJECT_NAME string = aiProjectResourceName
output AZURE_AI_AGENT_PROJECT_CONNECTION_STRING string = projectEndpoint
output AZURE_AI_AGENT_RESOURCE_GROUP_NAME string = resourceGroup().name
output AZURE_AI_AGENT_SUBSCRIPTION_ID string = subscription().subscriptionId
output AI_PROJECT_ENDPOINT string = projectEndpoint
output AZURE_CLIENT_ID string = ''
output AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME string = gptModelName
output AZURE_BLOB_CONTAINER_NAME string = processBlobContainerName
output COSMOSDB_DATABASE string = cosmosDatabaseName
output COSMOSDB_BATCH_CONTAINER string = 'processes'
output COSMOSDB_FILE_CONTAINER string = 'files'
output COSMOSDB_LOG_CONTAINER string = 'agent_telemetry'
output APPLICATIONINSIGHTS_CONNECTION_STRING string = ''
output MIGRATOR_AGENT_MODEL_DEPLOY string = gptModelName
output PICKER_AGENT_MODEL_DEPLOY string = gptModelName
output FIXER_AGENT_MODEL_DEPLOY string = gptModelName
output SEMANTIC_VERIFIER_AGENT_MODEL_DEPLOY string = gptModelName
output SYNTAX_CHECKER_AGENT_MODEL_DEPLOY string = gptModelName
