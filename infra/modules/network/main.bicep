@minLength(6)
@maxLength(25)
@description('Default name used for all resources.')
param resourcesName string

@minLength(3)
@description('Azure region for all services.')
param location string

@description('Resource ID of the Log Analytics Workspace for monitoring and diagnostics.')
param logAnalyticsWorkSpaceResourceId string

@description('Networking address prefix for the VNET only.')
param addressPrefixes array

@description('Array of subnets to be created within the VNET.')
param subnets array   

@description('Optional. Tags to be applied to the resources.')
param tags object = {}

                    
var vnetName = 'vnet-${resourcesName}'

// jumpbox parameters
param jumpboxVM bool = false                         
param jumpboxSubnet object = {}                      
param jumpboxAdminUser string = 'JumpboxAdminUser'   
@secure()
param jumpboxAdminPassword string                    
param jumpboxVmSize string = 'Standard_D2s_v3'  
var jumpboxVmName = 'jumpboxVM-${resourcesName}'            

// Azure Bastion Host parameters
param enableBastionHost bool = true                   
param bastionSubnet object = {}                 
var bastionHostName = 'bastionHost-${resourcesName}'  


// /****************************************************************************************************************************/
// Networking - NSGs, VNET and Subnets. Each subnet has its own NSG
// /****************************************************************************************************************************/

module virtualNetwork 'virtualNetwork.bicep' = {
  name: '${resourcesName}-virtualNetwork'
  params: {
    name: vnetName
    addressPrefixes: addressPrefixes
    subnets: subnets
    location: location
    tags: tags
    logAnalyticsWorkspaceId: logAnalyticsWorkSpaceResourceId
  }
}

// /****************************************************************************************************************************/
// // Create Azure Bastion Subnet and Azure Bastion Host
// /****************************************************************************************************************************/

module bastionHost 'bastionHost.bicep' = if (enableBastionHost && !empty(bastionSubnet)) {
  name: '${resourcesName}-bastionHost'
  params: {
    subnet: bastionSubnet
    location: location
    vnetName: virtualNetwork.outputs.name
    vnetId: virtualNetwork.outputs.resourceId
    name: bastionHostName
    logAnalyticsWorkspaceId: logAnalyticsWorkSpaceResourceId
    tags: tags
  }
}

// /****************************************************************************************************************************/
// // create Jumpbox NSG and Jumpbox Subnet, then create Jumpbox VM
// /****************************************************************************************************************************/

module jumpbox 'jumpbox.bicep' = if (jumpboxVM && !empty(jumpboxSubnet)) {
  name: '${resourcesName}-jumpbox'
  params: {
    vmName: jumpboxVmName
    location: location
    vnetName: virtualNetwork.outputs.name
    jumpboxVmSize: jumpboxVmSize
    jumpboxSubnet: jumpboxSubnet
    jumpboxAdminUser: jumpboxAdminUser
    jumpboxAdminPassword: jumpboxAdminPassword
    tags: tags
    logAnalyticsWorkspaceId: logAnalyticsWorkSpaceResourceId
  }
}

output vnetName string = virtualNetwork.outputs.name
output vnetResourceId string = virtualNetwork.outputs.resourceId
output subnets array = virtualNetwork.outputs.subnets // This one holds critical info for subnets, including NSGs

output bastionSubnetId string = bastionHost.outputs.subnetId
output bastionSubnetName string = bastionHost.outputs.subnetName
output bastionHostId string = bastionHost.outputs.resourceId
output bastionHostName string = bastionHost.outputs.name

output jumpboxSubnetName string = jumpbox.outputs.subnetId
output jumpboxSubnetId string = jumpbox.outputs.subnetId
output jumpboxVmName string = jumpbox.outputs.vmName
output jumpboxVmId string = jumpbox.outputs.vmId


