param(
  [Parameter(Mandatory = $true)]
  [string]$ResourceGroup,
  [string]$Assignee
)

$ErrorActionPreference = 'Stop'

$cmd = @('role', 'assignment', 'list', '--resource-group', $ResourceGroup, '--all')
if ($Assignee) {
  $cmd += @('--assignee', $Assignee)
}
$cmd += @('--query', "[].{role:roleDefinitionName,scope:scope,principalId:principalId,principalType:principalType}", '-o', 'table')

& az @cmd
