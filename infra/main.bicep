@description('Prefix for all resources created by this template.  This prefix will be used to create unique names for all resources.  The prefix must be unique within the resource group.')
param ResourcePrefix string

@description('Authorization requires permission to create an app identity in the subscription.  See readme for details.')
param Authorization bool = false

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
param AiLocation string  // The location used for all deployed resources.  This location must be in the same region as the resource group.
param capacity int = 5

@minLength(3)
@maxLength(10)
@description('A unique prefix for all resources in this deployment. This should be 3-10 characters long:')
param environmentName string 

@description('The location used for all deployed resources')
// Generate a unique string based on the base name and a unique identifier
//var uniqueSuffix = uniqueString(resourceGroup().id, ResourcePrefix)

// Take the first 4 characters of the unique string to use as a suffix
var randomSuffix = substring(environmentName, 0, min(10, length(environmentName)))

// Combine the base name with the random suffix
var finalName = '${ResourcePrefix}-${randomSuffix}'

var backEndVersion = Authorization ? 'rcauth' : 'rcnoauth'
var frontEndVersion = Authorization ? 'rcauth' : 'rcnoauth'
var location  = resourceGroup().location
var dblocation  = resourceGroup().location
var cosmosdbDatabase  = 'cmsadb'
var cosmosdbBatchContainer  = 'cmsabatch'
var cosmosdbFileContainer  = 'cmsafile'
var cosmosdbLogContainer  = 'cmsalog'
var deploymentType  = 'GlobalStandard'
var containerName  = 'appstorage'
var llmModel  = 'gpt-4o'
var prefixCleaned = replace(toLower(finalName), '-', '')
var storageSkuName = 'Standard_LRS'
var storageContainerName = '${prefixCleaned}contstorage'
var gptModelVersion = '2024-08-06'
var storageNameCleanedContainer = replace(storageContainerName, '-', '')
var aiServicesName = '${prefixCleaned}-aiservices'

var imageName = 'cmsacontainerreg.azurecr.io/cmsabackend:${frontEndVersion}'



var aiModelDeployments = [
  {
    name: llmModel
    model: llmModel
    version: gptModelVersion
    sku: {
      name: deploymentType
      capacity: capacity
    }
    raiPolicyName: 'Microsoft.Default'
  }
]

resource aiServices 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = {
  name: aiServicesName
  location: location
  sku: {
    name: 'S0'
  }
  kind: 'AIServices'
  properties: {
    customSubDomainName: aiServicesName
    apiProperties: {
      statisticsEnabled: false
    }
  }
}

@batchSize(1)
resource aiServicesDeployments 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = [for aiModeldeployment in aiModelDeployments: {
  parent: aiServices //aiServices_m
  name: aiModeldeployment.name
  properties: {
    model: {
      format: 'OpenAI'
      name: aiModeldeployment.model
      version: aiModeldeployment.version
    }
    raiPolicyName: aiModeldeployment.raiPolicyName
  }
  sku:{
    name: aiModeldeployment.sku.name
    capacity: aiModeldeployment.sku.capacity
  }
}]



//param storageAccountId string = 'storageAccountId'
module managedIdentityModule 'deploy_managed_identity.bicep' = {
  name: 'deploy_managed_identity'
  params: {
    solutionName: prefixCleaned
    solutionLocation: location 
  }
  scope: resourceGroup(resourceGroup().name)
}


// ==========Key Vault Module ========== //
module kvault 'deploy_keyvault.bicep' = {
  name: 'deploy_keyvault'
  params: {
    solutionName: prefixCleaned
    solutionLocation: location
    managedIdentityObjectId:managedIdentityModule.outputs.managedIdentityOutput.objectId
  }
  scope: resourceGroup(resourceGroup().name)
}


// ==========AI Foundry and related resources ========== //
module aifoundry 'deploy_ai_foundry.bicep' = {
  name: 'deploy_ai_foundry'
  params: {
    solutionName: prefixCleaned
    solutionLocation: AiLocation
    keyVaultName: kvault.outputs.keyvaultName
    gptModelName: llmModel
    gptModelVersion: gptModelVersion
    managedIdentityObjectId:managedIdentityModule.outputs.managedIdentityOutput.objectId
    aiServicesEndpoint: aiServices.properties.endpoint
    aiServicesKey: aiServices.listKeys().key1
    aiServicesId: aiServices.id
  }
  scope: resourceGroup(resourceGroup().name)
}

module containerAppsEnvironment 'br/public:avm/res/app/managed-environment:0.9.1' = {
  name: toLower('${prefixCleaned}conAppsEnv')
  params: {
    logAnalyticsWorkspaceResourceId: aifoundry.outputs.logAnalyticsId
    name: toLower('${prefixCleaned}manenv')
    location: location
    zoneRedundant: false
    managedIdentities: managedIdentityModule
  }
  scope: resourceGroup(resourceGroup().name)
}

