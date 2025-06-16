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

# ------------------ Validate Inputs ------------------
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

$ModelType = "OpenAI.$DeploymentType.$Model"

function Check-Quota {
    param ([string]$Region)

    try {
        $ModelInfoRaw = az cognitiveservices usage list --location $Region --query "[?name.value=='$ModelType']" --output json 2>$null
        $ModelInfo = $ModelInfoRaw | ConvertFrom-Json
        if (-not $ModelInfo -or $ModelInfo.Count -eq 0) {
            return $null
        }

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

# ------------------ Check Primary Region ------------------
Write-Host "`n🔍 Checking quota in the requested region '$Location'..."
$PrimaryResult = Check-Quota -Region $Location

if ($PrimaryResult) {
    $AllResults += $PrimaryResult
    if ($PrimaryResult.Available -ge $Capacity) {
        if ($RecommendedRegions -notcontains $Location -and $RecommendedRegions.Count -gt 0) {
            Write-Host "`n⚠️  Selected region '$Location' has sufficient quota but is not among the recommended regions (≥ $RECOMMENDED_TOKENS tokens)."
            Write-Host "🚨 Your application may not work as expected due to limited quota."
            Write-Host "`nℹ️  Recommended regions: $($RecommendedRegions -join ', ')"
            Write-Host "👉 It's advisable to deploy in one of these regions for optimal app performance."
            do {
                $choice = Read-Host "❓ Do you want to choose a recommended region instead? (y/n)"
                if ($choice -notmatch "^[YyNn]$") {
                    Write-Host "❌ Invalid input. Please enter 'y' or 'n'."
                }
            } while ($choice -notmatch "^[YyNn]$")

            if ($choice -match "^[Yy]$") {
                Show-Table
                break
            } else {
                if ($Capacity -gt 200) {
                    Write-Host "`n⚠️  Reducing capacity to 200 in '$BicepParamsFile' for safer deployment..."
                    (Get-Content $BicepParamsFile) -replace "capacity\s*:\s*\d+", "capacity: 200" | Set-Content $BicepParamsFile
                    Write-Host "✅ Updated '$BicepParamsFile' with capacity 200."
                }
                Set-DeploymentValues $Location $Capacity
                Write-Host "✅ Proceeding with '$Location' as selected."
                exit 0
            }
        } else {
            Write-Host "`n✅ Sufficient quota found in original region '$Location'."
            Set-DeploymentValues $Location $Capacity
            exit 0
        }
    } else {
        Write-Host "`n⚠️  Insufficient quota in '$LOCATION' (Available: $($PrimaryResult.Available), Required: $Capacity). Checking fallback regions..."
    }
} else {
    Write-Host "`n⚠️  Could not retrieve quota info for region '$Location'."
}

# ------------------ Check Fallback Regions ------------------
foreach ($region in $PreferredRegions) {
    if ($region -eq $Location) { continue }
    $result = Check-Quota -Region $region
    if ($result) {
        $AllResults += $result
        if ($result.Available -ge $Capacity) {
            $EligibleFallbacks += $region
        }
    }
}

Show-Table

if ($EligibleFallbacks.Count -gt 0) {
    Write-Host "`n➡️  Found fallback regions with sufficient quota."
    if ($RecommendedRegions.Count -gt 0) {
        Write-Host "`nℹ️  Recommended regions (≥ $RECOMMENDED_TOKENS tokens available):"
        foreach ($region in $RecommendedRegions) {
            Write-Host "  - $region"
        }
    }

    Write-Host "`n❗ The originally selected region '$Location' does not have enough quota."
    Write-Host "👉 You can manually choose one of the recommended fallback regions for deployment."
} else {
    Write-Host "`n❌ ERROR: No region has sufficient quota."
}

# ------------------ Manual Prompt ------------------
while ($true) {
    $ManualRegion = Read-Host "`nPlease enter a region you want to try manually"
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

    if ($ManualCapacity -lt 200) {
        Write-Host "`n⚠️  You have entered a capacity of $ManualCapacity, which is less than the recommended minimum (200)."
        Write-Host "🚨 This may cause performance issues or unexpected behavior."
        Write-Host "ℹ️  Recommended regions (≥ $RECOMMENDED_TOKENS tokens available): $($RecommendedRegions -join ', ')"
        do {
            $proceed = Read-Host "❓ Proceed anyway? (y/n)"
            if ($proceed -notmatch "^[YyNn]$") {
                Write-Host "❌ Invalid input. Please enter 'y' or 'n'."
            }
        } while ($proceed -notmatch "^[YyNn]$")

        if ($proceed -notmatch "^[Yy]$") {
            continue
        }
    }

    Write-Host "`n🔍 Checking quota in region '$ManualRegion' for requested capacity: $ManualCapacity..."
    $ManualResult = Check-Quota -Region $ManualRegion

    if (-not $ManualResult) {
        Write-Host "⚠️ Could not retrieve quota info for region '$ManualRegion'. Try again."
        continue
    }

    if ($ManualResult.Available -ge $ManualCapacity) {
        if ($ManualResult.Available -lt $RECOMMENDED_TOKENS) {
            Write-Host "`n⚠️  Region '$ManualRegion' has less than recommended ($RECOMMENDED_TOKENS) tokens."
            $proceed = Read-Host "❓ Proceed anyway? (y/n)"
            if ($proceed -notmatch "^[Yy]$") {
                continue
            }
        }

        Set-DeploymentValues $ManualRegion $ManualCapacity
        Write-Host "✅ Deployment values set. Exiting."
        exit 0
    } else {
        Write-Host "❌ Quota in region '$ManualRegion' is insufficient. Available: $($ManualResult.Available), Required: $ManualCapacity"
    }
}