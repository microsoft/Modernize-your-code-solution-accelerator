using './main.bicep'

param environmentName = readEnvironmentVariable('AZURE_ENV_NAME', 'envdev')
param AiLocation = readEnvironmentVariable('AZURE_LOCATION','japaneast')
param ResourcePrefix = readEnvironmentVariable('AZURE_ENV_NAME','azdtemp')
