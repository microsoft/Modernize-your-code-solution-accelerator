using './main.bicep'

param AiLocation = readEnvironmentVariable('AZURE_LOCATION','japaneast')
param Prefix = readEnvironmentVariable('AZURE_ENV_NAME','azdtemp')
