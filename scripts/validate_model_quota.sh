#!/bin/bash

LOCATION=""
MODEL=""
DEPLOYMENT_TYPE="Standard"
CAPACITY=0
RECOMMENDED_TOKENS=200
TABLE_SHOWN=false
RECOMMENDATIONS_SHOWN=false

ALL_REGIONS=('australiaeast' 'eastus' 'eastus2' 'francecentral' 'japaneast' 'norwayeast' 'southindia' 'swedencentral' 'uksouth' 'westus' 'westus3')

RECOMMENDED_REGIONS=()
NOT_RECOMMENDED_REGIONS=()
ALL_RESULTS=()
FALLBACK_RESULTS=()

# ---------- Helper Functions ----------

prompt_yes_no() {
  local prompt="$1"
  local response
  echo -n "$prompt"
  read -r response < /dev/tty
  while [[ ! "$response" =~ ^[YyNn]$ ]]; do
    echo "❌ Invalid input. Please enter 'y' or 'n': "
    read -r response < /dev/tty
  done
  [[ "$response" =~ ^[Yy]$ ]]
}

print_recommended_warning() {
  local capacity="$1"
  local recommended_list
  recommended_list=$(IFS=, ; echo "${RECOMMENDED_REGIONS[*]}")
  echo -e "\n⚠️  You have entered a capacity of $capacity, which is less than the recommended minimum ($RECOMMENDED_TOKENS)."
  echo -e "🚨 This may cause performance issues or unexpected behavior."
  echo -e "ℹ️  Recommended regions (≥ $RECOMMENDED_TOKENS tokens available): $recommended_list"
}

