// Creates a Log Analytics Workspace using the AVM module

//https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/operational-insights/workspace


@description('Name of the Log Analytics Workspace')
param logAnalyticsWorkSpaceName string

@description('Azure region for the workspace')
param location string = resourceGroup().location

@description('Optional: Tags for the workspace')
param tags object = {}

module workspace 'br/public:avm/res/operational-insights/workspace:0.11.2' = {
  name: logAnalyticsWorkSpaceName
  params: {
    // Required parameters
    name: logAnalyticsWorkSpaceName
    // Optional parameters
    location: location
    tags:tags 
  }
}

output workspaceId string = workspace.outputs.resourceId
