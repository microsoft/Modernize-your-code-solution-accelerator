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
var cleanSolutionName = replace(solutionName, ' ', '') // get rid of spaces
var resourceToken = toLower('${substring(cleanSolutionName, 0, 1)}${uniqueString(cleanSolutionName, resourceGroupName, subscription().id)}')
var resourceTokenTrimmed = length(resourceToken) > 9 ? substring(resourceToken, 0, 9) : resourceToken
var prefix = toLower(replace(resourceTokenTrimmed, '_', ''))

// Network parameters (these will be set via main_network.bicepparam)
param networkIsolation bool

//param vnetName string
param vnetAddressPrefixes array
param mySubnets array
var vnetName = '${prefix}-vnet'

param azureBationHost bool = false // Flag to create Azure Bastion Host
param azureBastionSubnet object = {}

param jumpboxVM bool = false //  Set to 'true' to deploy a jumpbox VM, 'false' to skip it
param jumpboxVmSize string = 'Standard_D2s_v3' // Default VM size for Jumpbox, can be overridden
param jumpboxSubnet object = {}
param jumpboxAdminUser string = 'JumpboxAdminUser' // Default admin username for Jumpbox VM
@secure()
param jumpboxAdminPassword string 

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

// 1. Create NSGs for subnets using the AVM NSG module, only if networkIsolation is true
// using AVM Network Security Group module
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/network/network-security-group

@batchSize(1)
module nsgs 'br/public:avm/res/network/network-security-group:0.5.1' = [
  for (subnet, i) in mySubnets: if (networkIsolation && !empty(subnet.networkSecurityGroup)) {
    name: '${prefix}-${subnet.networkSecurityGroup.name}'
    params: {
      name: '${prefix}-${subnet.networkSecurityGroup.name}'
      location: location
      securityRules: subnet.networkSecurityGroup.securityRules
      tags: tags
    }
  }
]

// 2. Create VNet and subnets with subnets associated with corresponding NSGs
// using AVM Virtual Network module
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/network/virtual-network

