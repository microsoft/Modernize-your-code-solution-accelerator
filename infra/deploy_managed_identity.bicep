// ========== Managed Identity ========== //
targetScope = 'resourceGroup'

@minLength(3)
@maxLength(15)
@description('Solution Name')
param solutionName string

@description('Solution Location')
param solutionLocation string

@description('Name')
param miName string = '${ solutionName }-managed-identity'

resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: miName
  location: solutionLocation
  tags: {
    app: solutionName
    location: solutionLocation
  }
}

@description('This is the built-in owner role. See https://docs.microsoft.com/azure/role-based-access-control/built-in-roles#owner')
resource ownerRoleDefinition 'Microsoft.Authorization/roleDefinitions@2018-01-01-preview' existing = {
  scope: resourceGroup()
  name: '8e3af657-a8ff-443c-a75c-2fe8c4bcb635'
}
resource managedIdentityBackendApp 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${solutionName}-backend-app-mi'
  location: solutionLocation
  tags: {
    app: solutionName
    location: solutionLocation
  }
}
resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, managedIdentity.id, ownerRoleDefinition.id)
  properties: {
    principalId: managedIdentity.properties.principalId
    roleDefinitionId:  ownerRoleDefinition.id
    principalType: 'ServicePrincipal' 
  }
}


output managedIdentityOutput object = {
  id: managedIdentity.id
  objectId: managedIdentity.properties.principalId
  resourceId: managedIdentity.id
  location: managedIdentity.location
  name: miName
}
output managedIdentityBackendAppOutput object = {
  id: managedIdentityBackendApp.id
  objectId: managedIdentityBackendApp.properties.principalId
  clientId: managedIdentityBackendApp.properties.clientId
  name: managedIdentityBackendApp.name
}

//output managedIdentityId string = managedIdentity.id
