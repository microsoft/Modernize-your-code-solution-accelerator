// /****************************************************************************************************************************/
// Create Jumpbox NSG and Jumpbox Subnet, then create Jumpbox VM
// /****************************************************************************************************************************/

@description('Required. Name of the Jumpbox Virtual Machine.')
param name string

@description('Optional. Azure region to deploy resources.')
param location string = resourceGroup().location

@description('Required. Name of the Virtual Network where the Jumpbox VM will be deployed.')
param vnetName string

@description('Required. Size of the Jumpbox Virtual Machine.')
param size string

import { subnetType } from 'virtualNetwork.bicep'
@description('Optional. Subnet configuration for the Jumpbox VM.')
param subnet subnetType?  

@minLength(3)
@maxLength(16)
@description('Required. A unique application/solution name for all resources in this deployment. This should be 3-16 characters long.')
param solutionName string = 'codemode'

@maxLength(5)
@description('Optional. A unique token for the solution. This is used to ensure resource names are unique for global resources. Defaults to a 5-character substring of the unique string generated from the subscription ID, resource group name, and solution name.')
param solutionUniqueToken string = substring(uniqueString(subscription().id, resourceGroup().name, solutionName), 0, 5)

@description('Username to access the Jumpbox VM.')
param username string

@secure()
@description('Password to access the Jumpbox VM.')
param password string 

@description('Optional. Tags to apply to the resources.')
param tags object = {}

@description('Required. Log Analytics Workspace Resource ID for VM diagnostics.')
param logAnalyticsWorkspaceId string

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@description('Optional. The resource group location.')
param solutionLocation string = resourceGroup().location

// ========== Virtual machine ========== //

var solutionSuffix = '${solutionName}${solutionUniqueToken}'
var maintenanceConfigurationResourceName = 'mc-${solutionSuffix}'
module maintenanceConfiguration 'br/public:avm/res/maintenance/maintenance-configuration:0.3.1' ={
  name: take('avm.res.compute.virtual-machine.${maintenanceConfigurationResourceName}', 64)
  params: {
    name: maintenanceConfigurationResourceName
    location: solutionLocation
    tags: tags
    enableTelemetry: enableTelemetry
    extensionProperties: {
      InGuestPatchMode: 'User'
    }
    maintenanceScope: 'InGuestPatch'
    maintenanceWindow: {
      startDateTime: '2024-06-16 00:00'
      duration: '03:55'
      timeZone: 'W. Europe Standard Time'
      recurEvery: '1Day'
    }
    visibility: 'Custom'
    installPatches: {
      rebootSetting: 'IfRequired'
      windowsParameters: {
        classificationsToInclude: [
          'Critical'
          'Security'
        ]
      }
      linuxParameters: {
        classificationsToInclude: [
          'Critical'
          'Security'
        ]
      }
    }
  }
}

// /******************************************************************************************************************/
//  Create Log Analytics Workspace for monitoring and diagnostics 
// /******************************************************************************************************************/
module logAnalyticsWorkspace 'br/public:avm/res/operational-insights/workspace:0.11.2' = {
  name: take('log-analytics-${solutionSuffix}-deployment', 64)
  params: {
    name: 'log-${solutionSuffix}'
    location: solutionLocation
    skuName: 'PerGB2018'
    dataRetention: 30
    diagnosticSettings: [{ useThisWorkspace: true }]
    tags: tags
  }
}

var dataCollectionRulesResourceName = 'dcr-${solutionSuffix}'
module windowsVmDataCollectionRules 'br/public:avm/res/insights/data-collection-rule:0.6.0' = {
  name: take('avm.res.insights.data-collection-rule.${dataCollectionRulesResourceName}', 64)
  params: {
    name: dataCollectionRulesResourceName
    tags: tags
    enableTelemetry: enableTelemetry
    location: solutionLocation
    dataCollectionRuleProperties: {
      kind: 'Windows'
      dataSources: {
        performanceCounters: [
          {
            streams: [
              'Microsoft-Perf'
            ]
            samplingFrequencyInSeconds: 60
            counterSpecifiers: [
              '\\Processor Information(_Total)\\% Processor Time'
              '\\Processor Information(_Total)\\% Privileged Time'
              '\\Processor Information(_Total)\\% User Time'
              '\\Processor Information(_Total)\\Processor Frequency'
              '\\System\\Processes'
              '\\Process(_Total)\\Thread Count'
              '\\Process(_Total)\\Handle Count'
              '\\System\\System Up Time'
              '\\System\\Context Switches/sec'
              '\\System\\Processor Queue Length'
              '\\Memory\\% Committed Bytes In Use'
              '\\Memory\\Available Bytes'
              '\\Memory\\Committed Bytes'
              '\\Memory\\Cache Bytes'
              '\\Memory\\Pool Paged Bytes'
              '\\Memory\\Pool Nonpaged Bytes'
              '\\Memory\\Pages/sec'
              '\\Memory\\Page Faults/sec'
              '\\Process(_Total)\\Working Set'
              '\\Process(_Total)\\Working Set - Private'
              '\\LogicalDisk(_Total)\\% Disk Time'
              '\\LogicalDisk(_Total)\\% Disk Read Time'
              '\\LogicalDisk(_Total)\\% Disk Write Time'
              '\\LogicalDisk(_Total)\\% Idle Time'
              '\\LogicalDisk(_Total)\\Disk Bytes/sec'
              '\\LogicalDisk(_Total)\\Disk Read Bytes/sec'
              '\\LogicalDisk(_Total)\\Disk Write Bytes/sec'
              '\\LogicalDisk(_Total)\\Disk Transfers/sec'
              '\\LogicalDisk(_Total)\\Disk Reads/sec'
              '\\LogicalDisk(_Total)\\Disk Writes/sec'
              '\\LogicalDisk(_Total)\\Avg. Disk sec/Transfer'
              '\\LogicalDisk(_Total)\\Avg. Disk sec/Read'
              '\\LogicalDisk(_Total)\\Avg. Disk sec/Write'
              '\\LogicalDisk(_Total)\\Avg. Disk Queue Length'
              '\\LogicalDisk(_Total)\\Avg. Disk Read Queue Length'
              '\\LogicalDisk(_Total)\\Avg. Disk Write Queue Length'
              '\\LogicalDisk(_Total)\\% Free Space'
              '\\LogicalDisk(_Total)\\Free Megabytes'
              '\\Network Interface(*)\\Bytes Total/sec'
              '\\Network Interface(*)\\Bytes Sent/sec'
              '\\Network Interface(*)\\Bytes Received/sec'
              '\\Network Interface(*)\\Packets/sec'
              '\\Network Interface(*)\\Packets Sent/sec'
              '\\Network Interface(*)\\Packets Received/sec'
              '\\Network Interface(*)\\Packets Outbound Errors'
              '\\Network Interface(*)\\Packets Received Errors'
            ]
            name: 'perfCounterDataSource60'
          }
        ]
      }
      destinations: {
        logAnalytics: [
          {
            workspaceResourceId: logAnalyticsWorkspace.outputs.resourceId
            name: 'la-${dataCollectionRulesResourceName}'
          }
        ]
      }
      dataFlows: [
        {
          streams: [
            'Microsoft-Perf'
          ]
          destinations: [
            'la-${dataCollectionRulesResourceName}'
          ]
          transformKql: 'source'
          outputStream: 'Microsoft-Perf'
        }
      ]
    }
  }
}

