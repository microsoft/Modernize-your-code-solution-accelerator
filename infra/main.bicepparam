using './main.bicep'

param azureAiServiceLocation = readEnvironmentVariable('AZURE_LOCATION','japaneast')
param prefix = readEnvironmentVariable('AZURE_ENV_NAME','azdtemp')
