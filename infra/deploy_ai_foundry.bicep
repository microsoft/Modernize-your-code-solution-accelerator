param location string

param projectName string
param hubName string 

param storageName string 
param keyVaultName string
param gptModelName string
param gptModelVersion string
param managedIdentityObjectId string

param aiServicesName string

var aiHubDescription = 'AI Hub for KM template'

resource keyVault 'Microsoft.KeyVault/vaults@2024-11-01' existing = {
  name: keyVaultName
}

resource aiServices 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: aiServicesName
}

var aiServicesKey = aiServices.listKeys().key1
var aiServicesEndpoint = aiServices.properties.endpoint
var storageAccountName = replace(replace(replace(replace('${storageName}cast', '-', ''), '_', ''), '.', ''),'/', '')

module storageAccount 'br/public:avm/res/storage/storage-account:0.17.0' = {
  name: 'foundry-storage-${storageAccountName}-deployment'
  params: {
    name: storageAccountName
    location: location
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
    roleAssignments: [
      {
        principalId: managedIdentityObjectId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: 'Storage Blob Data Contributor'
      }
    ]
  }
}

module hub 'br/public:avm/res/machine-learning-services/workspace:0.12.1' = {
  name: 'ai-hub-${hubName}-deployment'
  params: {
    name: hubName
    location: location
    sku: 'Standard'
    kind: 'Hub'
    description: aiHubDescription
    associatedKeyVaultResourceId: keyVault.id
    associatedStorageAccountResourceId: storageAccount.outputs.resourceId
    publicNetworkAccess: 'Enabled'
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
  }
}

module project 'br/public:avm/res/machine-learning-services/workspace:0.12.1' = {
  name: 'ai-project-${projectName}-deployment'
  params: {
    name: projectName
    kind: 'Project'
    sku: 'Standard'
    location: location
    hubResourceId: hub.outputs.resourceId
    publicNetworkAccess: 'Enabled'
    hbiWorkspace: false
    roleAssignments: [
      {
        principalId: managedIdentityObjectId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: 'Azure AI Developer'
      }
    ]
  }
}

// get reference to the AI Hub project to get access to the discovery URL property (not presently available on AVM)
// adjust this logic if support on the AVM module is added 
// resource projectReference 'Microsoft.MachineLearningServices/workspaces@2024-10-01' existing = {
//   name: projectName
//   dependsOn: [project]
// }

//var aiProjectConnString = '${split(projectReference.properties.discoveryUrl, '/')[2]};${subscription().subscriptionId};${resourceGroup().name};${projectReference.name}'
var aiProjectConnString = '${location}.api.azureml.ms;${subscription().subscriptionId};${resourceGroup().name};${projectName}'

resource projectConnStringSecret 'Microsoft.KeyVault/vaults/secrets@2024-11-01' = {
  parent: keyVault
  name: 'AZURE-AI-PROJECT-CONN-STRING'
  properties: {
    value: aiProjectConnString
  }
}

resource openAiKeySecret 'Microsoft.KeyVault/vaults/secrets@2024-11-01' = {
  parent: keyVault
  name: 'AZURE-OPENAI-KEY'
  properties: {
    value: aiServicesKey
  }
}

resource cogServicesKeySecret 'Microsoft.KeyVault/vaults/secrets@2024-11-01' = {
  parent: keyVault
  name: 'COG-SERVICES-KEY'
  properties: {
    value: aiServicesKey
  }
}

resource tenantIdSecret 'Microsoft.KeyVault/vaults/secrets@2024-11-01' = {
  parent: keyVault
  name: 'TENANT-ID'
  properties: {
    value: subscription().tenantId
  }
}

resource openAiInferenceEndpointSecret 'Microsoft.KeyVault/vaults/secrets@2024-11-01' = {
  parent: keyVault
  name: 'AZURE-OPENAI-INFERENCE-ENDPOINT'
  properties: {
    value: ''
  }
}

resource openAiInferenceKeySecret 'Microsoft.KeyVault/vaults/secrets@2024-11-01' = {
  parent: keyVault
  name: 'AZURE-OPENAI-INFERENCE-KEY'
  properties: {
    value: ''
  }
}

resource openAiDeploymentModelSecret 'Microsoft.KeyVault/vaults/secrets@2024-11-01' = {
  parent: keyVault
  name: 'AZURE-OPEN-AI-DEPLOYMENT-MODEL'
  properties: {
    value: gptModelName
  }
}

resource openAiPreviewApiVersionSecret 'Microsoft.KeyVault/vaults/secrets@2024-11-01' = {
  parent: keyVault
  name: 'AZURE-OPENAI-PREVIEW-API-VERSION'
  properties: {
    value: gptModelVersion
  }
}

resource openAiEndpointSecret 'Microsoft.KeyVault/vaults/secrets@2024-11-01' = {
  parent: keyVault
  name: 'AZURE-OPENAI-ENDPOINT'
  properties: {
    value: aiServicesEndpoint
  }
}

resource openAiCuVersionSecret 'Microsoft.KeyVault/vaults/secrets@2024-11-01' = {
  parent: keyVault
  name: 'AZURE-OPENAI-CU-VERSION'
  properties: {
    value: '?api-version=2024-12-01-preview'
  }
}

resource azureSearchIndexSecret 'Microsoft.KeyVault/vaults/secrets@2024-11-01' = {
  parent: keyVault
  name: 'AZURE-SEARCH-INDEX'
  properties: {
    value: 'transcripts_index'
  }
}

resource cogServicesEndpointSecret 'Microsoft.KeyVault/vaults/secrets@2024-11-01' = {
  parent: keyVault
  name: 'COG-SERVICES-ENDPOINT'
  properties: {
    value: aiServicesEndpoint
  }
}

resource cogServicesNameSecret 'Microsoft.KeyVault/vaults/secrets@2024-11-01' = {
  parent: keyVault
  name: 'COG-SERVICES-NAME'
  properties: {
    value: aiServices.name
  }
}

resource azureSubscriptionIdSecret 'Microsoft.KeyVault/vaults/secrets@2024-11-01' = {
  parent: keyVault
  name: 'AZURE-SUBSCRIPTION-ID'
  properties: {
    value: subscription().subscriptionId
  }
}

resource azureResourceGroupSecret 'Microsoft.KeyVault/vaults/secrets@2024-11-01' = {
  parent: keyVault
  name: 'AZURE-RESOURCE-GROUP'
  properties: {
    value: resourceGroup().name
  }
}

resource azureLocationSecret 'Microsoft.KeyVault/vaults/secrets@2024-11-01' = {
  parent: keyVault
  name: 'AZURE-LOCATION'
  properties: {
    value: location
  }
}

output projectName string = project.outputs.name
output hubName string = hub.outputs.name

output storageAccountName string = storageAccount.outputs.name
output storageAccountId string = storageAccount.outputs.resourceId

output projectConnectionString string = aiProjectConnString
