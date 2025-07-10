metadata name = 'AI Services and Project Module'
metadata description = 'This module creates an AI Services resource and an AI Foundry project within it. It supports private networking, OpenAI deployments, and role assignments.'

@description('Required. Name of the Cognitive Services resource. Must be unique in the resource group.')
param name string

@description('Optional. The location of the Cognitive Services resource.')
param location string // this should be passed 

@description('Optional. Kind of the Cognitive Services account. Use \'Get-AzCognitiveServicesAccountSku\' to determine a valid combinations of \'kind\' and \'SKU\' for your Azure region.')
@allowed([
  'AIServices'
  'AnomalyDetector'
  'CognitiveServices'
  'ComputerVision'
  'ContentModerator'
  'ContentSafety'
  'ConversationalLanguageUnderstanding'
  'CustomVision.Prediction'
  'CustomVision.Training'
  'Face'
  'FormRecognizer'
  'HealthInsights'
  'ImmersiveReader'
  'Internal.AllInOne'
  'LUIS'
  'LUIS.Authoring'
  'LanguageAuthoring'
  'MetricsAdvisor'
  'OpenAI'
  'Personalizer'
  'QnAMaker.v2'
  'SpeechServices'
  'TextAnalytics'
  'TextTranslation'
])
param kind string = 'AIServices'

@description('Optional. The SKU of the Cognitive Services account. Use \'Get-AzCognitiveServicesAccountSku\' to determine a valid combinations of \'kind\' and \'SKU\' for your Azure region.')
@allowed([
  'S'
  'S0'
  'S1'
  'S2'
  'S3'
  'S4'
  'S5'
  'S6'
  'S7'
  'S8'
])
param sku string = 'S0'

@description('Required. The name of the AI Foundry project to create.')
param projectName string

@description('Optional. The description of the AI Foundry project to create.')
param projectDescription string = projectName

@description('Optional. The resource ID of the Log Analytics workspace to use for diagnostic settings.')
param logAnalyticsWorkspaceResourceId string?

param existingFoundryProjectResourceId string = ''

@description('Optional. Specifies the OpenAI deployments to create.')
param deployments deploymentType[]?

import { roleAssignmentType } from 'br/public:avm/utl/types/avm-common-types:0.5.1'
@description('Optional. Array of role assignments to create.')
param roleAssignments roleAssignmentType[] = []

@description('Optional. Values to establish private networking for the AI Services resource.')
param privateNetworking aiServicesPrivateNetworkingType?

import { diagnosticSettingFullType } from 'br/public:avm/utl/types/avm-common-types:0.5.1'
@description('Optional. The diagnostic settings of the service.')
param diagnosticSettings diagnosticSettingFullType[]?

@description('Optional. Whether or not public network access is allowed for this resource. For security reasons it should be disabled. If not specified, it will be disabled by default if private endpoints are set and networkAcls are not set.')
@allowed([
  'Enabled'
  'Disabled'
])
param publicNetworkAccess string?

@description('Conditional. Subdomain name used for token-based authentication. Required if \'networkAcls\' or \'privateEndpoints\' are set.')
param customSubDomainName string?

@description('Optional. A collection of rules governing the accessibility from specific network locations.')
param networkAcls object?

import { privateEndpointSingleServiceType } from 'br/public:avm/utl/types/avm-common-types:0.5.1'
@description('Optional. Configuration details for private endpoints. For security reasons, it is recommended to use private endpoints whenever possible.')
param privateEndpoints privateEndpointSingleServiceType[]?

import { lockType } from 'br/public:avm/utl/types/avm-common-types:0.5.1'
@description('Optional. The lock settings of the service.')
param lock lockType?

@description('Optional. Tags to be applied to the resources.')
param tags object = {}

@description('Optional. List of allowed FQDN.')
param allowedFqdnList array?

@description('Optional. The API properties for special APIs.')
param apiProperties object?

