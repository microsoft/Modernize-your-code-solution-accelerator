// Creates a JumpBox VM using AVM
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/compute/virtual-machine

@description('Prefix for resource names')
param prefix string

@description('Name of the JumpBox VM')
param vmName string

@description('Azure region for the VM')
param location string = resourceGroup().location

@description('Resource ID of the subnet for the VM')
param subnetId string

@description('Admin username')
param adminUsername string

@description('Admin password or SSH public key')
@secure()
param adminPasswordOrKey string

@description('VM size (e.g., "Standard_B2ms")')
param vmSize string = 'Standard_D2s_v3'

@description('Optional: Tags for the VM')
param tags object = {}

@description('Log Analytics Workspace Resource ID for diagnostics')
param logAnalyticsWorkspaceId string

// Diagnostic settings for Log Analytics only
var diagnosticSettings = [
  {
    name: 'jumpboxDiagnostics'
    metricCategories: [
      {
        category: 'AllMetrics'
      }
    ]
    workspaceResourceId: logAnalyticsWorkspaceId
  }
]


module virtualMachine 'br/public:avm/res/compute/virtual-machine:0.15.0' = {
  name: '${prefix}vmJumpBox'
  params: {
    adminUsername: adminUsername
    adminPassword: adminPasswordOrKey
    name: vmName
    location: location
    vmSize: vmSize
    osType: 'Windows'
    imageReference: {
      offer: 'WindowsServer'
      publisher: 'MicrosoftWindowsServer'
      sku: '2019-datacenter'
      version: 'latest'
    }
    nicConfigurations: [
      {
        name: 'nic-01'
        ipConfigurations: [
          {
            name: 'ipconfig-01'
            subnetResourceId: subnetId
          }
        ]
        diagnosticSettings: diagnosticSettings
      }
    ]
    osDisk: {
      name: '${vmName}-osdisk'
      createOption: 'FromImage'
      managedDisk: {
        storageAccountType: 'Premium_LRS'
      }
      diskSizeGB: 128
      deleteOption: 'Delete'
    }
    encryptionAtHost: false // Some Azure subscriptions do not support encryption at host
    zone: 1
    tags: tags
  }
}

output vmId string = virtualMachine.outputs.resourceId
output vmName string = virtualMachine.outputs.name
