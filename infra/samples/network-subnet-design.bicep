// /******************************************************************************************************************/
//  This is an example test program to create private networking resources independently with sample network design.
//    It is an illustration of how to use the main.bicep in the infra/modules/network folder, with your own parameters.
//    You can independently deploy this module to create a network with subnets, NSGs, Azure Bastion Host, and Jumpbox VM.
//    Test them with this test program. Then integrate your design into the modules/network.bicep which is intended for 
//    a specific network design. 
//  
//  All things in infra/modules/network are designed to be reusable and composable without the need to modify 
//     any code in the network folder. 
//
//  Please review below modules to understand how things are wired together:
//    infra/main.bicep
//    infra/modules/network.bicep
//    infra/moddules/network/main.bicep 
//  
// /******************************************************************************************************************/

@minLength(6)
@maxLength(25)
@description('Name used for naming all network resources.')
param resourcesName string = 'nettest'

@minLength(3)
@description('Azure region for all services.')
param location string = resourceGroup().location

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@description('Optional. Tags to be applied to the resources.')
param tags object = {}

import { bastionHostConfigurationType } from '../modules/network/bastionHost.bicep'
@description('Optional. Configuration for the Azure Bastion Host. Leave null to omit Bastion creation.')
param bastionConfiguration bastionHostConfigurationType = {
  name: 'bastion-${resourcesName}'
  subnetAddressPrefixes: ['10.0.10.0/23'] // /23 (10.0.10.0 - 10.0.11.255), 512 addresses
}

import { jumpBoxConfigurationType } from '../modules/network/jumpbox.bicep'
@description('Optional. Configuration for the Jumpbox VM. Leave null to omit Jumpbox creation.')
param jumpboxConfiguration jumpBoxConfigurationType = {
  name: 'vm-jumpbox-${resourcesName}'
  size: 'Standard_D2s_v3' // Default size, can be overridden
  username: 'JumpboxAdminUser'
  password: 'JumpboxAdminP@ssw0rd1234!'
  subnet: {
    name: 'jumpbox-subnet'
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
              '10.0.10.0/23' // Azure Bastion subnet as an example here. You can adjust this as needed by adding more
            ]
            destinationAddressPrefixes: ['10.0.12.0/23']
          }
        }
      ]
    }
  }
}

// ====================================================================================================================
// Below paremeters define default the VNET and subnets. You can customize them as needed. 
// ====================================================================================================================
@description('Networking address prefix for the VNET.')
param addressPrefixes array = ['10.0.0.0/20'] // 4096 addresses (enough for 8 /23 subnets or 16 /24 subnets)

// Subnet Classless Inter-Doman Routing (CIDR)  Sizing Reference Table (Best Practices)
// | CIDR      | # of Addresses | # of /24s | Notes                                 |
// |-----------|---------------|-----------|----------------------------------------|
// | /24       | 256           | 1         | Smallest recommended for Azure subnets |
// | /23       | 512           | 2         | Good for 1-2 workloads per subnet      |
// | /22       | 1024          | 4         | Good for 2-4 workloads per subnet      |
// | /21       | 2048          | 8         |                                        |
// | /20       | 4096          | 16        | Used for default VNet in this solution |
// | /19       | 8192          | 32        |                                        |
// | /18       | 16384         | 64        |                                        |
// | /17       | 32768         | 128       |                                        |
// | /16       | 65536         | 256       |                                        |
// | /15       | 131072        | 512       |                                        |
// | /14       | 262144        | 1024      |                                        |
// | /13       | 524288        | 2048      |                                        |
// | /12       | 1048576       | 4096      |                                        |
// | /11       | 2097152       | 8192      |                                        |
// | /10       | 4194304       | 16384     |                                        |
// | /9        | 8388608       | 32768     |                                        |
// | /8        | 16777216      | 65536     |                                        |
//
// Best Practice Notes:
// - Use /24 as the minimum subnet size for Azure (smaller subnets are not supported for most services).
// - Plan for future growth: allocate larger address spaces (e.g., /20 or /21 for VNets) to allow for new subnets.
// - Avoid overlapping address spaces with on-premises or other VNets.
// - Use contiguous, non-overlapping ranges for subnets.
// - Document subnet usage and purpose in code comments.
// - For AVM modules, ensure only one delegation per subnet and leave delegations empty if not required.

