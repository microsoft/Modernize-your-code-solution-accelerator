@minLength(3)
@maxLength(20)
@description('A unique application/env name for all resources in this deployment. This should be 3-20 characters long')
param environmentName string

@minLength(3)
@description('Azure region for all services.')
param location string = resourceGroup().location

@allowed([
  'australiaeast'
  'brazilsouth'
  'canadacentral'
  'canadaeast'
  'eastus'
  'eastus2'
  'francecentral'
  'germanywestcentral'
  'japaneast'
  'koreacentral'
  'northcentralus'
  'norwayeast'
  'polandcentral'
  'southafricanorth'
  'southcentralus'
  'southindia'
  'swedencentral'
  'switzerlandnorth'
  'uaenorth'
  'uksouth'
  'westeurope'
  'westus'
  'westus3'
])
@description('Location for all AI service resources. This location can be different from the resource group location.')
param azureAiServiceLocation string = location

@description('AI model deployment token capacity. Defaults to 5K tokens per minute.')
param capacity int = 5

@description('Enable monitoring for the resources. This will enable Application Insights and Log Analytics. Defaults to false.')
param enableMonitoring bool = false

@description('Optional. Specifies the resource tags for all the resources. Tag "azd-env-name" is automatically added to all resources.')
param tags object = {}

var abbrs = loadJsonContent('./abbreviations.json')

var resourcesName = trim(replace(replace(replace(replace(replace(environmentName, '-', ''), '_', ''), '.', ''),'/', ''), ' ', ''))
var resourcesToken = substring(uniqueString(subscription().id, location, resourcesName), 0, 5)
var uniqueResourcesName = '${resourcesName}${resourcesToken}'

var defaultTags = {
  'azd-env-name': resourcesName
}
var allTags = union(defaultTags, tags)

var modelDeployment =  {
  name: 'gpt-4o'
  model: {
    name: 'gpt-4o'
    format: 'OpenAI'
    version: '2024-08-06'
  }
  sku: {
    name: 'GlobalStandard'
    capacity: capacity
  }
  raiPolicyName: 'Microsoft.Default'
}

module managedIdentity 'br/public:avm/res/managed-identity/user-assigned-identity:0.4.1' = {
  name: take('identity-${resourcesName}-deployment', 64)
  params: {
    name: '${abbrs.security.managedIdentity}${resourcesName}'
    location: location
    tags: allTags
  }
}

module logAnalyticsWorkspace 'br/public:avm/res/operational-insights/workspace:0.11.2' = if (enableMonitoring) {
  name: take('log-analytics-${resourcesName}-deployment', 64)
  params: {
    name: '${abbrs.managementGovernance.logAnalyticsWorkspace}${resourcesName}'
    location: location
    skuName: 'PerGB2018'
    dataRetention: 30
    diagnosticSettings: [{ useThisWorkspace: true }]
    tags: allTags
  }
}

module applicationInsights 'br/public:avm/res/insights/component:0.6.0' = if (enableMonitoring) {
  name: take('app-insights-${resourcesName}-deployment', 64)
  params: {
    name: '${abbrs.managementGovernance.applicationInsights}${resourcesName}'
    location: location
    workspaceResourceId: logAnalyticsWorkspace.outputs.resourceId
    diagnosticSettings: [{ workspaceResourceId: logAnalyticsWorkspace.outputs.resourceId }]
    tags: allTags
  }
}

module azureAiServices 'br/public:avm/res/cognitive-services/account:0.10.2' = {
  name: take('aiservices-${resourcesName}-deployment', 64)
  params: {
    name: '${abbrs.ai.aiServices}${uniqueResourcesName}'
    location: location
    sku: 'S0'
    kind: 'AIServices'
    customSubDomainName: '${abbrs.ai.aiServices}${uniqueResourcesName}'
    disableLocalAuth: false
    publicNetworkAccess: 'Enabled'
    deployments: [modelDeployment]
    diagnosticSettings: enableMonitoring ? [{workspaceResourceId: logAnalyticsWorkspace.outputs.resourceId}] : []
    roleAssignments: [
      {
        principalId: managedIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: 'Cognitive Services OpenAI Contributor'
      }
    ]
    tags: allTags
  }
}

