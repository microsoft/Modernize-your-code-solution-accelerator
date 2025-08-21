import os

import uvicorn
from dotenv import load_dotenv
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
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

# Resolved build directory path (used to prevent path traversal)
BUILD_DIR_PATH = Path(BUILD_DIR).resolve()

# Security: block serving of certain sensitive files by extension/name
FORBIDDEN_EXTENSIONS = {'.env', '.py', '.pem', '.key', '.db', '.sqlite', '.toml', '.ini'}
FORBIDDEN_FILENAMES = {'Dockerfile', '.env', '.secrets', '.gitignore'}

# Serve static files from build directory
app.mount(
    "/assets", StaticFiles(directory=os.path.join(BUILD_DIR, "assets")), name="assets"
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    resp = await call_next(request)
    # Basic security headers; applications should extend CSP per app needs
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    resp.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=()")
    return resp


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
    """
    Safely serve static files from the build directory or return the SPA index.html.

    Protections:
    - Prevent directory traversal by resolving candidate paths and ensuring they are inside BUILD_DIR.
    - Block dotfiles and sensitive extensions/names.
    - Return 404 on suspicious access instead of leaking details.
    """
    try:
        candidate = (BUILD_DIR_PATH / full_path).resolve()

        # Ensure resolved path is within BUILD_DIR
        if not str(candidate).startswith(str(BUILD_DIR_PATH)):
            raise HTTPException(status_code=404)

        # Compute relative parts and block dotfiles anywhere in path
        try:
            rel_parts = candidate.relative_to(BUILD_DIR_PATH).parts
        except Exception:
            raise HTTPException(status_code=404)

        if any(part.startswith('.') for part in rel_parts):
            raise HTTPException(status_code=404)

        if candidate.name in FORBIDDEN_FILENAMES:
            raise HTTPException(status_code=404)

        # If it's a regular file and allowed extension, serve it
        if candidate.is_file():
            if candidate.suffix.lower() in FORBIDDEN_EXTENSIONS:
                raise HTTPException(status_code=404)

            headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "Referrer-Policy": "no-referrer",
            }
            return FileResponse(str(candidate), headers=headers)

        # Not a file -> fall back to SPA entrypoint
        return FileResponse(INDEX_HTML, headers={
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "no-referrer",
        })

    except HTTPException:
        raise
    except Exception:
        # Hide internal errors and respond with 404 to avoid information leakage
        raise HTTPException(status_code=404)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3000)
