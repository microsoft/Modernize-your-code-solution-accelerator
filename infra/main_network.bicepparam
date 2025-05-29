// Parameters for main_network.bicep
// Use this file to provide default values for your network deployment

using './main_network.bicep'

param networkIsolation = true

param vnetName = 'my-vnet'
param addressPrefixes = [
  '10.0.0.0/20' //  4,096 IP addresses. Other options: (1) /16: 65,536 (2) /24: 256 Addresses 
]
param dnsServers = [
  '10.0.1.4'
  '10.0.1.5'
]
param subnets = [
  {
    name: 'web'
    addressPrefix: '10.0.1.0/24'
  }
  {
    name: 'app'
    addressPrefix: '10.0.2.0/24'
  }
  {
    name: 'ai'
    addressPrefix: '10.0.3.0/24'
  }
  {
    name: 'data'
    addressPrefix: '10.0.4.0/24'
  }
  {
    name: 'bastion'
    addressPrefix: '10.0.5.0/24'
  }
  {
    name: 'jumpbox'
    addressPrefix: '10.0.6.0/24'
  }
]

