# Environment Variables Comparison

## Overview
This document compares environment variables between the original `myc-main-original.bicep` and the current `main.bicep` file to ensure no critical environment variables are missing for the frontend and backend container apps.

## Frontend Container App
Both files have identical frontend environment variables:
- ✅ `API_URL` - Points to backend container app FQDN

## Backend Container App Environment Variables

| Environment Variable | Original (myc-main-original.bicep) | Current (main.bicep) | Status |
|---------------------|-----------------------------------|---------------------|---------|
| `COSMOSDB_ENDPOINT` | ✅ `databaseAccount.outputs.endpoint` | ✅ `cosmosDb.outputs.endpoint` | ✅ Present |
| `COSMOSDB_DATABASE` | ✅ `cosmosdbDatabase` (hardcoded) | ✅ `cosmosDb.outputs.databaseName` | ✅ Present (improved) |
| `COSMOSDB_BATCH_CONTAINER` | ✅ `cosmosdbBatchContainer` (hardcoded) | ✅ `cosmosDb.outputs.containerNames.batch` | ✅ Present (improved) |
| `COSMOSDB_FILE_CONTAINER` | ✅ `cosmosdbFileContainer` (hardcoded) | ✅ `cosmosDb.outputs.containerNames.file` | ✅ Present (improved) |
| `COSMOSDB_LOG_CONTAINER` | ✅ `cosmosdbLogContainer` (hardcoded) | ✅ `cosmosDb.outputs.containerNames.log` | ✅ Present (improved) |
| `AZURE_BLOB_ACCOUNT_NAME` | ✅ `storageContianerApp.name` | ✅ `storageAccount.outputs.name` | ✅ Present |
| `AZURE_BLOB_CONTAINER_NAME` | ✅ `containerName` (hardcoded) | ✅ `appStorageContainerName` | ✅ Present |
| `AZURE_OPENAI_ENDPOINT` | ✅ Static format | ✅ Static format | ✅ Present |
| `MIGRATOR_AGENT_MODEL_DEPLOY` | ✅ `llmModel` | ✅ `modelDeployment.name` | ✅ Present |
| `PICKER_AGENT_MODEL_DEPLOY` | ✅ `llmModel` | ✅ `modelDeployment.name` | ✅ Present |
| `FIXER_AGENT_MODEL_DEPLOY` | ✅ `llmModel` | ✅ `modelDeployment.name` | ✅ Present |
| `SEMANTIC_VERIFIER_AGENT_MODEL_DEPLOY` | ✅ `llmModel` | ✅ `modelDeployment.name` | ✅ Present |
| `SYNTAX_CHECKER_AGENT_MODEL_DEPLOY` | ✅ `llmModel` | ✅ `modelDeployment.name` | ✅ Present |
| `SELECTION_MODEL_DEPLOY` | ✅ `llmModel` | ✅ `modelDeployment.name` | ✅ Present |
| `TERMINATION_MODEL_DEPLOY` | ✅ `llmModel` | ✅ `modelDeployment.name` | ✅ Present |
| `AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME` | ✅ `llmModel` | ✅ `modelDeployment.name` | ✅ Present |
| `AZURE_AI_AGENT_PROJECT_NAME` | ✅ `aiProjectName` | ✅ `aiServices.outputs.project.name` | ✅ Present |
| `AZURE_AI_AGENT_RESOURCE_GROUP_NAME` | ✅ `resourceGroup().name` | ✅ `resourceGroup().name` | ✅ Present |
| `AZURE_AI_AGENT_SUBSCRIPTION_ID` | ✅ `subscription().subscriptionId` | ✅ `subscription().subscriptionId` | ✅ Present |
| `AI_PROJECT_ENDPOINT` | ✅ `aiFoundryProject.properties.endpoints['AI Foundry API']` | ❌ **MISSING** | ⚠️ **MISSING** |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | ✅ Always present | ✅ Conditional (enableMonitoring) | ✅ Present |
| `APPLICATIONINSIGHTS_INSTRUMENTATION_KEY` | ❌ Missing | ✅ Conditional (enableMonitoring) | ✅ **NEW** |
| `AZURE_AI_AGENT_ENDPOINT` | ❌ Missing | ✅ `aiServices.outputs.project.apiEndpoint` | ✅ **NEW** |
| `AZURE_CLIENT_ID` | ❌ Missing | ✅ `appIdentity.outputs.clientId` | ✅ **NEW** |

## Key Findings

### 🚨 Missing Environment Variable
- **`AI_PROJECT_ENDPOINT`** - This environment variable is present in the original file but missing from the current main.bicep. This should be added to maintain compatibility with the application code.

### ✅ Improvements in Current Version
- **Better parameterization**: Using module outputs instead of hardcoded values for Cosmos DB containers
- **Enhanced security**: Added `AZURE_CLIENT_ID` for managed identity authentication
- **Improved monitoring**: Added `APPLICATIONINSIGHTS_INSTRUMENTATION_KEY` for better telemetry
- **Conditional monitoring**: Monitoring variables are conditionally included based on `enableMonitoring` parameter
- **Cleaner architecture**: Better separation of concerns with dedicated modules

### 📋 Recommendations
1. **Add missing `AI_PROJECT_ENDPOINT`** environment variable to the current main.bicep
2. **Verify application code compatibility** with the new environment variable names and values
3. **Test deployment** to ensure all environment variables are correctly populated
4. **Update documentation** to reflect the new parameterization approach

## Next Steps
- [ ] Add `AI_PROJECT_ENDPOINT` environment variable to current main.bicep
- [ ] Test deployment with the updated environment variables
- [ ] Verify application functionality with the new configuration
- [ ] Update any application documentation that references environment variables
