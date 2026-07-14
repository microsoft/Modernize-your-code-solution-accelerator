#!/bin/bash
set -euo pipefail

# ---------------------------------------------------------------------------
# ACR Build and Push Script (Bash)
#
# Builds backend/frontend images remotely with az acr build, then updates the
# corresponding Container Apps. Supports:
# 1) azd environment output values (default path)
# 2) explicit resource group discovery (first argument)
#
# For WAF/private ACR deployments, the script temporarily relaxes ACR access
# restrictions and restores them in the EXIT trap.
# ---------------------------------------------------------------------------

RESOURCE_GROUP_INPUT="${1:-}"

echo "============================================================"
echo "ACR Build and Push - Starting..."
echo "============================================================"

if ! command -v az >/dev/null 2>&1; then
  echo "ERROR: Azure CLI ('az') is not installed. Install it from https://aka.ms/azcli" >&2
  exit 1
fi

if ! az account show --output none >/dev/null 2>&1; then
  echo "ERROR: You are not signed in to Azure CLI. Run 'az login' and retry." >&2
  exit 1
fi

get_env_value() {
  for name in "$@"; do
    local value="${!name:-}"
    if [ -z "$value" ]; then
      value=$(azd env get-value "$name" 2>/dev/null || true)
    fi
    if [ -n "$value" ]; then
      printf '%s' "$value"
      return 0
    fi
  done
  printf ''
}

get_apps_from_rg() {
  local rg="$1"
  local backend
  local frontend

  backend=$(az containerapp list --resource-group "$rg" --query "[?contains(name, 'backend')].name | [0]" -o tsv)
  frontend=$(az containerapp list --resource-group "$rg" --query "[?contains(name, 'frontend')].name | [0]" -o tsv)

  if [ -z "$backend" ]; then
    backend=$(az containerapp list --resource-group "$rg" --query "[0].name" -o tsv)
  fi

  if [ -z "$frontend" ]; then
    frontend=$(az containerapp list --resource-group "$rg" --query "[1].name" -o tsv)
  fi

  printf '%s|%s' "$backend" "$frontend"
}

ACR_NAME=""
ACR_ENDPOINT=""
RESOURCE_GROUP=""
BACKEND_APP=""
FRONTEND_APP=""

if [ -z "$RESOURCE_GROUP_INPUT" ]; then
  echo "Using azd environment values..."
  ACR_NAME=$(get_env_value AZURE_CONTAINER_REGISTRY_NAME CONTAINER_REGISTRY_NAME)
  ACR_ENDPOINT=$(get_env_value AZURE_CONTAINER_REGISTRY_ENDPOINT CONTAINER_REGISTRY_LOGIN_SERVER)
  RESOURCE_GROUP=$(get_env_value AZURE_RESOURCE_GROUP)
  BACKEND_APP=$(get_env_value BACKEND_CONTAINER_APP_NAME)
  FRONTEND_APP=$(get_env_value FRONTEND_CONTAINER_APP_NAME)
else
  echo "Using existing deployment from resource group: $RESOURCE_GROUP_INPUT"
  RESOURCE_GROUP="$RESOURCE_GROUP_INPUT"

  ACR_NAME=$(az acr list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv)
  ACR_ENDPOINT=$(az acr list --resource-group "$RESOURCE_GROUP" --query "[0].loginServer" -o tsv)

  if [ -z "$ACR_NAME" ]; then
    echo "ERROR: No Azure Container Registry found in resource group '$RESOURCE_GROUP'." >&2
    exit 1
  fi

  apps=$(get_apps_from_rg "$RESOURCE_GROUP")
  BACKEND_APP="${apps%%|*}"
  FRONTEND_APP="${apps##*|}"
fi

IMAGE_TAG=$(get_env_value AZURE_ENV_IMAGE_TAG)
IMAGE_TAG=${IMAGE_TAG:-latest}

if [ -z "$ACR_ENDPOINT" ] && [ -n "$ACR_NAME" ]; then
  ACR_ENDPOINT="${ACR_NAME}.azurecr.io"
fi

missing=""
[ -z "$ACR_NAME" ] && missing="$missing AZURE_CONTAINER_REGISTRY_NAME"
[ -z "$ACR_ENDPOINT" ] && missing="$missing AZURE_CONTAINER_REGISTRY_ENDPOINT"
[ -z "$RESOURCE_GROUP" ] && missing="$missing AZURE_RESOURCE_GROUP"
[ -z "$BACKEND_APP" ] && missing="$missing BACKEND_CONTAINER_APP_NAME"
[ -z "$FRONTEND_APP" ] && missing="$missing FRONTEND_CONTAINER_APP_NAME"
if [ -n "$missing" ]; then
  echo "ERROR: Missing required values:$missing" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_IMAGE="cmsabackend:${IMAGE_TAG}"
