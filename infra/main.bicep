@minLength(3)
@description('prefix for all resources created by this template. This should be 3-20 characters long. If your provide a prefix longer than 20 characters, it will be truncated to 20 characters.')
param prefix string

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
@description('Location for all Ai services resources. This location can be different from the resource group location.')
param azureAiServiceLocation string  // The location used for all deployed resources.  This location must be in the same region as the resource group.

param capacity int = 5

var abbrs = loadJsonContent('./abbreviations.json')
var safePrefix = length(prefix) > 20 ? substring(prefix, 0, 20) : prefix
var uniqueId = toLower(uniqueString(subscription().id, safePrefix, resourceGroup().location))
var uniquePrefix = 'cm${padLeft(take(uniqueId, 12), 12, '0')}'
var resourcePrefix = take('cm${safePrefix}${uniquePrefix}', 15)
var imageVersion = 'latest'
var location  = resourceGroup().location
var dblocation  = resourceGroup().location
var cosmosdbDatabase  = 'cmsadb'
var cosmosdbBatchContainer  = 'cmsabatch'
var cosmosdbFileContainer  = 'cmsafile'
var cosmosdbLogContainer  = 'cmsalog'
var deploymentType  = 'GlobalStandard'
var containerName  = 'appstorage'
var llmModel  = 'gpt-4o'
var storageSkuName = 'Standard_LRS'
var storageAccountForContainersName = replace(replace(replace(replace('${resourcePrefix}cast', '-', ''), '_', ''), '.', ''),'/', '')
var gptModelVersion = '2024-08-06'
var azureAiServicesName = '${abbrs.ai.aiServices}${resourcePrefix}'
var aiFoundryProjectName = '${abbrs.ai.aiHubProject}${resourcePrefix}'

module azureAiServices 'br/public:avm/res/cognitive-services/account:0.10.2' = {
  name: take('cog-${azureAiServicesName}-deployment', 64)
  params: {
    name: azureAiServicesName
    location: location
    sku: 'S0'
    kind: 'AIServices'
    customSubDomainName: azureAiServicesName
    disableLocalAuth: false
    publicNetworkAccess: 'Enabled'
    deployments: [
      {
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
    ]
    roleAssignments: [
      {
        principalId: managedIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: 'Cognitive Services OpenAI Contributor'
      }
    ]
  }
}

module managedIdentity 'br/public:avm/res/managed-identity/user-assigned-identity:0.4.1' = {
  name: take('${abbrs.security.managedIdentity}${resourcePrefix}-identity-deployment', 64)
  params: {
    name: '${abbrs.security.managedIdentity}${resourcePrefix}'
    location: location
    tags: {
      app: resourcePrefix
      location: location
    }
  }
}

module keyvault 'br/public:avm/res/key-vault/vault:0.12.1' = {
  name: take('${abbrs.security.keyVault}${resourcePrefix}-keyvault-deployment', 64)
  params: {
    name: '${abbrs.security.keyVault}${resourcePrefix}'
    location: location
    createMode: 'default'
    sku: 'standard'
    enableVaultForDeployment: true
    enableVaultForDiskEncryption: true
    enableVaultForTemplateDeployment: true
    enableRbacAuthorization: true
    publicNetworkAccess: 'Enabled'
    softDeleteRetentionInDays: 7
    roleAssignments: [
      {
        principalId: managedIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: 'Key Vault Administrator'
      }
    ]
  }
}

// TODO - verify if this is needed

// module logAnalyticsWorkspace 'br/public:avm/res/operational-insights/workspace:0.11.0' = {
//   name: 'log-analytics-deployment'
//   params: {
//     name: '${abbrs.managementGovernance.logAnalyticsWorkspace}${resourcePrefix}'
//     location: location
//     skuName: 'PerGB2018'
//     dataRetention: 30
//   }
// }

module azureAifoundry 'deploy_ai_foundry.bicep' = {
  name: 'deploy_ai_foundry-${azureAiServicesName}'
  params: {
    location: azureAiServiceLocation
    hubName: '${abbrs.ai.aiHub}${resourcePrefix}'
    projectName: aiFoundryProjectName
    storageName: '${abbrs.storage.storageAccount}${resourcePrefix}'
    keyVaultName: keyvault.outputs.name
    gptModelName: llmModel
    gptModelVersion: gptModelVersion
    managedIdentityObjectId: managedIdentity.outputs.principalId
    aiServicesName: azureAiServices.outputs.name
  }
}

module containerAppsEnvironment 'br/public:avm/res/app/managed-environment:0.11.1' = {
  name: toLower('${resourcePrefix}conAppsEnv')
  params: {
    name: toLower('${resourcePrefix}manenv')
    location: location
    zoneRedundant: false
    publicNetworkAccess: 'Enabled'
    managedIdentities: {
      userAssignedResourceIds: [
        managedIdentity.outputs.resourceId
      ]
    }
  }
}

var cosmosAccountName = toLower('${abbrs.databases.cosmosDBDatabase}${resourcePrefix}databaseAccount')

resource sqlContributorRoleDefinition 'Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions@2024-11-15' existing = {
  name: '${cosmosAccountName}/00000000-0000-0000-0000-000000000002'
}

module databaseAccount 'br/public:avm/res/document-db/database-account:0.15.0' = {
  name: 'cosmosdb-${cosmosAccountName}-deployment'
  params: {
    name: cosmosAccountName
    enableAnalyticalStorage: true
    location: dblocation
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
          name: cosmosdbBatchContainer
          paths:[
            '/batch_id'
          ]
        }
        {
          indexingPolicy: {
            automatic: true
          }
          name: cosmosdbFileContainer
          paths:[
            '/file_id'
          ]
        }
        {
          indexingPolicy: {
            automatic: true
          }
          name: cosmosdbLogContainer
          paths:[
            '/log_id'
          ]
        }
        ]
        name: cosmosdbDatabase
      }
    ]
    dataPlaneRoleAssignments: [
      {
        principalId: managedIdentity.outputs.principalId
        roleDefinitionId: sqlContributorRoleDefinition.id
      }
    ]
  }
}

