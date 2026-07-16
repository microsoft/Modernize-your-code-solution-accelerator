#Requires -Version 7.0
param(
    [string]$ResourceGroupName
)

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# ACR Build and Push Script (PowerShell)
# Adapted for this accelerator from the CPSA acr_build_push.ps1 workflow.
#
# Builds backend/frontend images remotely with az acr build, then updates the
# corresponding Container Apps. Supports:
# 1) azd environment output values (default path)
# 2) explicit resource group discovery (-ResourceGroupName)
#
# For WAF/private ACR deployments, the script temporarily relaxes ACR access
# restrictions and restores them in finally.
# ---------------------------------------------------------------------------

Write-Host '============================================================'
Write-Host 'ACR Build and Push - Starting...'
Write-Host '============================================================'

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw "Azure CLI ('az') is not installed. Install it from https://aka.ms/azcli"
}

az account show --output none 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "You are not signed in to Azure CLI. Run 'az login' and retry."
}

function Get-EnvValue {
    param([string[]]$Names)
    foreach ($name in $Names) {
        $value = [Environment]::GetEnvironmentVariable($name)
        if ([string]::IsNullOrWhiteSpace($value)) {
            $value = azd env get-value $name 2>$null
        }
        if (-not [string]::IsNullOrWhiteSpace($value)) {
            return $value
        }
    }
    return $null
}

function Get-ContainerAppsFromResourceGroup {
    param([string]$ResourceGroup)

    $apps = az containerapp list --resource-group $ResourceGroup --output json | ConvertFrom-Json
    $backend = $null
    $frontend = $null

    foreach ($app in $apps) {
        if ($null -eq $backend -and $app.name -match 'backend') {
            $backend = $app.name
            continue
        }
        if ($null -eq $frontend -and $app.name -match 'frontend') {
            $frontend = $app.name
            continue
        }
    }

    # Fallback when names do not contain backend/frontend.
    if ($null -eq $backend -and $apps.Count -ge 1) { $backend = $apps[0].name }
    if ($null -eq $frontend -and $apps.Count -ge 2) { $frontend = $apps[1].name }

    return @{
        BackendApp = $backend
        FrontendApp = $frontend
    }
}

$AcrName = $null
$AcrEndpoint = $null
$ResourceGroup = $null
$BackendApp = $null
$FrontendApp = $null

if ([string]::IsNullOrWhiteSpace($ResourceGroupName)) {
    Write-Host 'Using azd environment values...'
    $AcrName = Get-EnvValue @('AZURE_CONTAINER_REGISTRY_NAME', 'CONTAINER_REGISTRY_NAME')
    $AcrEndpoint = Get-EnvValue @('AZURE_CONTAINER_REGISTRY_ENDPOINT', 'CONTAINER_REGISTRY_LOGIN_SERVER')
    $ResourceGroup = Get-EnvValue @('AZURE_RESOURCE_GROUP')
    $BackendApp = Get-EnvValue @('BACKEND_CONTAINER_APP_NAME')
    $FrontendApp = Get-EnvValue @('FRONTEND_CONTAINER_APP_NAME')
}
else {
    Write-Host "Using existing deployment from resource group: $ResourceGroupName"
    $ResourceGroup = $ResourceGroupName

    $acr = az acr list --resource-group $ResourceGroup --query '[0]' --output json | ConvertFrom-Json
    if ($null -eq $acr) {
        throw "No Azure Container Registry found in resource group '$ResourceGroup'."
    }

    $AcrName = $acr.name
    $AcrEndpoint = $acr.loginServer

    $apps = Get-ContainerAppsFromResourceGroup -ResourceGroup $ResourceGroup
    $BackendApp = $apps.BackendApp
    $FrontendApp = $apps.FrontendApp
}

$ImageTag = Get-EnvValue @('AZURE_ENV_IMAGE_TAG')
if ([string]::IsNullOrWhiteSpace($ImageTag)) { $ImageTag = 'latest' }

if ([string]::IsNullOrWhiteSpace($AcrEndpoint) -and -not [string]::IsNullOrWhiteSpace($AcrName)) {
    $AcrEndpoint = "$AcrName.azurecr.io"
}

$missing = @()
if ([string]::IsNullOrWhiteSpace($AcrName)) { $missing += 'AZURE_CONTAINER_REGISTRY_NAME' }
if ([string]::IsNullOrWhiteSpace($AcrEndpoint)) { $missing += 'AZURE_CONTAINER_REGISTRY_ENDPOINT' }
if ([string]::IsNullOrWhiteSpace($ResourceGroup)) { $missing += 'AZURE_RESOURCE_GROUP' }
if ([string]::IsNullOrWhiteSpace($BackendApp)) { $missing += 'BACKEND_CONTAINER_APP_NAME' }
if ([string]::IsNullOrWhiteSpace($FrontendApp)) { $missing += 'FRONTEND_CONTAINER_APP_NAME' }
if ($missing.Count -gt 0) {
    throw "Missing required values: $($missing -join ', ')"
}

