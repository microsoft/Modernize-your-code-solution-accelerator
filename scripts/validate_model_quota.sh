#!/bin/bash

LOCATION=""
MODEL=""
DEPLOYMENT_TYPE="Standard"
CAPACITY=0
RECOMMENDED_TOKENS=350
TABLE_SHOWN=false
RECOMMENDATIONS_SHOWN=false
INITIAL_LOCATION=""

ALL_REGIONS=('australiaeast' 'eastus' 'eastus2' 'francecentral' 'japaneast' 'norwayeast' 'southindia' 'swedencentral' 'uksouth' 'westus' 'westus3')

RECOMMENDED_REGIONS=()
NOT_RECOMMENDED_REGIONS=()
ALL_RESULTS=()
FALLBACK_RESULTS=()


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

  # if [[ "$region" == "$LOCATION" ]]; then
  available=$AVAILABLE
  # fi

  if (( AVAILABLE >= RECOMMENDED_TOKENS )); then
    [[ ! " ${RECOMMENDED_REGIONS[*]} " =~ " $region " ]] && RECOMMENDED_REGIONS+=("$region")
  else
    [[ ! " ${NOT_RECOMMENDED_REGIONS[*]} " =~ " $region " ]] && NOT_RECOMMENDED_REGIONS+=("$region")
  fi
  
  (( AVAILABLE >= CAPACITY ))
}

