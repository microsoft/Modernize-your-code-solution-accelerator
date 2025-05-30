// Creates a Private DNS Zone using AVM
// https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/network/private-dns-zone

@description('Name of the Private DNS Zone (e.g., "privatelink.vaultcore.azure.net")')
param dnsZoneName string

@description('Optional: Tags for the DNS Zone')
param tags object = {}

module privateDnsZone 'br/public:avm/res/network/private-dns-zone:0.2.2' = {
  name: dnsZoneName
  params: {
    name: dnsZoneName
    tags: tags
  }
}

output dnsZoneId string = privateDnsZone.outputs.resourceId
