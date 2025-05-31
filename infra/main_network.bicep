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

param webSecurityRules array 
param appSecurityRules array 
param aiSecurityRules array 
param dataSecurityRules array 
param bastionSecurityRules array // Security rules for Bastion Host
param jumpboxSecurityRules array // Security rules for Jumpbox VM

//param vnetName string
param addressPrefixes array
param dnsServers array
param subnets array
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
    logs: [
      // Prioritized: Only most important categories for VNet/network security
      {
        category: 'NetworkSecurityGroupEvent'
        enabled: true
        retentionPolicy: {
          enabled: false
          days: 0
        }
      }
      {
        category: 'NetworkSecurityGroupRuleCounter'
        enabled: true
        retentionPolicy: {
          enabled: false
          days: 0
        }
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
        retentionPolicy: {
          enabled: false // for development, set to false
          days: 0
          // Replace with the following lines to enable retention policy
          // enabled: true
          // days: 30
        }
      }
    ]
  }
]


// 1. Create NSGs for subnets using the AVM NSG module
module nsgs 'modules/nsg.bicep' = [for (subnet, i) in subnets: if (!empty(subnet.networkSecurityGroup)) {
  name: '${prefix}-${subnet.networkSecurityGroup.name}'
  params: {
    nsgName: '${prefix}-${subnet.networkSecurityGroup.name}'
    location: location
    tags: tags
    securityRules: subnet.networkSecurityGroup.securityRules
  }
}]

// 2. Build subnets array with NSG resource IDs for AVM VNet module is now inlined below

// 3. Pass avmSubnets to the AVM VNet module
module network 'modules/network.bicep' = if (networkIsolation && !vnetReuse) {
  name: '${prefix}-vnet'
  params: {
    vnetName: vnetName
    location: location
    addressPrefixes: addressPrefixes
    dnsServers: dnsServers
    subnets: [
      for (subnet, i) in subnets: {
        name: subnet.name
        addressPrefix: subnet.addressPrefix
        networkSecurityGroupResourceId: !empty(subnet.networkSecurityGroup) ? nsgs[i].outputs.nsgResourceId : null
        // Add other properties as needed (e.g., routeTableResourceId)
      }
    ]
    tags: tags
    diagnosticSettings: diagnosticSettings
  }
}

// /**************************************************************************/
// // TODO: Bastion Host
// /**************************************************************************/
// // Create or reuse Bastion Host
// module bastionHost 'modules/bastionHost.bicep' = if (networkIsolation && !bastionHostReuse) {
//   name: '${prefix}-bastionHost'
//   params: {
//     location: location
//     tags: tags
//     virtualNetworkId: network.outputs.vnetId
//     publicIpAddressName: '${prefix}-bastionIp'
//     sku: 'Standard'
//   }
// }

// /**************************************************************************/
// //TODO: Jumpbox VM
// /**************************************************************************/
// // Create or reuse Jumpbox VM
// module jumpbox 'modules/jumpbox.bicep' = if (networkIsolation && !jumpboxReuse) {
//   name: '${prefix}-jumpbox'
//   params: {
//     location: location
//     tags: tags
//     virtualNetworkId: network.outputs.vnetId
//     subnetName: '${prefix}-default'
//     publicIpAddressName: '${prefix}-jumpboxIp'
//     adminUsername: jumboxAdminUser
//     vmSize: jumboxVmSize
//     osDiskSizeGb: 30
//     imagePublisher: 'Canonical'
//     imageOffer: 'UbuntuServer'
//     imageSku: '18.04-LTS'
//     sshKeyData: '' // Provide your SSH public key here
//   }
// }

// /**************************************************************************/
// // TODO: AI and Data Services
// /**************************************************************************/
// // Example: Deploy an AI service (e.g., Azure Cognitive Services)
// module aiService 'modules/aiService.bicep' = if (networkIsolation) {
//   name: '${prefix}-aiService'
//   params: {
//     location: location
//     tags: tags
//     virtualNetworkId: network.outputs.vnetId
//     subnetName: '${prefix}-default'
//     // Add other parameters as needed
//   }
// }

// // Example: Deploy a Data service (e.g., Azure SQL Database)
// module dataService 'modules/dataService.bicep' = if (networkIsolation) {
//   name: '${prefix}-dataService'
//   params: {
//     location: location
//     tags: tags
//     virtualNetworkId: network.outputs.vnetId
//     subnetName: '${prefix}-default'
//     // Add other parameters as needed
//   }
// }

// /**************************************************************************/
// // Outputs
// /**************************************************************************/
// output workspaceId string = logAnalyticsWorkSpace.outputs.workspaceId
// output workspacePrimaryKey string = logAnalyticsWorkSpace.outputs.primaryKey
// output workspaceSecondaryKey string = logAnalyticsWorkSpace.outputs.secondaryKey
// output workspaceName string = logAnalyticsWorkSpace.outputs.workspaceName

// // Example outputs for AI and Data services
// output aiServiceEndpoint string = aiService.outputs.endpoint
// output dataServiceConnectionString string = dataService.outputs.connectionString
