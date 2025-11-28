metadata name = 'Modernize Your Code Solution Accelerator'
metadata description = '''CSA CTO Gold Standard Solution Accelerator for Modernize Your Code. 
'''
targetScope = 'resourceGroup'

@minLength(3)
@maxLength(16)
@description('Required. A unique application/solution name for all resources in this deployment. This should be 3-16 characters long.')
param solutionName string

@maxLength(5)
@description('Optional. A unique token for the solution. This is used to ensure resource names are unique for global resources. Defaults to a 5-character substring of the unique string generated from the subscription ID, resource group name, and solution name.')
param solutionUniqueToken string = substring(uniqueString(subscription().id, resourceGroup().name, solutionName), 0, 5)

@minLength(3)
@metadata({ azd: { type: 'location' } })
@description('Optional. Azure region for all services. Defaults to the resource group location.')
param location string = resourceGroup().location

@allowed([
  'australiaeast'
  'eastus'
  'eastus2'
  'francecentral'
  'japaneast'
  'norwayeast'
  'southindia'
  'swedencentral'
  'uksouth'
  'westus'
  'westus3'
])
@metadata({
  azd : {
    type: 'location'
    usageName : [
      'OpenAI.GlobalStandard.gpt-4o, 150'
    ]
  }
})
@description('Required. Location for all AI service resources. This location can be different from the resource group location.')
param azureAiServiceLocation string

// Replica regions list based on article in [Azure regions list](https://learn.microsoft.com/azure/reliability/regions-list) and [Enhance resilience by replicating your Log Analytics workspace across regions](https://learn.microsoft.com/azure/azure-monitor/logs/workspace-replication#supported-regions) for supported regions for Log Analytics Workspace.
var replicaRegionPairs = {
  australiaeast: 'australiasoutheast'
  centralus: 'westus'
  eastasia: 'japaneast'
  eastus: 'centralus'
  eastus2: 'centralus'
  japaneast: 'eastasia'
  northeurope: 'westeurope'
  southeastasia: 'eastasia'
  uksouth: 'westeurope'
  westeurope: 'northeurope'
}
var replicaLocation = replicaRegionPairs[resourceGroup().location]

@description('Optional. AI model deployment token capacity. Defaults to 150K tokens per minute.')
param gptModelCapacity int = 150

@description('Optional. Enable monitoring for the resources. This will enable Application Insights and Log Analytics. Defaults to false.')
param enableMonitoring bool = false 

@description('Optional. Enable scaling for the container apps. Defaults to false.')
param enableScaling bool = false

@description('Optional. Enable redundancy for applicable resources. Defaults to false.')
param enableRedundancy bool = false

@description('Optional. The secondary location for the Cosmos DB account if redundancy is enabled.')
param secondaryLocation string?

@description('Optional. Enable private networking for the resources. Set to true to enable private networking. Defaults to false.')
param enablePrivateNetworking bool = false 

@description('Optional. Size of the Jumpbox Virtual Machine when created. Set to custom value if enablePrivateNetworking is true.')
param vmSize string? 

@description('Optional. Admin username for the Jumpbox Virtual Machine. Set to custom value if enablePrivateNetworking is true.')
@secure()
//param vmAdminUsername string = take(newGuid(), 20)
param vmAdminUsername string?

@description('Optional. Admin password for the Jumpbox Virtual Machine. Set to custom value if enablePrivateNetworking is true.')
@secure()
//param vmAdminPassword string = newGuid()
param vmAdminPassword string?

