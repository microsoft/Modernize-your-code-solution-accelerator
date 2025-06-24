using './main.bicep'

param solutionName = readEnvironmentVariable('AZURE_ENV_NAME')
param location = readEnvironmentVariable('AZURE_LOCATION')
//param azureAiServiceLocation = readEnvironmentVariable('AZURE_AI_SERVICE_LOCATION')

// //*******************************************************************************
// // WAF-aligned configuration
// //*******************************************************************************

param enableMonitoring = true
param enableScaling = true
param enableRedundancy = true
//param secondaryLocation = 'uksouth' // TODO - test this

param enablePrivateNetworking = true
param vmAdminUsername = 'JumpboxAdminUser'
param vmAdminPassword = 'JumpboxAdminP@ssw0rd1234!'