@description('Optional. Allow only Azure AD authentication. Should be enabled for security reasons.')
param disableLocalAuth bool = true

import { customerManagedKeyType } from 'br/public:avm/utl/types/avm-common-types:0.5.1'
@description('Optional. The customer managed key definition.')
param customerManagedKey customerManagedKeyType?

@description('Optional. The flag to enable dynamic throttling.')
param dynamicThrottlingEnabled bool = false

@secure()
@description('Optional. Resource migration token.')
param migrationToken string?

@description('Optional. Restore a soft-deleted cognitive service at deployment time. Will fail if no such soft-deleted resource exists.')
param restore bool = false

@description('Optional. Restrict outbound network access.')
param restrictOutboundNetworkAccess bool = true

@description('Optional. The storage accounts for this resource.')
param userOwnedStorage array?

import { managedIdentityAllType } from 'br/public:avm/utl/types/avm-common-types:0.5.1'
@description('Optional. The managed identity definition for this resource.')
param managedIdentities managedIdentityAllType?

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@description('Optional. Key vault reference and secret settings for the module\'s secrets export.')
param secretsExportConfiguration secretsExportConfigurationType?

@description('Optional. Enable/Disable project management feature for AI Foundry.')
param allowProjectManagement bool?

var formattedUserAssignedIdentities = reduce(
  map((managedIdentities.?userAssignedResourceIds ?? []), (id) => { '${id}': {} }),
  {},
  (cur, next) => union(cur, next)
) // Converts the flat array to an object like { '${id1}': {}, '${id2}': {} }

var identity = !empty(managedIdentities)
  ? {
      type: (managedIdentities.?systemAssigned ?? false)
        ? (!empty(managedIdentities.?userAssignedResourceIds ?? {}) ? 'SystemAssigned, UserAssigned' : 'SystemAssigned')
        : (!empty(managedIdentities.?userAssignedResourceIds ?? {}) ? 'UserAssigned' : null)
      userAssignedIdentities: !empty(formattedUserAssignedIdentities) ? formattedUserAssignedIdentities : null
    }
  : null
  
#disable-next-line no-deployments-resources
resource avmTelemetry 'Microsoft.Resources/deployments@2024-03-01' = if (enableTelemetry) {
  name: '46d3xbcp.res.cognitiveservices-account.${replace('-..--..-', '.', '-')}.${substring(uniqueString(deployment().name, location), 0, 4)}'
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

resource cMKKeyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = if (!empty(customerManagedKey.?keyVaultResourceId)) {
  name: last(split(customerManagedKey.?keyVaultResourceId!, '/'))
  scope: resourceGroup(
    split(customerManagedKey.?keyVaultResourceId!, '/')[2],
    split(customerManagedKey.?keyVaultResourceId!, '/')[4]
  )

  resource cMKKey 'keys@2023-07-01' existing = if (!empty(customerManagedKey.?keyVaultResourceId) && !empty(customerManagedKey.?keyName)) {
    name: customerManagedKey.?keyName!
  }
}

resource cMKUserAssignedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2025-01-31-preview' existing = if (!empty(customerManagedKey.?userAssignedIdentityResourceId)) {
  name: last(split(customerManagedKey.?userAssignedIdentityResourceId!, '/'))
  scope: resourceGroup(
    split(customerManagedKey.?userAssignedIdentityResourceId!, '/')[2],
    split(customerManagedKey.?userAssignedIdentityResourceId!, '/')[4]
  )
}

var useExistingService = !empty(existingFoundryProjectResourceId)

module cognitiveServicesPrivateDnsZone '../privateDnsZone.bicep' = if (!useExistingService && privateNetworking != null && empty(privateNetworking.?cogServicesPrivateDnsZoneResourceId)) {
  name: take('${name}-cognitiveservices-pdns-deployment', 64)
  params: {
    name: 'privatelink.cognitiveservices.${toLower(environment().name) == 'azureusgovernment' ? 'azure.us' : 'azure.com'}'
    virtualNetworkResourceId: privateNetworking.?virtualNetworkResourceId ?? ''
    tags: tags
  }
}

