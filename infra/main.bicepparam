using './main.bicep'

param solutionName = readEnvironmentVariable('AZURE_ENV_NAME')
param location = readEnvironmentVariable('AZURE_LOCATION')

// //*******************************************************************************
// // Uncomment the following lines to enable the WAF-aligned configuration
// //*******************************************************************************

// param enableMonitoring = true
// param enableScaling = true
// param enableRedundancy = true

// param enablePrivateNetworking = true
// param vmAdminUsername = 'JumpboxAdminUser'
// param vmAdminPassword = 'JumpboxAdminP@ssw0rd1234!'

//param secondaryLocation = 'uksouth' // TODO - test this
