@description('Required. Name of the Cosmos DB Account.')
param name string

@description('Required. Specifies the location for all the Azure resources.')
param location string

@description('Optional. Tags to be applied to the resources.')
param tags object = {}

@description('Required. Managed Identity principal to assign data plane roles for the Cosmos DB Account.')
param dataAccessIdentityPrincipalId string

@description('Optional. The resource ID of an existing Log Analytics workspace to associate with AI Foundry for monitoring.')
param logAnalyticsWorkspaceResourceId string?

@description('Required. Indicates whether the single-region account is zone redundant. This property is ignored for multi-region accounts.')
param zoneRedundant bool

@description('Optional. The secondary location for the Cosmos DB Account for failover and multiple writes.')
param secondaryLocation string?

import { resourcePrivateNetworkingType } from 'custom-types.bicep'
@description('Optional. Values to establish private networking for the Cosmos DB resource.')
param privateNetworking resourcePrivateNetworkingType?

import { roleAssignmentType } from 'br/public:avm/utl/types/avm-common-types:0.7.0'
@description('Optional. Array of role assignments to create.')
param roleAssignments roleAssignmentType[]?

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

// Compatibility wrapper for reference-aligned naming while preserving base implementation.
module cosmosDb './cosmos-db.bicep' = {
  name: 'cosmosDbNosql'
  params: {
    name: name
    location: location
    tags: tags
    dataAccessIdentityPrincipalId: dataAccessIdentityPrincipalId
    logAnalyticsWorkspaceResourceId: logAnalyticsWorkspaceResourceId
    zoneRedundant: zoneRedundant
    secondaryLocation: secondaryLocation
    privateNetworking: privateNetworking
    roleAssignments: roleAssignments
    enableTelemetry: enableTelemetry
  }
}

@description('Name of the Cosmos DB Account resource.')
output name string = cosmosDb.outputs.name

@description('Resource ID of the Cosmos DB Account.')
output resourceId string = cosmosDb.outputs.resourceId

@description('Endpoint of the Cosmos DB Account.')
output endpoint string = cosmosDb.outputs.endpoint

@description('Name of the Cosmos DB database.')
output databaseName string = cosmosDb.outputs.databaseName

@description('Complex object containing the names of the Cosmos DB containers.')
output containerNames object = cosmosDb.outputs.containerNames
