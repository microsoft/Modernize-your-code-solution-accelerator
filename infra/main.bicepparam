using './main.bicep'


param environmentName = readEnvironmentVariable('AZURE_ENV_NAME', 'env_dev')
param AiLocation = 'japaneast'
param ResourcePrefix = 'myPrefix'

