// Creates a Network Security Group (NSG) using AVM modules
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/network/network-security-group

@description('Name of the Network Security Group')
param nsgName string

@description('Azure region for the NSG')
param location string = resourceGroup().location

@description('Optional: Tags for the NSG')
param tags object = {}

@description('Optional: Security rules for the NSG')
param securityRules array = [
  {
    name: 'AllowHttpsInbound'
    priority: 100
    direction: 'Inbound'
    access: 'Allow'
    protocol: 'Tcp'
    sourcePortRange: '*'
    destinationPortRange: '443'
    sourceAddressPrefix: '*'
    destinationAddressPrefix: '*'
  }
]

module networkSecurityGroup 'br/public:avm/res/network/network-security-group:0.5.1' = {
  name: nsgName
  params: {
    name: nsgName
    location: location
    securityRules: [
      for rule in securityRules: {
        name: rule.name
        properties: {
          priority: rule.priority
          direction: rule.direction
          access: rule.access
          protocol: rule.protocol
          sourcePortRange: rule.sourcePortRange
          destinationPortRange: rule.destinationPortRange
          sourceAddressPrefix: rule.sourceAddressPrefix
          destinationAddressPrefix: rule.destinationAddressPrefix
        }
      }
    ]
    tags: tags
  }
}

output nsgName string = networkSecurityGroup.outputs.name
