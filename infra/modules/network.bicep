param resourcesName string
param logAnalyticsWorkSpaceResourceId string
param location string
param tags object = {}

module network 'network/main.bicep' =  {
  name: take('network-${resourcesName}-create', 64)
  params: {
    resourcesName: resourcesName
    location: location
    logAnalyticsWorkSpaceResourceId: logAnalyticsWorkSpaceResourceId
    tags: tags
    addressPrefixes: ['10.0.0.0/21']
    solutionSubnets: [
      // Only one delegation per subnet is supported by the AVM module as of June 2025.
      // For subnets that do not require delegation, leave the array empty.
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
        delegations: [
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
        delegations: [
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
        delegations: [] // No delegation required for this subnet.
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
        delegations: [] // No delegation required for this subnet.
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
        delegations: [] // No delegation required for this subnet.
      }
    ]
    azureBationHost: true // Set to true to enable Azure Bastion Host creation.
    azureBastionSubnet: {
      name: 'AzureBastionSubnet' // Required name for Azure Bastion
      addressPrefixes: ['10.0.5.0/27']
      networkSecurityGroup: null // Azure Bastion subnet must NOT have an NSG
    }
    jumpboxVM: true // Set to true to enable Jumpbox VM creation.
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
                '10.0.5.0/27' // Azure Bastion subnet as an example here. You can adjust this as needed by adding more
              ]
              destinationAddressPrefixes: ['10.0.6.0/24']
            }
          }
        ]
      }
    }
  }
}

output vnetName string = network.outputs.vnetName
output vnetResourceId string = network.outputs.vnetResourceId
output subnets array = network.outputs.subnets // This one holds critical info for subnets, including NSGs

output azureBastionSubnetId string = network.outputs.azureBastionSubnetId
output azureBastionSubnetName string = network.outputs.azureBastionSubnetName
output azureBastionHostId string = network.outputs.azureBastionHostId
output azureBastionHostName string = network.outputs.azureBastionHostName

output jumpboxSubnetName string = network.outputs.jumpboxSubnetName
output jumpboxSubnetId string = network.outputs.jumpboxSubnetId
output jumpboxVmName string = network.outputs.jumpboxVmName
output jumpboxVmId string = network.outputs.jumpboxVmId

