@description('The Azure region where resources will be deployed.')
param location string

@description('The name of the AI Foundry Project workspace.')
param projectName string

@description('The name of the AI Foundry Hub workspace.')
param hubName string

@description('The description of the AI Hub workspace.')
param hubDescription string = hubName

@description('The Resource Id of an existing storage account to attach to AI Foundry.')
param storageAccountResourceId string

@description('The resource ID of the Azure Key Vault to associate with AI Foundry.')
param keyVaultResourceId string

@description('The Princpal ID of the managed identity to assign access roles.')
param managedIdentityPrincpalId string

@description('Optional. The resource ID of an existing Log Analytics workspace to associate with AI Foundry for monitoring.')
param logAnalyticsWorkspaceResourceId string?

@description('Optional. The resource ID of an existing Application Insights resource to associate with AI Foundry for monitoring.')
param applicationInsightsResourceId string?

@description('The name of an existing Azure Cognitive Services account.')
param aiServicesName string

@description('Optional. Values to establish private networking for the AI Foundry resources.')
param privateNetworking machineLearningPrivateNetworkingType?

@description('Optional. Tags to be applied to the resources.')
param tags object = {}

module mlApiPrivateDnsZone 'br/public:avm/res/network/private-dns-zone:0.7.1' = if (privateNetworking != null && empty(privateNetworking.?apiPrivateDnsZoneResourceId)) {
  name: take('${hubName}-mlapi-pdns-deployment', 64)
  params: {
    name: 'privatelink.api.${toLower(environment().name) == 'azureusgovernment' ? 'ml.azure.us' : 'azureml.ms'}'
    virtualNetworkLinks: [
      {
        virtualNetworkResourceId: privateNetworking.?virtualNetworkResourceId ?? ''
      }
    ]
    tags: tags
  }
}

module mlNotebooksPrivateDnsZone 'br/public:avm/res/network/private-dns-zone:0.7.1' = if (privateNetworking != null && empty(privateNetworking.?notebooksPrivateDnsZoneResourceId)) {
  name: take('${hubName}-mlnotebook-pdns-deployment', 64)
  params: {
    name: 'privatelink.notebooks.${toLower(environment().name) == 'azureusgovernment' ? 'azureml.us' : 'azureml.net'}'
    virtualNetworkLinks: [
      {
        virtualNetworkResourceId: privateNetworking.?virtualNetworkResourceId ?? ''
      }
    ]
    tags: tags
  }
}

var apiPrivateDnsZoneResourceId = privateNetworking != null ? (empty(privateNetworking.?apiPrivateDnsZoneResourceId) ? mlApiPrivateDnsZone.outputs.resourceId ?? '' : privateNetworking.?apiPrivateDnsZoneResourceId) : ''
var notebooksPrivateDnsZoneResourceId = privateNetworking != null ? (empty(privateNetworking.?notebooksPrivateDnsZoneResourceId) ? mlNotebooksPrivateDnsZone.outputs.resourceId ?? '' : privateNetworking.?notebooksPrivateDnsZoneResourceId) : ''

resource aiServices 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: aiServicesName
}

var aiServicesKey = aiServices.listKeys().key1

module hub 'br/public:avm/res/machine-learning-services/workspace:0.12.1' = {
  name: take('ai-foundry-${hubName}-deployment', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [mlApiPrivateDnsZone, mlNotebooksPrivateDnsZone] // required due to optional flags that could change dependency
  params: {
    name: hubName
    location: location
    sku: 'Standard'
    kind: 'Hub'
    description: hubDescription
    associatedKeyVaultResourceId: keyVaultResourceId
    associatedStorageAccountResourceId: storageAccountResourceId
    associatedApplicationInsightsResourceId: applicationInsightsResourceId
    publicNetworkAccess: privateNetworking != null ? 'Disabled' : 'Enabled'
    managedIdentities: {
      systemAssigned: true
    }
    diagnosticSettings: !empty(logAnalyticsWorkspaceResourceId) ? [{workspaceResourceId: logAnalyticsWorkspaceResourceId}] : []
    privateEndpoints: privateNetworking != null ? [
      {
        privateDnsZoneGroup: {
          privateDnsZoneGroupConfigs: [
            {
              privateDnsZoneResourceId: apiPrivateDnsZoneResourceId
            }
            {
              privateDnsZoneResourceId: notebooksPrivateDnsZoneResourceId
            }
          ]
        }
        service: 'amlworkspace'
        subnetResourceId: privateNetworking.?subnetResourceId ?? ''
      }
    ] : []
    connections: [
      {
        name: aiServicesName
        value: null
        category: 'AIServices'
        target: aiServices.properties.endpoint
        connectionProperties: {
          authType: 'ApiKey'
          credentials: {
            key: aiServicesKey
          }
        }
        isSharedToAll: true
        metadata: {
          ApiType: 'Azure'
          ResourceId: aiServices.id
        }
      }
    ]
    tags: tags
  }
}

module project 'br/public:avm/res/machine-learning-services/workspace:0.12.1' = {
  name: take('ai-foundry-${projectName}-deployment', 64)
  params: {
    name: projectName
    kind: 'Project'
    sku: 'Standard'
    location: location
    hubResourceId: hub.outputs.resourceId
    publicNetworkAccess: privateNetworking != null ? 'Disabled' : 'Enabled'
    managedIdentities: {
      systemAssigned: true
    }
    diagnosticSettings: !empty(logAnalyticsWorkspaceResourceId) ? [{workspaceResourceId: logAnalyticsWorkspaceResourceId}] : []
    roleAssignments: [
      {
        principalId: managedIdentityPrincpalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: '64702f94-c441-49e6-a78b-ef80e0188fee' // Azure AI Developer
      }
    ]
    tags: tags
  }
}

// get reference to the AI Hub project to get access to the discovery URL property (not presently available on AVM)
// adjust this logic if support on the AVM module is added 
resource projectReference 'Microsoft.MachineLearningServices/workspaces@2024-10-01' existing = {
  name: projectName
  dependsOn: [project]
}

output projectName string = project.outputs.name
output hubName string = hub.outputs.name
output projectConnectionString string = '${split(projectReference.properties.discoveryUrl, '/')[2]};${subscription().subscriptionId};${resourceGroup().name};${projectReference.name}'

@export()
@description('Values to establish private networking for resources that support createing private endpoints.')
type machineLearningPrivateNetworkingType = {
  @description('Required. The Resource ID of the virtual network.')
  virtualNetworkResourceId: string

  @description('Required. The Resource ID of the subnet to establish the Private Endpoint(s).')
  subnetResourceId: string

  @description('Optional. The Resource ID of an existing "api" Private DNS Zone Resource to link to the virtual network. If not provided, a new "api" Private DNS Zone(s) will be created.')
  apiPrivateDnsZoneResourceId: string?

  @description('Optional. The Resource ID of an existing "notebooks" Private DNS Zone Resource to link to the virtual network. If not provided, a new "notebooks" Private DNS Zone(s) will be created.')
  notebooksPrivateDnsZoneResourceId: string?
}
