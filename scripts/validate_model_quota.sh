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
FALLBACK_REGIONS=()
ROW_NO=1
QUOTA_CHECKED=false

# -------------------- Output Table Header --------------------
printf "\n%-5s | %-20s | %-40s | %-10s | %-10s | %-10s\n" "No." "Region" "Model Name" "Limit" "Used" "Available"
printf -- "---------------------------------------------------------------------------------------------------------------------\n"

# -------------------- Check Quota --------------------
for region in "${ALL_REGIONS[@]}"; do
  MODEL_INFO=$(az cognitiveservices usage list --location "$region" --query "[?name.value=='$MODEL_TYPE']" --output json 2>/dev/null)

  if [[ -n "$MODEL_INFO" && "$MODEL_INFO" != "[]" ]]; then
    CURRENT_VALUE=$(echo "$MODEL_INFO" | jq -r '.[0].currentValue // 0' | cut -d'.' -f1)
    LIMIT=$(echo "$MODEL_INFO" | jq -r '.[0].limit // 0' | cut -d'.' -f1)
    AVAILABLE=$((LIMIT - CURRENT_VALUE))

    printf "%-5s | %-20s | %-40s | %-10s | %-10s | %-10s\n" "$ROW_NO" "$region" "$MODEL_TYPE" "$LIMIT" "$CURRENT_VALUE" "$AVAILABLE"

    if [[ "$region" == "$LOCATION" ]]; then
      QUOTA_CHECKED=true
      if [[ "$AVAILABLE" -ge "$CAPACITY" ]]; then
        echo -e "\n✅ Sufficient quota available in user-specified region: $LOCATION"
        exit 0
      fi
    elif [[ "$AVAILABLE" -ge "$CAPACITY" ]]; then
      FALLBACK_REGIONS+=("$region ($AVAILABLE)")
    fi
  fi
  ((ROW_NO++))
done

printf -- "---------------------------------------------------------------------------------------------------------------------\n"

# -------------------- Output Result --------------------
if ! $QUOTA_CHECKED; then
  echo -e "\n⚠️  Could not retrieve quota info for region: $LOCATION"
fi

if [[ ${#FALLBACK_REGIONS[@]} -gt 0 ]]; then
  echo -e "\n❌ Insufficient quota in '$LOCATION'."
  echo "➡️  You may retry using one of the following fallback regions with enough quota:"
  for region in "${FALLBACK_REGIONS[@]}"; do
    echo "   • $region"
  done
  echo -e "\n🔧 To proceed, run:"
  echo "    azd env set AZURE_AISERVICE_LOCATION '<region>'"
  echo "📌 To confirm, run:"
  echo "    azd env get-value AZURE_AISERVICE_LOCATION"
  echo "▶️  Then re-run: azd up"
  exit 2
fi

echo "❌ ERROR: No region has sufficient quota for '$MODEL_TYPE'."
exit 1