module openAiPrivateDnsZone '../privateDnsZone.bicep' = if (!useExistingService && privateNetworking != null && empty(privateNetworking.?openAIPrivateDnsZoneResourceId)) {
  name: take('${name}-openai-pdns-deployment', 64)
  params: {
    name: 'privatelink.openai.${toLower(environment().name) == 'azureusgovernment' ? 'azure.us' : 'azure.com'}'
    virtualNetworkResourceId: privateNetworking.?virtualNetworkResourceId ?? ''
    tags: tags
  }
}

module aiServicesPrivateDnsZone '../privateDnsZone.bicep' = if (!useExistingService && privateNetworking != null && empty(privateNetworking.?aiServicesPrivateDnsZoneResourceId)) {
  name: take('${name}-ai-services-pdns-deployment', 64)
  params: {
    name: 'privatelink.services.ai.${toLower(environment().name) == 'azureusgovernment' ? 'azure.us' : 'azure.com'}'
    virtualNetworkResourceId: privateNetworking.?virtualNetworkResourceId ?? ''
    tags: tags
  }
}

var cogServicesPrivateDnsZoneResourceId = privateNetworking != null
  ? (empty(privateNetworking.?cogServicesPrivateDnsZoneResourceId)
      ? cognitiveServicesPrivateDnsZone.outputs.resourceId ?? ''
      : privateNetworking.?cogServicesPrivateDnsZoneResourceId)
  : ''
var openAIPrivateDnsZoneResourceId = privateNetworking != null
  ? (empty(privateNetworking.?openAIPrivateDnsZoneResourceId)
      ? openAiPrivateDnsZone.outputs.resourceId ?? ''
      : privateNetworking.?openAIPrivateDnsZoneResourceId)
  : ''

var aiServicesPrivateDnsZoneResourceId = privateNetworking != null
  ? (empty(privateNetworking.?aiServicesPrivateDnsZoneResourceId)
      ? aiServicesPrivateDnsZone.outputs.resourceId ?? ''
      : privateNetworking.?aiServicesPrivateDnsZoneResourceId)
  : ''

resource cognitiveServiceNew 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = if(!useExistingService) {
  name: name
  kind: kind
  identity: identity
  location: location
  tags: tags
  sku: {
    name: sku
  }
  properties: {
    allowProjectManagement: true // allows project management for Cognitive Services accounts in AI Foundry - FDP updates
    customSubDomainName: name
    networkAcls: !empty(networkAcls ?? {})
      ? {
          defaultAction: networkAcls.?defaultAction
          virtualNetworkRules: networkAcls.?virtualNetworkRules ?? []
          ipRules: networkAcls.?ipRules ?? []
        }
      : null
    publicNetworkAccess: publicNetworkAccess != null
      ? publicNetworkAccess
      : (!empty(networkAcls) ? 'Enabled' : 'Disabled')
    allowedFqdnList: allowedFqdnList
    apiProperties: apiProperties
    disableLocalAuth: disableLocalAuth
    encryption: !empty(customerManagedKey)
      ? {
          keySource: 'Microsoft.KeyVault'
          keyVaultProperties: {
            identityClientId: !empty(customerManagedKey.?userAssignedIdentityResourceId ?? '')
              ? cMKUserAssignedIdentity.properties.clientId
              : null
            keyVaultUri: cMKKeyVault.properties.vaultUri
            keyName: customerManagedKey!.keyName
            keyVersion: !empty(customerManagedKey.?keyVersion ?? '')
              ? customerManagedKey!.?keyVersion
              : last(split(cMKKeyVault::cMKKey.properties.keyUriWithVersion, '/'))
          }
        }
      : null
    migrationToken: migrationToken
    restore: restore
    restrictOutboundNetworkAccess: restrictOutboundNetworkAccess
    userOwnedStorage: userOwnedStorage
    dynamicThrottlingEnabled: dynamicThrottlingEnabled
  }
}

