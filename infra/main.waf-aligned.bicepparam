using './main.bicep'

param solutionName = readEnvironmentVariable('AZURE_ENV_NAME')
param location = readEnvironmentVariable('AZURE_LOCATION')


//**************************************************************************************************
// WAF-aligned configurations:
// monitoring
// scaling
// redundancy
// private networking
//*************************************************************************************************

param enableMonitoring = true
param enableScaling = true

//*************************************************************************************************
// Redundancy, for azure storage and cosmos DB, set to true if you want to enable redundancy
param enableRedundancy = false // If true, need to set secondaryLocation
//param secondaryLocation = 'westus2'       // Set the secondary location for redundancy
//*************************************************************************************************

//*************************************************************************************************
// Private networking 
param enablePrivateNetworking = true
param vmAdminUsername = 'JumpboxAdminUser'
param vmAdminPassword = 'JumpboxAdminP@ssw0rd1234!'
//*************************************************************************************************
