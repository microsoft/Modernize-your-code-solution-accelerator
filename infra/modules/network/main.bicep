// /****************************************************************************************************************************/
//  This is an example test program to create private networking resources independently to show the usage of the modules
//    with sample inputs.
// 
//  Next Steps: 
//    Review infra/main.bicep and infra/modules/network.bicep for intended usage of the modules
//    Please infra/modules/network.bicep on how to  customize the networking resources for your application.
//  
// /****************************************************************************************************************************/

@minLength(6)
@maxLength(25)
@description('Default name used for all resources.')
param resourcesName string = 'testNetwork'

@minLength(3)
@description('Azure region for all services.')
param location string = 'eastus'

@description('Optional. Tags to be applied to the resources.')
param tags object = {}

var vnetName = 'vnet-${resourcesName}'
@description('Networking address prefix for the VNET only')
param addressPrefixes array = ['10.0.0.0/20'] // 4096 addresses (enough for 8 /23 subnets or 16 /24 subnets)

param enableBastionHost bool = true      
var bastionHostName = 'bastionHost-${resourcesName}'

param jumpboxVM bool = true       
param jumpboxAdminUser string = 'JumpboxAdminUser' 
@secure()
param jumpboxAdminPassword string = 'JumpboxAdminP@ssw0rd1234!'
param jumpboxVmSize string = 'Standard_D2s_v3'
var jumpboxVmName = 'jumpboxVM-${resourcesName}'

@description('Array of subnets to be created within the VNET.')
param subnets array = [
  // Only one delegation per subnet is supported by the AVM module as of June 2025.
  // For subnets that do not require delegation, leave the array empty.
  {
    name: 'web'
    addressPrefixes: ['10.0.0.0/23'] // /23 (10.0.0.0 - 10.0.1.255), 512 addresses
    networkSecurityGroup: {
      name: 'web-nsg'
      securityRules: [
        {
          name: 'AllowHttpsInbound'
          properties: {
            access: 'Allow'
            direction: 'Inbound'
            priority: 100
            protocol: 'Tcp'
            sourcePortRange: '*'
            destinationPortRange: '443'
            sourceAddressPrefixes: ['0.0.0.0/0']
            destinationAddressPrefixes: ['10.0.0.0/23']
          }
        }
      ]
    }
    delegations: [
      {
        name: 'containerapps-delegation'
        serviceName: 'Microsoft.App/environments'
      }
    ]
  }
  {
    name: 'app'
    addressPrefixes: ['10.0.2.0/23'] // /23 (10.0.2.0 - 10.0.3.255), 512 addresses
    networkSecurityGroup: {
      name: 'app-nsg'
      securityRules: [
        {
          name: 'AllowWebToApp'
          properties: {
            access: 'Allow'
            direction: 'Inbound'
            priority: 100
            protocol: 'Tcp'
            sourcePortRange: '*'
            destinationPortRange: '*'
            sourceAddressPrefixes: ['10.0.0.0/23'] // web subnet
            destinationAddressPrefixes: ['10.0.2.0/23']
          }
        }
      ]
    }
    delegations: [
      {
        name: 'containerapps-delegation'
        serviceName: 'Microsoft.App/environments'
      }
    ]
  }
  {
    name: 'ai'
    addressPrefixes: ['10.0.4.0/23'] // /23 (10.0.4.0 - 10.0.5.255), 512 addresses
    networkSecurityGroup: {
      name: 'ai-nsg'
      securityRules: [
        {
          name: 'AllowWebAppToAI'
          properties: {
            access: 'Allow'
            direction: 'Inbound'
            priority: 100
            protocol: 'Tcp'
            sourcePortRange: '*'
            destinationPortRange: '*'
            sourceAddressPrefixes: [
              '10.0.0.0/23' // web subnet
              '10.0.2.0/23' // app subnet
            ]
            destinationAddressPrefixes: ['10.0.4.0/23']
          }
        }
      ]
    }
    delegations: [] // No delegation required for this subnet.
  }
  {
    name: 'data'
    addressPrefixes: ['10.0.6.0/23'] // /23 (10.0.6.0 - 10.0.7.255)
    networkSecurityGroup: {
      name: 'data-nsg'
      securityRules: [
        {
          name: 'AllowWebAppAiToData'
          properties: {
            access: 'Allow'
            direction: 'Inbound'
            priority: 100
            protocol: 'Tcp'
            sourcePortRange: '*'
            destinationPortRange: '*'
            sourceAddressPrefixes: [
              '10.0.0.0/23' // web subnet
              '10.0.2.0/23' // app subnet
              '10.0.4.0/23' // ai subnet
            ]
            destinationAddressPrefixes: ['10.0.6.0/23']
          }
        }
      ]
    }
    delegations: [] // No delegation required for this subnet.
  }
  {
    name: 'services'
    addressPrefixes: ['10.0.8.0/23'] // /23 (10.0.8.0 - 10.0.9.255), 512 addresses
    networkSecurityGroup: {
      name: 'services-nsg'
      securityRules: [
        {
          name: 'AllowWebAppAiToServices'
          properties: {
            access: 'Allow'
            direction: 'Inbound'
            priority: 100
            protocol: 'Tcp'
            sourcePortRange: '*'
            destinationPortRange: '*'
            sourceAddressPrefixes: [
              '10.0.0.0/23' // web subnet
              '10.0.2.0/23' // app subnet
              '10.0.4.0/23' // ai subnet
            ]
            destinationAddressPrefixes: ['10.0.8.0/23']
          }
        }
      ]
    }
    delegations: [] // No delegation required for this subnet.
  }
]

