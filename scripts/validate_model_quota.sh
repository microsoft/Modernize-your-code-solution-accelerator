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
echo -e "\n🔍 Validating model deployment: $MODEL ..."

echo "🔍 Checking quota in the requested region '$LOCATION'..."

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

if [[ ${#FALLBACK_RESULTS[@]} -gt 0 ]]; then
  echo -e "\n❌ Deployment cannot proceed in '$LOCATION'."
  echo "➡️ You can retry using one of the following regions with sufficient quota:"
  echo ""
  for region in "${FALLBACK_RESULTS[@]}"; do
    for result in "${ALL_RESULTS[@]}"; do
      IFS='|' read -r rgn _ _ avail <<< "$result"
      if [[ "$rgn" == "$region" ]]; then
        echo "   • $region (Available: $avail)"
        break
      fi
    done
  done

  echo -e "\n🔧 To proceed, run:"
  echo "    azd env set AZURE_AISERVICE_LOCATION '<region>'"
  echo "📌 To confirm it's set correctly, run:"
  echo "    azd env get-value AZURE_AISERVICE_LOCATION"
  echo "▶️  Once confirmed, re-run azd up to deploy the model in the new region."
  exit 2
fi

echo -e "\n❌ ERROR: No available quota found in any region."
exit 1