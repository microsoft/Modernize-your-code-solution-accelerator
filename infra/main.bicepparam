using './main.bicep'

param solutionName = readEnvironmentVariable('AZURE_ENV_NAME')
param location = readEnvironmentVariable('AZURE_LOCATION')

// //*******************************************************************************
// // Uncomment the following lines to enable the WAF-aligned configuration
//    For a quick test of WAF-aligned configuration. Revert back to the original
//    configuration by commenting out (or delete) the following lines.
//      Refer to infra/main.waf-aligned.bicep for the WAF-aligned configuration
// //*******************************************************************************

param enableMonitoring = true
param enableScaling = true
param enableRedundancy = true
//param secondaryLocation = 'uksouth' // TODO - test this

param enablePrivateNetworking = true
param vmAdminUsername = 'JumpboxAdminUser'
param vmAdminPassword = 'JumpboxAdminP@ssw0rd1234!'


