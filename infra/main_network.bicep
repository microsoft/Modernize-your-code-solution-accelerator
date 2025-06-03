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
param networkIsolation bool = false                  //  set in .bicepparam file 
param vnetAddressPrefixes array = []                 // set in .bicepparam file
param mySubnets array = []                           // set in .bicepparam file
var vnetName = '${prefix}-vnet'

// jumpbox parameters
param jumpboxVM bool = false                         //  set in .bicepparam file  
param jumpboxSubnet object = {}                      // set in .bicepparam file 
param jumpboxAdminUser string = 'JumpboxAdminUser'   // set in .bicepparam file 
@secure()
param jumpboxAdminPassword string                    // set in .bicepparam file 
param jumpboxVmSize string = 'Standard_D2s_v3'  
var jumpboxVmName = '${prefix}-jumpboxVM'            

// Azure Bastion Host parameters
param azureBationHost bool = false                   // set in .bicepparam file 
param azureBastionSubnet object = {}                 // set in .bicepparam file 
var azureBastionHostName = '${prefix}-bastionHost'  

// Private Endpoint parameters
param privateEndPoint bool = false                    // set in .bicepparam file 

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

/****************************************************************************************************************************/
// Netowrking - NSGs, VNET and Subnets. Each subnet has its own NSG
/****************************************************************************************************************************/

module vnetWithSubnets 'modules/vnetWithSubnets.bicep' = if (networkIsolation) {
  name: '${prefix}-vnetWithSubnets'
  params: {
    vnetName: vnetName
    vnetAddressPrefixes: vnetAddressPrefixes
    subnetArray: mySubnets
    location: location
    tags: tags
    logAnalyticsWorkspaceId: logAnalyticsWorkSpace.outputs.workspaceId
  }
}


output vnetName string = vnetWithSubnets.outputs.vnetName
output vnetResourceId string = vnetWithSubnets.outputs.vnetResourceId
output subnetsOutput array = vnetWithSubnets.outputs.outputSubnetsArray // This one holds critical info for subnets, including NSGs


/****************************************************************************************************************************/
// // Create Azure Bastion Subnet and Azure Bastion Host
/****************************************************************************************************************************/

module azureBastionHost 'modules/azureBationHost.bicep' = if (networkIsolation && azureBationHost && !empty(azureBastionSubnet)) {
  name: '${prefix}-azureBastionHost'
  params: {
    azureBastionSubnet: azureBastionSubnet
    location: location
    vnetName: vnetWithSubnets.outputs.vnetName
    vnetId: vnetWithSubnets.outputs.vnetResourceId
    azureBationHostName: azureBastionHostName
    logAnalyticsWorkspaceId: logAnalyticsWorkSpace.outputs.workspaceId
    tags: tags
  }
}

output azureBastionSubnetId string = azureBastionHost.outputs.bastionSubnetId
output azureBastionSubnetName string = azureBastionHost.outputs.bastionSubnetName
output azureBastionHostId string = azureBastionHost.outputs.bastionHostId
output azureBastionHostName string = azureBastionHost.outputs.bastionHostName



// /****************************************************************************************************************************/
// // create Jumpbox NSG and Jumpbox Subnet, then create Jumpbox VM
// /****************************************************************************************************************************/

module jumpboxWithSubnet 'modules/jumpboxWithSubnet.bicep' = if (networkIsolation && jumpboxVM && !empty(jumpboxSubnet)) {
  name: '${prefix}-jumpboxWithSubnet'
  params: {
    vmName: jumpboxVmName
    location: location
    vnetName: vnetWithSubnets.outputs.vnetName
    jumpboxVmSize: jumpboxVmSize
    jumpboxSubnet: jumpboxSubnet
    jumpboxAdminUser: jumpboxAdminUser
    jumpboxAdminPassword: jumpboxAdminPassword
    tags: tags
    logAnalyticsWorkspaceId: logAnalyticsWorkSpace.outputs.workspaceId
  }
}

output jumpboxSubnetName string = jumpboxWithSubnet.outputs.jumpboxSubnetName
output jumpboxSubnetId string = jumpboxWithSubnet.outputs.jumpboxSubnetId
output jumpboxVmName string = jumpboxWithSubnet.outputs.jumpboxVmName
output jumpboxVmId string = jumpboxWithSubnet.outputs.jumpboxVmId


