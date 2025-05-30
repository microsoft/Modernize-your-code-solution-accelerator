using './main.bicep'

param AzureAiServiceLocation = readEnvironmentVariable('AZURE_LOCATION','japaneast')
param Prefix = readEnvironmentVariable('AZURE_ENV_NAME','azdtemp')
param existingLogAnalyticsWorkspaceId = readEnvironmentVariable('AZURE_ENV_LOG_ANALYTICS_WORKSPACE_ID', '')