var proximityPlacementGroupResourceName = 'ppg-${solutionSuffix}'
module proximityPlacementGroup 'br/public:avm/res/compute/proximity-placement-group:0.3.2' = {
  name: take('avm.res.compute.proximity-placement-group.${proximityPlacementGroupResourceName}', 64)
  params: {
    name: proximityPlacementGroupResourceName
    location: solutionLocation
    tags: tags
    enableTelemetry: enableTelemetry
  }
}

// 1. Create Jumpbox NSG 
// using AVM Network Security Group module
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/network/network-security-group
module nsg 'br/public:avm/res/network/network-security-group:0.5.1' = if (!empty(subnet)) {
  name: take('avm.res.network.network-security-group.${subnet.?networkSecurityGroup.name}', 64)
  params: {
    name: '${subnet.?networkSecurityGroup.name}-${vnetName}'
    location: location
    securityRules: subnet.?networkSecurityGroup.securityRules
    tags: tags
    enableTelemetry: enableTelemetry
  }
}

// 2. Create Jumpbox subnet as part of the existing VNet 
// using AVM Virtual Network Subnet module
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/network/virtual-network/subnet
module subnetResource 'br/public:avm/res/network/virtual-network/subnet:0.1.2' = if (!empty(subnet)) {
  name: take('avm.res.network.virtual-network.subnet.${subnet.?name}', 64)
  params: {
    virtualNetworkName: vnetName
    name: subnet.?name ?? ''
    addressPrefixes: subnet.?addressPrefixes
    networkSecurityGroupResourceId: nsg.outputs.resourceId
    enableTelemetry: enableTelemetry
  }
}

// 3. Create Jumpbox VM 
// using AVM Virtual Machine module 
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/compute/virtual-machine
var vmName = take(name, 15) // Shorten VM name to 15 characters to avoid Azure limits

module vm 'br/public:avm/res/compute/virtual-machine:0.15.0' = {
  name: take('avm.res.compute.virtual-machine.${vmName}', 64)
  params: {
    name: vmName
    vmSize: size
    location: location
    adminUsername: username
    adminPassword: password
    tags: tags
    zone: 0
    imageReference: {
      offer: 'WindowsServer'
      publisher: 'MicrosoftWindowsServer'
      sku: '2019-datacenter'
      version: 'latest'
    }
    osType: 'Windows'
    osDisk: {
      name: 'osdisk-${vmName}'
      managedDisk: {
        storageAccountType: 'Standard_LRS'
      }
    }
    encryptionAtHost: false // Some Azure subscriptions do not support encryption at host
    nicConfigurations: [
      {
        name: 'nic-${vmName}'
        ipConfigurations: [
          {
            name: 'ipconfig1'
            subnetResourceId: subnetResource.outputs.resourceId
          }
        ]
        networkSecurityGroupResourceId: nsg.outputs.resourceId
        diagnosticSettings: [
          {
            name: 'jumpboxDiagnostics'
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
      }
    ]
    enableTelemetry: enableTelemetry
  }
}

output resourceId string = vm.outputs.resourceId
output name string = vm.outputs.name
output location string = vm.outputs.location

output subnetId string = subnetResource.outputs.resourceId
output subnetName string = subnetResource.outputs.name
output nsgId string = nsg.outputs.resourceId
output nsgName string = nsg.outputs.name

@export()
@description('Custom type definition for establishing Jumpbox Virtual Machine and its associated resources.')
type jumpBoxConfigurationType = {
  @description('The name of the Virtual Machine.')
  name: string

  @description('The size of the VM.')
  size: string?

  @description('Username to access VM.')
  username: string

  @secure()
  @description('Password to access VM.')
  password: string

  @description('Optional. Subnet configuration for the Jumpbox VM.')
  subnet: subnetType?
}