module databaseAccount 'br/public:avm/res/document-db/database-account:0.9.0' = {
  name: toLower('${prefixCleaned}database')
  scope: resourceGroup(resourceGroup().name)
  params: {
    // Required parameters
    name: toLower('${prefixCleaned}databaseAccount')
    // Non-required parameters
    enableAnalyticalStorage: true
    location: dblocation
    managedIdentities: {
      systemAssigned: true
      userAssignedResourceIds: [
        managedIdentityModule.outputs.managedIdentityOutput.resourceId
      ]
    }
    networkRestrictions: {
      networkAclBypass: 'AzureServices'
      publicNetworkAccess: 'Enabled'
      ipRules: []  // Adding ipRules as an empty array
      virtualNetworkRules: [] // Adding virtualNetworkRules as an empty array
    }
    disableKeyBasedMetadataWriteAccess: false
    locations: [
      {
        failoverPriority: 0
        isZoneRedundant: false
        locationName: dblocation
      }
    ]
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
  
  }

}

module containerAppFrontend 'br/public:avm/res/app/container-app:0.13.0' = {
  name: toLower('${prefixCleaned}containerAppFrontend')
  scope: resourceGroup(resourceGroup().name)
  params: {
    managedIdentities: {
      systemAssigned: true
      userAssignedResourceIds: [
        managedIdentityModule.outputs.managedIdentityOutput.resourceId
      ]
    }
    // Required parameters
    containers: [
      {
        env: [
          {
            name: 'API_URL'
            value: 'https://${containerAppBackend.properties.configuration.ingress.fqdn}'
          }
        ]
        image: imageName
        name: 'cmsafrontend'
        resources: {
          cpu: '1'
          memory: '2.0Gi'
        }
      }
    ]
    ingressTargetPort: 3000
    ingressExternal: true
    scaleMinReplicas: 1
    scaleMaxReplicas: 1
    environmentResourceId: containerAppsEnvironment.outputs.resourceId
    name: toLower('${prefixCleaned}containerFrontend')
    // Non-required parameters
    location: location
  }
}


resource containerAppBackend 'Microsoft.App/containerApps@2023-05-01' = {
  name: toLower('${prefixCleaned}containerBackend')
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.outputs.resourceId
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
      }
    }
    template: {
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
      containers: [
        {
          name: 'cmsabackend'
          image: 'cmsacontainerreg.azurecr.io/cmsabackend:${backEndVersion}'
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
              value: storageContianerApp.name
            }
            {
              name: 'AZURE_BLOB_CONTAINER_NAME'
              value: containerName
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: 'https://${aifoundry.outputs.aiServicesName}.openai.azure.com/'
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
          ]
          resources: {
            cpu: 1
            memory: '2.0Gi'
          }
        }
      ]
    }
  }
}
resource storageContianerApp 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: storageNameCleanedContainer
  location: location
  sku: {
    name: storageSkuName
  }
  kind: 'StorageV2'
  identity: {
    type: 'SystemAssigned'  // Enables Managed Identity
  }
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowCrossTenantReplication: false
    allowSharedKeyAccess: false
    encryption: {
      keySource: 'Microsoft.Storage'
      requireInfrastructureEncryption: false
      services: {
        blob: {
          enabled: true
          keyType: 'Account'
        }
        file: {
          enabled: true
          keyType: 'Account'
        }
        queue: {
          enabled: true
          keyType: 'Service'
        }
        table: {
          enabled: true
          keyType: 'Service'
        }
      }
    }
    isHnsEnabled: false
    isNfsV3Enabled: false
    keyPolicy: {
      keyExpirationPeriodInDays: 7
    }
    largeFileSharesState: 'Disabled'
    minimumTlsVersion: 'TLS1_2'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
    supportsHttpsTrafficOnly: true
  }
}
resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerAppBackend.id, 'Storage Blob Data Contributor')
  scope: storageContianerApp
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe') // Storage Blob Data Contributor
    principalId: containerAppBackend.identity.principalId
  }
}
var openAiContributorRoleId = 'a001fd3d-188f-4b5d-821b-7da978bf7442'  // Fixed Role ID for OpenAI Contributor

resource openAiRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerAppBackend.id, openAiContributorRoleId)
  scope: aiServices
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', openAiContributorRoleId) // OpenAI Service Contributor
    principalId: containerAppBackend.identity.principalId
  }
}

var containerNames = [
  containerName
]

// Create a blob container resource for each container name.
resource containers 'Microsoft.Storage/storageAccounts/blobServices/containers@2021-08-01' = [for containerName in containerNames: {
  name: '${storageNameCleanedContainer}/default/${containerName}'

  properties: {
    publicAccess: 'None'
  }
  dependsOn: [aifoundry]
}]


resource contributorRoleDefinition 'Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions@2021-06-15' existing = {
  name: '${databaseAccount.name}/00000000-0000-0000-0000-000000000002'
}

var cosmosAssignCli  = 'az cosmosdb sql role assignment create --resource-group "${resourceGroup().name}" --account-name "${databaseAccount.outputs.name}" --role-definition-id "${contributorRoleDefinition.id}" --scope "${databaseAccount.outputs.resourceId}" --principal-id "${containerAppBackend.identity.principalId}"'

module deploymentScriptCLI 'br/public:avm/res/resources/deployment-script:0.5.1' = {
  name: 'deploymentScriptCLI'
  scope: resourceGroup(resourceGroup().name)
  params: {
    // Required parameters
    kind: 'AzureCLI'
    name: 'rdsmin001'
    // Non-required parameters
    azCliVersion: '2.69.0'
    location: resourceGroup().location
    managedIdentities: {
      userAssignedResourceIds: [
        managedIdentityModule.outputs.managedIdentityId
      ]
    }
    scriptContent: cosmosAssignCli
  }
}
