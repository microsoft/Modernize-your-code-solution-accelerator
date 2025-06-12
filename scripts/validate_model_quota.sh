#!/bin/bash

LOCATION=""
MODEL=""
DEPLOYMENT_TYPE="Standard"
CAPACITY=0

ALL_REGIONS=('australiaeast' 'eastus' 'eastus2' 'francecentral' 'japaneast' 'norwayeast' 'southindia' 'swedencentral' 'uksouth' 'westus' 'westus3')

# -------------------- Parse Args --------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)
      MODEL="$2"
      shift 2
      ;;
    --capacity)
      CAPACITY="$2"
      shift 2
      ;;
    --deployment-type)
      DEPLOYMENT_TYPE="$2"
      shift 2
      ;;
    --location)
      LOCATION="$2"
      shift 2
      ;;
    *)
      echo "❌ ERROR: Unknown option: $1"
      exit 1
      ;;
  esac
done

# -------------------- Validate Inputs --------------------
MISSING_PARAMS=()
[[ -z "$LOCATION" ]] && MISSING_PARAMS+=("location")
[[ -z "$MODEL" ]] && MISSING_PARAMS+=("model")
[[ "$CAPACITY" -le 0 ]] && MISSING_PARAMS+=("capacity")

if [[ ${#MISSING_PARAMS[@]} -ne 0 ]]; then
  echo "❌ ERROR: Missing or invalid parameters: ${MISSING_PARAMS[*]}"
  echo "Usage: $0 --location <LOCATION> --model <MODEL> --capacity <CAPACITY> [--deployment-type <DEPLOYMENT_TYPE>]"
  exit 1
fi

if [[ "$DEPLOYMENT_TYPE" != "Standard" && "$DEPLOYMENT_TYPE" != "GlobalStandard" ]]; then
  echo "❌ ERROR: Invalid deployment type: $DEPLOYMENT_TYPE. Allowed values: 'Standard', 'GlobalStandard'."
  exit 1
fi

MODEL_TYPE="OpenAI.$DEPLOYMENT_TYPE.$MODEL"
ALL_RESULTS=()
FALLBACK_RESULTS=()
ROW_NO=1

# Print validating message only once
echo "🔍 Checking quota in the requested region '$LOCATION' for the Model '$MODEL'..."

# -------------------- Function: Check Quota --------------------
check_quota() {
  local region="$1"
  local output
  output=$(az cognitiveservices usage list --location "$region" --query "[?name.value=='$MODEL_TYPE']" --output json 2>/dev/null)

  if [[ -z "$output" || "$output" == "[]" ]]; then
    return 2  # No data
  fi

  local CURRENT_VALUE
  local LIMIT
  CURRENT_VALUE=$(echo "$output" | jq -r '.[0].currentValue // 0' | cut -d'.' -f1)
  LIMIT=$(echo "$output" | jq -r '.[0].limit // 0' | cut -d'.' -f1)
  local AVAILABLE=$((LIMIT - CURRENT_VALUE))

  ALL_RESULTS+=("$region|$LIMIT|$CURRENT_VALUE|$AVAILABLE")

  if [[ "$AVAILABLE" -ge "$CAPACITY" ]]; then
    return 0
  else
    return 1
  fi
}

# -------------------- Check User-Specified Region --------------------
check_quota "$LOCATION"
primary_status=$?

if [[ $primary_status -eq 2 ]]; then
  echo -e "\n⚠️  Could not retrieve quota info for region: '$LOCATION'."
  exit 1
fi

if [[ $primary_status -eq 1 ]]; then
  # Get available quota from ALL_RESULTS for LOCATION to use in warning
  primary_entry="${ALL_RESULTS[0]}"
  IFS='|' read -r _ limit used available <<< "$primary_entry"
  echo -e "\n⚠️  Insufficient quota in '$LOCATION' (Available: $available, Required: $CAPACITY). Checking fallback regions..."
fi

# -------------------- Check Fallback Regions --------------------
for region in "${ALL_REGIONS[@]}"; do
  [[ "$region" == "$LOCATION" ]] && continue
  check_quota "$region"
  if [[ $? -eq 0 ]]; then
    FALLBACK_RESULTS+=("$region")
  fi
done

# -------------------- Print Results Table --------------------
echo ""
printf "%-6s | %-18s | %-35s | %-8s | %-8s | %-9s\n" "No." "Region" "Model Name" "Limit" "Used" "Available"
printf -- "-------------------------------------------------------------------------------------------------------------\n"

index=1
for result in "${ALL_RESULTS[@]}"; do
  IFS='|' read -r region limit used available <<< "$result"
  printf "| %-4s | %-16s | %-33s | %-7s | %-7s | %-9s |\n" "$index" "$region" "$MODEL_TYPE" "$limit" "$used" "$available"
  ((index++))
done
printf -- "-------------------------------------------------------------------------------------------------------------\n"

# -------------------- Output Result --------------------
if [[ $primary_status -eq 0 ]]; then
  echo -e "\n✅ Sufficient quota found in original region '$LOCATION'."
  exit 0
fi


# Function: Ask user for location and validate quota
ask_for_location() {
  echo "Please enter any other location from the above table where you want to deploy AI Services:"
  read LOCATION < /dev/tty

  # Validate user input
  if [[ -z "$LOCATION" ]]; then
    echo "❌ ERROR: No location entered. Exiting."
    exit 1
  fi

  echo "🔍 Checking quota in '$LOCATION'..."
  check_quota "$LOCATION"
  user_region_status=$?

  if [[ $user_region_status -eq 0 ]]; then
    echo "✅ Sufficient quota found in '$LOCATION'. Proceeding with deployment."
    azd env set AZURE_AISERVICE_LOCATION "$LOCATION"
    echo "➡️  Set AZURE_AISERVICE_LOCATION to '$LOCATION'."
    exit 0
  elif [[ $user_region_status -eq 2 ]]; then
    echo "⚠️ Could not retrieve quota info for region: '$LOCATION'. Exiting."
    exit 1
  else
    echo "❌ Insufficient quota in '$LOCATION'."
    ask_for_location  # **Recursively call the function until valid input is provided**
  fi
}

# Main Logic
if [[ ${#FALLBACK_RESULTS[@]} -gt 0 ]]; then
  echo -e "\n❌ Deployment cannot proceed in this location: '$LOCATION'."
  echo "➡️  Found fallback regions with sufficient quota."
  
  ask_for_location  # **Call function to prompt user for input**
fi