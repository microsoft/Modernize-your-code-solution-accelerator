import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Build paths
BUILD_DIR = os.path.join(os.path.dirname(__file__), "dist")
INDEX_HTML = os.path.join(BUILD_DIR, "index.html")


# Serve static files from build directory
app.mount(
    "/assets", StaticFiles(directory=os.path.join(BUILD_DIR, "assets")), name="assets"
)


@app.get("/")
async def serve_index():
    return FileResponse(INDEX_HTML)


@app.get("/config")
async def get_config():
    config = {
        "API_URL": os.getenv("API_URL", "API_URL not set"),
        "REACT_APP_MSAL_AUTH_CLIENTID": os.getenv(
            "REACT_APP_MSAL_AUTH_CLIENTID", "Client ID not set"
        ),
        "REACT_APP_MSAL_AUTH_AUTHORITY": os.getenv(
            "REACT_APP_MSAL_AUTH_AUTHORITY", "Authority not set"
        ),
        "REACT_APP_MSAL_REDIRECT_URL": os.getenv(
            "REACT_APP_MSAL_REDIRECT_URL", "Redirect URL not set"
        ),
        "REACT_APP_MSAL_POST_REDIRECT_URL": os.getenv(
            "REACT_APP_MSAL_POST_REDIRECT_URL", "Post Redirect URL not set"
        ),
        "ENABLE_AUTH": os.getenv("ENABLE_AUTH", "false"),
    }
    return config


@app.get("/{full_path:path}")
async def serve_app(full_path: str):
    # Remediation: normalize and check containment before serving
    file_path = os.path.normpath(os.path.join(BUILD_DIR, full_path))
    # Block traversal and dotfiles
    if not file_path.startswith(BUILD_DIR) or ".." in full_path or "/." in full_path or "\\." in full_path:
        return FileResponse(INDEX_HTML)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(INDEX_HTML)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3000)