import { subnetType } from '../modules/network/virtualNetwork.bicep'
@description('Array of subnets to be created within the VNET.')
param subnets subnetType[] = [
  {
    name: 'peps'
    addressPrefixes: ['10.0.0.0/23'] // /23 (10.0.0.0 - 10.0.1.255), 512 addresses
    privateEndpointNetworkPolicies: 'Disabled'         // 'Disabled': to use private endpoints in the subnet.
    privateLinkServiceNetworkPolicies: 'Disabled'      // 'Disabled': to deploy a private link service in the subnet.
    networkSecurityGroup: {
      name: 'peps-nsg'
      securityRules: []
    }
  }
  {
    name: 'web'
    addressPrefixes: ['10.0.2.0/23'] // /23 (10.0.2.0 - 10.0.3.255), 512 addresses
    privateEndpointNetworkPolicies: 'Enabled'        // 'Disabled' only if you need to support private endpoints or private link services in the subnet. 
    privateLinkServiceNetworkPolicies: 'Enabled'     // 'Disabled' only if you need to support private endpoints or private link services in the subnet.
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
    name: 'app'
    addressPrefixes: ['10.0.4.0/23'] // /23 (10.0.4.0 - 10.0.5.255), 512 addresses
    privateEndpointNetworkPolicies: 'Enabled'      // 'Disabled' only if you need to support private endpoints or private link services in the subnet.
    privateLinkServiceNetworkPolicies: 'Enabled'   // 'Disabled' only if you need to support private endpoints or private link services in the subnet.
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
            sourceAddressPrefixes: ['10.0.2.0/23'] // web subnet
            destinationAddressPrefixes: ['10.0.4.0/23']
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
    addressPrefixes: ['10.0.6.0/23'] // /23 (10.0.6.0 - 10.0.7.255), 512 addresses
    privateEndpointNetworkPolicies: 'Enabled'   // 'Disabled' only if you need to support private endpoints or private link services in the subnet.
    privateLinkServiceNetworkPolicies: 'Enabled' // 'Disabled' only if you need to support private endpoints or private link services in the subnet.
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
              '10.0.2.0/23' // web subnet
              '10.0.4.0/23' // app subnet
            ]
            destinationAddressPrefixes: ['10.0.6.0/23']
          }
        }
      ]
    }
    delegations: [] // No delegation required for this subnet.
  }
  {
    name: 'data'
    addressPrefixes: ['10.0.8.0/23'] // /23 (10.0.8.0 - 10.0.9.255), 512 addresses
    privateEndpointNetworkPolicies: 'Disabled'    // 'Disabled': to use private endpoints in the subnet.
    privateLinkServiceNetworkPolicies: 'Disabled' // 'Disabled': to deploy a private link service in the subnet.
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
              '10.0.2.0/23' // web subnet
              '10.0.4.0/23' // app subnet
              '10.0.6.0/23' // ai subnet
            ]
            destinationAddressPrefixes: ['10.0.8.0/23']
          }
        }
      ]
    }
    delegations: [] // No delegation required for this subnet.
  }
]

// /******************************************************************************************************************/
//  Create Log Analytics Workspace for monitoring and diagnostics 
// /******************************************************************************************************************/
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

// /******************************************************************************************************************/          
// Networking - NSGs, VNET and Subnets. Each subnet has its own NSG
// /******************************************************************************************************************/

module network '../modules/network/main.bicep' = {
  name: take('network-${resourcesName}-create', 64)
  params: {
    resourcesName: resourcesName
    location: location
    logAnalyticsWorkSpaceResourceId: logAnalyticsWorkspace.outputs.resourceId
    tags: tags
    addressPrefixes: addressPrefixes
    subnets: subnets
    bastionConfiguration: bastionConfiguration
    jumpboxConfiguration: jumpboxConfiguration
    enableTelemetry: enableTelemetry
  }
}


output vnetName string = network.outputs.vnetName
output vnetResourceId string = network.outputs.vnetResourceId

output subnetPrivateEndpointsResourceId string = first(filter(network.outputs.subnets, s => s.name == 'peps')).?resourceId ?? ''


output subnetWebResourceId string = first(filter(network.outputs.subnets, s => s.name == 'web')).?resourceId ?? ''
output subnetAppResourceId string = first(filter(network.outputs.subnets, s => s.name == 'app')).?resourceId ?? ''
output subnetAiResourceId string = first(filter(network.outputs.subnets, s => s.name == 'ai')).?resourceId ?? ''
output subnetDataResourceId string = first(filter(network.outputs.subnets, s => s.name == 'data')).?resourceId ?? ''

output bastionHostResourceId string = bastionConfiguration != null ? network.outputs.bastionHostId : ''
output bastionSubnetResourceId string = bastionConfiguration != null ? network.outputs.bastionSubnetId : ''

