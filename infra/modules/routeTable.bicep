// Creates a Route Table using AVM modules
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/network/route-table

@description('Name of the Route Table')
param routeTableName string

@description('Azure region for the Route Table')
param location string = resourceGroup().location

@description('Optional: Tags for the Route Table')
param tags object = {}

@description('Optional: Routes for the Route Table')
param routes array = [
  // Example route
  // {
  //   name: 'defaultRoute'
  //   addressPrefix: '0.0.0.0/0'
  //   nextHopType: 'Internet'
  // }
]

module routeTable 'br/public:avm/res/network/route-table:0.4.1' = {
  name: routeTableName
  params: {
    name: routeTableName
    location: location
    routes: [
      for route in routes: {
        name: route.name
        properties: {
          addressPrefix: route.addressPrefix
          nextHopType: route.nextHopType
          nextHopIpAddress: route.nextHopIpAddress
        }
      }
    ]
    tags: tags
  }
}

output routeTableId string = routeTable.outputs.resourceId
output routeTableName string = routeTable.outputs.name
