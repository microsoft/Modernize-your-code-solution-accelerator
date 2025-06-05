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


module network 'modules/network.bicep' = if (enablePrivateNetworking) {
  name: take('network-${resourcesName}-deployment', 64)
  params: {
    resourcesName: resourcesName
    logAnalyticsWorkSpaceResourceId: logAnalyticsWorkspace.outputs.resourceId
    location: location
    tags: allTags
  }
}
