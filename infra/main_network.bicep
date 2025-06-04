@minLength(3)
@maxLength(20)
@description('A unique application/env name for all resources in this deployment. This should be 3-20 characters long')
param environmentName string = 'Code Mod Dev'

@minLength(3)
@description('Azure region for all services.')
param location string = resourceGroup().location


@description('Optional. Enable private networking for the resources. Set to true to enable private networking.')
param enablePrivateNetworking bool = true


@description('Enable monitoring for the resources. This will enable Application Insights and Log Analytics. Defaults to false.')
param enableMonitoring bool = true

@description('Optional. Specifies the resource tags for all the resources. Tag "azd-env-name" is automatically added to all resources.')
param tags object = {}

var resourcesName = trim(replace(replace(replace(replace(replace(environmentName, '-', ''), '_', ''), '.', ''),'/', ''), ' ', ''))
var resourcesToken = substring(uniqueString(subscription().id, location, resourcesName), 0, 5)
var uniqueResourcesName = '${resourcesName}${resourcesToken}'

var defaultTags = {
  'azd-env-name': resourcesName
}
var allTags = union(defaultTags, tags)

module logAnalyticsWorkspace 'br/public:avm/res/operational-insights/workspace:0.11.2' = if (enableMonitoring || enablePrivateNetworking) {
  name: take('log-analytics-${resourcesName}-deployment', 64)
  params: {
    name: 'log-${resourcesName}'
    location: location
    skuName: 'PerGB2018'
    dataRetention: 30
    diagnosticSettings: [{ useThisWorkspace: true }]
    tags: allTags
  }
}

module network 'modules/network/network.bicep' = if (enablePrivateNetworking) {
  name: take('network-${resourcesName}-deployment', 64)
  params: {
    resourcesName: take('network-${resourcesName}',10)
    logAnalyticsWorkSpaceResourceId: logAnalyticsWorkspace.outputs.resourceId
    addressPrefixes: ['10.0.0.0/21']
    solutionSubnets: [
      {
        name: 'web'
        addressPrefixes: ['10.0.0.0/24']
        networkSecurityGroup: {
          name: 'web-nsg'
          securityRules: [
            {
              name: 'AllowHttpsInbound'
              properties: {
                access: 'Allow'
                direction: 'Inbound'
                priority: 100
                protocol: 'Tcp'
                sourcePortRange: '*'
                destinationPortRange: '443'
                sourceAddressPrefixes: ['0.0.0.0/0']
                destinationAddressPrefixes: ['10.0.0.0/24']
              }
            }
          ]
        }
      }
      {
        name: 'app'
        addressPrefixes: ['10.0.1.0/24']
        networkSecurityGroup: {
          name: 'app-nsg'
          securityRules: [
            {
              name: 'AllowWebToApp'
              properties: {
                access: 'Allow'
                direction: 'Inbound'
                priority: 100
                protocol: 'Tcp'
                sourcePortRange: '*'
                destinationPortRange: '*'
                sourceAddressPrefixes: ['10.0.0.0/24'] // web subnet
                destinationAddressPrefixes: ['10.0.1.0/24']
              }
            }
          ]
        }
      }
      {
        name: 'ai'
        addressPrefixes: ['10.0.2.0/24']
        networkSecurityGroup: {
          name: 'ai-nsg'
          securityRules: [
            {
              name: 'AllowAppToAI'
              properties: {
                access: 'Allow'
                direction: 'Inbound'
                priority: 100
                protocol: 'Tcp'
                sourcePortRange: '*'
                destinationPortRange: '*'
                sourceAddressPrefixes: ['10.0.1.0/24'] // app subnet
                destinationAddressPrefixes: ['10.0.2.0/24']
              }
            }
          ]
        }
      }
      {
        name: 'data'
        addressPrefixes: ['10.0.3.0/24']
        networkSecurityGroup: {
          name: 'data-nsg'
          securityRules: [
            {
              name: 'AllowWebAppAiToData'
              properties: {
                access: 'Allow'
                direction: 'Inbound'
                priority: 100
                protocol: 'Tcp'
                sourcePortRange: '*'
                destinationPortRange: '*'
                sourceAddressPrefixes: [
                  '10.0.0.0/24' // web subnet
                  '10.0.1.0/24' // app subnet
                  '10.0.2.0/24' // ai subnet
                ]
                destinationAddressPrefixes: ['10.0.3.0/24']
              }
            }
          ]
        }
      }
      {
        name: 'services'
        addressPrefixes: ['10.0.4.0/24']
        networkSecurityGroup: {
          name: 'services-nsg'
          securityRules: [
            {
              name: 'AllowWebAppAiToServices'
              properties: {
                access: 'Allow'
                direction: 'Inbound'
                priority: 100
                protocol: 'Tcp'
                sourcePortRange: '*'
                destinationPortRange: '*'
                sourceAddressPrefixes: [
                  '10.0.0.0/24' // web subnet
                  '10.0.1.0/24' // app subnet
                  '10.0.2.0/24' // ai subnet
                ]
                destinationAddressPrefixes: ['10.0.4.0/24']
              }
            }
          ]
        }
      }
    ]
    azureBationHost: true
    azureBastionSubnet: {
      name: 'AzureBastionSubnet' // Required name for Azure Bastion
      addressPrefixes: ['10.0.5.0/27']
      networkSecurityGroup: null // Must not have an NSG
    }
    jumpboxVM: true
    jumpboxVmSize: 'Standard_D2s_v3'
    jumpboxAdminUser: 'JumpboxAdminUser'
    jumpboxAdminPassword: 'JumpboxAdminP@ssw0rd1234!'
    jumpboxSubnet: {
      name: 'jumpbox'
      addressPrefixes: ['10.0.6.0/24']
      networkSecurityGroup: {
        name: 'jumpbox-nsg'
        securityRules: [
          {
            name: 'AllowJumpboxInbound'
            properties: {
              access: 'Allow'
              direction: 'Inbound'
              priority: 100
              protocol: 'Tcp'
              sourcePortRange: '*'
              destinationPortRange: '22'
              sourceAddressPrefixes: [
                '10.0.5.0/27' // Azure Bastion subnet
              ]
              destinationAddressPrefixes: ['10.0.6.0/24']
            }
          }
        ]
      }
    }
    location: location
    tags: allTags
  }
}
