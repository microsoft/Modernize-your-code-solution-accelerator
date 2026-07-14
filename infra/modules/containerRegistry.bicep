metadata name = 'Container Registry Module'
metadata description = 'Deploys Azure Container Registry with support for both WAF (private networking) and non-WAF deployments'

param acrName string
param location string
param acrSku string
param publicNetworkAccess string
param enablePrivateNetworking bool = false
param backendSubnetResourceId string = ''
param privateDnsZoneResourceId string = ''
param tags object = {}
param roleAssignments array = []
param enableTelemetry bool = true

// Azure Container Registry resource
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2025-11-01' = {
  name: acrName
  location: location
  sku: {
    name: acrSku
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: publicNetworkAccess
    // Configure network rules for Premium SKU
    networkRuleBypassAllowedForTasks: acrSku == 'Premium' ? true : null
    // Set default network rule action based on deployment type
    // For non-WAF (public access enabled): Allow all by default
    // For WAF (private networking): Will be managed by post-deployment scripts during build
    networkRuleSet: (acrSku == 'Premium' && publicNetworkAccess == 'Enabled') ? {
      defaultAction: 'Allow'
    } : null
  }
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
}

// Private endpoint for WAF deployments
module containerRegistryPrivateEndpoint 'br/public:avm/res/network/private-endpoint:0.12.0' = if (enablePrivateNetworking && !empty(privateDnsZoneResourceId)) {
  name: take('pep-${acrName}', 64)
  params: {
    name: 'pep-${acrName}'
    location: location
    customNetworkInterfaceName: 'nic-${acrName}'
    privateLinkServiceConnections: [
      {
        name: '${acrName}-connection'
        properties: {
          privateLinkServiceId: containerRegistry.id
          groupIds: ['registry']
        }
      }
    ]
    privateDnsZoneGroup: {
      privateDnsZoneGroupConfigs: [
        {
          name: 'acr-dns-zone-group'
          privateDnsZoneResourceId: privateDnsZoneResourceId
        }
      ]
    }
    subnetResourceId: backendSubnetResourceId
    tags: tags
  }
}

// Role assignments
resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for assignment in roleAssignments: {
  name: guid(containerRegistry.id, assignment.principalId, assignment.roleDefinitionIdOrName)
  scope: containerRegistry
  properties: {
    principalId: assignment.principalId
    principalType: assignment.principalType
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull
  }
}]

// AVM Telemetry
#disable-next-line no-deployments-resources
resource avmTelemetry 'Microsoft.Resources/deployments@2025-04-01' = if (enableTelemetry) {
  name: take('46d3xbcp.ptn.acr.${replace('-..--..-', '.', '-')}.${substring(uniqueString(deployment().name, location), 0, 4)}', 64)
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

// Outputs
output resourceId string = containerRegistry.id
output name string = containerRegistry.name
output loginServer string = containerRegistry.properties.loginServer
output systemAssignedMIPrincipalId string = containerRegistry.identity.principalId
