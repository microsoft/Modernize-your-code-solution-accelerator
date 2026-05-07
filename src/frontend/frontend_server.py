import asyncio
import logging
import os
from contextlib import asynccontextmanager

import httpx
import uvicorn
import websockets
from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Internal backend URL used by the server-side proxy.
# The browser never contacts this URL directly.
BACKEND_API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")

_proxy_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _proxy_client
    _proxy_client = httpx.AsyncClient(timeout=300.0)
    yield
    await _proxy_client.aclose()


app = FastAPI(lifespan=lifespan)

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
async def get_config(request: Request):
    # The browser receives the frontend's own origin as the API base so that
    # all /api/* requests (including /api/health) route through the frontend
    # reverse proxy rather than hitting the internal backend directly.
    browser_api_url = str(request.base_url).rstrip("/")
    config = {
        "API_URL": browser_api_url,
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


# ---------------------------------------------------------------------------
# Reverse proxy: WebSocket  (must be declared before the HTTP catch-all below)
# ---------------------------------------------------------------------------

@app.websocket("/api/socket/{batch_id}")
async def proxy_websocket(websocket: WebSocket, batch_id: str):
    """Proxy WebSocket connections from the browser to the internal backend."""
    await websocket.accept()

    backend_ws_url = (
        BACKEND_API_URL
        .replace("https://", "wss://")
        .replace("http://", "ws://")
    )
    backend_ws_url = f"{backend_ws_url}/api/socket/{batch_id}"

    try:
        async with websockets.connect(backend_ws_url) as backend_ws:

            async def forward_to_backend():
                try:
                    while True:
                        data = await websocket.receive_text()
                        await backend_ws.send(data)
                except WebSocketDisconnect:
                    logger.debug("Client disconnected from WebSocket proxy")
                except Exception as exc:
                    logger.warning("Error forwarding to backend WS: %s", exc)

            async def forward_to_client():
                try:
                    async for message in backend_ws:
                        await websocket.send_text(message)
                except WebSocketDisconnect:
                    logger.debug("Client disconnected while forwarding from backend")
                except Exception as exc:
                    logger.warning("Error forwarding to client WS: %s", exc)

            tasks = [
                asyncio.create_task(forward_to_backend()),
                asyncio.create_task(forward_to_client()),
            ]
            # When one direction finishes, cancel the other
            done, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
    except Exception as exc:
        logger.error("WebSocket proxy error for batch %s: %s", batch_id, exc)
        try:
            await websocket.close(code=1011, reason="backend connection error")
        except Exception:
            pass
    else:
        try:
            await websocket.close(code=1000, reason="proxy closed")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Reverse proxy: HTTP  (all /api/* routes proxied to the internal backend)
# ---------------------------------------------------------------------------


@app.api_route(
    "/api/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
)
async def proxy_api(request: Request, path: str):
    """Proxy HTTP API requests from the browser to the internal backend."""
    target_url = f"{BACKEND_API_URL}/api/{path}"
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"

    # Forward all headers except 'host' (would confuse the backend)
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() != "host"
    }

    body = await request.body()

    response = await _proxy_client.request(
        method=request.method,
        url=target_url,
        headers=headers,
        content=body,
    )

    # Strip hop-by-hop and content-encoding/length headers that must not be
    # forwarded (httpx decodes content-encoding, so lengths may not match).
    excluded_headers = {
        "content-encoding", "content-length", "transfer-encoding",
        "connection", "keep-alive", "proxy-authenticate",
        "proxy-authorization", "te", "trailers", "upgrade",
    }
    forwarded_headers = {
        k: v for k, v in response.headers.items()
        if k.lower() not in excluded_headers
    }

    return StreamingResponse(
        content=response.iter_bytes(),
        status_code=response.status_code,
        headers=forwarded_headers,
    )


# ---------------------------------------------------------------------------
# SPA catch-all (must be last)
# ---------------------------------------------------------------------------

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
