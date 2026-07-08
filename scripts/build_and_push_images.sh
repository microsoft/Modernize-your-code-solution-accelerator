#!/bin/bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Post-provision hook
#
# Builds the backend and frontend container images remotely inside the
# deployment's Azure Container Registry (ACR) using 'az acr build' (no local
# Docker required) and then updates the container apps to run the freshly
# built images.
#
# The required values are provided by azd as environment variables (they are
# outputs of infra/main.bicep). When the script is run outside of an azd hook
# the values are read back with 'azd env get-value'.
# ---------------------------------------------------------------------------

echo "==> Post-provision: building and pushing application images to ACR"

# Ensure the Azure CLI is available and authenticated (az acr build / containerapp
# update use the az CLI, which authenticates independently from azd).
if ! command -v az >/dev/null 2>&1; then
  echo "ERROR: Azure CLI ('az') is not installed. Install it from https://aka.ms/azcli" >&2
  exit 1
fi
if ! az account show >/dev/null 2>&1; then
  echo "ERROR: You are not signed in to the Azure CLI. Run 'az login' and retry." >&2
  exit 1
fi

# Reads an environment variable, falling back to the azd environment.
load_env_var() {
  local name="$1"
  local value="${!name:-}"
  if [ -z "$value" ]; then
    value=$(azd env get-value "$name" 2>/dev/null || true)
  fi
  printf '%s' "$value"
}

ACR_NAME=$(load_env_var AZURE_CONTAINER_REGISTRY_NAME)
ACR_ENDPOINT=$(load_env_var AZURE_CONTAINER_REGISTRY_ENDPOINT)
RESOURCE_GROUP=$(load_env_var AZURE_RESOURCE_GROUP)
BACKEND_APP=$(load_env_var BACKEND_CONTAINER_APP_NAME)
FRONTEND_APP=$(load_env_var FRONTEND_CONTAINER_APP_NAME)
IMAGE_TAG=$(load_env_var AZURE_ENV_IMAGE_TAG)
IMAGE_TAG=${IMAGE_TAG:-latest}

# Derive the login server from the registry name if the output was not available.
if [ -z "$ACR_ENDPOINT" ] && [ -n "$ACR_NAME" ]; then
  ACR_ENDPOINT="${ACR_NAME}.azurecr.io"
fi

missing=""
[ -z "$ACR_NAME" ] && missing="$missing AZURE_CONTAINER_REGISTRY_NAME"
[ -z "$RESOURCE_GROUP" ] && missing="$missing AZURE_RESOURCE_GROUP"
[ -z "$BACKEND_APP" ] && missing="$missing BACKEND_CONTAINER_APP_NAME"
[ -z "$FRONTEND_APP" ] && missing="$missing FRONTEND_CONTAINER_APP_NAME"
if [ -n "$missing" ]; then
  echo "ERROR: Missing required environment values:$missing" >&2
  exit 1
fi

get_acr_public_network_access() {
  az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query "publicNetworkAccess" -o tsv 2>/dev/null || true
}

set_acr_public_network_access() {
  local mode="$1"
  echo "==> Setting ACR public network access to $mode"
  az acr update --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --public-network-access "$mode"
}

ORIGINAL_ACR_PUBLIC_ACCESS=$(get_acr_public_network_access)
ACR_PUBLIC_ACCESS_REVERT=false
if [ "$ORIGINAL_ACR_PUBLIC_ACCESS" = "Disabled" ]; then
  set_acr_public_network_access "Enabled"
  ACR_PUBLIC_ACCESS_REVERT=true
fi

cleanup() {
  if [ "$ACR_PUBLIC_ACCESS_REVERT" = true ]; then
    echo "==> Restoring ACR public network access to Disabled"
    set_acr_public_network_access "Disabled"
  fi
}
trap cleanup EXIT

# Resolve the repository root (this script lives in <repo>/scripts).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

BACKEND_IMAGE="cmsabackend:${IMAGE_TAG}"
FRONTEND_IMAGE="cmsafrontend:${IMAGE_TAG}"

# Ensure the Microsoft.App resource provider is registered before updating the
# container apps. ARM registration can still be propagating after provisioning,
# which makes 'az containerapp update' fail with a "not registered" error.
echo "==> Ensuring the Microsoft.App resource provider is registered"
az provider register --namespace Microsoft.App --wait

echo "==> Building backend image ($BACKEND_IMAGE) in ACR '$ACR_NAME'"
az acr build \
  --registry "$ACR_NAME" \
  --image "$BACKEND_IMAGE" \
  --file "$REPO_ROOT/src/backend/Dockerfile" \
  "$REPO_ROOT/src/backend"

echo "==> Building frontend image ($FRONTEND_IMAGE) in ACR '$ACR_NAME'"
az acr build \
  --registry "$ACR_NAME" \
  --image "$FRONTEND_IMAGE" \
  --file "$REPO_ROOT/src/frontend/Dockerfile" \
  "$REPO_ROOT/src/frontend"

echo "==> Updating backend container app '$BACKEND_APP'"
az containerapp update \
  --name "$BACKEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --image "${ACR_ENDPOINT}/${BACKEND_IMAGE}" \
  --output none

echo "==> Updating frontend container app '$FRONTEND_APP'"
az containerapp update \
  --name "$FRONTEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --image "${ACR_ENDPOINT}/${FRONTEND_IMAGE}" \
  --output none

echo "==> Done. Container apps are now running the freshly built images."
