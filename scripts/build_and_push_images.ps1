#Requires -Version 7.0
$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# Post-provision hook (PowerShell)
#
# Builds the backend and frontend container images remotely inside the
# deployment's Azure Container Registry (ACR) using 'az acr build' (no local
# Docker required) and then updates the container apps to run the freshly
# built images.
#
# The required values are provided by azd as environment variables (they are
# outputs of infra/main.bicep). When the script is run outside of an azd hook
# the values are read back with 'azd env get-value'.
# ---------------------------------------------------------------------------

Write-Host "==> Post-provision: building and pushing application images to ACR"

# Ensure the Azure CLI is available and authenticated (az acr build / containerapp
# update use the az CLI, which authenticates independently from azd).
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "Azure CLI ('az') is not installed. Install it from https://aka.ms/azcli"
    exit 1
}
az account show --output none 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "You are not signed in to the Azure CLI. Run 'az login' and retry."
    exit 1
}

function Get-EnvValue {
    param([string]$Name)
    $value = [Environment]::GetEnvironmentVariable($Name)
    if ([string]::IsNullOrWhiteSpace($value)) {
        $value = (azd env get-value $Name 2>$null)
    }
    return $value
}

$AcrName       = Get-EnvValue 'AZURE_CONTAINER_REGISTRY_NAME'
$AcrEndpoint   = Get-EnvValue 'AZURE_CONTAINER_REGISTRY_ENDPOINT'
$ResourceGroup = Get-EnvValue 'AZURE_RESOURCE_GROUP'
$BackendApp    = Get-EnvValue 'BACKEND_CONTAINER_APP_NAME'
$FrontendApp   = Get-EnvValue 'FRONTEND_CONTAINER_APP_NAME'
$ImageTag      = Get-EnvValue 'AZURE_ENV_IMAGE_TAG'
if ([string]::IsNullOrWhiteSpace($ImageTag)) { $ImageTag = 'latest' }

# Derive the login server from the registry name if the output was not available.
if ([string]::IsNullOrWhiteSpace($AcrEndpoint) -and -not [string]::IsNullOrWhiteSpace($AcrName)) {
    $AcrEndpoint = "$AcrName.azurecr.io"
}

$missing = @()
if ([string]::IsNullOrWhiteSpace($AcrName))       { $missing += 'AZURE_CONTAINER_REGISTRY_NAME' }
if ([string]::IsNullOrWhiteSpace($ResourceGroup)) { $missing += 'AZURE_RESOURCE_GROUP' }
if ([string]::IsNullOrWhiteSpace($BackendApp))    { $missing += 'BACKEND_CONTAINER_APP_NAME' }
if ([string]::IsNullOrWhiteSpace($FrontendApp))   { $missing += 'FRONTEND_CONTAINER_APP_NAME' }
if ($missing.Count -gt 0) {
    Write-Error "Missing required environment values: $($missing -join ', ')"
    exit 1
}

function Get-AcrPublicNetworkAccess {
    $result = az acr show --name $AcrName --resource-group $ResourceGroup --query "publicNetworkAccess" -o tsv 2>$null
    return $result
}

function Set-AcrPublicNetworkAccess {
    param([string]$Mode)
    Write-Host "==> Setting ACR public network access to $Mode"
    az acr update --name $AcrName --resource-group $ResourceGroup --public-network-access $Mode | Out-Null
}

$AcrPublicAccess = Get-AcrPublicNetworkAccess
$AcrPublicAccessRevert = $false
if ($AcrPublicAccess -eq 'Disabled') {
    Set-AcrPublicNetworkAccess -Mode 'Enabled'
    $AcrPublicAccessRevert = $true
}

function Restore-AcrPublicNetworkAccess {
    if ($AcrPublicAccessRevert) {
        Write-Host "==> Restoring ACR public network access to Disabled"
        Set-AcrPublicNetworkAccess -Mode 'Disabled'
    }
}

Register-EngineEvent PowerShell.Exiting -Action { Restore-AcrPublicNetworkAccess } | Out-Null

# Resolve the repository root (this script lives in <repo>/scripts).
$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendImage  = "cmsabackend:$ImageTag"
$FrontendImage = "cmsafrontend:$ImageTag"

# Ensure the Microsoft.App resource provider is registered before updating the
# container apps. ARM registration can still be propagating after provisioning,
# which makes 'az containerapp update' fail with a "not registered" error.
Write-Host "==> Ensuring the Microsoft.App resource provider is registered"
az provider register --namespace Microsoft.App --wait
if ($LASTEXITCODE -ne 0) { throw "Failed to register the Microsoft.App resource provider." }

Write-Host "==> Building backend image ($BackendImage) in ACR '$AcrName'"
az acr build --registry $AcrName --image $BackendImage --file "$RepoRoot/src/backend/Dockerfile" "$RepoRoot/src/backend"
if ($LASTEXITCODE -ne 0) { throw "Backend image build failed." }

Write-Host "==> Building frontend image ($FrontendImage) in ACR '$AcrName'"
az acr build --registry $AcrName --image $FrontendImage --file "$RepoRoot/src/frontend/Dockerfile" "$RepoRoot/src/frontend"
if ($LASTEXITCODE -ne 0) { throw "Frontend image build failed." }

Write-Host "==> Updating backend container app '$BackendApp'"
az containerapp update --name $BackendApp --resource-group $ResourceGroup --image "$AcrEndpoint/$BackendImage" --output none
if ($LASTEXITCODE -ne 0) { throw "Backend container app update failed." }

Write-Host "==> Updating frontend container app '$FrontendApp'"
az containerapp update --name $FrontendApp --resource-group $ResourceGroup --image "$AcrEndpoint/$FrontendImage" --output none
if ($LASTEXITCODE -ne 0) { throw "Frontend container app update failed." }

Write-Host "==> Done. Container apps are now running the freshly built images."
