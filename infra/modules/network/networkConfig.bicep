// This module defines the network configuration only. 
// It does not create any resources. 
// the output networkConfig object contains the network configuration details. 

var inputNetworkConfig object = {
   addressPrefixes: ['10.0.0.0/21']
    solutionSubnets: [
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
        delegations: [ // only one delegation per subnet is supported by AVM
          {
            name: 'containerapps-delegation'
            serviceName: 'Microsoft.App/environments'
          }
        ]
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
        delegations: [ // only one delegation per subnet is supported by AVM
          {
            name: 'containerapps-delegation'
            serviceName: 'Microsoft.App/environments'
          }
        ]
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
        delegations: [] // only one delegation per subnet is supported by AVM
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
        delegations: [] // only one delegation per subnet is supported by AVM]
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
        delegations: [] // only one delegation per subnet is supported by AVM]
      }
    ]
    azureBationHost: true
    azureBastionSubnet: {
      name: 'AzureBastionSubnet' // Required name for Azure Bastion
      addressPrefixes: ['10.0.5.0/27']
      networkSecurityGroup: null // Must not have an NSG
    }
    jumpboxVM: true
    jumpboxVmSize: 'Standard_D2s_v3'
    jumpboxAdminUser: 'JumpboxAdminUser'
    jumpboxAdminPassword: 'JumpboxAdminP@ssw0rd1234!'
    jumpboxSubnet: {
      name: 'jumpbox'
      addressPrefixes: ['10.0.6.0/24']
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
                '10.0.5.0/27' // Azure Bastion subnet
              ]
              destinationAddressPrefixes: ['10.0.6.0/24']
            }
          }
        ]
      }
    }
  }

  output networkConfig object = inputNetworkConfig

