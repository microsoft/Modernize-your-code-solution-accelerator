using './main.bicep'

param solutionName = readEnvironmentVariable('AZURE_ENV_NAME')
param location = readEnvironmentVariable('AZURE_LOCATION')

param enableMonitoring = true
param enableScaling = true
param enableRedundancy = true
//param secondaryLocation = 'uksouth' // TODO - test this
param enablePrivateNetworking = true
