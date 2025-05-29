// Creates a JumpBox VM using AVM
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/compute/virtual-machine

@description('Name of the JumpBox VM')
param vmName string

@description('Azure region for the VM')
param location string = resourceGroup().location

@description('Resource ID of the subnet for the VM')
param subnetId string

@description('Admin username')
param adminUsername string

@description('Admin password or SSH public key')
@secure()
param adminPasswordOrKey string

@description('VM size (e.g., "Standard_B2ms")')
param vmSize string = 'Standard_B2ms'

@description('Optional: Tags for the VM')
param tags object = {}

module jumpbox 'br/public:avm/res/compute/virtual-machine:0.4.2' = {
  name: vmName
  params: {
    name: vmName
    location: location
    subnetResourceId: subnetId
    adminUsername: adminUsername
    adminPasswordOrKey: adminPasswordOrKey
    vmSize: vmSize
    tags: tags
  }
}

output vmId string = jumpbox.outputs.resourceId
