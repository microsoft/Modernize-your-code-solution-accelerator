// /****************************************************************************************************************************/
// Create Azure Bastion Subnet and Azure Bastion Host
// /****************************************************************************************************************************/


param azureBastionSubnet object = {}
param location string = resourceGroup().location
param vnetName string 
param vnetId string // Resource ID of the Virtual Network
param azureBationHostName string = 'AzureBastionHost' // Default name for Azure Bastion Host
param logAnalyticsWorkspaceId string
param tags object = {}


// 1. Create Azure Bastion Host using AVM Subnet Module with special config for Azure Bastion Subnet
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/network/virtual-network/subnet
module bastionSubnet 'br/public:avm/res/network/virtual-network/subnet:0.1.2' = if (!empty(azureBastionSubnet)) {
  name: azureBastionSubnet.name
  params: {
    virtualNetworkName: vnetName
    name: azureBastionSubnet.name
    addressPrefixes: azureBastionSubnet.addressPrefixes
  }
}

output bastionSubnetId string = bastionSubnet.outputs.resourceId
output bastionSubnetName string = bastionSubnet.outputs.name

// 2. Create Azure Bastion Host in AzureBastionSubnet using AVM Bastion Host module
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/network/bastion-host

module bastionHost 'br/public:avm/res/network/bastion-host:0.6.1' = if (!empty(azureBastionSubnet)) {
  name: azureBationHostName
  params: {
    name: azureBationHostName
    skuName: 'Standard'
    location: location
    virtualNetworkResourceId: vnetId
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

output bastionHostId string = bastionHost.outputs.resourceId
output bastionHostName string = bastionHost.outputs.name
