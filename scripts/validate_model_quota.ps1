param (
    [string]$Location,
    [string]$Model,
    [string]$DeploymentType = "Standard",
    [int]$Capacity
)

# Validate parameters
$MissingParams = @()
if (-not $Location) { $MissingParams += "location" }
if (-not $Model) { $MissingParams += "model" }
if (-not $Capacity) { $MissingParams += "capacity" }

if ($MissingParams.Count -gt 0) {
    Write-Error "❌ ERROR: Missing required parameters: $($MissingParams -join ', ')"
    Write-Host "Usage: .\validate_model_quota.ps1 -Location <LOCATION> -Model <MODEL> -Capacity <CAPACITY> [-DeploymentType <DEPLOYMENT_TYPE>]"
    exit 1
}

if ($DeploymentType -ne "Standard" -and $DeploymentType -ne "GlobalStandard") {
    Write-Error "❌ ERROR: Invalid deployment type: $DeploymentType. Allowed values are 'Standard' or 'GlobalStandard'."
    exit 1
}

$ModelType = "OpenAI.$DeploymentType.$Model"
$PreferredRegions = @('australiaeast', 'eastus', 'eastus2', 'francecentral', 'japaneast', 'norwayeast', 'southindia', 'swedencentral', 'uksouth', 'westus', 'westus3')
$AllResults = @()

function Check-Quota {
    param (
        [string]$Region
    )

    try {
        $ModelInfoRaw = az cognitiveservices usage list --location $Region --query "[?name.value=='$ModelType']" --output json
        $ModelInfo = $ModelInfoRaw | ConvertFrom-Json
        if (-not $ModelInfo) { return $null }

        $CurrentValue = ($ModelInfo | Where-Object { $_.name.value -eq $ModelType }).currentValue
        $Limit = ($ModelInfo | Where-Object { $_.name.value -eq $ModelType }).limit

        $CurrentValue = [int]($CurrentValue -replace '\.0+$', '')
        $Limit = [int]($Limit -replace '\.0+$', '')
        $Available = $Limit - $CurrentValue

        return [PSCustomObject]@{
            Region    = $Region
            Model     = $ModelType
            Limit     = $Limit
            Used      = $CurrentValue
            Available = $Available
        }
    } catch {
        return $null
    }
}

function Show-Table {
    Write-Host "`n--------------------------------------------------------------------------------------------"
    Write-Host "| No. | Region         | Model Name                          | Limit | Used  | Available |"
    Write-Host "--------------------------------------------------------------------------------------------"
    $count = 1
    foreach ($entry in $AllResults) {
        Write-Host ("| {0,-3} | {1,-14} | {2,-35} | {3,-5} | {4,-5} | {5,-9} |" -f $count, $entry.Region, $entry.Model, $entry.Limit, $entry.Used, $entry.Available)
        $count++
    }
    Write-Host "--------------------------------------------------------------------------------------------"
}

# ----------- First check the user-specified region -----------
Write-Host "`n🔍 Checking quota in the requested region '$Location'..."
$PrimaryResult = Check-Quota -Region $Location

if ($PrimaryResult) {
    $AllResults += $PrimaryResult
    if ($PrimaryResult.Available -ge $Capacity) {
        Write-Host "`n✅ Sufficient quota found in original region '$Location'."
        exit 0
    } else {
        Write-Host "`n⚠️  Insufficient quota in '$Location' (Available: $($PrimaryResult.Available), Required: $Capacity). Checking fallback regions..."
    }
} else {
    Write-Host "`n⚠️  Could not retrieve quota info for region '$Location'. Checking fallback regions..."
}

# ----------- Check all other fallback regions -----------
$FallbackRegions = $PreferredRegions | Where-Object { $_ -ne $Location }
$EligibleFallbacks = @()

foreach ($region in $FallbackRegions) {
    $result = Check-Quota -Region $region
    if ($result) {
        $AllResults += $result
        if ($result.Available -ge $Capacity) {
            $EligibleFallbacks += $result
        }
    }
}

# ----------- Show Table of All Regions Checked -----------
$AllResults = $AllResults | Where-Object { $_.Available -gt 50 }
Show-Table

# ----------- If eligible fallback regions found, ask user -----------
if ($EligibleFallbacks.Count -gt 0) {
    Write-Host "`n❌ Deployment cannot proceed in '$Location'."
    Write-Host "➡️  Found fallback regions with sufficient quota."
    
    while ($true) {
        Write-Host "`nPlease enter a fallback region from the list above to proceed:"
        $NewLocation = Read-Host "Enter region"

        if (-not $NewLocation) {
            Write-Host "❌ No location entered. Exiting."
            exit 1
        }

        $UserResult = Check-Quota -Region $NewLocation
        if (-not $UserResult) {
            Write-Host "⚠️ Could not retrieve quota info for region '$NewLocation'. Try again."
            continue
        }

        if ($UserResult.Available -ge $Capacity) {
            Write-Host "✅ Sufficient quota found in '$NewLocation'. Proceeding with deployment."
            azd env set AZURE_AISERVICE_LOCATION "$NewLocation" | Out-Null
            Write-Host "➡️  Set AZURE_AISERVICE_LOCATION to '$NewLocation'."
            exit 0
        } else {
            Write-Host "❌ Insufficient quota in '$NewLocation'. Try another."
        }
    }
}

Write-Error "`n❌ ERROR: No available quota found in any region."
exit 1