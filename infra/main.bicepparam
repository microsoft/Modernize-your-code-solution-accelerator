using './main.bicep'

param location = readEnvironmentVariable('AZURE_LOCATION','japaneast')
param azureAiServiceLocation = location
param environmentName = readEnvironmentVariable('AZURE_ENV_NAME','azdtemp')
