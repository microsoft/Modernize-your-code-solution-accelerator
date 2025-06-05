param (
    [string]$SubscriptionId,
    [string]$Location,
    [string]$ModelsParameter
)

# Verify all required parameters are provided
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

$JsonContent = Get-Content -Path "./infra/main.parameters.json" -Raw | ConvertFrom-Json

if (-not $JsonContent) {
    Write-Error "❌ ERROR: Failed to parse main.parameters.json. Ensure the JSON file is valid."
    exit 1
}

$aiModelDeployments = $JsonContent.parameters.$ModelsParameter.value

if (-not $aiModelDeployments -or -not ($aiModelDeployments -is [System.Collections.IEnumerable])) {
    Write-Error "❌ ERROR: The specified property $ModelsParameter does not exist or is not an array."
    exit 1
}

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
            # Quota error already printed inside the script, exit gracefully without reprinting
            exit 1
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