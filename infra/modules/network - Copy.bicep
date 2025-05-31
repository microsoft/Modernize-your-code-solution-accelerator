// networking.bicep
// Creates a VNet and subnets for the solution using AVM modules
//https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/network/virtual-network

param vnetName string 
param location string

@description('Optional: Tags for the VNet')
param tags object = {}

@description('Address prefixes for the VNet')
param addressPrefixes array 

@description('Optional: DNS servers for the VNet')
param dnsServers array = []

// Subnet definitions as an array of objects
@description('Subnets to create in the VNet')
param subnets array

@description('Optional: Diagnostic settings for the VNet')
param diagnosticSettings array = []

module virtualNetwork 'br/public:avm/res/network/virtual-network:0.7.0' =  {
  name: vnetName
  params: {
    addressPrefixes: addressPrefixes
    name: vnetName
    dnsServers: dnsServers
    location: location
    subnets: [
      for subnet in subnets: {
        name: subnet.name
        addressPrefix: subnet.addressPrefix

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
