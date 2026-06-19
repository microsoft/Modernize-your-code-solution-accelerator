metadata name = 'Identity Role Assignments'
metadata description = 'Creates RBAC role assignments for Storage Account, AI Services account, and AI project scopes.'

@description('Optional. Name of the storage account to scope storage role assignments to.')
param storageAccountName string = ''

@description('Optional. Name of the AI Services account to scope AI account/project role assignments to.')
param aiServicesAccountName string = ''

@description('Optional. Name of the AI project under the AI Services account.')
param aiProjectName string = ''

@description('Role assignments to create. scopeType must be one of: storage, aiAccount, aiProject.')
param roleAssignments array = []

resource storageAccount 'Microsoft.Storage/storageAccounts@2025-08-01' existing = if (!empty(storageAccountName)) {
  name: storageAccountName
}

resource aiServices 'Microsoft.CognitiveServices/accounts@2025-12-01' existing = if (!empty(aiServicesAccountName)) {
  name: aiServicesAccountName
}

resource aiProject 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' existing = if (!empty(aiServicesAccountName) && !empty(aiProjectName)) {
  parent: aiServices
  name: aiProjectName
}

resource storageRoleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for assignment in roleAssignments: if (assignment.scopeType == 'storage' && !empty(storageAccountName)) {
  name: guid(storageAccount.id, assignment.principalId, assignment.roleDefinitionId)
  scope: storageAccount
  properties: {
    principalId: assignment.principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', assignment.roleDefinitionId)
    principalType: assignment.principalType
  }
}]

resource aiAccountRoleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for assignment in roleAssignments: if (assignment.scopeType == 'aiAccount' && !empty(aiServicesAccountName)) {
  name: guid(aiServices.id, assignment.principalId, assignment.roleDefinitionId)
  scope: aiServices
  properties: {
    principalId: assignment.principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', assignment.roleDefinitionId)
    principalType: assignment.principalType
  }
}]

resource aiProjectRoleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for assignment in roleAssignments: if (assignment.scopeType == 'aiProject' && !empty(aiServicesAccountName) && !empty(aiProjectName)) {
  name: guid(aiProject.id, assignment.principalId, assignment.roleDefinitionId)
  scope: aiProject
  properties: {
    principalId: assignment.principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', assignment.roleDefinitionId)
    principalType: assignment.principalType
  }
}]

output appliedRoleAssignments int = length(roleAssignments)