# AVM Flavor

This folder contains AVM-oriented entrypoint templates for the Content Processing accelerator.

## Guidance

- Keep core modules in `../modules` unchanged.
- Apply GSA-specific behavior changes in `main.bicep` and `main_custom.bicep` parameters and orchestration only.
- If a core module change is required, raise a change request to the designated module owners.

## Files

- `main.bicep`: AVM deployment entrypoint.
- `main_custom.bicep`: AVM custom/local deployment entrypoint.
