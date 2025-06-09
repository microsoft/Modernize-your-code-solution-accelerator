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
param enableMonitoring bool = true

@description('Enable scaling for the container apps. Defaults to false.')
param enableScaling bool = true

@description('Enable redundancy for applicable resources. Defaults to false.')
param enableRedundancy bool = true

@description('Optional. The secondary location for the Cosmos DB account if redundancy is enabled.')
param secondaryLocation string?

@description('Optional. Enable private networking for the resources. Set to true to enable private networking.')
param enablePrivateNetworking bool = true

@description('Optional. Specifies the resource tags for all the resources. Tag "azd-env-name" is automatically added to all resources.')
param tags object = {}

var resourcesName = trim(replace(replace(replace(replace(replace(environmentName, '-', ''), '_', ''), '.', ''),'/', ''), ' ', ''))
var resourcesToken = substring(uniqueString(subscription().id, location, resourcesName), 0, 5)
var uniqueResourcesName = '${resourcesName}${resourcesToken}'

var appStorageContainerName = 'appstorage'

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
    name: 'id-${resourcesName}'
    location: location
    tags: allTags
  }
}

module logAnalyticsWorkspace 'br/public:avm/res/operational-insights/workspace:0.11.2' = if (enableMonitoring || enablePrivateNetworking) {
  name: take('log-analytics-${resourcesName}-deployment', 64)
  params: {
    name: 'log-${resourcesName}'
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
    name: 'appi-${resourcesName}'
    location: location
    workspaceResourceId: logAnalyticsWorkspace.outputs.resourceId
    diagnosticSettings: [{ workspaceResourceId: logAnalyticsWorkspace.outputs.resourceId }]
    tags: allTags
  }
}

module network 'modules/network.bicep' = if (enablePrivateNetworking) {
  name: take('network-${resourcesName}-deployment', 64)
  params: {
    resourcesName: resourcesName
    logAnalyticsWorkSpaceResourceId: logAnalyticsWorkspace.outputs.resourceId
    location: location
    tags: allTags
  }
}

