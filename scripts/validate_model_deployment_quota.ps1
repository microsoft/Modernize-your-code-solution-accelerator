param (
    [string]$SubscriptionId,
    [string]$Location,
    [string]$ModelsParameter
)

# Read from environment variables (do not pass in azure.yaml)
$AiServiceName = $env:AZURE_AISERVICE_NAME
$ResourceGroup = $env:AZURE_RESOURCE_GROUP

# Validate required parameters
$MissingParams = @()

if (-not $SubscriptionId) {
    $MissingParams += "subscription"
}
if (-not $Location) {
    $MissingParams += "location"
}
if (-not $ModelsParameter) {
    $MissingParams += "models-parameter"
}

if ($MissingParams.Count -gt 0) {
    Write-Error "❌ ERROR: Missing required parameters: $($MissingParams -join ', ')"
    Write-Host "Usage: .\validate_model_deployment_quotas.ps1 -SubscriptionId <SUBSCRIPTION_ID> -Location <LOCATION> -ModelsParameter <MODELS_PARAMETER>"
    exit 1
}

# Load main.parameters.json
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

# Check if AI resource + all deployments already exist
if ($AiServiceName -and $ResourceGroup) {
    $existing = az cognitiveservices account show `
        --name $AiServiceName `
        --resource-group $ResourceGroup `
        --query "name" --output tsv 2>$null

    if ($existing) {
        $deployedModels = az cognitiveservices account deployment list `
            --name $AiServiceName `
            --resource-group $ResourceGroup `
            --query "[].name" --output tsv 2>$null

        $requiredDeployments = @()
        foreach ($deployment in $aiModelDeployments) {
            $requiredDeployments += $deployment.name
        }

        $missingDeployments = @()
        foreach ($required in $requiredDeployments) {
            if ($deployedModels -notcontains $required) {
                $missingDeployments += $required
            }
        }

        if ($missingDeployments.Count -eq 0) {
            Write-Host "ℹ️ Azure AI service '$AiServiceName' exists and all required model deployments are provisioned."
            Write-Host "⏭️ Skipping quota validation."
            exit 0
        } else {
            Write-Host "🔍 AI service exists, but the following model deployments are missing: $($missingDeployments -join ', ')"
            Write-Host "➡️ Proceeding with quota validation for missing models..."
        }
    }
}

# Start quota validation
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
            exit 1  # already printed, graceful
        }
        Write-Error "❌ ERROR: Quota validation failed for model deployment: $name"
        $QuotaAvailable = $false
    }
}

if (-not $QuotaAvailable) {
    Write-Error "❌ ERROR: One or more model deployments failed validation."
    exit 1
} else {
    Write-Host "✅ All model deployments passed quota validation successfully."
    exit 0
}