var existingCognitiveServiceDetails = split(existingFoundryProjectResourceId, '/')

resource cognitiveServiceExisting 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = if(useExistingService) {
  name: existingCognitiveServiceDetails[8]
  scope: resourceGroup(existingCognitiveServiceDetails[2], existingCognitiveServiceDetails[4])
}
module cognitive_service_dependencies './dependencies.bicep' = if(!useExistingService) {
  name: take('${name}-cognitive-service-${cognitiveServiceNew.name}-dependencies', 64)
  params: {
    projectName: projectName
    projectDescription: projectDescription
    name: cognitiveServiceNew.name 
    location: location
    deployments: deployments
    diagnosticSettings: !empty(logAnalyticsWorkspaceResourceId)
      ? [
          {
            workspaceResourceId: logAnalyticsWorkspaceResourceId
          }
        ]
      : []
    lock: lock
    privateEndpoints:  privateNetworking != null
      ? [
          {
            name:'pep-${name}-aiservices' // private endpoint name
            customNetworkInterfaceName: 'nic-${name}-aiservices'
            subnetResourceId: privateNetworking.?subnetResourceId ?? ''
            privateDnsZoneGroup: {
              privateDnsZoneGroupConfigs: [
                {
                  privateDnsZoneResourceId: cogServicesPrivateDnsZoneResourceId
                }
                {
                  privateDnsZoneResourceId: openAIPrivateDnsZoneResourceId
                }
                {
                  privateDnsZoneResourceId: aiServicesPrivateDnsZoneResourceId
                }
              ]
            }
          }
        ]
      : []
    roleAssignments: roleAssignments
    secretsExportConfiguration: secretsExportConfiguration
    sku: sku
    tags: tags
  }
}

module existing_cognitive_service_dependencies './dependencies.bicep' = if(useExistingService) {
  name: take('existing-${name}-cognitive-service-${cognitiveServiceExisting.name}-dependencies', 64)
  params: {
    name:  cognitiveServiceExisting.name 
    projectName: projectName
    projectDescription: projectDescription
    azureExistingAIProjectResourceId: existingFoundryProjectResourceId
    location: location
    deployments: deployments
    diagnosticSettings: diagnosticSettings
    lock: lock
    privateEndpoints: privateEndpoints
    roleAssignments: roleAssignments
    secretsExportConfiguration: secretsExportConfiguration
    sku: sku
    tags: tags
  }
  scope: resourceGroup(existingCognitiveServiceDetails[2], existingCognitiveServiceDetails[4])
}

// module cognitiveService 'ai-services.bicep' = {
//   name: take('${name}-aiservices-deployment', 64)
//   #disable-next-line no-unnecessary-dependson
//   dependsOn: [cognitiveServicesPrivateDnsZone, openAiPrivateDnsZone, aiServicesPrivateDnsZone] // required due to optional flags that could change dependency
//   params: {
//     name: name
//     location: location
//     tags: tags
//     sku: sku
//     kind: kind
//     managedIdentities: {
//       systemAssigned: true
//     }
//     deployments: deployments
//     customSubDomainName: name
//     disableLocalAuth: false
//     publicNetworkAccess: privateNetworking != null ? 'Disabled' : 'Enabled'
//     // rules to allow firewall and virtual network access
//     networkAcls: {
//       defaultAction: 'Allow'
//       virtualNetworkRules: []
//       ipRules: []
//     }
//     diagnosticSettings: !empty(logAnalyticsWorkspaceResourceId)
//       ? [
//           {
//             workspaceResourceId: logAnalyticsWorkspaceResourceId
//           }
//         ]
//       : []
//     roleAssignments: roleAssignments
//     privateEndpoints: privateNetworking != null
//       ? [
//           {
//             name:'pep-${name}' // private endpoint name
//             customNetworkInterfaceName: 'nic-${name}'
//             subnetResourceId: privateNetworking.?subnetResourceId ?? ''
//             privateDnsZoneGroup: {
//               privateDnsZoneGroupConfigs: [
//                 {
//                   privateDnsZoneResourceId: cogServicesPrivateDnsZoneResourceId
//                 }
//                 {
//                   privateDnsZoneResourceId: openAIPrivateDnsZoneResourceId
//                 }
//                 {
//                   privateDnsZoneResourceId: aiServicesPrivateDnsZoneResourceId
//                 }
//               ]
//             }
//           }
//         ]
//       : []
//   }
// }


