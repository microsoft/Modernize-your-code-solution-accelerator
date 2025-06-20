param (
    [string]$Location,
    [string]$Model,
    [string]$DeploymentType = "Standard",
    [int]$Capacity
)

$RECOMMENDED_TOKENS = 200
$BicepParamsFile = "main.bicepparams"
$ParametersJsonFile = "./infra/main.parameters.json"
$PreferredRegions = @('australiaeast', 'eastus', 'eastus2', 'francecentral', 'japaneast', 'norwayeast', 'southindia', 'swedencentral', 'uksouth', 'westus', 'westus3')
$AllResults = @()
$RecommendedRegions = @()
$NotRecommendedRegions = @()
$EligibleFallbacks = @()

function Validate-Inputs {
    $MissingParams = @()
    if (-not $Location) { $MissingParams += "location" }
    if (-not $Model) { $MissingParams += "model" }
    if (-not $Capacity -or $Capacity -le 0) { $MissingParams += "capacity" }

    if ($MissingParams.Count -gt 0) {
        Write-Error "❌ ERROR: Missing or invalid parameters: $($MissingParams -join ', ')"
        Write-Host "Usage: .\validate_model_quota.ps1 -Location <LOCATION> -Model <MODEL> -Capacity <CAPACITY> [-DeploymentType <DEPLOYMENT_TYPE>]"
        exit 1
    }

    if ($DeploymentType -ne "Standard" -and $DeploymentType -ne "GlobalStandard") {
        Write-Error "❌ ERROR: Invalid deployment type: $DeploymentType. Allowed: 'Standard', 'GlobalStandard'"
        exit 1
    }
}

function Confirm-Action ($message) {
    do {
        $response = Read-Host "$message (y/n)"
        if ($response -notmatch "^[YyNn]$") {
            Write-Host "❌ Invalid input. Please enter 'y' or 'n'."
        }
    } while ($response -notmatch "^[YyNn]$")
    return $response -match "^[Yy]$"
}

function Check-Quota {
    param ([string]$Region)

    try {
        $ModelType = "OpenAI.$DeploymentType.$Model"
        $ModelInfoRaw = az cognitiveservices usage list --location $Region --query "[?name.value=='$ModelType']" --output json 2>$null
        $ModelInfo = $ModelInfoRaw | ConvertFrom-Json
        if (-not $ModelInfo -or $ModelInfo.Count -eq 0) { return $null }

        $Current = [int]$ModelInfo[0].currentValue
        $Limit = [int]$ModelInfo[0].limit
        $Available = $Limit - $Current

        if ($Available -ge $RECOMMENDED_TOKENS) {
            $script:RecommendedRegions += $Region
        } else {
            $script:NotRecommendedRegions += $Region
        }

        return [PSCustomObject]@{
            Region    = $Region
            Model     = $ModelType
            Limit     = $Limit
            Used      = $Current
            Available = $Available
        }
    } catch {
        return $null
    }
}

function Show-Table {
    Write-Host "`n--------------------------------------------------------------------------------------------------"
    Write-Host "| No. | Region          | Model Name                          | Limit | Used  | Available |"
    Write-Host "--------------------------------------------------------------------------------------------------"
    $i = 1
    foreach ($entry in $AllResults | Where-Object { $_.Available -gt 50 }) {
        Write-Host ("| {0,-3} | {1,-15} | {2,-35} | {3,-5} | {4,-5} | {5,-9} |" -f $i, $entry.Region, $entry.Model, $entry.Limit, $entry.Used, $entry.Available)
        $i++
    }
    Write-Host "--------------------------------------------------------------------------------------------------"
}

function Set-DeploymentValues($Region, $Capacity) {
    azd env set AZURE_AISERVICE_LOCATION "$Region" | Out-Null
    azd env set AZURE_ENV_MODEL_CAPACITY "$Capacity" | Out-Null

    if (Test-Path $ParametersJsonFile) {
        try {
            $json = Get-Content $ParametersJsonFile -Raw | ConvertFrom-Json
            if ($json.parameters.aiModelDeployments.value.Count -gt 0) {
                $json.parameters.aiModelDeployments.value[0].sku.capacity = $Capacity
                $json | ConvertTo-Json -Depth 20 | Set-Content $ParametersJsonFile -Force
                Write-Host "✅ Updated '$ParametersJsonFile' with capacity $Capacity."
            } else {
                Write-Host "⚠️  'aiModelDeployments.value' array is empty. No changes made."
            }
        } catch {
            Write-Host "❌ Failed to update '$ParametersJsonFile': $_"
        }
    } else {
        Write-Host "⚠️  '$ParametersJsonFile' not found. Skipping update."
    }
}