FRONTEND_IMAGE="cmsafrontend:${IMAGE_TAG}"

ACR_PUBLIC_ACCESS=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query "properties.publicNetworkAccess" -o tsv)
ACR_SKU=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query "sku.name" -o tsv)
DEPLOYMENT_TYPE=$(az group show --name "$RESOURCE_GROUP" --query "tags.Type" -o tsv 2>/dev/null || true)

IS_WAF_DEPLOYMENT=false
if [ "$DEPLOYMENT_TYPE" = "WAF" ] || [ "$ACR_PUBLIC_ACCESS" = "Disabled" ]; then
  IS_WAF_DEPLOYMENT=true
fi

echo ""
echo "  ACR Name: $ACR_NAME"
echo "  ACR Login Server: $ACR_ENDPOINT"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Backend App: $BACKEND_APP"
echo "  Frontend App: $FRONTEND_APP"
echo "  Image Tag: $IMAGE_TAG"
echo "  ACR SKU: $ACR_SKU"
echo "  ACR Public Access: $ACR_PUBLIC_ACCESS"
echo ""

cleanup() {
  if [ "$IS_WAF_DEPLOYMENT" = true ]; then
    echo ""
    echo "Restoring WAF/private ACR configuration..."

    if [ "$ACR_SKU" = "Premium" ]; then
      az acr update --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --default-action Deny --output none >/dev/null 2>&1 || true
    fi

    az acr update --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --public-network-enabled false --output none >/dev/null 2>&1 || true
    az acr update --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --allow-exports false --output none >/dev/null 2>&1 || true

    echo "ACR configuration restored."
  fi
}
trap cleanup EXIT

if [ "$IS_WAF_DEPLOYMENT" = true ]; then
  echo "WAF/private deployment detected. Temporarily relaxing ACR restrictions..."

  az acr update --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --allow-exports true --output none
  az acr update --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --public-network-enabled true --output none
  if [ "$ACR_SKU" = "Premium" ]; then
    az acr update --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --default-action Allow --output none
  fi

  max_retries=30
  for ((i=0; i<max_retries; i++)); do
    status=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query "properties.publicNetworkAccess" -o tsv 2>/dev/null || echo "")
    if [ "$status" = "Enabled" ]; then
      break
    fi
    sleep 1
  done
fi

echo "==> Ensuring the Microsoft.App resource provider is registered"
az provider register --namespace Microsoft.App --wait

echo "==> Verifying ACR '$ACR_NAME' connectivity"
acr_reachable=false
for ((i=0; i<5; i++)); do
  if az acr repository list --name "$ACR_NAME" --output none >/dev/null 2>&1; then
    acr_reachable=true
    break
  fi
  sleep 3
done
if [ "$acr_reachable" != true ]; then
  echo "ERROR: ACR '$ACR_NAME' is not reachable. Check network rules and access permissions." >&2
  exit 1
fi

echo "============================================================"
echo "Step 1: Building and pushing images to ACR..."
echo "============================================================"

echo "  Building $BACKEND_IMAGE"
az acr build \
  --registry "$ACR_NAME" \
  --image "$BACKEND_IMAGE" \
  --file "$REPO_ROOT/src/backend/Dockerfile" \
  "$REPO_ROOT/src/backend"

echo "  Building $FRONTEND_IMAGE"
az acr build \
  --registry "$ACR_NAME" \
  --image "$FRONTEND_IMAGE" \
  --file "$REPO_ROOT/src/frontend/Dockerfile" \
  "$REPO_ROOT/src/frontend"

echo ""
echo "============================================================"
echo "Step 2: Updating Container Apps with new images..."
echo "============================================================"

echo "  Updating $BACKEND_APP"
az containerapp update \
  --name "$BACKEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --image "${ACR_ENDPOINT}/${BACKEND_IMAGE}" \
  --output none

echo "  Updating $FRONTEND_APP"
az containerapp update \
  --name "$FRONTEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --image "${ACR_ENDPOINT}/${FRONTEND_IMAGE}" \
  --output none

echo ""
echo "============================================================"
echo "ACR Build and Push - Completed Successfully!"
echo "============================================================"
