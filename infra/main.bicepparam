using './main.bicep'

param Prefix = readEnvironmentVariable('AZURE_ENV_NAME','azdtemp')
param solutionLocation = readEnvironmentVariable('AZURE_LOCATION', 'eastus2')
param AzureAiServiceLocation = readEnvironmentVariable('AZURE_AISERVICE_LOCATION','japaneast')
param capacity = int(readEnvironmentVariable('AZURE_ENV_MODEL_CAPACITY', '200'))
param deploymentType = readEnvironmentVariable('AZURE_ENV_MODEL_DEPLOYMENT_TYPE', 'GlobalStandard')
param llmModel = readEnvironmentVariable('AZURE_ENV_MODEL_NAME', 'gpt-4o')
param gptModelVersion = readEnvironmentVariable('AZURE_ENV_MODEL_VERSION', '2024-08-06')
param imageVersion = readEnvironmentVariable('AZURE_ENV_IMAGETAG', 'latest')
param existingLogAnalyticsWorkspaceId = readEnvironmentVariable('AZURE_ENV_LOG_ANALYTICS_WORKSPACE_ID', '')
