metadata name = 'Modernize Your Code Solution Accelerator'
metadata description = '''CSA CTO Gold Standard Solution Accelerator for Modernize Your Code. 
'''

@description('Set to true if you want to deploy WAF-aligned infrastructure.')
param useWafAlignedArchitecture bool

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
  azd : {
    type: 'location'
    usageName : [
      'OpenAI.GlobalStandard.gpt-4o, 150'
    ]
  }
})
@description('Optional. Location for all AI service resources. This location can be different from the resource group location.')
param aiDeploymentsLocation string

@description('Optional. AI model deployment token capacity. Defaults to 150K tokens per minute.')
param capacity int = 150

@description('Optional. Enable monitoring for the resources. This will enable Application Insights and Log Analytics. Defaults to false.')
param enableMonitoring bool = useWafAlignedArchitecture? true : false

@description('Optional. Enable scaling for the container apps. Defaults to false.')
param enableScaling bool = useWafAlignedArchitecture? true : false

@description('Optional. Enable redundancy for applicable resources. Defaults to false.')
param enableRedundancy bool = false

@description('Optional. The secondary location for the Cosmos DB account if redundancy is enabled.')
param secondaryLocation string?

@description('Optional. Enable private networking for the resources. Set to true to enable private networking. Defaults to false.')
param enablePrivateNetworking bool = useWafAlignedArchitecture? true : false

@description('Optional. Size of the Jumpbox Virtual Machine when created. Set to custom value if enablePrivateNetworking is true.')
param vmSize string? 

@description('Optional. Admin username for the Jumpbox Virtual Machine. Set to custom value if enablePrivateNetworking is true.')
@secure()
//param vmAdminUsername string = take(newGuid(), 20)
param vmAdminUsername string?

@description('Optional. Admin password for the Jumpbox Virtual Machine. Set to custom value if enablePrivateNetworking is true.')
@secure()
//param vmAdminPassword string = newGuid()
param vmAdminPassword string?

@description('Optional. Specifies the resource tags for all the resources. Tag "azd-env-name" is automatically added to all resources.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@minLength(1)
@description('GPT model deployment type:')
param deploymentType string = 'GlobalStandard'

@minLength(1)
@description('Name of the GPT model to deploy:')
param llmModel string = 'gpt-4o'

@minLength(1)
@description('Set the Image tag:')
param imageVersion string = 'latest'

@minLength(1)
@description('Version of the GPT model to deploy:')
param gptModelVersion string = '2024-08-06'

param existingLogAnalyticsWorkspaceId string = ''

var allTags = union(
  {
    'azd-env-name': solutionName
  },
  tags
)

var resourcesName = toLower(trim(replace(
  replace(
    replace(replace(replace(replace('${solutionName}${solutionUniqueToken}', '-', ''), '_', ''), '.', ''), '/', ''),
    ' ',
    ''
  ),
  '*',
  ''
)))

var modelDeployment = {
  name: llmModel
  model: {
    name: llmModel
    format: 'OpenAI'
    version: gptModelVersion
  }
  sku: {
    name: deploymentType
    capacity: capacity
  }
  raiPolicyName: 'Microsoft.Default'
}

var abbrs = loadJsonContent('./abbreviations.json')

#disable-next-line no-deployments-resources
resource avmTelemetry 'Microsoft.Resources/deployments@2024-03-01' = if (enableTelemetry) {
  name: take(
    '46d3xbcp.ptn.sa-modernizeyourcode.${replace('-..--..-', '.', '-')}.${substring(uniqueString(deployment().name, location), 0, 4)}',
    64
  )
  properties: {
    mode: 'Incremental'
    template: {
      '$schema': 'https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#'
      contentVersion: '1.0.0.0'
      resources: []
      outputs: {
        telemetry: {
          type: 'String'
          value: 'For more information, see https://aka.ms/avm/TelemetryInfo'
        }
      }
    }
  }
}

module appIdentity 'br/public:avm/res/managed-identity/user-assigned-identity:0.4.1' = {
  name: take('identity-app-${resourcesName}-deployment', 64)
  params: {
    name: '${abbrs.security.managedIdentity}${resourcesName}'
    location: location
    tags: allTags
    enableTelemetry: enableTelemetry
  }
}
// Extracts subscription, resource group, and workspace name from the resource ID when using an existing Log Analytics workspace
var useExistingLogAnalytics = !empty(existingLogAnalyticsWorkspaceId)

var existingLawSubscription = useExistingLogAnalytics ? split(existingLogAnalyticsWorkspaceId, '/')[2] : ''
var existingLawResourceGroup = useExistingLogAnalytics ? split(existingLogAnalyticsWorkspaceId, '/')[4] : ''
var existingLawName = useExistingLogAnalytics ? split(existingLogAnalyticsWorkspaceId, '/')[8] : ''

resource existingLogAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2020-08-01' existing = if (useExistingLogAnalytics) {
  name: existingLawName
  scope: resourceGroup(existingLawSubscription, existingLawResourceGroup)
}

