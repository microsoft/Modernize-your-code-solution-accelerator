@minLength(3)
@maxLength(20)
@description('A unique application/env name for all resources in this deployment. This should be 3-20 characters long')
param environmentName string = 'Code Mod Dev'

@minLength(3)
@description('Azure region for all services.')
param location string = resourceGroup().location

@description('Optional. Enable private networking for the resources. Set to true to enable private networking.')
param enablePrivateNetworking bool = true

@description('Enable monitoring for the resources. This will enable Application Insights and Log Analytics. Defaults to false.')
param enableMonitoring bool = true

@description('Optional. Specifies the resource tags for all the resources. Tag "azd-env-name" is automatically added to all resources.')
param tags object = {}

var resourcesName = trim(replace(
  replace(replace(replace(replace(environmentName, '-', ''), '_', ''), '.', ''), '/', ''),
  ' ',
  ''
))
var resourcesToken = substring(uniqueString(subscription().id, location, resourcesName), 0, 5)
var uniqueResourcesName = '${resourcesName}${resourcesToken}'

var defaultTags = {
  'azd-env-name': resourcesName
}
var allTags = union(defaultTags, tags)

module logAnalyticsWorkspace 'br/public:avm/res/operational-insights/workspace:0.11.2' = if (enableMonitoring || enablePrivateNetworking) {
  name: take('log-analytics-${resourcesName}-deployment', 64)
  params: {
    name: 'log-${resourcesName}'
    location: location
    skuName: 'PerGB2018'
    dataRetention: 30
    diagnosticSettings: [{ useThisWorkspace: true }]
    tags: allTags
  }
}


// Attention: Below two modules are intended to be used together. 
// You need to edit and verity modules/network/networkConfig.bicep before using the modules below.
// // Otherwise, you will get the default configuration written in this file. 

module configNetwork 'modules/network/networkConfig.bicep' = if (enablePrivateNetworking) {
  name: take('network-${resourcesName}-config', 64)
  params: {
  }
}
module createNetwork 'modules/network/network.bicep' = if (enablePrivateNetworking) {
  name: take('network-${resourcesName}-create', 64)
  params: {
    resourcesName: take('network-${resourcesName}', 15)
    logAnalyticsWorkSpaceResourceId: logAnalyticsWorkspace.outputs.resourceId
    addressPrefixes: configNetwork.outputs.networkConfig.addressPrefixes
    solutionSubnets: configNetwork.outputs.networkConfig.solutionSubnets
    azureBationHost: configNetwork.outputs.networkConfig.azureBationHost
    azureBastionSubnet: configNetwork.outputs.networkConfig.azureBastionSubnet
    jumpboxVM: configNetwork.outputs.networkConfig.jumpboxVM
    jumpboxVmSize: configNetwork.outputs.networkConfig.jumpboxVmSize
    jumpboxAdminUser: configNetwork.outputs.networkConfig.jumpboxAdminUser
    jumpboxAdminPassword: configNetwork.outputs.networkConfig.jumpboxAdminPassword
    jumpboxSubnet:configNetwork.outputs.networkConfig.jumpboxSubnet
    location: location
    tags: allTags
  }
}
