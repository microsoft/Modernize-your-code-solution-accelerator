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

if ($MissingParams.Count -gt 0) {
    Write-Error "❌ ERROR: Missing required parameters: $($MissingParams -join ', ')"
    Write-Host "Usage: validate_model_deployment_quota.ps1 -SubscriptionId <SUBSCRIPTION_ID> -Location <LOCATION> -ModelsParameter <MODELS_PARAMETER>"
    exit 1
}

# Load model deployments from parameter file
$JsonContent = Get-Content -Path "./infra/main.parameters.json" -Raw | ConvertFrom-Json
$aiModelDeployments = $JsonContent.parameters.$ModelsParameter.value
if (-not $aiModelDeployments -or -not ($aiModelDeployments -is [System.Collections.IEnumerable])) {
    Write-Error "❌ ERROR: Failed to parse main.parameters.json or missing '$ModelsParameter'"
    exit 1
}

# Try to discover AI Foundry name if not set
if (-not $AiFoundryName -and $ResourceGroup) {
    $AiFoundryName = az cognitiveservices account list `
        --resource-group $ResourceGroup `
        --query "sort_by([?kind=='AIServices'], &name)[0].name" `
        -o tsv 2>$null
}

# Check if AI Foundry exists
if ($AiFoundryName -and $ResourceGroup) {
    $existing = az cognitiveservices account show `
        --name $AiFoundryName `
        --resource-group $ResourceGroup `
        --query "name" --output tsv 2>$null

    if ($existing) {
        # adding into .env
        azd env set AZURE_AIFOUNDRY_NAME $existing | Out-Null

        $deployedModelsOutput = az cognitiveservices account deployment list `
            --name $AiFoundryName `
            --resource-group $ResourceGroup `
            --query "[].name" --output tsv 2>$null

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
    }
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

    Write-Host ""
    Write-Host "🔍 Validating model deployment: $name ..."
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
