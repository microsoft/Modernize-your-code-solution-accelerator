# Guide to Local Development

This guide provides step-by-step instructions for setting up and running the **Modernize your code solution accelerator** locally for development and testing purposes.

## Requirements

Before you begin, ensure you have the following tools installed:

• **Python 3.9 or higher** + PIP  
• **Node.js 18+** and npm  
• **Azure CLI** and an Azure Subscription  
• **Docker Desktop** (optional, for containerized development)  
• **Visual Studio Code IDE** (recommended)  
• **Git** for version control  

## Local Setup

**Note for macOS Developers:** If you are using macOS on Apple Silicon (ARM64), you may experience compatibility issues with some Azure services. We recommend testing thoroughly and using alternative approaches if needed.

The easiest way to run this accelerator is in a VS Code Dev Container, which will open the project in your local VS Code using the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers):

1. **Start Docker Desktop** (install it if not already installed)
2. **Open the project:** [Open in Dev Containers](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/microsoft/Modernize-your-code-solution-accelerator)
3. In the VS Code window that opens, once the project files show up (this may take several minutes), open a terminal window

## Detailed Development Container Setup Instructions

The solution contains a [development container](https://code.visualstudio.com/docs/remote/containers) with all the required tooling to develop and deploy the accelerator. To deploy the Modernize your code Solution Accelerator using the provided development container you will also need:

• [Visual Studio Code](https://code.visualstudio.com/)  
• [Remote containers extension for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

If you are running this on Windows, we recommend you clone this repository in [WSL](https://code.visualstudio.com/docs/remote/wsl):

```bash
git clone https://github.com/microsoft/Modernize-your-code-solution-accelerator
```

Open the cloned repository in Visual Studio Code and connect to the development container:

```bash
code .
```

!!! tip 
    Visual Studio Code should recognize the available development container and ask you to open the folder using it. For additional details on connecting to remote containers, please see the [Open an existing folder in a container](https://code.visualstudio.com/docs/remote/containers#_quick-start-open-an-existing-folder-in-a-container) quickstart.

When you start the development container for the first time, the container will be built. This usually takes a few minutes. Please use the development container for all further steps.

The files for the dev container are located in `/.devcontainer/` folder.

## Local Deployment and Debugging

### 1. Clone the Repository

```bash
git clone https://github.com/microsoft/Modernize-your-code-solution-accelerator
cd Modernize-your-code-solution-accelerator
```

### 2. Log into the Azure CLI

• Check your login status using:
```bash
az account show
```

• If not logged in, use:
```bash
az login
```

• To specify a tenant, use:
```bash
az login --tenant <tenant_id>
```

### 3. Create a Resource Group

You can create it either through the Azure Portal or the Azure CLI:

```bash
az group create --name <resource-group-name> --location eastus
```

### 4. Deploy the Infrastructure

You can use the Azure Developer CLI (recommended) or deploy the Bicep template directly:

#### Option A: Using Azure Developer CLI (Recommended)

```bash
# Initialize the environment
azd env new <environment-name>

# Deploy the infrastructure and application
azd up
```

#### Option B: Using Azure CLI with Bicep

```bash
az deployment group create -g <resource-group-name> -f infra/main.bicep --query 'properties.outputs'
```

**Note:** You will be prompted for various parameters including:
- **principalId**: The ObjectID of your user in Entra ID. To find it, use:
  ```bash
  az ad signed-in-user show --query id -o tsv
  ```
- **Azure AI Service Location**: Choose from supported regions (eastus, japaneast, etc.)
- **Solution Name**: A unique name for your deployment

### 5. Configure Role Assignments

The Bicep deployment includes the assignment of appropriate roles. If you need to add additional permissions for local development, use these commands:

```bash
# Cosmos DB permissions
az cosmosdb sql role assignment create \
  --resource-group <resource-group-name> \
  --account-name <cosmos-db-account-name> \
  --role-definition-name "Cosmos DB Built-in Data Contributor" \
  --principal-id <aad-user-object-id> \
  --scope /subscriptions/<subscription-id>/resourceGroups/<resource-group-name>/providers/Microsoft.DocumentDB/databaseAccounts/<cosmos-db-account-name>

# Azure OpenAI permissions
az role assignment create \
  --assignee <aad-user-upn> \
  --role "Cognitive Services OpenAI User" \
  --scope /subscriptions/<subscription-id>/resourceGroups/<resource-group-name>/providers/Microsoft.CognitiveServices/accounts/<azure-openai-name>
```

### 6. Create Environment Files

Navigate to the backend directory and create a `.env` file based on the provided `.env.sample`:

```bash
cd src/backend
cp .env.sample .env
```

Fill in the `.env` file with values from your Azure deployment. You can find these in:
- Azure Portal under "Deployments" in your resource group
- Output from the `azd up` command
- Azure resources directly in the portal

### 7. Set up Virtual Environments (Optional)

If you are using `venv`, create and activate your virtual environment for the backend:

```bash
# Backend setup
cd src/backend
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 8. Install Python Dependencies

In the backend directory with your virtual environment activated:

```bash
pip install -r requirements.txt
```

### 9. Install Frontend Dependencies

In the frontend directory:

```bash
cd src/frontend
npm install
```

### 10. Run the Application

#### Start the Backend API:

From the `src/backend` directory:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

#### Start the Frontend:

In a new terminal from the `src/frontend` directory:

```bash
npm run dev
```

### 11. Access the Application

• **Frontend:** Open a browser and navigate to `http://localhost:3000`  
• **API Documentation:** Navigate to `http://localhost:8000/docs` for Swagger documentation  
• **API Health Check:** Navigate to `http://localhost:8000/health`

## Debugging the Solution Locally

### Backend Debugging

You can debug the API backend running locally with VSCode using the following `launch.json` entry:

```json
{
  "name": "Python Debugger: Modernize Code API",
  "type": "debugpy",
  "request": "launch",
  "cwd": "${workspaceFolder}/src/backend",
  "module": "uvicorn",
  "args": ["app:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
  "jinja": true,
  "envFile": "${workspaceFolder}/src/backend/.env"
}
```

### Frontend Debugging

For debugging the React frontend, you can use the browser's developer tools or set up debugging in VS Code with the appropriate extensions.

### Agent System Debugging

To debug the SQL agents system:

1. **Enable debug logging** in your `.env` file:
   ```
   APP_LOGGING_LEVEL=DEBUG
   ```

2. **Monitor agent interactions** through the application logs and WebSocket messages

3. **Test individual agents** using the API endpoints directly

## Using Docker for Local Development

### Run with Docker Compose

```bash
# Build and start all services
docker-compose -f docker/docker-compose.yml up --build

# Run in detached mode
docker-compose -f docker/docker-compose.yml up -d --build
```

### Access Services

• **Frontend:** `http://localhost:3000`  
• **Backend:** `http://localhost:8000`

## Troubleshooting

### Common Issues

**Python Module Not Found:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Node.js Dependencies Issues:**
```bash
# Clear npm cache and reinstall
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

**Port Conflicts:**
```bash
# Check what's using the port
netstat -tulpn | grep :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows
```

**Azure Authentication Issues:**
```bash
# Re-authenticate
az logout
az login
```

**CORS Issues:**
• Ensure API CORS settings include the web app URL  
• Check browser network tab for CORS errors  
• Verify API is running on the expected port

**Environment Variables Not Loading:**
• Verify `.env` file is in the correct directory  
• Check file permissions (especially on Linux/macOS)  
• Ensure no extra spaces in variable assignments

**Agent Initialization Failures:**
• Verify Azure AI Foundry endpoint is correct  
• Check Azure OpenAI model deployments are available  
• Ensure proper authentication and permissions

### Debug Mode

Enable detailed logging by setting these environment variables in your `.env` file:

```
APP_LOGGING_LEVEL=DEBUG
AZURE_OPENAI_API_VERSION=2024-08-01-preview
```

### Database Issues

**Using a Different Database in Cosmos:**

You can set the solution up to use a different database in Cosmos. For example, you can name it something like `modernize-dev`. To do this:

1. Change the environment variable `AZURE_COSMOS_DATABASE` to the new database name
2. Create the database in the Cosmos DB account from the Data Explorer pane in the portal

---

For production deployment instructions, see the [Deployment Guide](./DeploymentGuide.md).
