using './main.bicep'


param environmentName = readEnvironmentVariable('AZURE_ENV_NAME', 'env_dev')
param AiLocation = readEnvironmentVariable('AZURE_ENV_NAME','japaneast')
param ResourcePrefix = readEnvironmentVariable('AZURE_ENV_NAME','myPrefix')
