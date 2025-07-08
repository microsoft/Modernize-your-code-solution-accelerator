// /****************************************************************************************************************************/
// Create Azure Bastion Subnet and Azure Bastion Host
// /****************************************************************************************************************************/

@description('Name of the Azure Bastion Host resource.')
param name string

@description('Azure region to deploy resources.')
param location string = resourceGroup().location

@description('Conditional. List of address prefixes for the subnet. Leave empty to skip subnet creation.')
param subnetAddressPrefixes string[]?

@description('Resource ID of the Virtual Network where the Azure Bastion Host will be deployed.')
param vnetId string

@description('Name of the Virtual Network where the Azure Bastion Host will be deployed.')
param vnetName string

@description('Resource ID of the Log Analytics Workspace for monitoring and diagnostics.')
param logAnalyticsWorkspaceId string

@description('Optional. Tags to apply to the resources.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

// 1. Create Azure Bastion Host using AVM Subnet Module with special config for Azure Bastion Subnet
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/network/virtual-network/subnet
module bastionSubnet 'br/public:avm/res/network/virtual-network/subnet:0.1.2' = if (!empty(subnetAddressPrefixes)) {
  name: take('bastionSubnet-${vnetName}', 64)
  params: {
    virtualNetworkName: vnetName
    name: 'AzureBastionSubnet' // this name required as is for Azure Bastion Host subnet
    addressPrefixes: subnetAddressPrefixes
    enableTelemetry: enableTelemetry
  }
}

// 2. Create Azure Bastion Host in AzureBastionsubnetSubnet using AVM Bastion Host module
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/network/bastion-host

module bastionHost 'br/public:avm/res/network/bastion-host:0.6.1' = {
  name: take('bastionHost-${vnetName}-${name}', 64)
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
    enableTelemetry: enableTelemetry
    publicIPAddressObject: {
      name: 'pip-${name}'
      zones:[]
    }
  }
}

output resourceId string = bastionHost.outputs.resourceId
output name string = bastionHost.outputs.name
output subnetId string = bastionSubnet.outputs.resourceId
output subnetName string = bastionSubnet.outputs.name

@export()
@description('Custom type definition for establishing Bastion Host for remote connection.')
type bastionHostConfigurationType = {
  @description('The name of the Bastion Host resource.')
  name: string

  @description('Optional. List of address prefixes for the subnet.')
  subnetAddressPrefixes: string[]?
}