// module aiProject 'project.bicep' = {
//   name: take('${name}-ai-project-${projectName}-deployment', 64)
//   params: {
//     name: projectName
//     desc: projectDescription
//     aiServicesName: cognitiveService.outputs.name
//     location: location
//     roleAssignments: roleAssignments
//     tags: tags
//     enableTelemetry: enableTelemetry
//   }
// }

var cognitiveService = useExistingService ? cognitiveServiceExisting : cognitiveServiceNew

@description('The name of the cognitive services account.')
output name string = useExistingService ? cognitiveServiceExisting.name : cognitiveServiceNew.name

@description('The resource ID of the cognitive services account.')
output resourceId string = useExistingService ? cognitiveServiceExisting.id : cognitiveServiceNew.id

@description('The resource group the cognitive services account was deployed into.')
output subscriptionId string =  useExistingService ? existingCognitiveServiceDetails[2] : subscription().subscriptionId

@description('The resource group the cognitive services account was deployed into.')
output resourceGroupName string =  useExistingService ? existingCognitiveServiceDetails[4] : resourceGroup().name

@description('The service endpoint of the cognitive services account.')
output endpoint string = useExistingService ? cognitiveServiceExisting.properties.endpoint : cognitiveService.properties.endpoint

@description('All endpoints available for the cognitive services account, types depends on the cognitive service kind.')
output endpoints endpointType = useExistingService ? cognitiveServiceExisting.properties.endpoints : cognitiveService.properties.endpoints

@description('The principal ID of the system assigned identity.')
output systemAssignedMIPrincipalId string? = useExistingService ? cognitiveServiceExisting.identity.principalId : cognitiveService.?identity.?principalId

@description('The location the resource was deployed into.')
output location string = useExistingService ? cognitiveServiceExisting.location : cognitiveService.location

import { secretsOutputType } from 'br/public:avm/utl/types/avm-common-types:0.5.1'
@description('A hashtable of references to the secrets exported to the provided Key Vault. The key of each reference is each secret\'s name.')
output exportedSecrets secretsOutputType = useExistingService ? existing_cognitive_service_dependencies.outputs.exportedSecrets : cognitive_service_dependencies.outputs.exportedSecrets

@description('The private endpoints of the congitive services account.')
output privateEndpoints privateEndpointOutputType[] = useExistingService ? existing_cognitive_service_dependencies.outputs.privateEndpoints : cognitive_service_dependencies.outputs.privateEndpoints

import { aiProjectOutputType } from './project.bicep'
output aiProjectInfo aiProjectOutputType = useExistingService ? existing_cognitive_service_dependencies.outputs.aiProjectInfo : cognitive_service_dependencies.outputs.aiProjectInfo

@export()
@description('A custom AVM-aligned type for a role assignment for AI Services and Project.')
type aiServicesRoleAssignmentType = {
  @description('Optional. The name (as GUID) of the role assignment. If not provided, a GUID will be generated.')
  name: string?

  @description('Required. The role to assign. You can provide either the role definition GUID or its fully qualified ID in the following format: \'/providers/Microsoft.Authorization/roleDefinitions/c2f4ef07-c644-48eb-af81-4b1b4947fb11\'.')
  roleDefinitionId: string

  @description('Required. The principal ID of the principal (user/group/identity) to assign the role to.')
  principalId: string

  @description('Optional. The principal type of the assigned principal ID.')
  principalType: ('ServicePrincipal' | 'Group' | 'User' | 'ForeignGroup' | 'Device')?
}
// ================ //
// Definitions      //
// ================ //