module virtualNetwork 'br/public:avm/res/network/virtual-network:0.7.0' = if (networkIsolation) {
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
    diagnosticSettings: [
      {
        name: 'vnetDiagnostics'
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
    tags: tags
  }
}

output vnetName string = virtualNetwork.outputs.name
output vnetLocation string = virtualNetwork.outputs.location
output vnetId string = virtualNetwork.outputs.resourceId

output subnetIds array = virtualNetwork.outputs.subnetResourceIds

// /****************************************************************************************************************************/
// // create Jumpbox NSG and Jumpbox Subnet, then create Jumpbox VM
// /****************************************************************************************************************************/
// // // Create or reuse Jumpbox VM
// Craete NSG for Jumpbox subnet if jumpboxSubnet is not empty and networkIsolation is true
module jumpboxNsg 'br/public:avm/res/network/network-security-group:0.5.1' = if (networkIsolation && jumpboxVM && !empty(jumpboxSubnet)) {
  name: '${prefix}-jumpbox-nsg'
  params: {
    name: '${prefix}-jumpbox-nsg'
    location: location
    securityRules: jumpboxSubnet.networkSecurityGroup.securityRules
    tags: tags
  }
}

// Create jumpbox subnet if jumpboxSubnet is not empty and networkIsolation is true
module avmJumpboxSubnet 'br/public:avm/res/network/virtual-network/subnet:0.1.2' = if (networkIsolation && jumpboxVM && !empty(jumpboxSubnet)) {
  name: '${prefix}-jumpbox-subnet'
  params: {
    virtualNetworkName: virtualNetwork.outputs.name
    name: jumpboxSubnet.name
    addressPrefixes: jumpboxSubnet.addressPrefixes
    networkSecurityGroupResourceId: jumpboxNsg.outputs.resourceId
  }
}

output jumpboxSubnetId string = avmJumpboxSubnet.outputs.resourceId
output jumpboxNsgId string = jumpboxNsg.outputs.resourceId

output jumpboxNsgName string = jumpboxNsg.outputs.name
output jumpboxSubnetName string = avmJumpboxSubnet.outputs.name
output jumpboxSubnetAddressPrefixes array = avmJumpboxSubnet.outputs.addressPrefixes
output jumpboxSubnetNetworkSecurityGroupId string = jumpboxNsg.outputs.resourceId
output jumpboxSubnetNetworkSecurityGroupName string = jumpboxNsg.outputs.name

// // Variables for dynamic Jumpbox subnet reference (must be after subnetIds output)
// var subnetNames = [for subnet in mySubnets: subnet.name]
// var jumpboxSubnetIndex = indexOf(subnetNames, 'jumpbox')

module avmJumpboxVM 'br/public:avm/res/compute/virtual-machine:0.15.0' = if (networkIsolation && jumpboxVM) {
  name: '${prefix}-jbVM' 
  params: {
    name: take('${prefix}-jbVm', 15)
    vmSize: jumpboxVmSize
    location: location
    adminUsername: jumpboxAdminUser
    adminPassword: jumpboxAdminPassword
    tags: tags
    zone: 2
    imageReference: {
      offer: 'WindowsServer'
      publisher: 'MicrosoftWindowsServer'
      sku: '2019-datacenter'
      version: 'latest'
    }
    osType: 'Windows'
    osDisk: {
      managedDisk: {
        storageAccountType: 'Standard_LRS'
      }
    }
    encryptionAtHost: false // Some Azure subscriptions do not support encryption at host
    nicConfigurations: [
      {
        name: 'nicJumpbox'
        ipConfigurations: [
          {
            name: 'ipconfig1'
            subnetResourceId: avmJumpboxSubnet.outputs.resourceId
          }
        ]
        networkSecurityGroupResourceId: jumpboxNsg.outputs.resourceId
        diagnosticSettings: [
          {
            name: 'jumpboxDiagnostics'
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
      }
    ]
  }
}

output jumpboxVMId string = avmJumpboxVM.outputs.resourceId
output jumpboxVMName string = avmJumpboxVM.outputs.name
output jumpboxVMLocation string = avmJumpboxVM.outputs.location


/****************************************************************************************************************************/
// // Create Azure Bastion Subnet and Azure Bastion Host
/****************************************************************************************************************************/
// 1. Create or reuse Azure Bastion Host Using AVM Subnet Module With special config for Azure Bastion Subnet
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/network/virtual-network/subnet

//  Create Azure Bastion Subnet if azureBastionSubnet is not empty and networkIsolation is true
module avmAzureBastionSubnet 'br/public:avm/res/network/virtual-network/subnet:0.1.2' = if (networkIsolation && azureBationHost && !empty(azureBastionSubnet)) {
  name: '${prefix}-AzureBastionSubnet'
  params: {
    virtualNetworkName: virtualNetwork.outputs.name
    name: azureBastionSubnet.name
    addressPrefixes: azureBastionSubnet.addressPrefixes
  }
}

output azureBastionSubnetId string = avmAzureBastionSubnet.outputs.resourceId
output azureBastionSubnetName string = avmAzureBastionSubnet.outputs.name
output azureBastionSubnetAddressPrefixes array = avmAzureBastionSubnet.outputs.addressPrefixes

// 2. Create Azure Bastion Host in AzureBastionSubnet using AVM Bastion Host module
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/network/bastion-host

module avmBastionHost 'br/public:avm/res/network/bastion-host:0.6.1' = if (networkIsolation && azureBationHost && !empty(azureBastionSubnet)) {
  name: '${prefix}-bastionhost'
  params: {
    name: '${prefix}-bastionhost'
    skuName: 'Standard'
    location: location
    virtualNetworkResourceId: virtualNetwork.outputs.resourceId
    diagnosticSettings: [
      {
        name: 'bastionDiagnostics'
        workspaceResourceId: logAnalyticsWorkspaceId
        logCategoriesAndGroups: [
          {
            categoryGroup: 'allLogs'
            enabled: true
          }
        ]
      }
    ]
    tags: tags
  }
}

output bastionHostId string = avmBastionHost.outputs.resourceId
output bastionHostName string = avmBastionHost.outputs.name
output bastionHostLocation string = avmBastionHost.outputs.location

