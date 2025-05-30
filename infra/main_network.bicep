@minLength(6)
@maxLength(25)
@description('Name of the solution. This is used to generate a short unique hash used in all resources.')
param solutionName string = 'Code Modernization'
param solutionType string = 'Solution Accelerator'

param tags object = {
  'Solution Name': solutionName
  'Solution Type': solutionType
}

/**************************************************************************/
// prefix generation 
/**************************************************************************/
var cleanSolutionName = replace(solutionName, ' ', '')  // get rid of spaces
var resourceToken = toLower(uniqueString(subscription().id, cleanSolutionName))
var resourceTokenTrimmed = length(resourceToken) > 5 ? substring(resourceToken, 0, 5) : resourceToken
var prefix = toLower(replace(resourceTokenTrimmed, '_', ''))

// Network parameters (these will be set via main_network.bicepparam)
param networkIsolation bool 
param vnetName string
param location string = resourceGroup().location
param addressPrefixes array
param dnsServers array
param subnets array
param diagnosticSettings array = []

/**************************************************************************/
// Network Resource Modules
/**************************************************************************/

// 1. Deploy the Virtual Network and Subnets
module network 'modules/network.bicep' = if (networkIsolation) {
  name: '${prefix}network'
  params: {
    vnetName: vnetName
    location: location
    addressPrefixes: addressPrefixes
    dnsServers: dnsServers
    subnets: subnets
    tags: tags
    diagnosticSettings: diagnosticSettings
  }
}

// 2. Deploy NSGs for each subnet (example for web, app, ai, data, bastion, jumpbox)
module webNsg 'modules/nsg.bicep' = if (networkIsolation) {
  name: '${prefix}webNsg'
  params: {
    nsgName: 'web-nsg'
    location: location
    tags: tags
  }
}
module appNsg 'modules/nsg.bicep' = if (networkIsolation) {
  name: '${prefix}appNsg'
  params: {
    nsgName: '${prefix}appNsg'
    location: location
    tags: tags
  }
}
module aiNsg 'modules/nsg.bicep' = if (networkIsolation) {
  name: '${prefix}aiNsg'
  params: {
    nsgName: '${prefix}aiNsg'
    location: location
    tags: tags
  }
}
module dataNsg 'modules/nsg.bicep' = if (networkIsolation) {
  name: '${prefix}dataNsg'
  params: {
    nsgName: '${prefix}dataNsg'
    location: location
    tags: tags
  }
}
module bastionNsg 'modules/nsg.bicep' = if (networkIsolation) {
  name: '${prefix}bastionNsg'
  params: {
    nsgName: '${prefix}bastionNsg'
    location: location
    tags: tags
  }
}
module jumpboxNsg 'modules/nsg.bicep' = if (networkIsolation) {
  name: '${prefix}jumpboxNsg'
  params: {
    nsgName: '${prefix}jumpboxNsg'
    location: location
    tags: tags
  }
}

// 3. Deploy Route Tables (example for web and app subnets)
module webRouteTable 'modules/routeTable.bicep' = if (networkIsolation) {
  name: '${prefix}webRouteTable'
  params: {
    routeTableName: '${prefix}webRouteTable'
    location: location
    tags: tags
  }
}
module appRouteTable 'modules/routeTable.bicep' = {
  name: '${prefix}appRouteTable'
  params: {
    routeTableName: '${prefix}appRouteTable'
    location: location
    tags: tags
  }
}





// 4. (Optional) Deploy Bastion Host and JumpBox VM using outputs from network module
// module bastionHost 'modules/bastionHost.bicep' = {
//   name: 'bastionHost'
//   params: {
//     bastionHostName: 'bastion-host'
//     location: location
//     vnetId: network.outputs.vnetId
//     subnetId: network.outputs.subnetIds[4] // index for 'bastion' subnet
//     tags: tags
//   }
// }
// module jumpbox 'modules/jumpbox.bicep' = {
//   name: 'jumpbox'
//   params: {
//     vmName: 'jumpbox-vm'
//     location: location
//     subnetId: network.outputs.subnetIds[5] // index for 'jumpbox' subnet
//     adminUsername: '<admin-username>'
//     adminPasswordOrKey: '<admin-password-or-ssh-key>'
//     tags: tags
//   }
// }