$ScriptDir = $PSScriptRoot
$RepoRoot = Resolve-Path (Join-Path $ScriptDir '..')
$BackendImage = "cmsabackend:$ImageTag"
$FrontendImage = "cmsafrontend:$ImageTag"

$acrInfo = az acr show --name $AcrName --resource-group $ResourceGroup --output json | ConvertFrom-Json
$acrPublicAccess = $acrInfo.properties.publicNetworkAccess
$acrSku = $acrInfo.sku.name

$DeploymentType = az group show --name $ResourceGroup --query 'tags.Type' -o tsv 2>$null
$IsWafDeployment = ($DeploymentType -eq 'WAF') -or ($acrPublicAccess -eq 'Disabled')

Write-Host ''
Write-Host "  ACR Name: $AcrName"
Write-Host "  ACR Login Server: $AcrEndpoint"
Write-Host "  Resource Group: $ResourceGroup"
Write-Host "  Backend App: $BackendApp"
Write-Host "  Frontend App: $FrontendApp"
Write-Host "  Image Tag: $ImageTag"
Write-Host "  ACR SKU: $acrSku"
Write-Host "  ACR Public Access: $acrPublicAccess"
Write-Host ''

try {
    if ($IsWafDeployment) {
        Write-Host 'WAF/private deployment detected. Temporarily relaxing ACR restrictions...'

        az acr update --name $AcrName --resource-group $ResourceGroup --allow-exports true --output none
        if ($LASTEXITCODE -ne 0) { throw 'Failed to enable ACR exports.' }

        az acr update --name $AcrName --resource-group $ResourceGroup --public-network-enabled true --output none
        if ($LASTEXITCODE -ne 0) { throw 'Failed to enable ACR public network access.' }

        if ($acrSku -eq 'Premium') {
            az acr update --name $AcrName --resource-group $ResourceGroup --default-action Allow --output none
            if ($LASTEXITCODE -ne 0) { throw 'Failed to set ACR default action to Allow.' }
        }

        $maxRetries = 30
        for ($i = 0; $i -lt $maxRetries; $i++) {
            $status = az acr show --name $AcrName --resource-group $ResourceGroup --query 'properties.publicNetworkAccess' -o tsv 2>$null
            if ($status -eq 'Enabled') { break }
            Start-Sleep -Seconds 1
        }
    }

    Write-Host '==> Ensuring the Microsoft.App resource provider is registered'
    az provider register --namespace Microsoft.App --wait
    if ($LASTEXITCODE -ne 0) { throw 'Failed to register Microsoft.App resource provider.' }

    Write-Host "==> Verifying ACR '$AcrName' connectivity"
    $acrReachable = $false
    for ($i = 0; $i -lt 5; $i++) {
        az acr repository list --name $AcrName --output none 2>$null
        if ($LASTEXITCODE -eq 0) {
            $acrReachable = $true
            break
        }
        Start-Sleep -Seconds 3
    }
    if (-not $acrReachable) {
        throw "ACR '$AcrName' is not reachable. Check network rules and access permissions."
    }

    Write-Host '============================================================'
    Write-Host 'Step 1: Building and pushing images to ACR...'
    Write-Host '============================================================'

    Write-Host "  Building $BackendImage"
    az acr build --registry $AcrName --image $BackendImage --file "$RepoRoot/src/backend/Dockerfile" "$RepoRoot/src/backend"
    if ($LASTEXITCODE -ne 0) { throw 'Failed to build backend image.' }

    Write-Host "  Building $FrontendImage"
    az acr build --registry $AcrName --image $FrontendImage --file "$RepoRoot/src/frontend/Dockerfile" "$RepoRoot/src/frontend"
    if ($LASTEXITCODE -ne 0) { throw 'Failed to build frontend image.' }

    Write-Host ''
    Write-Host '============================================================'
    Write-Host 'Step 2: Updating Container Apps with new images...'
    Write-Host '============================================================'

    Write-Host "  Updating $BackendApp"
    az containerapp update --name $BackendApp --resource-group $ResourceGroup --image "$AcrEndpoint/$BackendImage" --output none
    if ($LASTEXITCODE -ne 0) { throw "Failed to update $BackendApp." }

    Write-Host "  Updating $FrontendApp"
    az containerapp update --name $FrontendApp --resource-group $ResourceGroup --image "$AcrEndpoint/$FrontendImage" --output none
    if ($LASTEXITCODE -ne 0) { throw "Failed to update $FrontendApp." }

    Write-Host ''
    Write-Host '============================================================'
    Write-Host 'ACR Build and Push - Completed Successfully!'
    Write-Host '============================================================'
}
finally {
    if ($IsWafDeployment) {
        Write-Host ''
        Write-Host 'Restoring WAF/private ACR configuration...'

        if ($acrSku -eq 'Premium') {
            az acr update --name $AcrName --resource-group $ResourceGroup --default-action Deny --output none 2>$null
        }
        az acr update --name $AcrName --resource-group $ResourceGroup --public-network-enabled false --output none 2>$null
        az acr update --name $AcrName --resource-group $ResourceGroup --allow-exports false --output none 2>$null

        Write-Host 'ACR configuration restored.'
    }
}