// Deploy new Log Analytics workspace only if required and not using existing
module logAnalyticsWorkspace 'br/public:avm/res/operational-insights/workspace:0.11.2' = if ((enableMonitoring || enablePrivateNetworking) && !useExistingLogAnalytics) {
  name: take('log-analytics-${resourcesName}-deployment', 64)
  params: {
    name: '${abbrs.managementGovernance.logAnalyticsWorkspace}${resourcesName}'
    location: location
    skuName: 'PerGB2018'
    dataRetention: 30
    diagnosticSettings: [{ useThisWorkspace: true }]
    tags: allTags
    enableTelemetry: enableTelemetry
  }
}

// Log Analytics workspace ID, customer ID, and shared key (existing or new) 
var logAnalyticsWorkspaceResourceId = useExistingLogAnalytics ? existingLogAnalyticsWorkspaceId : logAnalyticsWorkspace.outputs.resourceId
var LogAnalyticsPrimarySharedKey string = useExistingLogAnalytics? existingLogAnalyticsWorkspace.listKeys().primarySharedKey : logAnalyticsWorkspace.outputs.primarySharedKey
var LogAnalyticsWorkspaceId = useExistingLogAnalytics? existingLogAnalyticsWorkspace.properties.customerId : logAnalyticsWorkspace.outputs.logAnalyticsWorkspaceId

module applicationInsights 'br/public:avm/res/insights/component:0.6.0' = if (enableMonitoring) {
  name: take('app-insights-${resourcesName}-deployment', 64)
  params: {
    name: '${abbrs.managementGovernance.applicationInsights}${resourcesName}'
    location: location
    workspaceResourceId: logAnalyticsWorkspaceResourceId
    diagnosticSettings: [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }]
    tags: allTags
    enableTelemetry: enableTelemetry
  }
}


module network 'modules/network.bicep' = if (enablePrivateNetworking) {
  name: take('network-${resourcesName}-deployment', 64)
  params: {
    resourcesName: resourcesName
    logAnalyticsWorkSpaceResourceId: logAnalyticsWorkspaceResourceId
    vmAdminUsername: vmAdminUsername ?? 'JumpboxAdminUser'
    vmAdminPassword: vmAdminPassword ?? 'JumpboxAdminP@ssw0rd1234!'
    vmSize: vmSize ??  'Standard_DS2_v2' // Default VM size 
    location: location
    tags: allTags
    enableTelemetry: enableTelemetry
  }
}

