# Build Infra Bicep

Use these commands from repository root:

- Build top-level entrypoint:
  - `az bicep build --file infra/main.bicep --outdir infra`
- Build AVM flavor entrypoint:
  - `az bicep build --file infra/avm/main.bicep --outdir infra/avm`
- Build classic bicep flavor entrypoint:
  - `az bicep build --file infra/bicep/main.bicep --outdir infra/bicep`

Optional custom entrypoints:

- `az bicep build --file infra/main_custom.bicep --outdir infra`
- `az bicep build --file infra/avm/main_custom.bicep --outdir infra/avm`
- `az bicep build --file infra/bicep/main_custom.bicep --outdir infra/bicep`
