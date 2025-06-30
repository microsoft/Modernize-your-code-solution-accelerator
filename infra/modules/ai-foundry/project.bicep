@description('Required. Name of the AI Services project.')
param name string

@description('Required. The location of the Project resource.')
param location string = resourceGroup().location

@description('Optional. The description of the AI Foundry project to create. Defaults to the project name.')
param desc string = name

@description('Required. Name of the existing Cognitive Services resource to create the AI Foundry project in.')
param aiServicesName string

import { roleAssignmentType } from 'br/public:avm/utl/types/avm-common-types:0.5.1'
@description('Optional. Array of role assignments to create.')
param roleAssignments roleAssignmentType[] = []

@description('Optional. Tags to be applied to the resources.')
param tags object = {}

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@description('Optional. Use this parameter to use an existing AI project resource ID from different resource group')
param azureExistingAIProjectResourceId string = ''

// Extract components from existing AI Project Resource ID if provided
var useExistingProject = !empty(azureExistingAIProjectResourceId)
var existingProjName = useExistingProject ? last(split(azureExistingAIProjectResourceId, '/')) : ''
var existingCogServiceName = useExistingProject ? split(azureExistingAIProjectResourceId, '/')[8] : ''
var existingRgName = useExistingProject ? split(azureExistingAIProjectResourceId, '/')[4] : ''
var existingSubscriptionId = useExistingProject ? split(azureExistingAIProjectResourceId, '/')[2] : ''
var existingProjEndpoint = useExistingProject ? format('https://{0}.services.ai.azure.com/api/projects/{0}', existingProjName) : ''

// using a few built-in roles here that makes sense for Foundry projects only
var builtInRoleNames = {
  'Cognitive Services OpenAI Contributor': subscriptionResourceId(
    'Microsoft.Authorization/roleDefinitions',
    'a001fd3d-188f-4b5d-821b-7da978bf7442'
  )
  'Cognitive Services OpenAI User': subscriptionResourceId(
    'Microsoft.Authorization/roleDefinitions',
    '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
  )
  'Azure AI Developer': subscriptionResourceId(
    'Microsoft.Authorization/roleDefinitions',
    '64702f94-c441-49e6-a78b-ef80e0188fee'
  )
  'Azure AI User': subscriptionResourceId(
    'Microsoft.Authorization/roleDefinitions',
    '53ca6127-db72-4b80-b1b0-d745d6d5456d'
  )
}

var formattedRoleAssignments = [
  for (roleAssignment, index) in (roleAssignments ?? []): union(roleAssignment, {
    roleDefinitionId: builtInRoleNames[?roleAssignment.roleDefinitionIdOrName] ?? (contains(
        roleAssignment.roleDefinitionIdOrName,
        '/providers/Microsoft.Authorization/roleDefinitions/'
      )
      ? roleAssignment.roleDefinitionIdOrName
      : subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleAssignment.roleDefinitionIdOrName))
  })
]

// Reference to cognitive service in current resource group for new projects
resource cogServiceReference 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = if (!useExistingProject) {
  name: aiServicesName
}

// Create new AI project only if not reusing existing one
resource aiProject 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = if (!useExistingProject) {
  parent: cogServiceReference
  name: name
  tags: tags
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    description: desc
    displayName: name
  }
}

// Role assignments for new project
module newProjectRoleAssignments 'br/public:avm/ptn/authorization/resource-role-assignment:0.1.2' = [
  for (roleAssignment, i) in (useExistingProject ? [] : formattedRoleAssignments): {
    name: 'new-role-${i}-${take(uniqueString(name, roleAssignment.roleDefinitionId, roleAssignment.principalId), 8)}'
    params: {
      roleDefinitionId: roleAssignment.roleDefinitionId
      principalId: roleAssignment.principalId
      principalType: 'ServicePrincipal'
      resourceId: aiProject.id
      enableTelemetry: enableTelemetry
    }
  }
]

// Role assignments for existing project from different resource group
// Deploy to the same subscription but different resource group where the AI project exists
module existingProjectRoleAssignments 'br/public:avm/ptn/authorization/resource-role-assignment:0.1.2' = [
  for (roleAssignment, i) in (useExistingProject ? formattedRoleAssignments : []): {
    name: 'existing-role-${i}-${take(uniqueString(azureExistingAIProjectResourceId, roleAssignment.roleDefinitionId, roleAssignment.principalId), 8)}'
    scope: resourceGroup(existingSubscriptionId, existingRgName)
    params: {
      roleDefinitionId: roleAssignment.roleDefinitionId
      principalId: roleAssignment.principalId
      principalType: 'ServicePrincipal'
      resourceId: azureExistingAIProjectResourceId // Use the full resource ID directly
      enableTelemetry: enableTelemetry
    }
  }
]

@description('Name of the AI Foundry project.')
output name string = useExistingProject ? existingProjName : aiProject.name

@description('Resource ID of the AI Foundry project.')
output resourceId string = useExistingProject ? azureExistingAIProjectResourceId : aiProject.id

@description('API endpoint for the AI Foundry project.')
output apiEndpoint string = useExistingProject ? existingProjEndpoint : aiProject.properties.endpoints['AI Foundry API']

@export()
@description('Output type representing AI project information.')
type aiProjectOutputType = {
  @description('Required. Name of the AI project.')
  name: string

  @description('Required. Resource ID of the AI project.')
  resourceId: string

  @description('Required. API endpoint for the AI project.')
  apiEndpoint: string
}
