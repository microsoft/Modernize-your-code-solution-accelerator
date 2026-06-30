# AGENTS

## Purpose
This repository is an Azure solution accelerator for SQL modernization. It combines a Python backend, a React/Vite frontend, Azure infrastructure deployment via `azd`, and helper scripts for quota and deployment validation.

## High-level structure
- `src/backend/`: FastAPI backend application and Python service code.
- `src/frontend/`: React + Vite frontend UI.
- `infra/`: Bicep and Azure Developer CLI configuration for deployment.
- `scripts/`: deployment and quota-check helper scripts.
- `docs/`: authoritative docs for local development, deployment, authentication, and quota checks.
- `tests/`: E2E test framework and sample tests.

## Key workflows
### Local development
- Backend: `cd src/backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && uvicorn app:app --reload --host 0.0.0.0 --port 8000`
- Frontend: `cd src/frontend && npm install && npm run dev`
- Use separate terminals for backend and frontend.
- Backend and frontend each use their own `.env` file in `src/backend/` and `src/frontend/` respectively.

### Deployment
- Primary deployment mechanism: Azure Developer CLI (`azd`).
- Common commands:
  - `azd init -t microsoft/Modernize-your-Code-Solution-Accelerator/`
  - `azd env new <environment-name>`
  - `azd up`
  - `azd down`
- Quota-related helper: `./scripts/quota_check_params.sh`.

### Testing and linting
- Backend tests: run from `src/backend` with `pytest`. Requires `pytest-asyncio` (in requirements.txt) for async test collection.
- Frontend lint: run from `src/frontend` with `npm run lint`.
- End-to-end tests live in `tests/e2e-test/` and use Playwright + pytest.

## Important conventions
- Use the repository root for top-level docs and deployment instructions.
- Do not assume a single combined service; backend and frontend are separate local services.
- Azure config is managed through `azd env set` and project environment settings.
- The backend initializes AI agents from Azure AI Foundry at startup using `AzureAIAgent`.

## Reference docs
- [Local development setup](./docs/LocalDevelopmentSetup.md)
- [Deployment guide](./docs/DeploymentGuide.md)
- [Azd parameter customization](./docs/CustomizingAzdParameters.md)
- [Quota check instructions](./docs/quota_check.md)

## Notes for AI coding agents
- Prefer linking to existing documentation rather than duplicating detailed deployment/configuration steps.
- Preserve environment-specific behavior: `src/backend` is Python/FastAPI, `src/frontend` is React/Vite.
- Review Azure deployment and quota docs when changing infrastructure or model capacity behavior.
