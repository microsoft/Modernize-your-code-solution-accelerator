// Parameters for main_network.bicep
// Use this file to provide default values for your network deployment

using './main_network.bicep'

param resourceGroupName = 'gaiye-avm-waf-02-rg' // Name of the resource group for the network resources
param location = 'eastus'

param networkIsolation = true
param privateEndPoint = true


//***************************************************************************************
// Vnet and Solution Subnets with respective NSGs. i.g. web, app, ai, data, services
// Jumbox and Azure Bastion subnets are defined separately and optional. 
//***************************************************************************************

param vnetAddressPrefixes = [
  '10.0.0.0/21' // /21: 2048 addresses, good for up to 8-16 subnets. Other options: /23:512, /22:1024, /21:2048, /20:4096, /16: 65,536 (max for a VNet)
]

param mySubnets = [
  {
    name: 'web'
    addressPrefixes: ['10.0.0.0/24']
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
            destinationAddressPrefixes: ['10.0.0.0/24']
          }
        }
      ]
    }
  }
  {
    name: 'app'
    addressPrefixes: ['10.0.1.0/24']
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
            sourceAddressPrefixes: ['10.0.0.0/24'] // web subnet
            destinationAddressPrefixes: ['10.0.1.0/24']
          }
        }
      ]
    }
  }
  {
    name: 'ai'
    addressPrefixes: ['10.0.2.0/24']
    networkSecurityGroup: {
      name: 'ai-nsg'
      securityRules: [
        {
          name: 'AllowAppToAI'
          properties: {
            access: 'Allow'
            direction: 'Inbound'
            priority: 100
            protocol: 'Tcp'
            sourcePortRange: '*'
            destinationPortRange: '*'
            sourceAddressPrefixes: ['10.0.1.0/24'] // app subnet
            destinationAddressPrefixes: ['10.0.2.0/24']
          }
        }
      ]
    }
  }
  {
    name: 'data'
    addressPrefixes: ['10.0.3.0/24']
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
              '10.0.0.0/24' // web subnet
              '10.0.1.0/24' // app subnet
              '10.0.2.0/24' // ai subnet
            ]
            destinationAddressPrefixes: ['10.0.3.0/24']
          }
        }
      ]
    }
  }
  {
    name: 'services'
    addressPrefixes: ['10.0.4.0/24']
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
              '10.0.0.0/24' // web subnet
              '10.0.1.0/24' // app subnet
              '10.0.2.0/24' // ai subnet
            ]
            destinationAddressPrefixes: ['10.0.4.0/24']
          }
        }
      ]
    }
  }
]

//***************************************************************************************
// Jumpbox VM parameters
// jumpboxVM must be set to true to deploy a jumpbox VM.
//***************************************************************************************
param jumpboxVM = true // Set to 'true' to deploy a jumpbox VM, 'false' to skip it
param jumpboxAdminUser = 'JumpboxAdminUser' // Admin user for the jumpbox VM
@secure()
param jumpboxAdminPassword = 'JumpboxAdminP@ssw0rd1234!' // Password for the jumpbox VM admin user, must meet Azure password complexity requirements
param jumpboxVmSize = 'Standard_D2s_v3' // 'Standard_B2s' not good enough for WAF 

param jumpboxSubnet = {
   name: 'jumpbox'
    addressPrefixes: ['10.0.5.0/24']
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
            sourceAddressPrefixes: ['0.0.0.0/0']
            destinationAddressPrefixes: ['10.0.5.0/24']
          }
        }
      ]
    }
  }

  
//***************************************************************************************
// Azure Bastion parameters
// azureBationHost must be set to true to deploy Azure Bastion.
//***************************************************************************************
param azureBationHost = true // Set to 'true' to deploy Azure Bastion, 'false' to skip it
param azureBastionSubnet = {
  name: 'AzureBastionSubnet' // Required name for Azure Bastion
  addressPrefixes: ['10.0.6.0/27']
  networkSecurityGroup: null // Must not have an NSG
}
