# Infra Scripts

This folder mirrors the reference solution accelerator script layout.

## Structure

- `build`: local Bicep build helpers
- `pre-provision`: quota and model validation helpers
- `post-provision`: deployment verification helpers
- `utilities`: shared utility scripts

The scripts in this folder are lightweight wrappers around the repository's existing root-level scripts so existing workflows keep working while the infra layout follows the standardized pattern.
