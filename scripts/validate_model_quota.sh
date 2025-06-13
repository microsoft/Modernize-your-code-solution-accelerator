#!/bin/bash

LOCATION=""
MODEL=""
DEPLOYMENT_TYPE="Standard"
CAPACITY=0
RECOMMENDED_TOKENS=200

ALL_REGIONS=('australiaeast' 'eastus' 'eastus2' 'francecentral' 'japaneast' 'norwayeast' 'southindia' 'swedencentral' 'uksouth' 'westus' 'westus3')

# Globals for recommended/not recommended regions
RECOMMENDED_REGIONS=()
NOT_RECOMMENDED_REGIONS=()
ALL_RESULTS=()
FALLBACK_RESULTS=()

# -------------------- Utility: Update .env and main.parameters.json --------------------
update_env_and_parameters() {
  local new_location="$1"
  local new_capacity="$2"

  echo "➡️  Updating environment and parameters with Location='$new_location' and Capacity='$new_capacity'..."

  # Update the AZD environment
  azd env set AZURE_AISERVICE_LOCATION "$new_location"
  azd env set AZURE_ENV_MODEL_CAPACITY "$new_capacity"

  # Update main.parameters.json
  local PARAM_FILE="./infra/main.parameters.json"
  if [[ ! -f "$PARAM_FILE" ]]; then
    echo "❌ ERROR: $PARAM_FILE not found, cannot update parameters."
    return 1
  fi

  jq --arg loc "$new_location" \
     '.parameters.location.value = $loc' "$PARAM_FILE" > "${PARAM_FILE}.tmp" && mv "${PARAM_FILE}.tmp" "$PARAM_FILE"

  jq --argjson cap "$new_capacity" --arg model "$MODEL" \
     '(.parameters.aiModelDeployments.value[] | select(.name == $model) | .sku.capacity) |= $cap' "$PARAM_FILE" > "${PARAM_FILE}.tmp" && mv "${PARAM_FILE}.tmp" "$PARAM_FILE"

  echo "✅ Updated .env and $PARAM_FILE successfully."
}

# -------------------- Function: Check Quota --------------------
check_quota() {
  local region="$1"
  local MODEL_TYPE="OpenAI.$DEPLOYMENT_TYPE.$MODEL"
  local output

  output=$(az cognitiveservices usage list --location "$region" --query "[?name.value=='$MODEL_TYPE']" --output json 2>/dev/null)

  if [[ -z "$output" || "$output" == "[]" ]]; then
    return 2  # No data
  fi

  local CURRENT_VALUE=$(echo "$output" | jq -r '.[0].currentValue // 0' | cut -d'.' -f1)
  local LIMIT=$(echo "$output" | jq -r '.[0].limit // 0' | cut -d'.' -f1)
  local AVAILABLE=$((LIMIT - CURRENT_VALUE))

  ALL_RESULTS+=("$region|$LIMIT|$CURRENT_VALUE|$AVAILABLE")

  if [[ "$AVAILABLE" -ge "$RECOMMENDED_TOKENS" ]]; then
    RECOMMENDED_REGIONS+=("$region")
  else
    NOT_RECOMMENDED_REGIONS+=("$region")
  fi

  if [[ "$AVAILABLE" -ge "$CAPACITY" ]]; then
    return 0
  else
    return 1
  fi
}

# -------------------- Input Validation --------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)
      MODEL="$2"; shift 2 ;;
    --capacity)
      CAPACITY="$2"; shift 2 ;;
    --deployment-type)
      DEPLOYMENT_TYPE="$2"; shift 2 ;;
    --location)
      LOCATION="$2"; shift 2 ;;
    *)
      echo "❌ ERROR: Unknown option: $1"; exit 1 ;;
  esac
done

[[ -z "$LOCATION" ]] && MISSING_PARAMS+=("location")
[[ -z "$MODEL" ]] && MISSING_PARAMS+=("model")
if ! [[ "$CAPACITY" =~ ^[0-9]+$ ]] || [[ "$CAPACITY" -le 0 ]]; then
  MISSING_PARAMS+=("capacity")
fi

