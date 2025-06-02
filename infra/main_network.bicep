//targetScope = 'subscription'
targetScope = 'resourceGroup'

@minLength(6)
@maxLength(25)
@description('Name of the solution. This is used to generate a short unique hash used in all resources.')
param solutionName string = 'Code Modernization'

@description('Type of the solution. This is used for tagging and categorization.')
param solutionType string = 'Solution Accelerator'

param resourceGroupName string 
param location string 


param tags object = {
  'Solution Name': solutionName
  'Solution Type': solutionType
}

/****************************************************************************************************************************/
// prefix generation 
/****************************************************************************************************************************/
var cleanSolutionName = replace(solutionName, ' ', '')  // get rid of spaces
var resourceToken = toLower('${substring(cleanSolutionName, 0, 1)}${uniqueString(cleanSolutionName, resourceGroupName, subscription().id)}')
var resourceTokenTrimmed = length(resourceToken) > 9 ? substring(resourceToken, 0, 9) : resourceToken
var prefix = toLower(replace(resourceTokenTrimmed, '_', ''))

// Network parameters (these will be set via main_network.bicepparam)
param networkIsolation bool 

//param vnetName string
param vnetAddressPrefixes array
param mySubnets array 
var vnetName = '${prefix}-vnet'

param azureBastionSubnet object = {}

param jumboxAdminUser string 
param jumboxVmSize string = 'Standard_D2s_v3' // Default VM size for Jumpbox, can be overridden
param privateEndPoint bool = true


/****************************************************************************************************************************/
// Log Analytics Workspace that will be used across the solution
/****************************************************************************************************************************/
// prefix generation 
// crate a Log Analytics Workspace using AVM

module logAnalyticsWorkSpace 'modules/logAnalyticsWorkSpace.bicep' = {
  name: '${prefix}logAnalyticsWorkspace'
  params: {
    logAnalyticsWorkSpaceName: '${prefix}-law'
    location: location
    tags: tags
  }
}

var logAnalyticsWorkspaceId = logAnalyticsWorkSpace.outputs.workspaceId

/****************************************************************************************************************************/
// Netowrking - NSGs, VNET and Subnets. Each subnet has its own NSG
/****************************************************************************************************************************/


// Diagnostic settings for VNet using Log Analytics Workspace
var diagnosticSettings = [
  {
    name: '${prefix}vnetDiagnostics'
    workspaceResourceId: logAnalyticsWorkspaceId
    logCategoriesAndGroups: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metricCategories: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
]


// 1. Create NSGs for subnets using the AVM NSG module, only if networkIsolation is true
@batchSize(1)
module nsgs 'br/public:avm/res/network/network-security-group:0.5.1' = [for (subnet, i) in mySubnets: if (networkIsolation && !empty(subnet.networkSecurityGroup)) {
  name: '${prefix}-${subnet.networkSecurityGroup.name}'
  params: {
    name: '${prefix}-${subnet.networkSecurityGroup.name}'
    location: location
    securityRules: subnet.networkSecurityGroup.securityRules
    tags: tags
  }
}]

// 2. Create VNet and subnets using AVM Virtual Network module
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/network/virtual-network



module virtualNetwork 'br/public:avm/res/network/virtual-network:0.7.0' =  if (networkIsolation) {
  name: vnetName
  params: {
    name: vnetName
    location: location
    addressPrefixes: vnetAddressPrefixes
    subnets: [
      for (subnet, i) in mySubnets: {
        name: subnet.name
        addressPrefixes: subnet.addressPrefixes
        networkSecurityGroupResourceId: !empty(subnet.networkSecurityGroup) ? nsgs[i].outputs.resourceId : null
      }
    ]
    diagnosticSettings: diagnosticSettings
    tags: tags
  }
}
output vnetName string = virtualNetwork.outputs.name
output vnetLocation string = virtualNetwork.outputs.location
output vnetId string = virtualNetwork.outputs.resourceId
output subnetIds array = virtualNetwork.outputs.subnetResourceIds

/****************************************************************************************************************************/
// // TODO: Bastion Host
/****************************************************************************************************************************/
// // Create or reuse Azure Bastion Host Using AVM Subnet Module With special config for Azure Bastion Subnet
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/network/virtual-network/subnet

//  Create Azure Bastion Subnet if azureBastionSubnet is not empty and networkIsolation is true
module azureBastionSubnetRes 'br/public:avm/res/network/virtual-network/subnet:0.1.2' = if (networkIsolation && !empty(azureBastionSubnet)) {
  name: '${prefix}-AzureBastionSubnet'
  params: {
    virtualNetworkName:virtualNetwork.outputs.name
    name: azureBastionSubnet.name
    addressPrefixes: azureBastionSubnet.addressPrefixes
  }
}


/****************************************************************************************************************************/
// //TODO: Jumpbox VM
/****************************************************************************************************************************/
// // Create or reuse Jumpbox VM


// module jumpbox 'modules/jumpbox.bicep' = if (networkIsolation && !jumpboxReuse) {
//   name: '${prefix}-jumpbox'
//   params: {
//     prefix:prefix
//     vmName:vnetName
//     location: location
//     tags: tags
//     logAnalyticsWorkspaceId: logAnalyticsWorkspaceId
//     adminUsername: jumboxAdminUser
//     adminPasswordOrKey: 'your-admin-password-or-ssh-key' // Replace with your secure value
//     vmSize: jumboxVmSize
//     subnetId: !empty(subnetIds) ? subnetIds[5].id : null // subnets 0 = web, 1-app, 2-ai, 3-data, 4-bastion, 5-jumpbox
//   }
// }
