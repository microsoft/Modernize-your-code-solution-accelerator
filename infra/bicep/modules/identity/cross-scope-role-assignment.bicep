metadata name = 'Modernize Base Placeholder Module'
metadata description = 'Base-repo-owned placeholder module created to align infra structure with reference layout without importing external implementation.'

@description('Optional pass-through settings for future module implementation.')
param settings object = {}

@description('Optional tags.')
param tags object = {}

@description('Echoes input settings so callers can safely compose with this module when needed.')
output settings object = settings