if [[ ${#MISSING_PARAMS[@]} -ne 0 ]]; then
  echo "❌ ERROR: Missing/invalid: ${MISSING_PARAMS[*]}"
  echo "Usage: $0 --location <LOCATION> --model <MODEL> --capacity <CAPACITY> [--deployment-type <DEPLOYMENT_TYPE>]"
  exit 1
fi

if [[ "$DEPLOYMENT_TYPE" != "Standard" && "$DEPLOYMENT_TYPE" != "GlobalStandard" ]]; then
  echo "❌ ERROR: Invalid deployment type: $DEPLOYMENT_TYPE"
  exit 1
fi

# -------------------- Main Logic Starts --------------------
echo "🔍 Checking quota in '$LOCATION' for model '$MODEL'..."

check_quota "$LOCATION"
primary_status=$?

if [[ $primary_status -eq 1 ]]; then
  primary_entry="${ALL_RESULTS[0]}"
  IFS='|' read -r _ limit used available <<< "$primary_entry"
  echo -e "\n⚠️  Insufficient quota in '$LOCATION' (Available: $available, Required: $CAPACITY). Checking fallback regions..."
fi

for region in "${ALL_REGIONS[@]}"; do
  [[ "$region" == "$LOCATION" ]] && continue
  check_quota "$region"
  [[ $? -eq 0 ]] && FALLBACK_RESULTS+=("$region")
done

# -------------------- Quota Table Output --------------------
echo ""
printf "%-5s | %-16s | %-33s | %-6s | %-6s | %-9s\n" "No." "Region" "Model Name" "Limit" "Used" "Available"
printf -- "---------------------------------------------------------------------------------------------\n"

index=1
REGIONS_WITH_QUOTA=()
for result in "${ALL_RESULTS[@]}"; do
  IFS='|' read -r region limit used available <<< "$result"
  if (( available >= 50 )); then
    printf "| %-3s | %-16s | %-33s | %-6s | %-6s | %-9s |\n" "$index" "$region" "OpenAI.$DEPLOYMENT_TYPE.$MODEL" "$limit" "$used" "$available"
    REGIONS_WITH_QUOTA+=("$region|$available")
    ((index++))
  fi
done
printf -- "---------------------------------------------------------------------------------------------\n"

# -------------------- Prompt if No Region Has Enough --------------------
if [[ $primary_status -ne 0 && ${#FALLBACK_RESULTS[@]} -eq 0 ]]; then
  echo -e "\n❌ No region has sufficient quota (≥ $CAPACITY tokens)."

  max_available=0; max_region=""
  for result in "${ALL_RESULTS[@]}"; do
    IFS='|' read -r region limit used available <<< "$result"
    if (( available > max_available )); then
      max_available=$available
      max_region=$region
    fi
  done

  if (( max_available == 0 )); then
    echo "⚠️ No quota info from any region. Cannot proceed."
    exit 1
  fi

  echo "➡️ Highest available quota: $max_available tokens in '$max_region'."
  echo -n "❓ Enter new capacity to use (<= $max_available): "
  read -r new_capacity < /dev/tty

  if ! [[ "$new_capacity" =~ ^[0-9]+$ ]] || (( new_capacity > max_available )) || (( new_capacity <= 0 )); then
    echo "❌ Invalid capacity entered. Exiting."
    exit 1
  fi

  echo -n "❓ Enter location to use (default: $max_region): "
  read -r new_location < /dev/tty
  new_location="${new_location:-$max_region}"

  CAPACITY=$new_capacity
  LOCATION=$new_location

  check_quota "$LOCATION"
  [[ $? -eq 0 ]] || { echo "❌ Insufficient quota in '$LOCATION'. Exiting."; exit 1; }

  update_env_and_parameters "$LOCATION" "$CAPACITY"
  echo "✅ Deployment settings updated."
  exit 0
fi

# -------------------- Handle Fallback Prompt --------------------
ask_for_location() {
  echo -e "\nPlease choose a region from the above list:"
  echo -n "📍 Enter region: "
  read -r new_location < /dev/tty

  if [[ -z "$new_location" ]]; then
    echo "❌ ERROR: No location entered. Exiting."
    exit 1
  fi

  echo -n "🔢 Enter capacity (tokens): "
  read -r new_capacity < /dev/tty

  if ! [[ "$new_capacity" =~ ^[0-9]+$ ]] || (( new_capacity <= 0 )); then
    echo "❌ Invalid capacity entered."
    ask_for_location
    return
  fi

  CAPACITY=$new_capacity
  LOCATION=$new_location

  check_quota "$LOCATION"
  if [[ $? -eq 0 ]]; then
    update_env_and_parameters "$LOCATION" "$CAPACITY"
    echo "✅ Updated and ready to deploy in '$LOCATION'."
    exit 0
  else
    echo "❌ Insufficient quota in '$LOCATION'. Try another."
    ask_for_location
  fi
}

# -------------------- Final Decision Logic --------------------
if [[ $primary_status -eq 0 ]]; then
  
  if [[ " ${NOT_RECOMMENDED_REGIONS[*]} " == *" $LOCATION "* ]]; then
    recommended_list=$(IFS=, ; echo "${RECOMMENDED_REGIONS[*]}")
    bold_regions=$(printf "\033[1m%s\033[0m" "$recommended_list")
    echo -e "\n⚠️  \033[1mWarning:\033[0m Region '$LOCATION' has available tokens less than the recommended threshold ($RECOMMENDED_TOKENS)."
    echo -e "🚨 Your application may not work as expected due to limited quota."
    echo -e "\nℹ️  Recommended regions (≥ $RECOMMENDED_TOKENS tokens available): $bold_regions"
    echo -e "👉 It's advisable to deploy in one of these regions for optimal app performance."
    
    echo -n "❓ Proceed anyway? (y/n): "
    read -r proceed < /dev/tty
    if [[ "$proceed" =~ ^[Yy]$ ]]; then
      update_env_and_parameters "$LOCATION" "$CAPACITY"
      echo "✅ Proceeding with '$LOCATION'."
      exit 0
    else
      ask_for_location
    fi
  else
    update_env_and_parameters "$LOCATION" "$CAPACITY"
    echo "✅ Quota is sufficient in '$LOCATION'. Proceeding."
    exit 0
  fi
else
  ask_for_location
fi
