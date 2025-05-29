@description('Name of the Cosmos DB Account.')
param name string

@description('Specifies the location for all the Azure resources.')
param location string

@description('Optional. Tags to be applied to the resources.')
param tags object = {}

@description('Managed Identity princpial to assign data plane roles for the Cosmos DB Account.')
param managedIdentityPrincipalId string

resource sqlContributorRoleDefinition 'Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions@2024-11-15' existing = {
  name: '${name}/00000000-0000-0000-0000-000000000002'
}

var databaseName  = 'cmsadb'
var batchContainerName  = 'cmsabatch'
var fileContainerName  = 'cmsafile'
var logContainerName  = 'cmsalog'

module cosmosAccount 'br/public:avm/res/document-db/database-account:0.15.0' = {
  name: take('${name}-account-deployment', 64)
  params: {
    name: name
    enableAnalyticalStorage: true
    location: location
    networkRestrictions: {
      networkAclBypass: 'AzureServices'
      publicNetworkAccess: 'Enabled'
      ipRules: [] 
      virtualNetworkRules: []
    }
    zoneRedundant: false
    disableKeyBasedMetadataWriteAccess: false
    sqlDatabases: [
      {
        containers: [
          {
          indexingPolicy: {
            automatic: true
          }
          name: batchContainerName
          paths:[
            '/batch_id'
          ]
        }
        {
          indexingPolicy: {
            automatic: true
          }
          name: fileContainerName
          paths:[
            '/file_id'
          ]
        }
        {
          indexingPolicy: {
            automatic: true
          }
          name: logContainerName
          paths:[
            '/log_id'
          ]
        }
        ]
        name: databaseName
      }
    ]
    dataPlaneRoleAssignments: [
      {
        principalId: managedIdentityPrincipalId
        roleDefinitionId: sqlContributorRoleDefinition.id
      }
    ]
    tags: tags
  }
}

output resourceId string = cosmosAccount.outputs.resourceId
output name string = cosmosAccount.outputs.name
output endpoint string = cosmosAccount.outputs.endpoint
output databaseName string = databaseName

output containers object = {
  batch: {
    name: batchContainerName
    resourceId: '${cosmosAccount.outputs.resourceId}/sqlDatabases/${databaseName}/containers/${batchContainerName}'
  }
  file: {
    name: fileContainerName
    resourceId: '${cosmosAccount.outputs.resourceId}/sqlDatabases/${databaseName}/containers/${fileContainerName}'
  }
  log: {
    name: logContainerName
    resourceId: '${cosmosAccount.outputs.resourceId}/sqlDatabases/${databaseName}/containers/${logContainerName}'
  }
}
