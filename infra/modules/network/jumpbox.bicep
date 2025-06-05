// /****************************************************************************************************************************/
// Create Jumpbox NSG and Jumpbox Subnet, then create Jumpbox VM
// /****************************************************************************************************************************/
param vmName string = 'jumpboxVM' // Default name for Jumpbox VM
param location string = resourceGroup().location
param vnetName string 
param jumpboxVmSize string = 'Standard_D2s_v3' // Default VM size for Jumpbox, can be overridden

param jumpboxSubnet object = {} // This was defined in the .param file as a complex object 
param jumpboxAdminUser string = 'JumpboxAdminUser' // Default admin username for Jumpbox VM
@secure()
param jumpboxAdminPassword string 

param tags object = {}
param logAnalyticsWorkspaceId string

// 1. Create Jumpbox NSG 
// using AVM Network Security Group module
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/network/network-security-group
module jbNsg 'br/public:avm/res/network/network-security-group:0.5.1' = if (!empty(jumpboxSubnet)) {
  name: '${vnetName}-${jumpboxSubnet.networkSecurityGroup.name}'
  params: {
    name: '${vnetName}-${jumpboxSubnet.networkSecurityGroup.name}'
    location: location
    securityRules: jumpboxSubnet.networkSecurityGroup.securityRules
    tags: tags
  }
}

// 2. Create Jumpbox subnet as part of the existing VNet 
// using AVM Virtual Network Subnet module
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/network/virtual-network/subnet
module jbSubnet 'br/public:avm/res/network/virtual-network/subnet:0.1.2' = if (!empty(jumpboxSubnet)) {
  name: jumpboxSubnet.name
  params: {
    virtualNetworkName: vnetName
    name: jumpboxSubnet.name
    addressPrefixes: jumpboxSubnet.addressPrefixes
    networkSecurityGroupResourceId: jbNsg.outputs.resourceId
  }
}

// 3. Create Jumpbox VM 
// using AVM Virtual Machine module 
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/compute/virtual-machine
var limitedVmName = take(vmName, 15) // Shorten VM name to 15 characters to avoid Azure limits
module jbVm 'br/public:avm/res/compute/virtual-machine:0.15.0' = {
  name: vmName
  params: {
    name: limitedVmName
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
        name: '${limitedVmName}-nic'
        ipConfigurations: [
          {
            name: 'ipconfig1'
            subnetResourceId: jbSubnet.outputs.resourceId
          }
        ]
        networkSecurityGroupResourceId: jbNsg.outputs.resourceId
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

output vmId string = jbVm.outputs.resourceId
output vmName string = jbVm.outputs.name
output vMLocation string = jbVm.outputs.location

output subnetId string = jbSubnet.outputs.resourceId
output subnetName string = jbSubnet.outputs.name
output nsgId string = jbNsg.outputs.resourceId
output nsgName string = jbNsg.outputs.name
