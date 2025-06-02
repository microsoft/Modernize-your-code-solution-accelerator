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

param logAnalyticsWorkspaceReuse bool = false // If true, will reuse existing Log Analytics Workspace if available
param vnetReuse bool = false // If true, will reuse existing VNet if available
param bastionHostReuse bool = false // If true, will reuse existing Bastion Host if available
param jumpboxReuse bool = false // If true, will reuse existing Jumpbox VM if available

/**************************************************************************/
// prefix generation 
/**************************************************************************/
var cleanSolutionName = replace(solutionName, ' ', '')  // get rid of spaces
var resourceToken = toLower('${substring(cleanSolutionName, 0, 1)}${uniqueString(cleanSolutionName, resourceGroupName, subscription().id)}')
var resourceTokenTrimmed = length(resourceToken) > 9 ? substring(resourceToken, 0, 9) : resourceToken
var prefix = toLower(replace(resourceTokenTrimmed, '_', ''))

// Network parameters (these will be set via main_network.bicepparam)
param networkIsolation bool 

//param vnetName string
param vnetAddressPrefixes array
param mySubnets array 
param testSubnets array = []
var vnetName = '${prefix}-vnet'



param jumboxAdminUser string 
param jumboxVmSize string = 'Standard_D2s_v3' // Default VM size for Jumpbox, can be overridden
param privateEndPoint bool = true



/**************************************************************************/
// Log Analytics Workspace that will be used across the solution
/**************************************************************************/
// crate a Log Analytics Workspace using AVM
resource existingLogAnalyticsWorkSpace 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = if (logAnalyticsWorkspaceReuse) {
  name: '${prefix}logAnalyticsWorkspace'
}

module logAnalyticsWorkSpace 'modules/logAnalyticsWorkSpace.bicep' = if (!logAnalyticsWorkspaceReuse) {
  name: '${prefix}logAnalyticsWorkspace'
  params: {
    logAnalyticsWorkSpaceName: '${prefix}law'
    location: location
    tags: tags
  }
}

var logAnalyticsWorkspaceId  = logAnalyticsWorkspaceReuse ? existingLogAnalyticsWorkSpace.id : logAnalyticsWorkSpace.outputs.workspaceId

/**************************************************************************/
// Network Structures 
/**************************************************************************/

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


// module nsg 'br/public:avm/res/network/network-security-group:0.5.1' = {
//   name: 'my-nsg-deployment'
//   params: {
//     name: 'my-nsg'
//     location: location
//     securityRules: [
//       {
//         name: 'AllowHttpsInbound'
//         properties: {
//           access: 'Allow'
//           direction: 'Inbound'
//           priority: 100
//           protocol: 'Tcp'
//           sourcePortRange: '*'
//           destinationPortRange: '443'
//           sourceAddressPrefixes: ['0.0.0.0/0']
//           destinationAddressPrefixes: ['10.0.0.0/24']
//         }
//       }
//       // Add more rules as needed
//     ]
//     tags: {
//       environment: 'dev'
//     }
//   }
// }


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
module virtualNetwork 'br/public:avm/res/network/virtual-network:0.7.0' =  {
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


// // 2. Create VNet using the AVM VNet module

// resource existingVnet 'Microsoft.Network/virtualNetworks@2024-05-01' existing = if (vnetReuse) {
//   name: vnetName
// }

// module network 'modules/network.bicep' = if (networkIsolation && !vnetReuse) {
//   name: '${prefix}-vnet'
//   params: {
//     vnetName: vnetName
//     location: location
//     addressPrefixes: addressPrefixes
//     dnsServers: dnsServers
//     subnets: [
//       for (subnet, i) in subnets: {
//         name: subnet.name
//         addressPrefix: subnet.addressPrefix
//         networkSecurityGroupResourceId: !empty(subnet.networkSecurityGroup) ? nsgs[i].outputs.nsgResourceId : null
//         // Add other properties as needed (e.g., routeTableResourceId)
//       }
//     ]
//     tags: tags
//     diagnosticSettings: diagnosticSettings
//   }
// }
// // need this value for later resorurces
// var vnetId = vnetReuse ? existingVnet.id : network.outputs.vnetId
// var subnetIds = network.outputs.subnetIds
// var subnetNames = network.outputs.subnetNames


// /**************************************************************************/
// // TODO: Bastion Host
// /**************************************************************************/
// // Create or reuse Bastion Host
// module bastionHost 'modules/bastionHost.bicep' = if (networkIsolation && !bastionHostReuse) {
//   name: '${prefix}-bastionHost'
//   params: {
//     bastionHostName: '${prefix}-bastionHost'
//     location: location
//     vnetId: vnetId
//     tags: tags
   
//   }
// }

// /**************************************************************************/
// //TODO: Jumpbox VM
// /**************************************************************************/
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
