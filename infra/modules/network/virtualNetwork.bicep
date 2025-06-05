/****************************************************************************************************************************/
// Networking - NSGs, VNET and Subnets. Each subnet has its own NSG
/****************************************************************************************************************************/

param location string = resourceGroup().location
param vnetName string 
param vnetAddressPrefixes array
param subnetArray array
param tags object = {}
param logAnalyticsWorkspaceId string


// 1. Create NSGs for subnets 
// using AVM Network Security Group module
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/network/network-security-group

@batchSize(1)
module nsgs 'br/public:avm/res/network/network-security-group:0.5.1' = [
  for (subnet, i) in subnetArray: if (!empty(subnet.networkSecurityGroup)) {
    name: '${vnetName}-${subnet.networkSecurityGroup.name}'
    params: {
      name: '${vnetName}-${subnet.networkSecurityGroup.name}'
      location: location
      securityRules: subnet.networkSecurityGroup.securityRules
      tags: tags
    }
  }
]

// 2. Create VNet and subnets, with subnets associated with corresponding NSGs
// using AVM Virtual Network module
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/network/virtual-network

module virtualNetwork 'br/public:avm/res/network/virtual-network:0.7.0' =  {
  name: vnetName
  params: {
    name: vnetName
    location: location
    addressPrefixes: vnetAddressPrefixes
    subnets: [
      for (subnet, i) in subnetArray: {
        name: subnet.name
        addressPrefixes: subnet.addressPrefixes
        networkSecurityGroupResourceId: !empty(subnet.networkSecurityGroup) ? nsgs[i].outputs.resourceId : null
        delegation: !empty(subnet.delegations) ? subnet.delegations[0].serviceName : null  // AVM module expects a single delegation per subnet
      }
    ]
    diagnosticSettings: [
      {
        name: 'vnetDiagnostics'
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
    tags: tags
  }
}

output vnetName string = virtualNetwork.outputs.name
output vnetResourceId string = virtualNetwork.outputs.resourceId

// combined output array that holds subnet details along with NSG information
output subnets array = [
  for (subnet, i) in subnetArray: {
    name: subnet.name
    resourceId: virtualNetwork.outputs.subnetResourceIds[i]
    nsgName: !empty(subnet.networkSecurityGroup) ? subnet.networkSecurityGroup.name : null
    nsgResourceId: !empty(subnet.networkSecurityGroup) ? nsgs[i].outputs.resourceId : null
  }
]
