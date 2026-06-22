# Build Bicep -> ARM

This repo ships both `main.bicep` (authoring source) and `main.json` (compiled
ARM template) for each deployable root template. After editing any `.bicep`
file you must regenerate the corresponding `.json` so the two stay in sync.

## Prerequisites

- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) `>= 2.55`
- Bicep CLI: `az bicep install` or `az bicep upgrade`

## Top-level templates

```bash
# From the repository root
az bicep build --file infra/main.bicep
az bicep build --file infra/main_custom.bicep
```

## Sub-folder templates

The `infra/bicep/` folder mirrors the top-level templates (the "custom Bicep"
implementation kept side-by-side with future AVM templates under
`infra/avm/`).

```bash
az bicep build --file infra/bicep/main.bicep
az bicep build --file infra/bicep/main_custom.bicep
```

When the AVM rewrite under `infra/avm/` is added, build it the same way:

```bash
az bicep build --file infra/avm/main.bicep
```

## Validation

```bash
# What-if against an existing resource group
az deployment group what-if \
  --resource-group <rg-name> \
  --template-file infra/main.bicep \
  --parameters @infra/main.parameters.json
```

## Notes

- The compiled `main.json` files are committed because some downstream tooling
  (e.g. portal "Deploy to Azure" buttons, Azure DevOps `AzureResourceManagerTemplateDeployment@3`
  tasks) prefer ARM JSON.
- Do not hand-edit `main.json` &mdash; always edit the Bicep source and
  regenerate.