module containerAppFrontend 'br/public:avm/res/app/container-app:0.16.0' = {
  name: toLower('${abbrs.containers.containerApp}${resourcePrefix}containerAppFrontend')
  params: {
    name: toLower('${abbrs.containers.containerApp}${resourcePrefix}Frontend')
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
      minReplicas: 1
      maxReplicas: 1
    }
  }
}

module containerAppBackend 'br/public:avm/res/app/container-app:0.16.0' = {
  name: toLower('${abbrs.containers.containerApp}${resourcePrefix}containerAppBackend')
  params: {
    name: toLower('${abbrs.containers.containerApp}${resourcePrefix}Backend')
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
        image: 'cmsacontainerreg.azurecr.io/cmsabackend:${imageVersion}'
        env: [
          {
            name: 'COSMOSDB_ENDPOINT'
            value: databaseAccount.outputs.endpoint
          }
          {
            name: 'COSMOSDB_DATABASE'
            value: cosmosdbDatabase
          }
          {
            name: 'COSMOSDB_BATCH_CONTAINER'
            value: cosmosdbBatchContainer
          }
          {
            name: 'COSMOSDB_FILE_CONTAINER'
            value: cosmosdbFileContainer
          }
          {
            name: 'COSMOSDB_LOG_CONTAINER'
            value: cosmosdbLogContainer
          }
          {
            name: 'AZURE_BLOB_ACCOUNT_NAME'
            value: storageAccountForContainersName
          }
          {
            name: 'AZURE_BLOB_CONTAINER_NAME'
            value: containerName
          }
          {
            name: 'AZURE_OPENAI_ENDPOINT'
            value: 'https://${azureAiServices.outputs.name}.openai.azure.com/'
          }
          {
            name: 'MIGRATOR_AGENT_MODEL_DEPLOY'
            value: llmModel
          }
          {
            name: 'PICKER_AGENT_MODEL_DEPLOY'
            value: llmModel
          }
          {
            name: 'FIXER_AGENT_MODEL_DEPLOY'
            value: llmModel
          }
          {
            name: 'SEMANTIC_VERIFIER_AGENT_MODEL_DEPLOY'
            value: llmModel
          }
          {
            name: 'SYNTAX_CHECKER_AGENT_MODEL_DEPLOY'
            value: llmModel
          }
          {
            name: 'SELECTION_MODEL_DEPLOY'
            value: llmModel
          }
          {
            name: 'TERMINATION_MODEL_DEPLOY'
            value: llmModel
          }
          {
            name: 'AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME'
            value: llmModel
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
        ]
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
  }
}

module storageAccountForContainers 'br/public:avm/res/storage/storage-account:0.17.0' = {
  name: 'storage-account-${storageAccountForContainersName}-deployment'
  params: {
    name: storageAccountForContainersName
    location: location
    managedIdentities: {
      systemAssigned: true
    }
    kind: 'StorageV2'
    skuName: storageSkuName
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
    blobServices: {
      containers: [
        {
          name: containerName
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
  }
}