update_env_and_parameters() {
  local new_location="$1"
  local new_capacity="$2"
  echo "➡️  Updating environment and parameters with Location='$new_location' and Capacity='$new_capacity'..."

  azd env set AZURE_AISERVICE_LOCATION "$new_location"
  azd env set AZURE_ENV_MODEL_CAPACITY "$new_capacity"

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

check_quota() {
  local region="$1"
  local MODEL_TYPE="OpenAI.$DEPLOYMENT_TYPE.$MODEL"
  local output

  output=$(az cognitiveservices usage list --location "$region" --query "[?name.value=='$MODEL_TYPE']" --output json 2>/dev/null)

  if [[ -z "$output" || "$output" == "[]" ]]; then
    [[ "$region" == "$LOCATION" ]] && echo "⚠️ Could not retrieve the quota info for the region: $LOCATION"
    return 2
  fi

  local CURRENT_VALUE=$(echo "$output" | jq -r '.[0].currentValue // 0' | cut -d'.' -f1)
  local LIMIT=$(echo "$output" | jq -r '.[0].limit // 0' | cut -d'.' -f1)
  local AVAILABLE=$((LIMIT - CURRENT_VALUE))

  ALL_RESULTS+=("$region|$LIMIT|$CURRENT_VALUE|$AVAILABLE")

  if (( AVAILABLE >= RECOMMENDED_TOKENS )); then
    [[ ! " ${RECOMMENDED_REGIONS[*]} " =~ " $region " ]] && RECOMMENDED_REGIONS+=("$region")
  else
    [[ ! " ${NOT_RECOMMENDED_REGIONS[*]} " =~ " $region " ]] && NOT_RECOMMENDED_REGIONS+=("$region")
  fi

  (( AVAILABLE >= CAPACITY ))
}

show_table() {
  echo -e "\n--------------------------------------------------------------------------------------------------"
  echo -e "| No. | Region          | Model Name                          | Limit | Used  | Available |"
  echo -e "--------------------------------------------------------------------------------------------------"
  local index=1
  for result in "${ALL_RESULTS[@]}"; do
    IFS='|' read -r region limit used available <<< "$result"
    if (( available >= 50 )); then
      printf "| %-3s | %-16s | %-33s | %-6s | %-6s | %-9s |\n" "$index" "$region" "OpenAI.$DEPLOYMENT_TYPE.$MODEL" "$limit" "$used" "$available"
      ((index++))
    fi
  done
  echo -e "--------------------------------------------------------------------------------------------------"
}

ask_for_location() {
  echo -e "\nPlease choose a region from the above list:"
  echo -n "📍 Enter region: "
  read -r new_location < /dev/tty

  [[ -z "$new_location" ]] && echo "❌ ERROR: No location entered. Exiting." && exit 1

  echo -n "🔢 Enter capacity (tokens): "
  read -r new_capacity < /dev/tty

  if ! [[ "$new_capacity" =~ ^[0-9]+$ ]] || (( new_capacity <= 0 )); then
    echo "❌ Invalid capacity entered."
    ask_for_location
    return
  fi

  if (( new_capacity < RECOMMENDED_TOKENS )); then
    print_recommended_warning "$new_capacity"
    prompt_yes_no "❓ Proceed anyway? (y/n): " || { ask_for_location; return; }
  fi

  echo -e "\n🔍 Checking quota in region '$new_location' for requested capacity: $new_capacity..."
  CAPACITY=$new_capacity
  LOCATION=$new_location

  if check_quota "$LOCATION"; then
    if (( CAPACITY < RECOMMENDED_TOKENS )); then
      print_recommended_warning "$CAPACITY"
      prompt_yes_no "❓ Proceed anyway? (y/n): " || { ask_for_location; exit 0; }
    fi
    update_env_and_parameters "$LOCATION" "$CAPACITY"
    echo "✅ Proceeding with deployment in '$LOCATION'."
    exit 0
  else
    check_fallback_regions
  fi
}

check_fallback_regions() {
  for region in "${ALL_REGIONS[@]}"; do
    [[ "$region" == "$LOCATION" ]] && continue
    check_quota "$region" && FALLBACK_RESULTS+=("$region")
  done

  if [[ "$TABLE_SHOWN" == false ]]; then
    show_table
    TABLE_SHOWN=true
  fi

  if [[ ${#FALLBACK_RESULTS[@]} -gt 0 ]]; then
    echo -e "\n➡️  Found fallback regions with sufficient quota."
    if [[ ${#RECOMMENDED_REGIONS[@]} -gt 0 ]]; then
      echo -e "\nℹ️  Recommended regions (≥ $RECOMMENDED_TOKENS tokens available):"
      for region in "${RECOMMENDED_REGIONS[@]}"; do
        echo "  - $region"
      done
    fi
    echo -e "\n❗ The originally selected region '$LOCATION' does not have enough quota."
    echo -e "👉 You can manually choose one of the recommended fallback regions for deployment."
    RECOMMENDATIONS_SHOWN=true
  else
    echo -e "\n❌ ERROR: No region has sufficient quota."
  fi

  prompt_yes_no "❓ Would you like to retry with a different region? (y/n): " && ask_for_location || {
    echo "Exiting... No region with sufficient quota."
    exit 1
  }
}

# ---------- Parse Inputs ----------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --location) LOCATION="$2"; shift ;;
    --model) MODEL="$2"; shift ;;
    --deployment-type) DEPLOYMENT_TYPE="$2"; shift ;;
    --capacity) CAPACITY="$2"; shift ;;
    *) echo "❌ Unknown option: $1"; exit 1 ;;
  esac
  shift
done

# ---------- Validate Inputs ----------
if [[ -z "$LOCATION" || -z "$MODEL" || -z "$CAPACITY" || "$CAPACITY" -le 0 ]]; then
  echo "❌ Missing required parameters. Usage: $0 --location <LOCATION> --model <MODEL> --capacity <CAPACITY>"
  exit 1
fi

# ---------- Start Process ----------
echo -e "\n🔍 Checking quota in the requested region '$LOCATION'..."
if check_quota "$LOCATION"; then
  if (( CAPACITY < RECOMMENDED_TOKENS )); then
    print_recommended_warning "$CAPACITY"
    prompt_yes_no "❓ Proceed anyway? (y/n): " || {
      ask_for_location
      exit 0
    }
  fi
  update_env_and_parameters "$LOCATION" "$CAPACITY"
  echo "✅ Proceeding with deployment in '$LOCATION'."
  exit 0
else
  primary_entry="${ALL_RESULTS[0]}"
  IFS='|' read -r _ limit used available <<< "$primary_entry"
  echo "❌ Quota insufficient in '$LOCATION' (Available: $available, Required: $CAPACITY). Checking fallback regions..."
  check_fallback_regions
fi