@description('Optional. Specifies the resource tags for all the resources. Tag "azd-env-name" is automatically added to all resources.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@minLength(1)
@description('Optional. GPT model deployment type. Defaults to GlobalStandard.')
param gptModelDeploymentType string = 'GlobalStandard'

@minLength(1)
@description('Optional. Name of the GPT model to deploy. Defaults to gpt-4o.')
param gptModelName string = 'gpt-4o'

@description('Optional. Container image name for backend service. Used by azd for container deployments.')
param backendImageName string = ''
@description('Optional. Container image name for frontend service. Used by azd for container deployments.')
param frontendImageName string = ''

@minLength(1)
@description('Optional. Set the Image tag. Defaults to latest')
param imageVersion string = 'latest'

@minLength(1)
@description('Optional. Version of the GPT model to deploy. Defaults to 2024-08-06.')
param gptModelVersion string = '2024-08-06'

@description('Optional. Use this parameter to use an existing AI project resource ID. Defaults to empty string.')
param azureExistingAIProjectResourceId string = ''

@description('Optional. Use this parameter to use an existing Log Analytics workspace resource ID. Defaults to empty string.')
param existingLogAnalyticsWorkspaceId string = ''

var allTags = union(
  {
    'azd-env-name': solutionName
  },
  tags
)

var solutionSuffix = toLower(trim(replace(
  replace(
    replace(replace(replace(replace('${solutionName}${solutionUniqueToken}', '-', ''), '_', ''), '.', ''), '/', ''),
    ' ',
    ''
  ),
  '*',
  ''
)))

var modelDeployment = {
  name: gptModelName
  model: {
    name: gptModelName
    format: 'OpenAI'
    version: gptModelVersion
  }
  sku: {
    name: gptModelDeploymentType
    capacity: gptModelCapacity
  }
  raiPolicyName: 'Microsoft.Default'
}

@description('Optional. Tag, Created by user name. Defaults to user principal name or object ID.')
param createdBy string = contains(deployer(), 'userPrincipalName')? split(deployer().userPrincipalName, '@')[0]: deployer().objectId
 

// ========== Resource Group Tag ========== //
resource resourceGroupTags 'Microsoft.Resources/tags@2021-04-01' = {
  name: 'default'
  properties: {
    tags: {
      ...resourceGroup().tags
      ...allTags
      TemplateName: 'Code Modernization'
      Type: enablePrivateNetworking ? 'WAF' : 'Non-WAF'
      CreatedBy: createdBy
    }
  }
}

#disable-next-line no-deployments-resources
resource avmTelemetry 'Microsoft.Resources/deployments@2024-03-01' = if (enableTelemetry) {
  name: take(
    '46d3xbcp.ptn.sa-modernizeyourcode.${replace('-..--..-', '.', '-')}.${substring(uniqueString(deployment().name, location), 0, 4)}',
    64
  )
  properties: {
    mode: 'Incremental'
    template: {
      '$schema': 'https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#'
      contentVersion: '1.0.0.0'
      resources: []
      outputs: {
        telemetry: {
          type: 'String'
          value: 'For more information, see https://aka.ms/avm/TelemetryInfo'
        }
      }
    }
  }
}

module appIdentity 'br/public:avm/res/managed-identity/user-assigned-identity:0.4.2' = {
  name: take('avm.res.managed-identity.user-assigned-identity.${solutionSuffix}', 64)
  params: {
    name: 'id-${solutionSuffix}'
    location: location
    tags: allTags
    enableTelemetry: enableTelemetry
  }
}
// Extracts subscription, resource group, and workspace name from the resource ID when using an existing Log Analytics workspace
var useExistingLogAnalytics = !empty(existingLogAnalyticsWorkspaceId)

var existingLawSubscription = useExistingLogAnalytics ? split(existingLogAnalyticsWorkspaceId, '/')[2] : ''
var existingLawResourceGroup = useExistingLogAnalytics ? split(existingLogAnalyticsWorkspaceId, '/')[4] : ''
var existingLawName = useExistingLogAnalytics ? split(existingLogAnalyticsWorkspaceId, '/')[8] : ''

resource existingLogAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2020-08-01' existing = if (useExistingLogAnalytics) {
  name: existingLawName
  scope: resourceGroup(existingLawSubscription, existingLawResourceGroup)
}

// Deploy new Log Analytics workspace only if required and not using existing
module logAnalyticsWorkspace 'br/public:avm/res/operational-insights/workspace:0.12.0' = if ((enableMonitoring || enablePrivateNetworking) && !useExistingLogAnalytics) {
  name: take('avm.res.operational-insights.workspace.${solutionSuffix}', 64)
  params: {
    name: 'log-${solutionSuffix}'
    location: location
    skuName: 'PerGB2018'
    dataRetention: enablePrivateNetworking ? 365 : 30
    diagnosticSettings: [{ useThisWorkspace: true }]
    tags: allTags
    enableTelemetry: enableTelemetry
    // WAF aligned configuration for Redundancy
    dailyQuotaGb: enableRedundancy ? 10 : null //WAF recommendation: 10 GB per day is a good starting point for most workloads
    replication: enableRedundancy
      ? {
          enabled: true
          location: replicaLocation
        }
      : null
    // WAF aligned configuration for Private Networking
    publicNetworkAccessForIngestion: enablePrivateNetworking ? 'Disabled' : 'Enabled'
    publicNetworkAccessForQuery: enablePrivateNetworking ? 'Disabled' : 'Enabled'
    dataSources: enablePrivateNetworking
      ? [
          {
            tags: allTags
            eventLogName: 'Application'
            eventTypes: [
              {
                eventType: 'Error'
              }
              {
                eventType: 'Warning'
              }
              {
                eventType: 'Information'
              }
            ]
            kind: 'WindowsEvent'
            name: 'applicationEvent'
          }
          {
            counterName: '% Processor Time'
            instanceName: '*'
            intervalSeconds: 60
            kind: 'WindowsPerformanceCounter'
            name: 'windowsPerfCounter1'
            objectName: 'Processor'
          }
          {
            kind: 'IISLogs'
            name: 'sampleIISLog1'
            state: 'OnPremiseEnabled'
          }
        ]
      : null
  }
}

