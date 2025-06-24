using './main.bicep'

param solutionName = readEnvironmentVariable('AZURE_ENV_NAME')
param location = readEnvironmentVariable('AZURE_LOCATION')

//**************************************************************************************************
// WAF-aligned configurations:
//   Monitoring
//   Scaling
//   Redundancy
//   Private networking
//*************************************************************************************************

param enableMonitoring = true
param enableScaling = true

//*************************************************************************************************
// Redundancy, for azure storage and cosmos DB, set to true if you want to enable redundancy
//    !!! Please check capacity and availability for redundancy in your desirable regions first 
//    and set it accordingly. We recommend to set this to false if you are not sure.
// 
param enableRedundancy = false                    // If true, need to set secondaryLocation
//param secondaryLocation = 'westus2'             // Set the secondary location for redundancy
//*************************************************************************************************

//*************************************************************************************************
// Private networking 
param enablePrivateNetworking = true
param vmAdminUsername = 'JumpboxAdminUser'          // update this to your desired admin username
param vmAdminPassword = 'JumpboxAdminP@ssw0rd1234!' // update this to your desired admin password
//*************************************************************************************************