module aiServices 'modules/ai-foundry/main.bicep' = {
  name: take('aiservices-${resourcesName}-deployment', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [logAnalyticsWorkspace, network] // required due to optional flags that could change dependency
  params: {
    name: '${abbrs.ai.aiFoundry}${resourcesName}'
    location: aiDeploymentsLocation
    sku: 'S0'
    kind: 'AIServices'
    deployments: [modelDeployment]
    projectName: '${abbrs.ai.aiFoundryProject}${resourcesName}'
    logAnalyticsWorkspaceResourceId: enableMonitoring ? logAnalyticsWorkspaceResourceId : ''
    privateNetworking: enablePrivateNetworking
      ? {
          virtualNetworkResourceId: network.outputs.vnetResourceId
          subnetResourceId: network.outputs.subnetPrivateEndpointsResourceId
        }
      : null
    roleAssignments: [
      {
        principalId: appIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: 'Cognitive Services OpenAI Contributor'
      }
      {
        principalId: appIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: '64702f94-c441-49e6-a78b-ef80e0188fee' // Azure AI Developer
      }
      {
        principalId: appIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: '53ca6127-db72-4b80-b1b0-d745d6d5456d' // Azure AI User
      }
    ]
    tags: allTags
    enableTelemetry: enableTelemetry
  }
}

var appStorageContainerName = 'appstorage'

module storageAccount 'modules/storageAccount.bicep' = {
  name: take('storage-account-${resourcesName}-deployment', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [logAnalyticsWorkspace, network] // required due to optional flags that could change dependency
  params: {
    name: take('${abbrs.storage.storageAccount}${resourcesName}', 24)
    location: location
    tags: allTags
    skuName: enableRedundancy ? 'Standard_GZRS' : 'Standard_LRS'
    logAnalyticsWorkspaceResourceId: enableMonitoring ? logAnalyticsWorkspaceResourceId : ''
    privateNetworking: enablePrivateNetworking
      ? {
          virtualNetworkResourceId: network.outputs.vnetResourceId
          subnetResourceId: network.outputs.subnetPrivateEndpointsResourceId
        }
      : null
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
        principalId: appIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: 'Storage Blob Data Contributor'
      }
    ]
    enableTelemetry: enableTelemetry
  }
}

