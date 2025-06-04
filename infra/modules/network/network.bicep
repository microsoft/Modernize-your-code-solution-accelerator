@minLength(6)
@maxLength(25)
@description('Default name used for all resources.')
param resourcesName string

@minLength(3)
@description('Azure region for all services.')
param location string

@description('Resource ID of the Log Analytics Workspace for monitoring and diagnostics.')
param logAnalyticsWorkSpaceResourceId string

@description('Networking address prefix for the VNET and subnets.')
param addressPrefixes array

@description('Optional. Tags to be applied to the resources.')
param tags object = {}

param solutionSubnets array   
                    
var vnetName = 'vnet-${resourcesName}'

// jumpbox parameters
param jumpboxVM bool = false                         // set in .bicepparam file  
param jumpboxSubnet object = {}                      // set in .bicepparam file 
param jumpboxAdminUser string = 'JumpboxAdminUser'   // set in .bicepparam file 
@secure()
param jumpboxAdminPassword string                    // set in .bicepparam file 
param jumpboxVmSize string = 'Standard_D2s_v3'  
var jumpboxVmName = 'jumpboxVM-${resourcesName}'            

// Azure Bastion Host parameters
param azureBationHost bool = false                   // set in .bicepparam file 
param azureBastionSubnet object = {}                 // set in .bicepparam file 
var azureBastionHostName = 'bastionHost-${resourcesName}'  


// /****************************************************************************************************************************/
// Networking - NSGs, VNET and Subnets. Each subnet has its own NSG
// /****************************************************************************************************************************/

module vnetWithSubnets 'vnetWithSubnets.bicep' = {
  name: '${resourcesName}-vnetWithSubnets'
  params: {
    vnetName: vnetName
    vnetAddressPrefixes: addressPrefixes
    subnetArray: solutionSubnets
    location: location
    tags: tags
    logAnalyticsWorkspaceId: logAnalyticsWorkSpaceResourceId
  }
}

// /****************************************************************************************************************************/
// // Create Azure Bastion Subnet and Azure Bastion Host
// /****************************************************************************************************************************/

module azureBastionHost 'azureBationHost.bicep' = if (azureBationHost && !empty(azureBastionSubnet)) {
  name: '${resourcesName}-azureBastionHost'
  params: {
    azureBastionSubnet: azureBastionSubnet
    location: location
    vnetName: vnetWithSubnets.outputs.vnetName
    vnetId: vnetWithSubnets.outputs.vnetResourceId
    azureBationHostName: azureBastionHostName
    logAnalyticsWorkspaceId: logAnalyticsWorkSpaceResourceId
    tags: tags
  }
}

// /****************************************************************************************************************************/
// // create Jumpbox NSG and Jumpbox Subnet, then create Jumpbox VM
// /****************************************************************************************************************************/

module jumpboxWithSubnet 'jumpboxWithSubnet.bicep' = if (jumpboxVM && !empty(jumpboxSubnet)) {
  name: '${resourcesName}-jumpboxWithSubnet'
  params: {
    vmName: jumpboxVmName
    location: location
    vnetName: vnetWithSubnets.outputs.vnetName
    jumpboxVmSize: jumpboxVmSize
    jumpboxSubnet: jumpboxSubnet
    jumpboxAdminUser: jumpboxAdminUser
    jumpboxAdminPassword: jumpboxAdminPassword
    tags: tags
    logAnalyticsWorkspaceId: logAnalyticsWorkSpaceResourceId
  }
}


output vnetName string = vnetWithSubnets.outputs.vnetName
output vnetResourceId string = vnetWithSubnets.outputs.vnetResourceId
output subnets array = vnetWithSubnets.outputs.outputSubnetsArray // This one holds critical info for subnets, including NSGs

output azureBastionSubnetId string = azureBastionHost.outputs.bastionSubnetId
output azureBastionSubnetName string = azureBastionHost.outputs.bastionSubnetName
output azureBastionHostId string = azureBastionHost.outputs.bastionHostId
output azureBastionHostName string = azureBastionHost.outputs.bastionHostName

output jumpboxSubnetName string = jumpboxWithSubnet.outputs.jumpboxSubnetName
output jumpboxSubnetId string = jumpboxWithSubnet.outputs.jumpboxSubnetId
output jumpboxVmName string = jumpboxWithSubnet.outputs.jumpboxVmName
output jumpboxVmId string = jumpboxWithSubnet.outputs.jumpboxVmId


