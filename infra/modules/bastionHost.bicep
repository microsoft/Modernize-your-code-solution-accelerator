// Creates an Azure Bastion Host using AVM
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/network/bastion-host

@description('Name of the Bastion Host')
param bastionHostName string

@description('Azure region for the Bastion Host')
param location string = resourceGroup().location

@description('Resource ID of the VNet')
param vnetId string

@description('Resource ID of the Bastion subnet')
param subnetId string

@description('Optional: Tags for the Bastion Host')
param tags object = {}

module bastion 'br/public:avm/res/network/bastion-host:0.2.2' = {
  name: bastionHostName
  params: {
    name: bastionHostName
    location: location
    virtualNetworkResourceId: vnetId
    subnetResourceId: subnetId
    tags: tags
  }
}

output bastionHostId string = bastion.outputs.resourceId