// jumpbox parameters
param jumpboxSubnet object = {
  name: 'jumpbox'
  addressPrefixes: ['10.0.12.0/23'] // /23 (10.0.12.0 - 10.0.13.255), 512 addresses
  networkSecurityGroup: {
    name: 'jumpbox-nsg'
    securityRules: [
      {
        name: 'AllowJumpboxInbound'
        properties: {
          access: 'Allow'
          direction: 'Inbound'
          priority: 100
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '22'
          sourceAddressPrefixes: [
            '10.0.7.0/24' // Azure Bastion subnet as an example here. You can adjust this as needed by adding more
          ]
          destinationAddressPrefixes: ['10.0.12.0/23']
        }
      }
    ]
  }
}

// Azure Bastion Host parameters
param bastionSubnet object = {
  addressPrefixes: ['10.0.10.0/23'] // /23 (10.0.10.0 - 10.0.11.255), 512 addresses
  networkSecurityGroup: null // Azure Bastion subnet must NOT have an NSG
}


// /****************************************************************************************************************************/
// Create Log Analytics Workspace for monitoring and diagnostics 
// /****************************************************************************************************************************/

module logAnalyticsWorkspace 'br/public:avm/res/operational-insights/workspace:0.11.2' = {
  name: take('log-analytics-${resourcesName}-deployment', 64)
  params: {
    name: 'log-${resourcesName}'
    location: location
    skuName: 'PerGB2018'
    dataRetention: 30
    diagnosticSettings: [{ useThisWorkspace: true }]
    tags: tags
  }
}

// /****************************************************************************************************************************/
//  Networking - NSGs, VNET and Subnets. Each subnet has its own NSG
// /****************************************************************************************************************************/

module virtualNetwork 'virtualNetwork.bicep' = {
  name: '${resourcesName}-virtualNetwork'
  params: {
    name: vnetName
    addressPrefixes: addressPrefixes
    subnets: subnets
    location: location
    tags: tags
    logAnalyticsWorkspaceId: logAnalyticsWorkspace.outputs.resourceId
  }
}

// /****************************************************************************************************************************/
// // Create Azure Bastion Subnet and Azure Bastion Host
// /****************************************************************************************************************************/

module bastionHost 'bastionHost.bicep' = if(enableBastionHost && !empty(bastionSubnet)) {
  name: '${resourcesName}-bastionHost'
  params: {
    subnet: bastionSubnet
    location: location
    vnetName: virtualNetwork.outputs.name
    vnetId: virtualNetwork.outputs.resourceId
    name: bastionHostName
    logAnalyticsWorkspaceId: logAnalyticsWorkspace.outputs.resourceId
    tags: tags
  }
}

// /****************************************************************************************************************************/
// // create Jumpbox NSG and Jumpbox Subnet, then create Jumpbox VM
// /****************************************************************************************************************************/

module jumpbox 'jumpbox.bicep' =  if (jumpboxVM && !empty(jumpboxSubnet)) {
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
    logAnalyticsWorkspaceId: logAnalyticsWorkspace.outputs.resourceId
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
