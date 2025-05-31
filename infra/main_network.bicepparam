// Parameters for main_network.bicep
// Use this file to provide default values for your network deployment

using './main_network.bicep'

param resourceGroupName = 'gaiye-avm-09-rg'
param location = 'eastus'

param networkIsolation = true
param privateEndPoint = true

param jumboxAdminUser = 'JumpboxAdmin' // Admin user for the jumpbox VM
param jumboxVmSize = 'Standard_D2s_v3' // 'Standard_B2s' not good enough for WAF 

param logAnalyticsWorkspaceReuse = true
param vnetReuse = false // set it to true if you want to reuse an existing VNet already creatd
param bastionHostReuse = false
param jumpboxReuse = false

//*******************************************************************
// Network Security Groups (NSGs) and their rules
//*******************************************************************

param addressPrefixes = [
  '10.0.0.0/20' //  4,096 IP addresses. Other options: (1) /16: 65,536 (2) /24: 256 Addresses 
]
param dnsServers = [
  '10.0.1.4'
  '10.0.1.5'
]


param webSecurityRules = [
  {
    name: 'AllowHttpsInbound'
    priority: 100
    direction: 'Inbound'
    access: 'Allow'
    protocol: 'Tcp'
    sourcePortRange: '*'
    destinationPortRange: '443'
    sourceAddressPrefixes: ['0.0.0.0/0']
    destinationAddressPrefixes: ['0.0.0.0/0']
  }
]

param appSecurityRules = [
  {
    name: 'AllowWebToApp'
    priority: 100
    direction: 'Inbound'
    access: 'Allow'
    protocol: 'Tcp'
    sourcePortRange: '*'
    destinationPortRange: '*'
    sourceAddressPrefixes: ['10.0.1.0/24'] // Web subnet
    destinationAddressPrefixes: ['0.0.0.0/0']
  }
]

param aiSecurityRules = [
  {
    name: 'AllowAppToAI'
    priority: 100
    direction: 'Inbound'
    access: 'Allow'
    protocol: 'Tcp'
    sourcePortRange: '*'
    destinationPortRange: '*'
    sourceAddressPrefixes: [
      '10.0.1.0/24' // Web subnet
      '10.0.2.0/24' // App subnet
    ]
    destinationAddressPrefixes: ['0.0.0.0/0']
  }
]

param dataSecurityRules = [
  {
    name: 'AllowWebandAppToData'
    priority: 100
    direction: 'Inbound'
    access: 'Allow'
    protocol: 'Tcp'
    sourcePortRange: '*'
    destinationPortRange: '*'
    sourceAddressPrefixes: [
      '10.0.1.0/24' // Web subnet
      '10.0.2.0/24' // App subnet
    ]
    destinationAddressPrefixes: ['0.0.0.0/0']
  }
]

param bastionSecurityRules = [
  {
    name: 'AllowBastionInbound'
    priority: 100
    direction: 'Inbound'
    access: 'Allow'
    protocol: 'Tcp'
    sourcePortRange: '*'
    destinationPortRange: '22'
    sourceAddressPrefixes: ['0.0.0.0/0']
    destinationAddressPrefixes: ['10.0.5.0/24']
  }
]

param jumpboxSecurityRules = [
  {
    name: 'AllowJumpboxInbound'
    priority: 100
    direction: 'Inbound'
    access: 'Allow'
    protocol: 'Tcp'
    sourcePortRange: '*'
    destinationPortRange: '22'
    sourceAddressPrefixes: ['0.0.0.0/0']
    destinationAddressPrefixes: ['10.0.6.0/24']
  }
]

param subnets = [
  {
    name: 'web'
    addressPrefix: '10.0.1.0/24'
    networkSecurityGroup: {
      name: 'web-nsg'
      securityRules: webSecurityRules
    }
  }
  {
    name: 'app'
    addressPrefix: '10.0.2.0/24'
    networkSecurityGroup: {
      name: 'app-nsg'
      securityRules: appSecurityRules
    }
  }
  {
    name: 'ai'
    addressPrefix: '10.0.3.0/24'
    networkSecurityGroup: {
      name: 'ai-nsg'
      securityRules: aiSecurityRules
    }
  }
  {
    name: 'data'
    addressPrefix: '10.0.4.0/24'
    networkSecurityGroup: {
      name: 'data-nsg'
      securityRules: dataSecurityRules
    }
  }
  {
    name: 'bastion'
    addressPrefix: '10.0.5.0/24'
    networkSecurityGroup: {
      name: 'bastion-nsg'
      securityRules: bastionSecurityRules
    }
  }
  {
    name: 'jumpbox'
    addressPrefix: '10.0.6.0/24'
    networkSecurityGroup: {
      name: 'jumpbox-nsg'
      securityRules: jumpboxSecurityRules
    }
  }
]
