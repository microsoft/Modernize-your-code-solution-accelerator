$ErrorActionPreference = 'Stop'
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
& (Join-Path $repoRoot 'scripts\validate_model_deployment_quota.ps1') @args
