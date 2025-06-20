@description('Name of the Cognitive Services resource. Must be unique in the resource group.')
param name string

@description('The location of the Cognitive Services resource.')
param location string

@description('Required. Kind of the Cognitive Services account. Use \'Get-AzCognitiveServicesAccountSku\' to determine a valid combinations of \'kind\' and \'SKU\' for your Azure region.')
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

@description('Required. The SKU of the Cognitive Services account. Use \'Get-AzCognitiveServicesAccountSku\' to determine a valid combinations of \'kind\' and \'SKU\' for your Azure region.')
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

@description('Optional. The resource ID of the Log Analytics workspace to use for diagnostic settings.')
param logAnalyticsWorkspaceResourceId string?

import { deploymentType } from 'br/public:avm/res/cognitive-services/account:0.10.2'
@description('Optional. Specifies the OpenAI deployments to create.')
param deployments deploymentType[] = []

import { roleAssignmentType } from 'br/public:avm/utl/types/avm-common-types:0.5.1'
@description('Optional. Array of role assignments to create.')
param roleAssignments roleAssignmentType[]?

@description('Optional. Values to establish private networking for the AI Services resource.')
param privateNetworking aiServicesPrivateNetworkingType?

@description('Optional. Tags to be applied to the resources.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

module cognitiveServicesPrivateDnsZone 'br/public:avm/res/network/private-dns-zone:0.7.1' = if (privateNetworking != null && empty(privateNetworking.?cogServicesPrivateDnsZoneResourceId)) {
  name: take('${name}-cognitiveservices-pdns-deployment', 64) 
  params: {
    name: 'privatelink.cognitiveservices.${toLower(environment().name) == 'azureusgovernment' ? 'azure.us' : 'azure.com'}'
    virtualNetworkLinks: [
      {
        virtualNetworkResourceId: privateNetworking.?virtualNetworkResourceId ?? ''
      }
    ]
    tags: tags
    enableTelemetry: enableTelemetry
  }
}

module openAiPrivateDnsZone 'br/public:avm/res/network/private-dns-zone:0.7.1' = if (privateNetworking != null && empty(privateNetworking.?openAIPrivateDnsZoneResourceId)) {
  name: take('${name}-openai-pdns-deployment', 64) 
  params: {
    name: 'privatelink.openai.${toLower(environment().name) == 'azureusgovernment' ? 'azure.us' : 'azure.com'}'
    virtualNetworkLinks: [
      {
        virtualNetworkResourceId: privateNetworking.?virtualNetworkResourceId ?? ''
      }
    ]
    tags: tags
    enableTelemetry: enableTelemetry
  }
}

var cogServicesPrivateDnsZoneResourceId = privateNetworking != null ? (empty(privateNetworking.?cogServicesPrivateDnsZoneResourceId) ? cognitiveServicesPrivateDnsZone.outputs.resourceId ?? '' : privateNetworking.?cogServicesPrivateDnsZoneResourceId) : ''
var openAIPrivateDnsZoneResourceId = privateNetworking != null ? (empty(privateNetworking.?openAIPrivateDnsZoneResourceId) ? openAiPrivateDnsZone.outputs.resourceId ?? '' : privateNetworking.?openAIPrivateDnsZoneResourceId) : ''

//AVM module uses 'Microsoft.CognitiveServices/accounts@2023-05-01' 
module cognitiveService 'br/public:avm/res/cognitive-services/account:0.10.2' = {
  name: take('${name}-aiservices-deployment', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [cognitiveServicesPrivateDnsZone, openAiPrivateDnsZone] // required due to optional flags that could change dependency
  params: {
    name: name
    location: location
    tags: tags
    sku: sku
    kind: kind
    managedIdentities: {
      systemAssigned: true
    }
    deployments: deployments
    customSubDomainName: name
    disableLocalAuth: false
    publicNetworkAccess: privateNetworking != null ? 'Disabled' : 'Enabled'
    apiProperties: {
      allowProjectManagement: true
    }
    diagnosticSettings: !empty(logAnalyticsWorkspaceResourceId) ? [
      {
        workspaceResourceId: logAnalyticsWorkspaceResourceId
      } 
    ] : []
    roleAssignments: roleAssignments
    privateEndpoints: privateNetworking != null ? [
      {
        privateDnsZoneGroup: {
          privateDnsZoneGroupConfigs: [
            {
              privateDnsZoneResourceId: cogServicesPrivateDnsZoneResourceId
            }
            {
              privateDnsZoneResourceId: openAIPrivateDnsZoneResourceId
            } 
          ]
        }
        subnetResourceId: privateNetworking.?subnetResourceId ?? ''
      }
    ] : []
    enableTelemetry: enableTelemetry
  }
}

output resourceId string = cognitiveService.outputs.resourceId
output name string = cognitiveService.outputs.name
output systemAssignedMIPrincipalId string? = cognitiveService.outputs.?systemAssignedMIPrincipalId
output endpoint string = cognitiveService.outputs.endpoint

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
}

