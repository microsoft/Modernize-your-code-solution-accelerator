@description('The Azure region where resources will be deployed.')
param location string

@description('The name of the AI Foundry Project workspace.')
param projectName string

@description('The name of the AI Foundry Hub workspace.')
param hubName string

@description('The description of the AI Hub workspace.')
param hubDescription string = hubName

@description('The name of the storage account to be created for AI Foundry.')
param storageName string

@description('The resource ID of the Azure Key Vault to associate with AI Foundry.')
param keyVaultResourceId string

@description('The Princpal ID of the managed identity to assign access roles.')
param managedIdentityPrincpalId string

@description('Optional. The resource ID of an existing Log Analytics workspace to associate with AI Foundry for monitoring.')
param logAnalyticsWorkspaceResourceId string?

@description('The name of an existing Azure Cognitive Services account.')
param aiServicesName string

@description('Optional. Tags to be applied to the resources.')
param tags object = {}

resource aiServices 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: aiServicesName
}

var aiServicesKey = aiServices.listKeys().key1

module storageAccount 'br/public:avm/res/storage/storage-account:0.17.0' = {
  name: take('aifoundry-${storageName}-deployment', 64)
  params: {
    name: storageName
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
    diagnosticSettings: !empty(logAnalyticsWorkspaceResourceId) ? [{workspaceResourceId: logAnalyticsWorkspaceResourceId}] : []
    roleAssignments: [
      {
        principalId: managedIdentityPrincpalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: 'Storage Blob Data Contributor'
      }
    ]
    tags: tags
  }
}

module hub 'br/public:avm/res/machine-learning-services/workspace:0.12.1' = {
  name: take('ai-foundry-${hubName}-deployment', 64)
  params: {
    name: hubName
    location: location
    sku: 'Standard'
    kind: 'Hub'
    description: hubDescription
    associatedKeyVaultResourceId: keyVaultResourceId
    associatedStorageAccountResourceId: storageAccount.outputs.resourceId
    publicNetworkAccess: 'Enabled'
    managedIdentities: {
      systemAssigned: true
    }
    diagnosticSettings: !empty(logAnalyticsWorkspaceResourceId) ? [{workspaceResourceId: logAnalyticsWorkspaceResourceId}] : []
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
    publicNetworkAccess: 'Enabled'
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

var aiProjectConnString = '${split(projectReference.properties.discoveryUrl, '/')[2]};${subscription().subscriptionId};${resourceGroup().name};${projectReference.name}'

output projectName string = project.outputs.name
output hubName string = hub.outputs.name

output storageAccountName string = storageAccount.outputs.name
output storageAccountId string = storageAccount.outputs.resourceId

output projectConnectionString string = aiProjectConnString
