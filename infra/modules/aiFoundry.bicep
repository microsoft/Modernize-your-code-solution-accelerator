@description('The Azure region where resources will be deployed.')
param location string

@description('Required. The name of the AI Foundry project to create.')
param projectName string

@description('Required. The description of the AI Foundry project to create.')
param projectDescription string

// @description('The name of the AI Foundry Hub workspace.')
// param hubName string

// @description('The description of the AI Hub workspace.')
// param hubDescription string = hubName

@description('The Resource Id of an existing storage account to attach to AI Foundry.')
param storageAccountResourceId string

@description('The resource ID of the Azure Key Vault to associate with AI Foundry.')
param keyVaultResourceId string

@description('The Resource ID of the managed identity to assign to the AI Foundry Project workspace.')
param userAssignedIdentityResourceId string

@description('Optional. The resource ID of an existing Log Analytics workspace to associate with AI Foundry for monitoring.')
param logAnalyticsWorkspaceResourceId string?

@description('Optional. The resource ID of an existing Application Insights resource to associate with AI Foundry for monitoring.')
param applicationInsightsResourceId string?

@description('The name of an existing Azure Cognitive Services account.')
param aiServicesName string

@description('Optional. Values to establish private networking for the AI Foundry resources.')
param privateNetworking machineLearningPrivateNetworkingType?

import { roleAssignmentType } from 'br/public:avm/utl/types/avm-common-types:0.5.1'
@description('Optional. Array of role assignments to create.')
param roleAssignments roleAssignmentType[]?

@description('Optional. Tags to be applied to the resources.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

module mlApiPrivateDnsZone 'br/public:avm/res/network/private-dns-zone:0.7.1' = if (privateNetworking != null && empty(privateNetworking.?apiPrivateDnsZoneResourceId)) {
  name: take('${projectName}-mlapi-pdns-deployment', 64)
  params: {
    name: 'privatelink.api.${toLower(environment().name) == 'azureusgovernment' ? 'ml.azure.us' : 'azureml.ms'}'
    virtualNetworkLinks: [
      {
        virtualNetworkResourceId: privateNetworking.?virtualNetworkResourceId ?? ''
      }
    ]
    tags: tags
    enableTelemetry: enableTelemetry
  }
}

module mlNotebooksPrivateDnsZone 'br/public:avm/res/network/private-dns-zone:0.7.1' = if (privateNetworking != null && empty(privateNetworking.?notebooksPrivateDnsZoneResourceId)) {
  name: take('${projectName}-mlnotebook-pdns-deployment', 64)
  params: {
    name: 'privatelink.notebooks.${toLower(environment().name) == 'azureusgovernment' ? 'azureml.us' : 'azureml.net'}'
    virtualNetworkLinks: [
      {
        virtualNetworkResourceId: privateNetworking.?virtualNetworkResourceId ?? ''
      }
    ]
    tags: tags
    enableTelemetry: enableTelemetry
  }
}

var apiPrivateDnsZoneResourceId = privateNetworking != null ? (empty(privateNetworking.?apiPrivateDnsZoneResourceId) ? mlApiPrivateDnsZone.outputs.resourceId ?? '' : privateNetworking.?apiPrivateDnsZoneResourceId) : ''
var notebooksPrivateDnsZoneResourceId = privateNetworking != null ? (empty(privateNetworking.?notebooksPrivateDnsZoneResourceId) ? mlNotebooksPrivateDnsZone.outputs.resourceId ?? '' : privateNetworking.?notebooksPrivateDnsZoneResourceId) : ''

//AVM module uses 'Microsoft.CognitiveServices/accounts@2023-05-01' 
resource aiServices 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: aiServicesName
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  parent: aiServices
  name: projectName
  tags: tags
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    description: projectDescription
    displayName: projectName
  }
}



// get reference to the AI Hub project to get access to the discovery URL property (not presently available on AVM)
// adjust this logic if support on the AVM module is added 
resource projectReference 'Microsoft.MachineLearningServices/workspaces@2024-10-01' existing = {
  name: projectName
  dependsOn: [project]
}

output projectName string = project.name
//output hubName string = hub.outputs.name
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