// Log Analytics workspace ID, customer ID, and shared key (existing or new) 
var logAnalyticsWorkspaceResourceId = useExistingLogAnalytics ? existingLogAnalyticsWorkspaceId : logAnalyticsWorkspace!.outputs.resourceId
var LogAnalyticsPrimarySharedKey string = useExistingLogAnalytics? existingLogAnalyticsWorkspace.listKeys().primarySharedKey : logAnalyticsWorkspace.outputs.primarySharedKey
var LogAnalyticsWorkspaceId = useExistingLogAnalytics? existingLogAnalyticsWorkspace.properties.customerId : logAnalyticsWorkspace!.outputs.logAnalyticsWorkspaceId
var logAnalyticsWorkspaceName = useExistingLogAnalytics ? existingLawName : logAnalyticsWorkspace!.outputs.name

module applicationInsights 'br/public:avm/res/insights/component:0.7.0' = if (enableMonitoring) {
  name: take('avm.res.insights.component.${solutionSuffix}', 64)
  params: {
    name: 'appi-${solutionSuffix}'
    location: location
    workspaceResourceId: logAnalyticsWorkspaceResourceId
    diagnosticSettings: [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }]
    tags: allTags
    enableTelemetry: enableTelemetry
    retentionInDays: 365
    kind: 'web'
    disableIpMasking: false
    disableLocalAuth: true
    flowType: 'Bluefield'
  }
}


// Virtual Network with NSGs and Subnets
module virtualNetwork 'modules/virtualNetwork.bicep' = if (enablePrivateNetworking) {
  name: take('module.virtualNetwork.${solutionSuffix}', 64)
  params: {
    name: 'vnet-${solutionSuffix}'
    addressPrefixes: ['10.0.0.0/20'] // 4096 addresses (enough for 8 /23 subnets or 16 /24)
    location: location
    tags: tags
    logAnalyticsWorkspaceId: logAnalyticsWorkspaceResourceId
    resourceSuffix: solutionSuffix
    enableTelemetry: enableTelemetry
  }
}

// ========== Private DNS Zones ========== //
var privateDnsZones = [
  'privatelink.cognitiveservices.azure.com'
  'privatelink.openai.azure.com'
  'privatelink.services.ai.azure.com'
  'privatelink.documents.azure.com'
  'privatelink.vaultcore.azure.net'
  'privatelink.blob.${environment().suffixes.storage}'
  'privatelink.file.${environment().suffixes.storage}'
]

// DNS Zone Index Constants
var dnsZoneIndex = {
  cognitiveServices: 0
  openAI: 1
  aiServices: 2
  cosmosDB: 3
  keyVault: 4
  storageBlob: 5
  storageFile: 6
}

// ===================================================
// DEPLOY PRIVATE DNS ZONES
// - Deploys all zones if no existing Foundry project is used
// - Excludes AI-related zones when using with an existing Foundry project
// ===================================================
@batchSize(5)
module avmPrivateDnsZones 'br/public:avm/res/network/private-dns-zone:0.8.0' = [
  for (zone, i) in privateDnsZones: if (enablePrivateNetworking) {
    name: take('avm.res.network.private-dns-zone.${split(zone, '.')[1]}.${solutionSuffix}', 64)
    params: {
      name: zone
      tags: allTags
      enableTelemetry: enableTelemetry
      virtualNetworkLinks: [
        {
          name: take('vnetlink-${virtualNetwork!.outputs.name}-${split(zone, '.')[1]}', 80)
          virtualNetworkResourceId: virtualNetwork!.outputs.resourceId
        }
      ]
    }
  }
]

// Azure Bastion Host
var bastionHostName = 'bas-${solutionSuffix}'
module bastionHost 'br/public:avm/res/network/bastion-host:0.8.0' = if (enablePrivateNetworking) {
  name: take('avm.res.network.bastion-host.${bastionHostName}', 64)
  params: {
    name: bastionHostName
    skuName: 'Standard'
    location: location
    virtualNetworkResourceId: virtualNetwork!.outputs.resourceId
    diagnosticSettings: [
      {
        name: 'bastionDiagnostics'
        workspaceResourceId: logAnalyticsWorkspaceResourceId
        logCategoriesAndGroups: [
          {
            categoryGroup: 'allLogs'
            enabled: true
          }
        ]
      }
    ]
    tags: tags
    enableTelemetry: enableTelemetry
    publicIPAddressObject: {
      name: 'pip-${bastionHostName}'
      zones: []
    }
  }
}