module keyvault 'br/public:avm/res/key-vault/vault:0.12.1' = {
  name: take('keyvault-${resourcesName}-deployment', 64)
  params: {
    name: take('${abbrs.security.keyVault}${uniqueResourcesName}', 24)
    location: location
    createMode: 'default'
    sku: 'standard'
    enableVaultForDeployment: true
    enableVaultForDiskEncryption: true
    enableVaultForTemplateDeployment: true
    enableRbacAuthorization: true
    publicNetworkAccess: 'Enabled'
    softDeleteRetentionInDays: 7
    diagnosticSettings: enableMonitoring ? [{workspaceResourceId: logAnalyticsWorkspace.outputs.resourceId}] : []
    roleAssignments: [
      {
        principalId: managedIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: 'Key Vault Administrator'
      }
    ]
    tags: allTags
  }
}

module azureAifoundry 'modules/aiFoundry.bicep' = {
  name: take('aifoundry-${resourcesName}-deployment', 64)
  params: {
    location: azureAiServiceLocation
    hubName: '${abbrs.ai.hub}${resourcesName}'
    hubDescription: 'AI Hub for Modernize Your Code'
    projectName: '${abbrs.ai.project}${resourcesName}'
    storageName: take('${abbrs.storage.storageAccount}ai${uniqueResourcesName}', 24)
    keyVaultResourceId: keyvault.outputs.resourceId
    managedIdentityPrincpalId: managedIdentity.outputs.principalId
    logAnalyticsWorkspaceResourceId: enableMonitoring ? logAnalyticsWorkspace.outputs.resourceId : ''
    aiServicesName: azureAiServices.outputs.name
    tags: allTags
  }
}

module cosmosDb 'modules/cosmosDb.bicep' = {
  name: take('cosmos-${resourcesName}-deployment', 64)
  params: {
    name: '${abbrs.databases.cosmosDBDatabase}${uniqueResourcesName}'
    location: location
    managedIdentityPrincipalId: managedIdentity.outputs.principalId
    logAnalyticsWorkspaceResourceId: enableMonitoring ? logAnalyticsWorkspace.outputs.resourceId : ''
    tags: allTags
  }
}

module containerAppsEnvironment 'br/public:avm/res/app/managed-environment:0.11.2' = {
  name: take('container-env-${resourcesName}-deployment', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [applicationInsights] // required due to optional flags that could change dependency
  params: {
    name: '${abbrs.containers.containerAppsEnvironment}${resourcesName}'
    location: location
    zoneRedundant: false
    publicNetworkAccess: 'Enabled'
    managedIdentities: {
      userAssignedResourceIds: [
        managedIdentity.outputs.resourceId
      ]
    }
    appInsightsConnectionString: enableMonitoring ? applicationInsights.outputs.connectionString : null
    appLogsConfiguration: enableMonitoring ? {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.outputs.logAnalyticsWorkspaceId
        sharedKey: logAnalyticsWorkspace.outputs.primarySharedKey
      }
    } : {}
    tags: allTags
  }
}

var appStorageContainerName = 'appstorage'

module containerAppFrontend 'br/public:avm/res/app/container-app:0.16.0' = {
  name: take('container-app-frontend-${resourcesName}-deployment', 64)
  params: {
    name: take('${abbrs.containers.containerApp}${uniqueResourcesName}frontend', 32)
    location: location
    environmentResourceId: containerAppsEnvironment.outputs.resourceId
    managedIdentities: {
      userAssignedResourceIds: [
        managedIdentity.outputs.resourceId
      ]
    }
    containers: [
      {
        env: [
          {
            name: 'API_URL'
            value: 'https://${containerAppBackend.outputs.fqdn}'
          }
        ]
        image: 'cmsacontainerreg.azurecr.io/cmsafrontend:latest'
        name: 'cmsafrontend'
        resources: {
          cpu: '1'
          memory: '2.0Gi'
        }
      }
    ]
    ingressTargetPort: 3000
    ingressExternal: true
    scaleSettings: {
      minReplicas: 1
      maxReplicas: 1
    }
    tags: allTags
  }
}

