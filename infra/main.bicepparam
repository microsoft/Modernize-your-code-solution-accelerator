using './main.bicep'

param AiLocation = readEnvironmentVariable('AZURE_LOCATION','japaneast')
param ResourcePrefix = readEnvironmentVariable('AZURE_ENV_NAME','azdtemp')
