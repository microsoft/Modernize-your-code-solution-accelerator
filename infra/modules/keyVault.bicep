@description('Name of the Key Vault.')
param name string

@description('Specifies the location for all the Azure resources.')
param location string

@description('Optional. Tags to be applied to the resources.')
param tags object = {}

@description('Optional. Specifies the SKU for the vault.')
@allowed([
  'premium'
  'standard'
])
param sku string = 'premium'

@description('Optional. Resource ID of the Log Analytics workspace to use for diagnostic settings.')
param logAnalyticsWorkspaceResourceId string?

@description('Optional. Values to establish private networking for the Key Vault resource.')
param privateNetworking resourcePrivateNetworkingType?

@description('Optional. Array of role assignments to create.')
param roleAssignments roleAssignmentType[]?

@description('Optional. Array of secrets to create in the Key Vault.')
param secrets secretType[]?

module privateDnsZone 'br/public:avm/res/network/private-dns-zone:0.7.1' = if (privateNetworking != null && empty(privateNetworking.?privateDnsZoneResourceId)) {
  name: take('${name}-kv-pdns-deployment', 64)
  params: {
    name: 'privatelink.${toLower(environment().name) == 'azureusgovernment' ? 'vaultcore.usgovcloudapi.net' : 'vaultcore.azure.net'}'
    virtualNetworkLinks: [
      {
        virtualNetworkResourceId: privateNetworking.?virtualNetworkResourceId ?? ''
      }
    ]
    tags: tags
  }
}

var privateDnsZoneResourceId = privateNetworking != null ? (empty(privateNetworking.?privateDnsZoneResourceId) ? privateDnsZone.outputs.resourceId ?? '' : privateNetworking.?privateDnsZoneResourceId ?? '') : ''

module keyvault 'br/public:avm/res/key-vault/vault:0.12.1' = {
  name: take('${name}-kv-deployment', 64)
  #disable-next-line no-unnecessary-dependson
  dependsOn: [privateDnsZone] // required due to optional flags that could change dependency
  params: {
    name: name
    location: location
    tags: tags
    createMode: 'default'
    sku: sku
    publicNetworkAccess: privateNetworking != null ?  'Disabled' : 'Enabled'
    networkAcls: {
     defaultAction: 'Allow'
    }
    enableVaultForDeployment: true
    enableVaultForDiskEncryption: true
    enableVaultForTemplateDeployment: true
    enablePurgeProtection: false
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    diagnosticSettings: [
      {
        workspaceResourceId: logAnalyticsWorkspaceResourceId
      } 
    ]
    privateEndpoints: privateNetworking != null ? [
      {
        privateDnsZoneGroup: {
          privateDnsZoneGroupConfigs: [
            {
              privateDnsZoneResourceId: privateDnsZoneResourceId
            }
          ]
        }
        service: 'vault'
        subnetResourceId: privateNetworking.?subnetResourceId ?? ''
      }
    ] : []
    roleAssignments: roleAssignments
    secrets: secrets
  }
}

import { resourcePrivateNetworkingType } from 'customTypes.bicep'
import { roleAssignmentType } from 'br/public:avm/utl/types/avm-common-types:0.5.1'
import { secretType } from 'br/public:avm/res/key-vault/vault:0.12.1'

output resourceId string = keyvault.outputs.resourceId
output name string = keyvault.outputs.name