module containerAppBackend 'br/public:avm/res/app/container-app:0.16.0' = {
  name: take('container-app-backend-${resourcesName}-deployment', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [applicationInsights] // required due to optional flags that could change dependency
  params: {
    name: take('${abbrs.containers.containerApp}${uniqueResourcesName}backend', 32)
    location: location
    environmentResourceId: containerAppsEnvironment.outputs.resourceId
    managedIdentities: {
      userAssignedResourceIds: [
        managedIdentity.outputs.resourceId
      ]
    }
    containers: [
      {
        name: 'cmsabackend'
        image: 'cmsacontainerreg.azurecr.io/cmsabackend:latest'
        env: concat([
          {
            name: 'COSMOSDB_ENDPOINT'
            value: cosmosDb.outputs.endpoint
          }
          {
            name: 'COSMOSDB_DATABASE'
            value: cosmosDb.outputs.databaseName
          }
          {
            name: 'COSMOSDB_BATCH_CONTAINER'
            value: cosmosDb.outputs.containers.batch.name
          }
          {
            name: 'COSMOSDB_FILE_CONTAINER'
            value: cosmosDb.outputs.containers.file.name
          }
          {
            name: 'COSMOSDB_LOG_CONTAINER'
            value: cosmosDb.outputs.containers.log.name
          }
          {
            name: 'AZURE_BLOB_ACCOUNT_NAME'
            value: storageAccountForContainers.outputs.name
          }
          {
            name: 'AZURE_BLOB_CONTAINER_NAME'
            value: appStorageContainerName
          }
          {
            name: 'AZURE_OPENAI_ENDPOINT'
            value: 'https://${azureAiServices.outputs.name}.openai.azure.com/'
          }
          {
            name: 'MIGRATOR_AGENT_MODEL_DEPLOY'
            value: modelDeployment.name
          }
          {
            name: 'PICKER_AGENT_MODEL_DEPLOY'
            value: modelDeployment.name
          }
          {
            name: 'FIXER_AGENT_MODEL_DEPLOY'
            value: modelDeployment.name
          }
          {
            name: 'SEMANTIC_VERIFIER_AGENT_MODEL_DEPLOY'
            value: modelDeployment.name
          }
          {
            name: 'SYNTAX_CHECKER_AGENT_MODEL_DEPLOY'
            value: modelDeployment.name
          }
          {
            name: 'SELECTION_MODEL_DEPLOY'
            value: modelDeployment.name
          }
          {
            name: 'TERMINATION_MODEL_DEPLOY'
            value: modelDeployment.name
          }
          {
            name: 'AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME'
            value: modelDeployment.name
          }
          {
            name: 'AZURE_AI_AGENT_PROJECT_NAME'
            value: azureAifoundry.outputs.projectName
          }
          {
            name: 'AZURE_AI_AGENT_RESOURCE_GROUP_NAME'
            value: resourceGroup().name
          }
          {
            name: 'AZURE_AI_AGENT_SUBSCRIPTION_ID'
            value: subscription().subscriptionId
          }
          {
            name: 'AZURE_AI_AGENT_PROJECT_CONNECTION_STRING'
            value: azureAifoundry.outputs.projectConnectionString
          }
          {
            name: 'AZURE_CLIENT_ID'
            value: managedIdentity.outputs.clientId // TODO - VERIFY -> NOTE: This is the client ID of the managed identity, not the Entra application, and is needed for the App Service to access the Cosmos DB account.
          }
        ], enableMonitoring ? [
          {
            name: 'APPLICATIONINSIGHTS_INSTRUMENTATION_KEY'
            value: applicationInsights.outputs.instrumentationKey
          }
          {
            name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
            value: applicationInsights.outputs.connectionString
          }
        ] : [])
        resources: {
          cpu: 1
          memory: '2.0Gi'
        }
      }
    ]
    ingressTargetPort: 8000
    ingressExternal: true
    scaleSettings: {
      minReplicas: 1
      maxReplicas: 1
    }
    tags: allTags
  }
}

module storageAccountForContainers 'br/public:avm/res/storage/storage-account:0.17.0' = {
  name: take('storage-apps-${resourcesName}-deployment', 64)
  params: {
    name: take('${abbrs.storage.storageAccount}app${uniqueResourcesName}', 24)
    location: location
    managedIdentities: {
      systemAssigned: true
    }
    kind: 'StorageV2'
    skuName: 'Standard_LRS'
    publicNetworkAccess: 'Enabled'
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    allowCrossTenantReplication: false
    requireInfrastructureEncryption: false
    keyType: 'Service'
    enableHierarchicalNamespace: false
    enableNfsV3: false
    largeFileSharesState: 'Disabled'
    minimumTlsVersion: 'TLS1_2'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
    supportsHttpsTrafficOnly: true
    diagnosticSettings: enableMonitoring ? [{workspaceResourceId: logAnalyticsWorkspace.outputs.resourceId}] : []
    blobServices: {
      containers: [
        {
          name: appStorageContainerName
          properties: {
            publicAccess: 'None'
          }
        }
      ]
    }
    roleAssignments: [
      {
        principalId: managedIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: 'Storage Blob Data Contributor'
      }
    ]
    tags: allTags
  }
}
