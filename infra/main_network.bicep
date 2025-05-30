targetScope = 'subscription'

@minLength(6)
@maxLength(25)
@description('Name of the solution. This is used to generate a short unique hash used in all resources.')
param solutionName string = 'Code Modernization'

@description('Type of the solution. This is used for tagging and categorization.')
param solutionType string = 'Solution Accelerator'

param resourceGroupName string 
param location string 

param tags object = {
  'Solution Name': solutionName
  'Solution Type': solutionType
}


param vnetReuse bool = false // If true, will reuse existing VNet if available
param bastionHostReuse bool = false // If true, will reuse existing Bastion Host if available
param jumpboxReuse bool = false // If true, will reuse existing Jumpbox VM if available

/**************************************************************************/
// prefix generation 
/**************************************************************************/
var cleanSolutionName = replace(solutionName, ' ', '')  // get rid of spaces
var resourceToken = toLower('${substring(cleanSolutionName, 0, 1)}${uniqueString(cleanSolutionName, resourceGroupName, subscription().id)}')
var resourceTokenTrimmed = length(resourceToken) > 9 ? substring(resourceToken, 0, 9) : resourceToken
var prefix = toLower(replace(resourceTokenTrimmed, '_', ''))

// Network parameters (these will be set via main_network.bicepparam)
param networkIsolation bool 

param defaultSecurityRules array
param webSecurityRules array 
param appSecurityRules array 
param aiSecurityRules array 
param dataSecurityRules array 

//param vnetName string
param addressPrefixes array
param dnsServers array
param subnets array
var vnetName = '${prefix}-vnet'


param jumboxAdminUser string 
param jumboxVmSize string = 'Standard_D2s_v3' // Default VM size for Jumpbox, can be overridden
param privateEndPoint bool = true



resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: resourceGroupName
  location: location
}


/**************************************************************************/
// Log Analytics Workspace that will be used across the solution
/**************************************************************************/
// crate a Log Analytics Workspace using AVM
module logAnalyticsWorkSpace 'modules/logAnalyticsWorkSpace.bicep' = {
  name: '${prefix}logAnalyticsWorkspace'
  scope: rg
  params: {
    logAnalyticsWorkSpaceName: '${prefix}law'
    location: location
    tags: tags
  }
}
output logAnalyticsWorkspaceId string = logAnalyticsWorkSpace.outputs.workspaceId



/**************************************************************************/
// Network Structures 
/**************************************************************************/

// Diagnostic settings for VNet using Log Analytics Workspace
var diagnosticSettings = [
  {
    name: '${prefix}vnetDiagnostics'
    workspaceResourceId: logAnalyticsWorkSpace.outputs.workspaceId
    logs: [
      // Prioritized: Only most important categories for VNet/network security
      {
        category: 'NetworkSecurityGroupEvent'
        enabled: true
        retentionPolicy: {
          enabled: false
          days: 0
        }
      }
      {
        category: 'NetworkSecurityGroupRuleCounter'
        enabled: true
        retentionPolicy: {
          enabled: false
          days: 0
        }
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
        retentionPolicy: {
          enabled: false  // for development, set to fals=
          days: 0
          // Replace with the following lines to enable retention policy
          // enabled: true
          // days: 30
        }
      }
    ]
  }
]

// 1. Deploy the Virtual Network and Subnets
// Reference an existing Virtual Network if vnetReuse is true
resource existingVnet 'Microsoft.Network/virtualNetworks@2023-09-01' existing = if (networkIsolation && vnetReuse) {
  name: vnetName
  scope: rg
}

