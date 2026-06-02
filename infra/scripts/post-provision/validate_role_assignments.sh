#!/usr/bin/env bash
set -euo pipefail

resource_group="${1:-}"
assignee="${2:-}"

if [[ -z "$resource_group" ]]; then
  echo "Usage: validate_role_assignments.sh <resource-group> [principal-id-or-upn]" >&2
  exit 1
fi

args=(role assignment list --resource-group "$resource_group" --all)
if [[ -n "$assignee" ]]; then
  args+=(--assignee "$assignee")
fi

az "${args[@]}" --query "[].{role:roleDefinitionName,scope:scope,principalId:principalId,principalType:principalType}" -o table
