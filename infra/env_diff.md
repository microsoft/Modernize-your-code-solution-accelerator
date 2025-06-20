# Environment Variables Differences

## Overview
This document highlights **only the differences** in environment variables between `myc-main-original.bicep` and the current `main.bicep` file.

## Frontend Container App
✅ **No differences** - Both files have identical frontend environment variables.

## Backend Container App - Differences Only

### 🚨 Missing from Current main.bicep
| Environment Variable | Original Value | Impact |
|---------------------|----------------|---------|
| `AI_PROJECT_ENDPOINT` | `aiFoundryProject.properties.endpoints['AI Foundry API']` | **Critical** - May break AI Foundry integration |

### ✅ New in Current main.bicep
| Environment Variable | New Value | Benefit |
|---------------------|-----------|---------|
| `APPLICATIONINSIGHTS_INSTRUMENTATION_KEY` | `applicationInsights.outputs.instrumentationKey` (conditional) | Enhanced telemetry |
| `AZURE_AI_AGENT_ENDPOINT` | `aiServices.outputs.project.apiEndpoint` | Better AI project integration |
| `AZURE_CLIENT_ID` | `appIdentity.outputs.clientId` | Managed identity authentication |

### 🔄 Changed Implementation (Same Variable, Different Source)
| Environment Variable | Original Source | New Source | Improvement |
|---------------------|----------------|------------|-------------|
| `COSMOSDB_DATABASE` | `cosmosdbDatabase` (hardcoded) | `cosmosDb.outputs.databaseName` | Dynamic from module |
| `COSMOSDB_BATCH_CONTAINER` | `cosmosdbBatchContainer` (hardcoded) | `cosmosDb.outputs.containerNames.batch` | Dynamic from module |
| `COSMOSDB_FILE_CONTAINER` | `cosmosdbFileContainer` (hardcoded) | `cosmosDb.outputs.containerNames.file` | Dynamic from module |
| `COSMOSDB_LOG_CONTAINER` | `cosmosdbLogContainer` (hardcoded) | `cosmosDb.outputs.containerNames.log` | Dynamic from module |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | Always present | Conditional (`enableMonitoring`) | Parameter-controlled |

## Action Required

### 🚨 **Priority 1: Add Missing Variable**
```bicep
{
  name: 'AI_PROJECT_ENDPOINT'
  value: aiServices.outputs.project.apiEndpoint // or equivalent
}
```

### ✅ **Verification Needed**
- Confirm application code can handle the new `AZURE_CLIENT_ID` variable
- Test AI agent functionality with new `AZURE_AI_AGENT_ENDPOINT`
- Verify monitoring works with conditional Application Insights variables