module network 'modules/network.bicep' = if (networkIsolation && !vnetReuse) {
  scope: rg
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

// Use vnetId for dependencies
var vnetId = vnetReuse ? existingVnet.id : network.outputs.vnetId


// 2. Deploy NSGs for each subnet (example for web, app, ai, data, bastion, jumpbox)

module webNsg 'modules/nsg.bicep' = if (networkIsolation && !vnetReuse) {
  scope:rg
  name: '${prefix}WebNsg'
  params: {
    nsgName: '${prefix}WebNsg'
    location: location
    securityRules: webSecurityRules
    tags: tags
  }
}
module appNsg 'modules/nsg.bicep' = if (networkIsolation && !vnetReuse) {
  scope:rg
  name: '${prefix}AppNsg'
  params: {
    nsgName: '${prefix}AppNsg'
    location: location
    securityRules: appSecurityRules
    tags: tags
  }
}
module aiNsg 'modules/nsg.bicep' = if (networkIsolation && !vnetReuse) {
  scope:rg
  name: '${prefix}AiNsg'
  params: {
    nsgName: '${prefix}AiNsg'
    location: location
    securityRules: aiSecurityRules
    tags: tags
  }
}
module dataNsg 'modules/nsg.bicep' = if (networkIsolation && !vnetReuse) {
  scope:rg
  name: '${prefix}DataNsg'
  params: {
    nsgName: '${prefix}DataNsg'
    location: location
    securityRules: dataSecurityRules
    tags: tags
  }
}
module bastionNsg 'modules/nsg.bicep' = if (networkIsolation && !vnetReuse) {
  scope:rg
  name: '${prefix}BastionNsg'
  params: {
    nsgName: '${prefix}BastionNsg'
    location: location
    securityRules: defaultSecurityRules
    tags: tags
  }
}
module jumpboxNsg 'modules/nsg.bicep' = if (networkIsolation && !jumpboxReuse) {
  scope:rg
  name: '${prefix}JumpboxNsg'
  params: {
    nsgName: '${prefix}JumpboxNsg'
    location: location
    securityRules: defaultSecurityRules
    tags: tags
  }
}

// 3. Deploy Route Tables (example for web and app subnets)
module webRouteTable 'modules/routeTable.bicep' = if (networkIsolation) {
  scope:rg
  name: '${prefix}WebRouteTable'
  params: {
    routeTableName: '${prefix}webRouteTable'
    location: location
    tags: tags
  }
}
module appRouteTable 'modules/routeTable.bicep' = {
  scope:rg
  name: '${prefix}AppRouteTable'
  params: {
    routeTableName: '${prefix}appRouteTable'
    location: location
    tags: tags
  }
}

// *********************************************************************************************
// Bastion Host and JumpBox VM
// This section is optional and can be enabled based on the network isolation requirements.
// *********************************************************************************************

// 4. (Optional) Deploy Bastion Host and JumpBox VM using outputs from network module
resource existingBastionHost 'Microsoft.Network/bastionHosts@2023-09-01' existing = if (networkIsolation && bastionHostReuse) {
  name: '${prefix}bastionHost'
  scope: rg
}

module bastionHost 'modules/bastionHost.bicep' = if (networkIsolation && !bastionHostReuse) {
  scope: rg
  name: '${prefix}BastionHost'
  params: {
    bastionHostName: '${prefix}bastionHost'
    location: location
    vnetId: vnetId
    tags: tags
  }
}

var bastionHostId = bastionHostReuse ? existingBastionHost.id : bastionHost.outputs.bastionHostId

// Reference an existing JumpBox VM if jumpboxReuse is true
resource existingJumpbox 'Microsoft.Compute/virtualMachines@2023-09-01' existing = if (networkIsolation && jumpboxReuse) {
  name: '${prefix}jumpbox-vm'
  scope: rg
}

module jumpbox 'modules/jumpbox.bicep' = if (networkIsolation && !jumpboxReuse) {
  scope: rg
  name: '${prefix}jumpbox-vm'
  params: {
    prefix: prefix
    vmName: '${prefix}jumpbox-vm'
    location: location
    subnetId: network.outputs.subnetIds[5] // index for 'jumpbox' subnet
    adminUsername: jumboxAdminUser
    adminPasswordOrKey: 'P@ssword123456789$$$' // TODO - take this from Key Vault later on
    vmSize: jumboxVmSize
    tags: tags
    logAnalyticsWorkspaceId: logAnalyticsWorkSpace.outputs.workspaceId
  }
}

var jumpboxId = jumpboxReuse ? existingJumpbox.id : jumpbox.outputs.vmId
