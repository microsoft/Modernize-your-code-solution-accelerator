// /****************************************************************************************************************************/
// Create Azure Bastion Subnet and Azure Bastion Host
// /****************************************************************************************************************************/

param subnet object = {}
param location string = resourceGroup().location
param vnetName string 
param vnetId string // Resource ID of the Virtual Network
param name string = 'AzureBastionHost' // Default name for Azure Bastion Host
param logAnalyticsWorkspaceId string
param tags object = {}

// 1. Create Azure Bastion Host using AVM Subnet Module with special config for Azure Bastion Subnet
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/network/virtual-network/subnet
module bastionSubnet 'br/public:avm/res/network/virtual-network/subnet:0.1.2' = if (!empty(subnet)) {
  name: take('bastionSubnet-${vnetName}', 64)
  params: {
    virtualNetworkName: vnetName
    name: 'AzureBastionSubnet' 
    addressPrefixes: subnet.addressPrefixes
  }
}

// 2. Create Azure Bastion Host in AzureBastionsubnetSubnet using AVM Bastion Host module
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/network/bastion-host

module bastionHost 'br/public:avm/res/network/bastion-host:0.6.1' = if (!empty(subnet)) {
  name: name
  params: {
    name: name
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

output resourceId string = bastionHost.outputs.resourceId
output name string = bastionHost.outputs.name
output subnetId string = bastionSubnet.outputs.resourceId
output subnetName string = bastionSubnet.outputs.name
