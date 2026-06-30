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
if (-not $DeploymentType) { $MissingParams += "deployment-type" }

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
        if (-not $ModelInfo) { return }

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
        return
    }
}

# First, check the user-specified region
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

# Remove primary region from fallback list
$FallbackRegions = $PreferredRegions | Where-Object { $_ -ne $Location }

foreach ($region in $FallbackRegions) {
    $result = Check-Quota -Region $region
    if ($result) {
        $AllResults += $result
    }
}

# Display Results Table
Write-Host "`n-------------------------------------------------------------------------------------------------------------"
Write-Host "| No.  | Region            | Model Name                           | Limit   | Used    | Available |"
Write-Host "-------------------------------------------------------------------------------------------------------------"

$count = 1
foreach ($entry in $AllResults) {
    $modelShort = $entry.Model.Substring($entry.Model.LastIndexOf(".") + 1)
    Write-Host ("| {0,-4} | {1,-16} | {2,-35} | {3,-7} | {4,-7} | {5,-9} |" -f $count, $entry.Region, $entry.Model, $entry.Limit, $entry.Used, $entry.Available)
    $count++
}
Write-Host "-------------------------------------------------------------------------------------------------------------"

# Suggest fallback regions
$EligibleFallbacks = $AllResults | Where-Object { $_.Region -ne $Location -and $_.Available -ge $Capacity }

if ($EligibleFallbacks.Count -gt 0) {
    Write-Host "`n❌ Deployment cannot proceed in '$Location'."
    Write-Host "➡️ You can retry using one of the following regions with sufficient quota:`n"
    foreach ($region in $EligibleFallbacks) {
        Write-Host "   • $($region.Region) (Available: $($region.Available))"
    }

    Write-Host "`n🔧 To proceed, run:"
    Write-Host "    azd env set AZURE_AISERVICE_LOCATION '<region>'"
    Write-Host "📌 To confirm it's set correctly, run:"
    Write-Host "    azd env get-value AZURE_AISERVICE_LOCATION"
    Write-Host "▶️  Once confirmed, re-run azd up to deploy the model in the new region."
    exit 2
}

Write-Error "`n❌ ERROR: No available quota found in any region."
exit 1