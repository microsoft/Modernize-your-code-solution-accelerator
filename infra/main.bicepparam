using './main.bicep'

param AzureAiServiceLocation = readEnvironmentVariable('AZURE_LOCATION','japaneast')
param Prefix = readEnvironmentVariable('AZURE_ENV_NAME','azdtemp')