print_recommended_warning() {
  local location="$1"
  local capacity="$2"
  local matched_entry=""

  for entry in "${ALL_RESULTS[@]}"; do
    IFS='|' read -r region _ _ _ <<< "$entry"
    if [[ "$region" == "$location" ]]; then
      matched_entry="$entry"
      break
    fi
  done

  if [[ -n "$matched_entry" ]]; then
    IFS='|' read -r _ limit used available <<< "$matched_entry"
    echo -e "\n📊 Available quota in \e[1m$location\e[0m: \e[1m$available\e[0m | Required for deployment: \e[1m$capacity\e[0m | Recommended for optimal performance: \e[1m$RECOMMENDED_TOKENS\e[0m"
    if (( available < RECOMMENDED_TOKENS )); then
      echo -e "\n⚠️  \033[1mWarning:\033[0m Region \e[1m$location\e[0m has available tokens less than the recommended threshold \e[1m$RECOMMENDED_TOKENS\e[0m."
      echo "🚨 Your application may not work as expected due to limited quota."
      echo -e "\nChecking other regions: \033[1m$(IFS=, ; echo "${ALL_REGIONS[*]}")\033[0m..."

      check_fallback_regions
    else
      echo -e "ℹ️  Sufficient quota available for deployment and optimal performance."
      if (( capacity < RECOMMENDED_TOKENS )); then
        echo -e "\n⚠️  Capacity is set to $capacity (default $CAPACITY), which may impact performance. This region has enough recommended tokens."
        prompt_yes_no "❓ Do you want to update the token size or location to recommended? (y/n): " && {
          ask_for_location
          return 1
        }
      fi
    fi
  else
    echo -e "\n⚠️  Capacity entered is below recommended, but region quota data was not found."
  fi

  if [[ ${#RECOMMENDED_REGIONS[@]} -gt 0 ]]; then
    if [[ ${#RECOMMENDED_REGIONS[@]} -eq 1 && "${RECOMMENDED_REGIONS[0]}" == "$location" ]]; then
    # Only one recommended region and it's the same as current location; skip showing
    :
    else
      local recommended_list
      recommended_list=$(IFS=, ; echo "${RECOMMENDED_REGIONS[*]}")
      echo -e "ℹ️  Regions with sufficient tokens (\e[1m≥ $RECOMMENDED_TOKENS\e[0m ) for optimal performance: \033[1m$recommended_list\033[0m"
      echo  
    fi
  fi
}

ask_for_location() {
  echo -n "📍 Enter region: "
  read -r new_location < /dev/tty

 # Reject empty or numeric-only input
  if [[ -z "$new_location" || "$new_location" =~ ^[0-9]+$ ]]; then
    echo "❌ ERROR: Invalid region entered. Region cannot be empty or contain only numbers. Please enter again."
    ask_for_location
    return
  fi

  echo -n "🔢 Enter capacity (tokens): "
  read -r new_capacity < /dev/tty

  if ! [[ "$new_capacity" =~ ^[0-9]+$ ]] || (( new_capacity <= 0 )); then
    echo "❌ Invalid capacity entered. Capacity cannot be characters. Please enter again."
    ask_for_location
    return
  fi

  local requested_location="$new_location"
  local requested_capacity="$new_capacity"

  # LOCATION="$new_location"
  # CAPACITY="$new_capacity"

  echo -e "\n🔍 Checking quota in region '$requested_location' for requested capacity: $requested_capacity..."

  if check_quota "$requested_location"; then
    if (( requested_capacity < RECOMMENDED_TOKENS )); then
      print_recommended_warning "$requested_location" "$requested_capacity" || exit 0
      prompt_yes_no "❓ Proceed anyway with $requested_capacity tokens? (y/n): " || {
        ask_for_location
      }
    fi

    if (( available < requested_capacity )); then
      echo -e "❌ Region '\033[1m$requested_location\033[0m' does not have sufficient quota for \033[1m$requested_capacity\033[0m tokens."
      if prompt_yes_no "❓ Do you want to check for other regions with sufficient quota? (y/n): "; then
        echo -e "ℹ️  Checking other regions for sufficient quota..."
        check_fallback_regions
        return
      fi
    else
      LOCATION="$requested_location"
      CAPACITY="$requested_capacity"
    fi

    
    
    prompt_yes_no "❓ Do you want to proceed with deployment in '$LOCATION'? for AI Services (y/n): " || {
      ask_for_location
      return
    }
    
    update_env_and_parameters "$LOCATION" "$CAPACITY"
    echo -e "✅ Proceeding with deployment in \033[1m$LOCATION\033[0m for AI Services with capacity \033[1m$CAPACITY\033[0m tokens."
    exit 0
  else
    echo -e "\n❌ Quota insufficient in \033[1m$requested_location\033[0m (Available: \033[1m$available\033[0m, Required: \033[1m$requested_capacity\033[0m). \n Checking other regions: \033[1m$(IFS=, ; echo "${ALL_REGIONS[*]}")\033[0m..."
    check_fallback_regions
  fi
}

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

update_env_and_parameters() {
  local new_location="$1"
  local new_capacity="$2"

   # Get current environment values
  local current_location
  local current_capacity

  current_location=$(azd env get-values --output json | jq -r '.AZURE_AISERVICE_LOCATION // empty')
  current_capacity=$(azd env get-values --output json | jq -r '.AZURE_ENV_MODEL_CAPACITY // empty')

   # Check if update is needed
  if [[ "$new_location" == "$current_location" && "$new_capacity" == "$current_capacity" ]]; then
    echo "ℹ️  No changes detected in location or capacity. Skipping environment and parameter update."
    return 0
  fi

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
}

show_table() {
  local index=1
  local printed_any=0

  for result in "${ALL_RESULTS[@]}"; do
    IFS='|' read -r region limit used available <<< "$result"
    if (( available >= CAPACITY ))  && [[ -z "${printed_regions[$region]}" ]]; then
      if (( printed_any == 0 )); then
        echo -e "\n\e[1mBelow is the list of regions with their quota information which have minimum quota for the deployment:\e[0m"
        echo -e "--------------------------------------------------------------------------------------------------"
        echo -e "| No. | Region          | Model Name                          | Limit | Used  | Available |"
        echo -e "--------------------------------------------------------------------------------------------------"
         printed_any=1
      fi
      printf "| %-3s | %-16s | %-33s | %-6s | %-6s | %-9s |\n" "$index" "$region" "OpenAI.$DEPLOYMENT_TYPE.$MODEL" "$limit" "$used" "$available"
      ((index++))
    fi
  done
  if (( printed_any == 1 )); then
    echo -e "--------------------------------------------------------------------------------------------------"
  fi
}

check_fallback_regions() {
  for region in "${ALL_REGIONS[@]}"; do
    [[ "$region" == "$LOCATION" ]] && continue
    check_quota "$region" && FALLBACK_RESULTS+=("$region")
  done

  if [[ ${#FALLBACK_RESULTS[@]} -gt 0 ]]; then
    echo -e "\n➡️  Found other regions with sufficient quota."
    if [[ "$TABLE_SHOWN" == false ]]; then
      show_table
      TABLE_SHOWN=true
    fi

    if [[ ${#RECOMMENDED_REGIONS[@]} -gt 0 ]]; then
      echo -e "ℹ️  Regions with sufficient tokens (≥ $RECOMMENDED_TOKENS) for optimal performance: \033[1m$recommended_list\033[0m"
      for region in "${RECOMMENDED_REGIONS[@]}"; do
        echo "  - $region"
      done
      echo

      if prompt_yes_no "❓ Do you want to proceed by selecting one of these regions? (y/n): "; then
        ask_for_location
      else
        check_quota "$LOCATION"
        if (( available < CAPACITY )); then
          echo -e "⚠️  The selected region '\033[1m$LOCATION\033[0m' has only \033[1m$available\033[0m quota, but \033[1m$CAPACITY\033[0m is required."
          echo -e "\033[1m⚠️  Proceeding may result in deployment failure due to insufficient quota.\033[0m"

          if ! prompt_yes_no "❓ Do you still want to proceed with deployment in '$LOCATION'? (y/n): "; then
            echo "ℹ️  Please select another region with sufficient quota."
            ask_for_location
          else
            print_recommended_warning "$LOCATION" "$available" || exit 0
            echo -e "✅ Proceeding with deployment in \033[1m$LOCATION\033[0m for AI Services with capacity \033[1m$CAPACITY\033[0m."
            update_env_and_parameters "$LOCATION" "$CAPACITY"
            exit 0
          fi
        else
          echo -e "✅ Proceeding with deployment in \033[1m$LOCATION\033[0m for AI Services with capacity \033[1m$CAPACITY\033[0m."
          update_env_and_parameters "$LOCATION" "$CAPACITY"
          exit 0
        fi
      fi
    fi
  else
    echo -e "\n❌ ERROR: No region has sufficient quota for the required deployment."
    return 1
  fi
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
INITIAL_LOCATION="$LOCATION"

echo -e "🔍 Checking quota in the requested region \e[1m$LOCATION\e[0m with capacity \e[1m$CAPACITY\e[0m tokens..."

if check_quota "$LOCATION"; then
  if (( CAPACITY < RECOMMENDED_TOKENS )); then
    print_recommended_warning "$LOCATION" "$CAPACITY"
    prompt_yes_no "❓ Proceed anyway? (y/n): " || {
      ask_for_location
      exit 0
    }
   else
    echo -e "✅ Region \033[1m$LOCATION\033[0m has sufficient tokens \033[1m$CAPACITY\033[0m and meets the recommended threshold \033[1m$RECOMMENDED_TOKENS\033[0m tokens.\n🚀 Suitable for deployment and optimal application performance."
  fi

  update_env_and_parameters "$LOCATION" "$CAPACITY"
  echo -e "✅ Proceeding with deployment in \033[1m$LOCATION\033[0m for AI Services with capacity \033[1m$CAPACITY\033[0m."
  exit 0
else
  primary_entry="${ALL_RESULTS[0]}"
  IFS='|' read -r _ limit used available <<< "$primary_entry"
  echo -e "\n❌ Quota insufficient in '\033[1m$LOCATION\033[0m' (Available: \033[1m$available\033[0m, Required: \033[1m$CAPACITY\033[0m). \n Checking other regions: \033[1m$(IFS=, ; echo "${ALL_REGIONS[*]}")\033[0m..."
  check_fallback_regions
fi