module keyVault 'modules/keyVault.bicep' = {
  name: take('keyvault-${resourcesName}-deployment', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [logAnalyticsWorkspace, network] // required due to optional flags that could change dependency
  params: {
    name: take('${abbrs.security.keyVault}${resourcesName}', 24)
    location: location
    sku: 'standard'
    logAnalyticsWorkspaceResourceId: enableMonitoring ? logAnalyticsWorkspaceResourceId : ''
    privateNetworking: enablePrivateNetworking
      ? {
          virtualNetworkResourceId: network.outputs.vnetResourceId
          subnetResourceId: network.outputs.subnetPrivateEndpointsResourceId
        }
      : null
    roleAssignments: [
      {
        principalId: aiServices.outputs.?systemAssignedMIPrincipalId ?? ''
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: 'Key Vault Reader'
      }
    ]
    tags: allTags
    enableTelemetry: enableTelemetry
  }
}

module cosmosDb 'modules/cosmosDb.bicep' = {
  name: take('cosmos-${resourcesName}-deployment', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [logAnalyticsWorkspace, network] // required due to optional flags that could change dependency
  params: {
    name: take('${abbrs.databases.cosmosDBDatabase}${resourcesName}', 44)
    location: location
    dataAccessIdentityPrincipalId: appIdentity.outputs.principalId
    logAnalyticsWorkspaceResourceId: enableMonitoring ? logAnalyticsWorkspaceResourceId : ''
    zoneRedundant: enableRedundancy
    secondaryLocation: enableRedundancy && !empty(secondaryLocation) ? secondaryLocation : ''
    privateNetworking: enablePrivateNetworking
      ? {
          virtualNetworkResourceId: network.outputs.vnetResourceId
          subnetResourceId: network.outputs.subnetPrivateEndpointsResourceId
        }
      : null
    tags: allTags
    enableTelemetry: enableTelemetry
  }
}

var containerAppsEnvironmentName = '${abbrs.containers.containerAppsEnvironment}${resourcesName}'

module containerAppsEnvironment 'br/public:avm/res/app/managed-environment:0.11.2' = {
  name: take('container-env-${resourcesName}-deployment', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [applicationInsights, logAnalyticsWorkspace, network] // required due to optional flags that could change dependency
  params: {
    name: containerAppsEnvironmentName
    infrastructureResourceGroupName: '${resourceGroup().name}-ME-${containerAppsEnvironmentName}'
    location: location
    zoneRedundant: enableRedundancy && enablePrivateNetworking
    publicNetworkAccess: 'Enabled' // public access required for frontend
    infrastructureSubnetResourceId: enablePrivateNetworking ? network.outputs.subnetWebResourceId : null
    managedIdentities: {
      userAssignedResourceIds: [
        appIdentity.outputs.resourceId
      ]
    }
    appInsightsConnectionString: enableMonitoring ? applicationInsights.outputs.connectionString : null
    appLogsConfiguration: enableMonitoring
      ? {
          destination: 'log-analytics'
          logAnalyticsConfiguration: {
            customerId: LogAnalyticsWorkspaceId
            sharedKey: LogAnalyticsPrimarySharedKey
          }
        }
      : {}
    workloadProfiles: enablePrivateNetworking
      ? [
          // NOTE: workload profiles are required for private networking
          {
            name: 'Consumption'
            workloadProfileType: 'Consumption'
          }
        ]
      : []
    tags: allTags
    enableTelemetry: enableTelemetry
  }
}

module containerAppBackend 'br/public:avm/res/app/container-app:0.17.0' = {
  name: take('container-app-backend-${resourcesName}-deployment', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [applicationInsights] // required due to optional flags that could change dependency
  params: {
    name: take('${abbrs.containers.containerApp}backend-${resourcesName}', 32)
    location: location
    environmentResourceId: containerAppsEnvironment.outputs.resourceId
    managedIdentities: {
      userAssignedResourceIds: [
        appIdentity.outputs.resourceId
      ]
    }
    containers: [
      {
        name: 'cmsabackend'
        image: 'cmsacontainerreg.azurecr.io/cmsabackend:${imageVersion}'
        env: concat(
          [
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
              value: cosmosDb.outputs.containerNames.batch
            }
            {
              name: 'COSMOSDB_FILE_CONTAINER'
              value: cosmosDb.outputs.containerNames.file
            }
            {
              name: 'COSMOSDB_LOG_CONTAINER'
              value: cosmosDb.outputs.containerNames.log
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
              value: 'https://${aiServices.outputs.name}.openai.azure.com/'
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
              name: 'AI_PROJECT_ENDPOINT'
              value: aiServices.outputs.project.apiEndpoint // or equivalent
            }
            {
              name: 'AZURE_AI_AGENT_PROJECT_CONNECTION_STRING' // This was not really used in code. 
              value: aiServices.outputs.project.apiEndpoint
            }
            {
              name: 'AZURE_AI_AGENT_PROJECT_NAME'
              value: aiServices.outputs.project.name
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
              name: 'AZURE_AI_AGENT_ENDPOINT'
              value: aiServices.outputs.project.apiEndpoint
            }
            {
              name: 'AZURE_CLIENT_ID'
              value: appIdentity.outputs.clientId // NOTE: This is the client ID of the managed identity, not the Entra application, and is needed for the App Service to access the Cosmos DB account.
            }
          ],
          enableMonitoring
            ? [
                {
                  name: 'APPLICATIONINSIGHTS_INSTRUMENTATION_KEY'
                  value: applicationInsights.outputs.instrumentationKey
                }
                {
                  name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
                  value: applicationInsights.outputs.connectionString
                }
              ]
            : []
        )
        resources: {
          cpu: 1
          memory: '2.0Gi'
        }
        probes: enableMonitoring
          ? [
              {
                httpGet: {
                  path: '/health'
                  port: 8000
                }
                initialDelaySeconds: 3
                periodSeconds: 3
                type: 'Liveness'
              }
            ]
          : []
      }
    ]
    ingressTargetPort: 8000
    ingressExternal: true
    scaleSettings: {
      maxReplicas: enableScaling ? 3 : 1
      minReplicas: 1
      rules: enableScaling
        ? [
            {
              name: 'http-scaler'
              http: {
                metadata: {
                  concurrentRequests: 100
                }
              }
            }
          ]
        : []
    }
    tags: allTags
    enableTelemetry: enableTelemetry
  }
}

module containerAppFrontend 'br/public:avm/res/app/container-app:0.17.0' = {
  name: take('container-app-frontend-${resourcesName}-deployment', 64)
  params: {
    name: take('${abbrs.containers.containerApp}frontend-${resourcesName}', 32)
    location: location
    environmentResourceId: containerAppsEnvironment.outputs.resourceId
    managedIdentities: {
      userAssignedResourceIds: [
        appIdentity.outputs.resourceId
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
        image: 'cmsacontainerreg.azurecr.io/cmsafrontend:${imageVersion}'
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
      rules: enableScaling
        ? [
            {
              name: 'http-scaler'
              http: {
                metadata: {
                  concurrentRequests: 100
                }
              }
            }
          ]
        : []
    }
    tags: allTags
    enableTelemetry: enableTelemetry
  }
}

@description('The resource group the resources were deployed into.')
output resourceGroupName string = resourceGroup().name
output WEB_APP_URL string = 'https://${containerAppFrontend.outputs.fqdn}'
