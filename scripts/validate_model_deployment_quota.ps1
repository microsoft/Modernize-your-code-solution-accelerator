param (
    [string]$SubscriptionId,
    [string]$Location,
    [string]$ModelsParameter
)

$AiFoundryName = $env:AZURE_AIFOUNDRY_NAME
$ResourceGroup = $env:AZURE_RESOURCE_GROUP

# Validate required parameters
$MissingParams = @()
if (-not $SubscriptionId) { $MissingParams += "SubscriptionId" }
if (-not $Location) { $MissingParams += "Location" }
if (-not $ModelsParameter) { $MissingParams += "ModelsParameter" }
if (-not $AiFoundryName) { $MissingParams += "AZURE_AISERVICE_NAME" }
if (-not $ResourceGroup) { $MissingParams += "AZURE_RESOURCE_GROUP" }

if ($MissingParams.Count -gt 0) {
    Write-Error "❌ ERROR: Missing required parameters: $($MissingParams -join ', ')"
    exit 1
}

# Load model deployment parameters
$JsonContent = Get-Content -Path "./infra/main.parameters.json" -Raw | ConvertFrom-Json
if (-not $JsonContent) {
    Write-Error "❌ ERROR: Failed to parse main.parameters.json. Ensure the JSON file is valid."
    exit 1
}

$aiModelDeployments = $JsonContent.parameters.$ModelsParameter.value

if (-not $aiModelDeployments -or -not ($aiModelDeployments -is [System.Collections.IEnumerable])) {
    Write-Error "❌ ERROR: The specified property '$ModelsParameter' does not exist or is not an array."
    exit 1
}

# Check if AI Foundry and model deployments already exist
$existing = az cognitiveservices account show `
    --name $AiFoundryName `
    --resource-group $ResourceGroup `
    --query "name" --output tsv 2>$null

if ($existing) {
    $deployedModelsOutput = az cognitiveservices account deployment list `
        --name $AiFoundryName `
        --resource-group $ResourceGroup `
        --query "[].name" --output tsv 2>$null

    # Normalize output to array
    $deployedModels = @()
    if ($deployedModelsOutput -is [string]) {
        $deployedModels += $deployedModelsOutput
    } elseif ($deployedModelsOutput) {
        $deployedModels = $deployedModelsOutput -split "`r?`n"
    }

    $requiredDeployments = $aiModelDeployments | ForEach-Object { $_.name }
    $missingDeployments = $requiredDeployments | Where-Object { $_ -notin $deployedModels }

    if ($missingDeployments.Count -eq 0) {
        Write-Host "ℹ️ AI Foundry '$AiFoundryName' exists and all required model deployments are already provisioned."
        Write-Host "⏭️ Skipping quota validation."
        exit 0
    } else {
        Write-Host "🔍 AI Foundry exists, but the following model deployments are missing: $($missingDeployments -join ', ')"
        Write-Host "➡️ Proceeding with quota validation for missing models..."
    }
} else {
    Write-Host "❌ AI Foundry '$AiFoundryName' not found. Proceeding with quota validation."
}

# Run quota validation
az account set --subscription $SubscriptionId
Write-Host "🎯 Active Subscription: $(az account show --query '[name, id]' --output tsv)"

$QuotaAvailable = $true

foreach ($deployment in $aiModelDeployments) {
    $name = if ($env:AZURE_ENV_MODEL_NAME) { $env:AZURE_ENV_MODEL_NAME } else { $deployment.name }
    $model = if ($env:AZURE_ENV_MODEL_NAME) { $env:AZURE_ENV_MODEL_NAME } else { $deployment.model.name }
    $type = if ($env:AZURE_ENV_MODEL_DEPLOYMENT_TYPE) { $env:AZURE_ENV_MODEL_DEPLOYMENT_TYPE } else { $deployment.sku.name }
    $capacity = if ($env:AZURE_ENV_MODEL_CAPACITY) { $env:AZURE_ENV_MODEL_CAPACITY } else { $deployment.sku.capacity }

    Write-Host "`n🔍 Validating model deployment: $name ..."
    & .\scripts\validate_model_quota.ps1 -Location $Location -Model $model -Capacity $capacity -DeploymentType $type
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        if ($exitCode -eq 2) {
            exit 1
        }
        Write-Error "❌ ERROR: Quota validation failed for model deployment: $name"
        $QuotaAvailable = $false
    }
}

if (-not $QuotaAvailable) {
    Write-Error "❌ ERROR: One or more model deployments failed quota validation."
    exit 1
} else {
    Write-Host "✅ All model deployments passed quota validation successfully."
    exit 0
}
