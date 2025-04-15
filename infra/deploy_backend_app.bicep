param location string 
param ResourcePrefix string
param userassignedIdentityId string = '' 
param imageVersion string 
param comsosEndpoint string
param cosmosdbDatabase string
param cosmosdbBatchContainer string
param cosmosdbFileContainer string
param cosmosdbLogContainer string
param storageContianerAppName string
param llmModel string
param containerName string
param openServiceName string 
param managedEnvironmentId string
resource containerAppBackend 'Microsoft.App/containerApps@2023-05-01' = {
  name: toLower('${ResourcePrefix}Backend')
  location: location
  identity: userassignedIdentityId == '' ? {
    type: 'SystemAssigned'
  } : {
    type: 'SystemAssigned, UserAssigned'
    userAssignedIdentities: {
      '${userassignedIdentityId}': {}
    }
  }  
  properties: {
    managedEnvironmentId: managedEnvironmentId
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
          image: 'cmsacontainerreg.azurecr.io/cmsabackend:${imageVersion}'
          env: [
            {
              name: 'COSMOSDB_ENDPOINT'
              value: comsosEndpoint
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
              value: storageContianerAppName
            }
            {
              name: 'AZURE_BLOB_CONTAINER_NAME'
              value: containerName
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: 'https://${openServiceName}.openai.azure.com/'
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

output identityPrincipalId string = containerAppBackend.identity.principalId
output containerAppBackendId string = containerAppBackend.id
output apiUrl string = containerAppBackend.properties.configuration.ingress.fqdn
