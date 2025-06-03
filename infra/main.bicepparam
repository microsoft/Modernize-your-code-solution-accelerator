using './main.bicep'

param Prefix = readEnvironmentVariable('AZURE_ENV_NAME','azdtemp')
param AzureAiServiceLocation = readEnvironmentVariable('AZURE_LOCATION','japaneast')
param capacity = int(readEnvironmentVariable('AZURE_ENV_MODEL_CAPACITY', '200'))
param deploymentType = readEnvironmentVariable('AZURE_ENV_MODEL_DEPLOYMENT_TYPE', 'GlobalStandard')
param llmModel = readEnvironmentVariable('AZURE_ENV_MODEL_NAME', 'gpt-4o')
param existingLogAnalyticsWorkspaceId = readEnvironmentVariable('AZURE_ENV_LOG_ANALYTICS_WORKSPACE_ID', '')