// ========== Jumpbox Virtual machine ========== //
var maintenanceConfigurationResourceName = 'mc-${solutionSuffix}'
module maintenanceConfiguration 'br/public:avm/res/maintenance/maintenance-configuration:0.3.2' = if (enablePrivateNetworking) {
  name: take('avm.res.compute.virtual-machine.${maintenanceConfigurationResourceName}', 64)
  params: {
    name: maintenanceConfigurationResourceName
    location: location
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

var dataCollectionRulesResourceName = 'dcr-${solutionSuffix}'
var dataCollectionRulesLocation = useExistingLogAnalytics
  ? existingLogAnalyticsWorkspace!.location
  : logAnalyticsWorkspace!.outputs.location
module windowsVmDataCollectionRules 'br/public:avm/res/insights/data-collection-rule:0.8.0' = if (enablePrivateNetworking && enableMonitoring) {
  name: take('avm.res.insights.data-collection-rule.${dataCollectionRulesResourceName}', 64)
  params: {
    name: dataCollectionRulesResourceName
    tags: tags
    enableTelemetry: enableTelemetry
    location: dataCollectionRulesLocation
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
        windowsEventLogs: [
          {
            name: 'SecurityAuditEvents'
            streams: [
              'Microsoft-WindowsEvent'
            ]
            eventLogName: 'Security'
            eventTypes: [
              {
                eventType: 'Audit Success'
              }
              {
                eventType: 'Audit Failure'
              }
            ]
            xPathQueries: [
              'Security!*[System[(EventID=4624 or EventID=4625)]]'
            ]
          }
        ]
      }
      destinations: {
        logAnalytics: [
          {
            workspaceResourceId: logAnalyticsWorkspaceResourceId
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
module proximityPlacementGroup 'br/public:avm/res/compute/proximity-placement-group:0.4.1' = if (enablePrivateNetworking) {
  name: take('avm.res.compute.proximity-placement-group.${proximityPlacementGroupResourceName}', 64)
  params: {
    name: proximityPlacementGroupResourceName
    location: location
    tags: tags
    enableTelemetry: enableTelemetry
    availabilityZone: enableRedundancy ? 1 : -1
  }
}


var virtualMachineResourceName = take('vm-jumpbox-${solutionSuffix}', 15)
module virtualMachine 'br/public:avm/res/compute/virtual-machine:0.20.0' = if (enablePrivateNetworking) {
  name: take('avm.res.compute.virtual-machine.${virtualMachineResourceName}', 64)
  params: {
    name: virtualMachineResourceName
    location: location
    tags: tags
    enableTelemetry: enableTelemetry
    computerName: take(virtualMachineResourceName, 15)
    osType: 'Windows'
    vmSize: vmSize ?? 'Standard_D2s_v3'
    adminUsername: vmAdminUsername ?? 'JumpboxAdminUser'
    adminPassword: vmAdminPassword ?? 'JumpboxAdminP@ssw0rd1234!'
    managedIdentities: {
      systemAssigned: true
    }
    patchMode: 'AutomaticByPlatform'
    bypassPlatformSafetyChecksOnUserSchedule: true
    maintenanceConfigurationResourceId: maintenanceConfiguration.outputs.resourceId
    enableAutomaticUpdates: true
    encryptionAtHost: false
    proximityPlacementGroupResourceId: proximityPlacementGroup.outputs.resourceId
    availabilityZone: enableRedundancy ? 1 : -1
    imageReference: {
      publisher: 'microsoft-dsvm'
      offer: 'dsvm-win-2022'
      sku: 'winserver-2022'
      version: 'latest'
    }
    osDisk: {
      name: 'osdisk-${virtualMachineResourceName}'
      caching: 'ReadWrite'
      createOption: 'FromImage'
      deleteOption: 'Delete'
      diskSizeGB: 128
      managedDisk: { 
        // WAF aligned configuration - use Premium storage for better SLA when redundancy is enabled
        storageAccountType: enableRedundancy ? 'Premium_LRS' : 'Standard_LRS'
      }
    }
    nicConfigurations: [
      {
        name: 'nic-${virtualMachineResourceName}'
        tags: tags
        deleteOption: 'Delete'
        diagnosticSettings: enableMonitoring //WAF aligned configuration for Monitoring
          ? [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }]
          : null
        ipConfigurations: [
          {
            name: '${virtualMachineResourceName}-nic01-ipconfig01'
            subnetResourceId: virtualNetwork!.outputs.jumpboxSubnetResourceId
            diagnosticSettings: enableMonitoring //WAF aligned configuration for Monitoring
              ? [{ workspaceResourceId: logAnalyticsWorkspaceResourceId }]
              : null
          }
        ]
      }
    ]
    extensionAadJoinConfig: {
      enabled: true
      tags: tags
      typeHandlerVersion: '1.0'
      settings: {
        mdmId:''
      }
    }
    extensionAntiMalwareConfig: {
      enabled: true
      settings: {
        AntimalwareEnabled: 'true'
        Exclusions: {}
        RealtimeProtectionEnabled: 'true'
        ScheduledScanSettings: {
          day: '7'
          isEnabled: 'true'
          scanType: 'Quick'
          time: '120'
        }
      }
      tags: tags
    }
    //WAF aligned configuration for Monitoring
    extensionMonitoringAgentConfig: enableMonitoring
      ? {
          dataCollectionRuleAssociations: [
            {
              dataCollectionRuleResourceId: windowsVmDataCollectionRules.outputs.resourceId
              name: 'send-${logAnalyticsWorkspaceName}'
            }
          ]
          enabled: true
          tags: tags
        }
      : null
    extensionNetworkWatcherAgentConfig: {
      enabled: true
      tags: tags
    }
  }
}

module aiServices 'modules/ai-foundry/aifoundry.bicep' = {
  name: take('module.aifoundry.${solutionSuffix}', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [logAnalyticsWorkspace, virtualNetwork] // required due to optional flags that could change dependency
  params: {
    name: 'aif-${solutionSuffix}'
    location: azureAiServiceLocation
    sku: 'S0'
    kind: 'AIServices'
    deployments: [ modelDeployment ]
    projectName: 'proj-${solutionSuffix}'
    projectDescription: 'proj-${solutionSuffix}'
    logAnalyticsWorkspaceResourceId: enableMonitoring ? logAnalyticsWorkspaceResourceId : ''
    privateNetworking: enablePrivateNetworking
      ? {
          virtualNetworkResourceId: virtualNetwork!.outputs.resourceId
          subnetResourceId: virtualNetwork!.outputs.pepsSubnetResourceId
          cogServicesPrivateDnsZoneResourceId: avmPrivateDnsZones[dnsZoneIndex.cognitiveServices]!.outputs.resourceId
          openAIPrivateDnsZoneResourceId: avmPrivateDnsZones[dnsZoneIndex.openAI]!.outputs.resourceId
          aiServicesPrivateDnsZoneResourceId: avmPrivateDnsZones[dnsZoneIndex.aiServices]!.outputs.resourceId
        }
      : null
    existingFoundryProjectResourceId: azureExistingAIProjectResourceId
    disableLocalAuth: true //Should be set to true for WAF aligned configuration
    customSubDomainName: 'aif-${solutionSuffix}'
    apiProperties: {
      //staticsEnabled: false
    }
    allowProjectManagement: true
    managedIdentities: {
      systemAssigned: true
    }
    publicNetworkAccess: enablePrivateNetworking ? 'Disabled' : 'Enabled'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
    privateEndpoints: []
    roleAssignments: [
      {
        principalId: appIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: 'Cognitive Services OpenAI Contributor'
      }
      {
        principalId: appIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: '64702f94-c441-49e6-a78b-ef80e0188fee' // Azure AI Developer
      }
      {
        principalId: appIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: '53ca6127-db72-4b80-b1b0-d745d6d5456d' // Azure AI User
      }
    ]
    tags: allTags
    enableTelemetry: enableTelemetry
  }
}

var appStorageContainerName = 'appstorage'

module storageAccount 'modules/storageAccount.bicep' = {
  name: take('module.storageAccount.${solutionSuffix}', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [logAnalyticsWorkspace, virtualNetwork] // required due to optional flags that could change dependency
  params: {
    name: take('st${solutionSuffix}', 24)
    location: location
    tags: allTags
    skuName: enableRedundancy ? 'Standard_GZRS' : 'Standard_LRS'
    logAnalyticsWorkspaceResourceId: enableMonitoring ? logAnalyticsWorkspaceResourceId : ''
    privateNetworking: enablePrivateNetworking
      ? {
          virtualNetworkResourceId: virtualNetwork!.outputs.resourceId
          subnetResourceId: virtualNetwork!.outputs.pepsSubnetResourceId
          blobPrivateDnsZoneResourceId: avmPrivateDnsZones[dnsZoneIndex.storageBlob]!.outputs.resourceId
          filePrivateDnsZoneResourceId: avmPrivateDnsZones[dnsZoneIndex.storageFile]!.outputs.resourceId
        }
      : null
    containers: [
      {
        name: appStorageContainerName
        properties: {
          publicAccess: 'None'
        }
      }
    ]
    roleAssignments: [
      {
        principalId: appIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: 'Storage Blob Data Contributor'
      }
    ]
    enableTelemetry: enableTelemetry
  }
}

// Azure Container Registry for azd container deployments
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: take('acrreg${solutionSuffix}', 50)
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
  }
  tags: allTags
}
// ACR Pull role assignment for the managed identity
resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid('acr-role-assignment', solutionSuffix)
  scope: containerRegistry
  properties: {
    principalId: appIdentity.outputs.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull
  }
}

module keyVault 'modules/keyVault.bicep' = {
  name: take('module.keyVault.${solutionSuffix}', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [logAnalyticsWorkspace, virtualNetwork] // required due to optional flags that could change dependency
  params: {
    name: take('kv-${solutionSuffix}', 24)
    location: location
    sku: 'standard'
    logAnalyticsWorkspaceResourceId: enableMonitoring ? logAnalyticsWorkspaceResourceId : ''
    privateNetworking: enablePrivateNetworking
      ? {
          virtualNetworkResourceId: virtualNetwork!.outputs.resourceId
          subnetResourceId: virtualNetwork!.outputs.pepsSubnetResourceId
          privateDnsZoneResourceId: avmPrivateDnsZones[dnsZoneIndex.keyVault]!.outputs.resourceId
        }
      : null
    roleAssignments: [
      {
        principalId: aiServices.outputs.?systemAssignedMIPrincipalId ?? appIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: 'Key Vault Administrator'
      }
    ]
    tags: allTags
    enableTelemetry: enableTelemetry
  }
}

module cosmosDb 'modules/cosmosDb.bicep' = {
  name: take('module.cosmosDb.${solutionSuffix}', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [logAnalyticsWorkspace, virtualNetwork] // required due to optional flags that could change dependency
  params: {
    name: take('cosmos-${solutionSuffix}', 44)
    location: location
    dataAccessIdentityPrincipalId: appIdentity.outputs.principalId
    logAnalyticsWorkspaceResourceId: enableMonitoring ? logAnalyticsWorkspaceResourceId : ''
    zoneRedundant: enableRedundancy
    secondaryLocation: enableRedundancy && !empty(secondaryLocation) ? secondaryLocation : ''
    privateNetworking: enablePrivateNetworking
      ? {
          virtualNetworkResourceId: virtualNetwork!.outputs.resourceId
          subnetResourceId: virtualNetwork!.outputs.pepsSubnetResourceId
          privateDnsZoneResourceId: avmPrivateDnsZones[dnsZoneIndex.cosmosDB]!.outputs.resourceId
        }
      : null
    tags: allTags
    enableTelemetry: enableTelemetry
  }
}

var containerAppsEnvironmentName = 'cae-${solutionSuffix}'

module containerAppsEnvironment 'br/public:avm/res/app/managed-environment:0.11.3' = {
  name: take('avm.res.app.managed-environment.${solutionSuffix}', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [applicationInsights, logAnalyticsWorkspace, virtualNetwork] // required due to optional flags that could change dependency
  params: {
    name: containerAppsEnvironmentName
    infrastructureResourceGroupName: '${resourceGroup().name}-ME-${containerAppsEnvironmentName}'
    location: location
    zoneRedundant: enableRedundancy && enablePrivateNetworking
    publicNetworkAccess: 'Enabled' // public access required for frontend
    infrastructureSubnetResourceId: enablePrivateNetworking ? virtualNetwork!.outputs.webSubnetResourceId : null
    managedIdentities: {
      userAssignedResourceIds: [
        appIdentity.outputs.resourceId
      ]
    }
    appInsightsConnectionString: enableMonitoring ? applicationInsights.outputs.connectionString : null
    appLogsConfiguration: enableMonitoring
      ? {
          destination: 'log-analytics'
          logAnalyticsConfiguration: {
            customerId: LogAnalyticsWorkspaceId
            sharedKey: LogAnalyticsPrimarySharedKey
          }
        }
      : {}
    workloadProfiles: enablePrivateNetworking
      ? [
          // NOTE: workload profiles are required for private networking
          {
            name: 'Consumption'
            workloadProfileType: 'Consumption'
          }
        ]
      : []
    tags: allTags
    enableTelemetry: enableTelemetry
  }
}

module containerAppBackend 'br/public:avm/res/app/container-app:0.19.0' = {
  name: take('avm.res.app.container-app.backend.${solutionSuffix}', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [applicationInsights] // required due to optional flags that could change dependency
  params: {
    name: take('ca-backend-${solutionSuffix}', 32)
    location: location
    environmentResourceId: containerAppsEnvironment.outputs.resourceId
    managedIdentities: {
      userAssignedResourceIds: [
        appIdentity.outputs.resourceId
      ]
    }
    registries: [
      {
        server: containerRegistry.properties.loginServer
        identity: appIdentity.outputs.resourceId
      }
    ]
    containers: [
      {
        name: 'cmsabackend'
        image: !empty(backendImageName) ? backendImageName : 'cmsacontainerreg.azurecr.io/cmsabackend:${imageVersion}'
        env: concat(
          [
            {
              name: 'COSMOSDB_ENDPOINT'
              value: cosmosDb.outputs.endpoint
            }
            {
              name: 'COSMOSDB_DATABASE'
              value: cosmosDb.outputs.databaseName
            }
            {
              name: 'COSMOSDB_BATCH_CONTAINER'
              value: cosmosDb.outputs.containerNames.batch
            }
            {
              name: 'COSMOSDB_FILE_CONTAINER'
              value: cosmosDb.outputs.containerNames.file
            }
            {
              name: 'COSMOSDB_LOG_CONTAINER'
              value: cosmosDb.outputs.containerNames.log
            }
            {
              name: 'AZURE_BLOB_ACCOUNT_NAME'
              value: storageAccount.outputs.name
            }
            {
              name: 'AZURE_BLOB_CONTAINER_NAME'
              value: appStorageContainerName
            }

            {
              name: 'MIGRATOR_AGENT_MODEL_DEPLOY'
              value: modelDeployment.name
            }
            {
              name: 'PICKER_AGENT_MODEL_DEPLOY'
              value: modelDeployment.name
            }
            {
              name: 'FIXER_AGENT_MODEL_DEPLOY'
              value: modelDeployment.name
            }
            {
              name: 'SEMANTIC_VERIFIER_AGENT_MODEL_DEPLOY'
              value: modelDeployment.name
            }
            {
              name: 'SYNTAX_CHECKER_AGENT_MODEL_DEPLOY'
              value: modelDeployment.name
            }
            {
              name: 'SELECTION_MODEL_DEPLOY'
              value: modelDeployment.name
            }
            {
              name: 'TERMINATION_MODEL_DEPLOY'
              value: modelDeployment.name
            }
            {
              name: 'AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME'
              value: modelDeployment.name
            }
            {
              name: 'AI_PROJECT_ENDPOINT'
              value: aiServices.outputs.aiProjectInfo.apiEndpoint // or equivalent
            }
            {
              name: 'AZURE_AI_AGENT_PROJECT_NAME'
              value: aiServices.outputs.aiProjectInfo.name
            }
            {
              name: 'AZURE_AI_AGENT_RESOURCE_GROUP_NAME'
              value: resourceGroup().name
            }
            {
              name: 'AZURE_AI_AGENT_SUBSCRIPTION_ID'
              value: subscription().subscriptionId
            }
            {
              name: 'AZURE_AI_AGENT_ENDPOINT'
              value: aiServices.outputs.aiProjectInfo.apiEndpoint
            }
            {
              name: 'AZURE_CLIENT_ID'
              value: appIdentity.outputs.clientId // NOTE: This is the client ID of the managed identity, not the Entra application, and is needed for the App Service to access the Cosmos DB account.
            }
            {
              name: 'APP_ENV'
              value: 'prod'
            }
            {
              name: 'AZURE_BASIC_LOGGING_LEVEL'
              value: 'INFO'
            }
            {
              name: 'AZURE_PACKAGE_LOGGING_LEVEL'
              value: 'WARNING'
            }
            {
              name: 'AZURE_LOGGING_PACKAGES'
              value: ''
            }
          ],
          enableMonitoring
            ? [
                {
                  name: 'APPLICATIONINSIGHTS_INSTRUMENTATION_KEY'
                  value: applicationInsights.outputs.instrumentationKey
                }
                {
                  name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
                  value: applicationInsights.outputs.connectionString
                }
              ]
            : []
        )
        resources: {
          cpu: 1
          memory: '2.0Gi'
        }
        probes: enableMonitoring
          ? [
              {
                httpGet: {
                  path: '/health'
                  port: 8000
                }
                initialDelaySeconds: 3
                periodSeconds: 3
                type: 'Liveness'
              }
            ]
          : []
      }
    ]
    ingressTargetPort: 8000
    ingressExternal: true
    scaleSettings: {
      // maxReplicas: enableScaling ? 3 : 1
      maxReplicas: 1 // maxReplicas set to 1 (not 3) due to multiple agents created per type during WAF deployment
      minReplicas: 1
      rules: enableScaling
        ? [
            {
              name: 'http-scaler'
              http: {
                metadata: {
                  concurrentRequests: 100
                }
              }
            }
          ]
        : []
    }
    tags: union(allTags, {
      'azd-service-name': 'backend'
    })
    enableTelemetry: enableTelemetry
  }
}

module containerAppFrontend 'br/public:avm/res/app/container-app:0.19.0' = {
  name: take('avm.res.app.container-app.frontend.${solutionSuffix}', 64)
  params: {
    name: take('ca-frontend-${solutionSuffix}', 32)
    location: location
    environmentResourceId: containerAppsEnvironment.outputs.resourceId
    managedIdentities: {
      userAssignedResourceIds: [
        appIdentity.outputs.resourceId
      ]
    }
    registries: [
      {
        server: containerRegistry.properties.loginServer
        identity: appIdentity.outputs.resourceId
      }
    ]
    containers: [
      {
        env: [
          {
            name: 'API_URL'
            value: 'https://${containerAppBackend.outputs.fqdn}'
          }
          {
            name: 'APP_ENV'
            value: 'prod'
          }
        ]
        image: !empty(frontendImageName) ? frontendImageName : 'cmsacontainerreg.azurecr.io/cmsafrontend:${imageVersion}'
        name: 'cmsafrontend'
        resources: {
          cpu: 1
          memory: '2.0Gi'
        }
      }
    ]
    ingressTargetPort: 3000
    ingressExternal: true
    scaleSettings: {
      maxReplicas: enableScaling ? 3 : 1
      minReplicas: 1
      rules: enableScaling
        ? [
            {
              name: 'http-scaler'
              http: {
                metadata: {
                  concurrentRequests: 100
                }
              }
            }
          ]
        : []
    }
    tags: union(allTags, {
      'azd-service-name': 'frontend'
    })
    enableTelemetry: enableTelemetry
  }
}

@description('The resource group the resources were deployed into.')
output resourceGroupName string = resourceGroup().name
output WEB_APP_URL string = 'https://${containerAppFrontend.outputs.fqdn}'
output COSMOSDB_ENDPOINT string = cosmosDb.outputs.endpoint
output AZURE_BLOB_ACCOUNT_NAME string = storageAccount.outputs.name
output AZURE_BLOB_ENDPOINT string = 'https://${storageAccount.outputs.name}.blob.core.windows.net/'
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.properties.loginServer
output AZURE_AI_AGENT_PROJECT_NAME string = aiServices.outputs.aiProjectInfo.name
output AZURE_AI_AGENT_ENDPOINT string = aiServices.outputs.aiProjectInfo.apiEndpoint
output AZURE_AI_AGENT_RESOURCE_GROUP_NAME string = resourceGroup().name
output AZURE_AI_AGENT_SUBSCRIPTION_ID string = subscription().subscriptionId
output AI_PROJECT_ENDPOINT string = aiServices.outputs.aiProjectInfo.apiEndpoint
output AZURE_CLIENT_ID string = appIdentity.outputs.clientId
output AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME string = modelDeployment.name
output AZURE_BLOB_CONTAINER_NAME string = appStorageContainerName
output COSMOSDB_DATABASE string = cosmosDb.outputs.databaseName
output COSMOSDB_BATCH_CONTAINER string = cosmosDb.outputs.containerNames.batch
output COSMOSDB_FILE_CONTAINER string = cosmosDb.outputs.containerNames.file
output COSMOSDB_LOG_CONTAINER string = cosmosDb.outputs.containerNames.log
output APPLICATIONINSIGHTS_CONNECTION_STRING string = enableMonitoring ? applicationInsights.outputs.connectionString : ''
output MIGRATOR_AGENT_MODEL_DEPLOY string = modelDeployment.name
output PICKER_AGENT_MODEL_DEPLOY string = modelDeployment.name
output FIXER_AGENT_MODEL_DEPLOY string = modelDeployment.name
output SEMANTIC_VERIFIER_AGENT_MODEL_DEPLOY string = modelDeployment.name
output SYNTAX_CHECKER_AGENT_MODEL_DEPLOY string = modelDeployment.name  
