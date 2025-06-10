param resourcesName string
param logAnalyticsWorkSpaceResourceId string
param location string
param tags object = {}


// Subnet Classless Inter-Doman Routing (CIDR)  Sizing Reference Table (Best Practices)
// | CIDR      | # of Addresses | # of /24s | Notes                                 |
// |-----------|---------------|-----------|---------------------------------------|
// | /24       | 256           | 1         | Smallest recommended for Azure subnets |
// | /23       | 512           | 2         | Good for 1-2 workloads per subnet      |
// | /22       | 1024          | 4         | Good for 2-4 workloads per subnet      |
// | /21       | 2048          | 8         | Good for larger scale, future growth   |
// | /20       | 4096          | 16        | Used for default VNet in this solution |
// | /19       | 8192          | 32        |                                       |
// | /18       | 16384         | 64        |                                       |
// | /17       | 32768         | 128       |                                       |
// | /16       | 65536         | 256       |                                       |
// | /15       | 131072        | 512       |                                       |
// | /14       | 262144        | 1024      |                                       |
// | /13       | 524288        | 2048      |                                       |
// | /12       | 1048576       | 4096      |                                       |
// | /11       | 2097152       | 8192      |                                       |
// | /10       | 4194304       | 16384     |                                       |
// | /9        | 8388608       | 32768     |                                       |
// | /8        | 16777216      | 65536     |                                       |
//
// Best Practice Notes:
// - Use /24 as the minimum subnet size for Azure (smaller subnets are not supported for most services).
// - Plan for future growth: allocate larger address spaces (e.g., /20 or /21 for VNets) to allow for new subnets.
// - Avoid overlapping address spaces with on-premises or other VNets.
// - Use contiguous, non-overlapping ranges for subnets.
// - Document subnet usage and purpose in code comments.
// - For AVM modules, ensure only one delegation per subnet and leave delegations empty if not required.
//

module network 'network/main.bicep' =  {
  name: take('network-${resourcesName}-create', 64)
  params: {
    resourcesName: resourcesName
    location: location
    logAnalyticsWorkSpaceResourceId: logAnalyticsWorkSpaceResourceId
    tags: tags
    addressPrefixes: ['10.0.0.0/20'] // 4096 addresses (enough for 8 /23 subnets or 16 /24)
    subnets: [
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
    enableBastionHost: true // Set to true to enable Azure Bastion Host creation.
    bastionSubnet: {
      addressPrefixes: ['10.0.10.0/23'] // /23 (10.0.10.0 - 10.0.11.255), 512 addresses
      networkSecurityGroup: null // Azure Bastion subnet must NOT have an NSG
    }
    jumpboxVM: true // Set to true to enable Jumpbox VM creation.
    jumpboxVmSize: 'Standard_D2s_v3'
    jumpboxAdminUser: 'JumpboxAdminUser'
    jumpboxAdminPassword: 'JumpboxAdminP@ssw0rd1234!'
    jumpboxSubnet: {
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
  }
}

output vnetName string = network.outputs.vnetName
output vnetResourceId string = network.outputs.vnetResourceId
output subnets array = network.outputs.subnets // This one holds critical info for subnets, including NSGs

output bastionSubnetId string = network.outputs.bastionSubnetId
output bastionSubnetName string = network.outputs.bastionSubnetName
output bastionHostId string = network.outputs.bastionHostId
output bastionHostName string = network.outputs.bastionHostName

output jumpboxSubnetName string = network.outputs.jumpboxSubnetName
output jumpboxSubnetId string = network.outputs.jumpboxSubnetId
output jumpboxVmName string = network.outputs.jumpboxVmName
output jumpboxVmId string = network.outputs.jumpboxVmId