module storageAccount 'modules/storageAccount.bicep' = {
  name: take('storage-account-${resourcesName}-deployment', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [logAnalyticsWorkspace, network] // required due to optional flags that could change dependency
  params: {
    name: take('st${uniqueResourcesName}', 24)
    location: location
    tags: allTags
    skuName: enableRedundancy ? 'Standard_GZRS' : 'Standard_LRS'
    logAnalyticsWorkspaceResourceId: enableMonitoring ? logAnalyticsWorkspace.outputs.resourceId : ''
    privateNetworking: enablePrivateNetworking ? {
      virtualNetworkResourceId: network.outputs.vnetResourceId
      subnetResourceId: first(filter(network.outputs.subnets, s => s.name == 'data')).resourceId
    } : null
    containers: [
        {
          name: appStorageContainerName
          properties: {
            publicAccess: 'None'
          }
        }
      ]
    roleAssignments: [
      {
        principalId: managedIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: 'Storage Blob Data Contributor'
      }
    ]
  }
}

module azureAiServices 'modules/aiServices.bicep' = {
  name: take('aiservices-${resourcesName}-deployment', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [logAnalyticsWorkspace, network] // required due to optional flags that could change dependency
  params: {
    name: 'ais-${uniqueResourcesName}'
    location: location
    sku: 'S0'
    kind: 'AIServices'
    deployments: [modelDeployment]
    logAnalyticsWorkspaceResourceId: enableMonitoring ? logAnalyticsWorkspace.outputs.resourceId : ''
    privateNetworking: enablePrivateNetworking ? {
      virtualNetworkResourceId: network.outputs.vnetResourceId
      subnetResourceId: first(filter(network.outputs.subnets, s => s.name == 'ai')).resourceId
    } : null
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

module keyVault 'modules/keyVault.bicep' = {
  name: take('keyvault-${resourcesName}-deployment', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [logAnalyticsWorkspace, network] // required due to optional flags that could change dependency
  params: {
    name: take('kv-${uniqueResourcesName}', 24)
    location: location
    sku: 'standard'
    logAnalyticsWorkspaceResourceId: enableMonitoring ? logAnalyticsWorkspace.outputs.resourceId : ''
    privateNetworking: enablePrivateNetworking ? {
      virtualNetworkResourceId: network.outputs.vnetResourceId
      subnetResourceId: first(filter(network.outputs.subnets, s => s.name == 'data')).resourceId
    } : null 
    tags: allTags
  }
}

module azureAifoundry 'modules/aiFoundry.bicep' = {
  name: take('aifoundry-${resourcesName}-deployment', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [logAnalyticsWorkspace, network] // required due to optional flags that could change dependency
  params: {
    location: azureAiServiceLocation
    hubName: 'hub-${resourcesName}'
    hubDescription: 'AI Hub for Modernize Your Code'
    projectName: 'proj-${resourcesName}'
    storageAccountResourceId: storageAccount.outputs.resourceId
    keyVaultResourceId: keyVault.outputs.resourceId
    managedIdentityPrincpalId: managedIdentity.outputs.principalId
    logAnalyticsWorkspaceResourceId: enableMonitoring ? logAnalyticsWorkspace.outputs.resourceId : ''
    aiServicesName: azureAiServices.outputs.name
    privateNetworking: enablePrivateNetworking ? {
      virtualNetworkResourceId: network.outputs.vnetResourceId
      subnetResourceId: first(filter(network.outputs.subnets, s => s.name == 'ai')).resourceId
    } : null 
    tags: allTags
  }
}

module cosmosDb 'modules/cosmosDb.bicep' = {
  name: take('cosmos-${resourcesName}-deployment', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [logAnalyticsWorkspace, network] // required due to optional flags that could change dependency
  params: {
    name: 'cosmos-${uniqueResourcesName}'
    location: location
    managedIdentityPrincipalId: managedIdentity.outputs.principalId
    logAnalyticsWorkspaceResourceId: enableMonitoring ? logAnalyticsWorkspace.outputs.resourceId : ''
    zoneRedundant: enableRedundancy
    secondaryLocation: enableRedundancy && !empty(secondaryLocation) ? secondaryLocation : ''
    privateNetworking: enablePrivateNetworking ? {
      virtualNetworkResourceId: network.outputs.vnetResourceId
      subnetResourceId: first(filter(network.outputs.subnets, s => s.name == 'data')).resourceId
    } : null
    tags: allTags
  }
}

module containerAppsEnvironment 'br/public:avm/res/app/managed-environment:0.11.2' = {
  name: take('container-env-${resourcesName}-deployment', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [applicationInsights, logAnalyticsWorkspace, network] // required due to optional flags that could change dependency
  params: {
    name: 'cae-${resourcesName}${enablePrivateNetworking ? '-frontend' : ''}'
    location: location
    zoneRedundant: enableRedundancy && enablePrivateNetworking
    publicNetworkAccess: 'Enabled'
    infrastructureSubnetResourceId: enablePrivateNetworking ? first(filter(network.outputs.subnets, s => s.name == 'web')).resourceId : null
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
    workloadProfiles: enablePrivateNetworking ? [ // NOTE: workload profiles are required for private networking
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ] : []
    tags: allTags
  }
}

module containerAppFrontend 'br/public:avm/res/app/container-app:0.16.0' = {
  name: take('container-app-frontend-${resourcesName}-deployment', 64)
  params: {
    name: take('ca-${uniqueResourcesName}frontend', 32)
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
      maxReplicas: enableScaling ? 3 : 1
      minReplicas: 1
      rules: enableScaling ? [
        {
          name: 'http-scaler'
          http: {
            metadata: {
              concurrentRequests: 100
            }
          }
        }
      ] : []
    }
    tags: allTags
  }
}

module containerAppsEnvironmentBackend 'br/public:avm/res/app/managed-environment:0.11.2' = if (enablePrivateNetworking) {
  name: take('container-env-backend-${resourcesName}-deployment', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [applicationInsights, logAnalyticsWorkspace] // required due to optional flags that could change dependency
  params: {
    name: 'cae-${resourcesName}-backend'
    location: location
    zoneRedundant: enableRedundancy
    publicNetworkAccess: 'Enabled' // This most likely needs to remain public so the container app can be deployed
    infrastructureSubnetResourceId: first(filter(network.outputs.subnets, s => s.name == 'app')).resourceId
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
    workloadProfiles: [ // NOTE: workload profiles are required for private networking
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
    tags: allTags
  }
}

var containerAppsEnvironmentResourceId = enablePrivateNetworking ? containerAppsEnvironmentBackend.outputs.resourceId : containerAppsEnvironment.outputs.resourceId

module containerAppBackend 'br/public:avm/res/app/container-app:0.16.0' = {
  name: take('container-app-backend-${resourcesName}-deployment', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [applicationInsights, containerAppsEnvironmentBackend] // required due to optional flags that could change dependency
  params: {
    name: take('ca-${uniqueResourcesName}backend', 32)
    location: location
    environmentResourceId: containerAppsEnvironmentResourceId
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
            value: storageAccount.outputs.name
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
        probes: enableMonitoring ? [
          {
            httpGet: {
              path: '/health'
              port: 8000
            }
            initialDelaySeconds: 3
            periodSeconds: 3
            type: 'Liveness'
          }
        ] : []
      }
    ]
    ingressTargetPort: 8000
    ingressExternal: true
    scaleSettings: {
      maxReplicas: enableScaling ? 3 : 1
      minReplicas: 1
      rules: enableScaling ? [
        {
          name: 'http-scaler'
          http: {
            metadata: {
              concurrentRequests: 100
            }
          }
        }
      ] : []
    }
    tags: allTags
  }
}