@export()
@description('The type for the private endpoint output.')
type privateEndpointOutputType = {
  @description('The name of the private endpoint.')
  name: string

  @description('The resource ID of the private endpoint.')
  resourceId: string

  @description('The group Id for the private endpoint Group.')
  groupId: string?

  @description('The custom DNS configurations of the private endpoint.')
  customDnsConfigs: {
    @description('FQDN that resolves to private endpoint IP address.')
    fqdn: string?

    @description('A list of private IP addresses of the private endpoint.')
    ipAddresses: string[]
  }[]

  @description('The IDs of the network interfaces associated with the private endpoint.')
  networkInterfaceResourceIds: string[]
}

@export()
@description('The type for a cognitive services account deployment.')
type deploymentType = {
  @description('Optional. Specify the name of cognitive service account deployment.')
  name: string?

  @description('Required. Properties of Cognitive Services account deployment model.')
  model: {
    @description('Required. The name of Cognitive Services account deployment model.')
    name: string

    @description('Required. The format of Cognitive Services account deployment model.')
    format: string

    @description('Required. The version of Cognitive Services account deployment model.')
    version: string
  }

  @description('Optional. The resource model definition representing SKU.')
  sku: {
    @description('Required. The name of the resource model definition representing SKU.')
    name: string

    @description('Optional. The capacity of the resource model definition representing SKU.')
    capacity: int?

    @description('Optional. The tier of the resource model definition representing SKU.')
    tier: string?

    @description('Optional. The size of the resource model definition representing SKU.')
    size: string?

    @description('Optional. The family of the resource model definition representing SKU.')
    family: string?
  }?

  @description('Optional. The name of RAI policy.')
  raiPolicyName: string?

  @description('Optional. The version upgrade option.')
  versionUpgradeOption: string?
}

@export()
@description('The type for a cognitive services account endpoint.')
type endpointType = {
  @description('Type of the endpoint.')
  name: string?
  @description('The endpoint URI.')
  endpoint: string?
}

@export()
@description('The type of the secrets exported to the provided Key Vault.')
type secretsExportConfigurationType = {
  @description('Required. The key vault name where to store the keys and connection strings generated by the modules.')
  keyVaultResourceId: string

  @description('Optional. The name for the accessKey1 secret to create.')
  accessKey1Name: string?

  @description('Optional. The name for the accessKey2 secret to create.')
  accessKey2Name: string?
}

@export()
@description('Values to establish private networking for resources that support createing private endpoints.')
type aiServicesPrivateNetworkingType = {
  @description('Required. The Resource ID of the virtual network.')
  virtualNetworkResourceId: string

  @description('Required. The Resource ID of the subnet to establish the Private Endpoint(s).')
  subnetResourceId: string

  @description('Optional. The Resource ID of an existing "cognitiveservices" Private DNS Zone Resource to link to the virtual network. If not provided, a new "cognitiveservices" Private DNS Zone(s) will be created.')
  cogServicesPrivateDnsZoneResourceId: string?

  @description('Optional. The Resource ID of an existing "openai" Private DNS Zone Resource to link to the virtual network. If not provided, a new "openai" Private DNS Zone(s) will be created.')
  openAIPrivateDnsZoneResourceId: string?
  
  @description('Optional. The Resource ID of an existing "services.ai" Private DNS Zone Resource to link to the virtual network. If not provided, a new "services.ai" Private DNS Zone(s) will be created.')
  aiServicesPrivateDnsZoneResourceId: string?
}