function Manual-Prompt {
    while ($true) {
        Write-Host "`n📍 Recommended regions (≥ $RECOMMENDED_TOKENS tokens available): $($RecommendedRegions -join ', ')"
        $ManualRegion = Read-Host "Please enter a region you want to try manually"
        if (-not $ManualRegion) {
            Write-Host "❌ ERROR: No region entered. Exiting."
            exit 1
        }

        $ManualCapacityStr = Read-Host "Enter the capacity you want to use (numeric value)"
        if (-not ($ManualCapacityStr -as [int]) -or [int]$ManualCapacityStr -le 0) {
            Write-Host "❌ Invalid capacity value. Try again."
            continue
        }

        $ManualCapacity = [int]$ManualCapacityStr

        if ($ManualCapacity -lt $RECOMMENDED_TOKENS) {
            Write-Host "`n⚠️  You have entered a capacity of $ManualCapacity, which is less than the recommended minimum ($RECOMMENDED_TOKENS)."
            Write-Host "🚨 This may cause performance issues or unexpected behavior."
            Write-Host "ℹ️  Recommended regions (≥ $RECOMMENDED_TOKENS tokens available): $($RecommendedRegions -join ', ')"
            if (-not (Confirm-Action "❓ Proceed anyway?")) { continue }
        }

        Write-Host "`n🔍 Checking quota in region '$ManualRegion' for requested capacity: $ManualCapacity..."
        $ManualResult = Check-Quota -Region $ManualRegion

        if (-not $ManualResult) {
            Write-Host "⚠️ Could not retrieve quota info for region '$ManualRegion'. Try again."
            continue
        }

        if ($ManualResult.Available -ge $ManualCapacity) {
            if ($ManualResult.Available -lt $RECOMMENDED_TOKENS) {
                if (-not (Confirm-Action "❓ Proceed anyway?")) { continue }
            }
            Set-DeploymentValues $ManualRegion $ManualCapacity
            Write-Host "✅ Deployment values set. Exiting."
            exit 0
        } else {
            Write-Host "❌ Quota in region '$ManualRegion' is insufficient. Available: $($ManualResult.Available), Required: $ManualCapacity"
        }
    }
}

# Start validation and quota checks
Validate-Inputs

Write-Host "`n🔍 Checking quota in the requested region '$Location'..."
$PrimaryResult = Check-Quota -Region $Location
if ($PrimaryResult) {
    $AllResults = @($AllResults) + $PrimaryResult
}

foreach ($region in $PreferredRegions) {
    if ($region -ne $Location) {
        $fallbackResult = Check-Quota -Region $region
        if ($fallbackResult) {
            $AllResults = @($AllResults) + $fallbackResult
            if ($fallbackResult.Available -ge $Capacity) {
                $EligibleFallbacks += $region
            }
        }
    }
}

Show-Table

if ($Capacity -lt $RECOMMENDED_TOKENS) {
    Write-Host "`n⚠️  You have entered a capacity of $Capacity, which is less than the recommended minimum ($RECOMMENDED_TOKENS)."
    Write-Host "🚨 This may cause performance issues or unexpected behavior."
    Write-Host "ℹ️  Recommended regions (≥ $RECOMMENDED_TOKENS tokens available):"
    if ($RecommendedRegions.Count -gt 0) {
        foreach ($region in $RecommendedRegions) {
            Write-Host "  - $region"
        }
    } else {
        Write-Host "  ❌ No recommended regions currently available."
    }
    if (-not (Confirm-Action "❓ Proceed anyway?")) {
        Manual-Prompt
        exit 0
    }
}

if ($PrimaryResult -and $PrimaryResult.Available -ge $Capacity) {
    Set-DeploymentValues $Location $Capacity
    Write-Host "✅ Proceeding with '$Location' as selected."
    exit 0
}

Write-Host "`n❗ The originally selected region '$Location' does not have enough quota."
if ($EligibleFallbacks.Count -gt 0) {
    Write-Host "👉 You can manually choose one of the recommended fallback regions for deployment."
} else {
    Write-Host "❌ ERROR: No region has sufficient quota."
}

Manual-Prompt