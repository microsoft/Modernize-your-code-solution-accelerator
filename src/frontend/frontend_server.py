import os
import asyncio
import logging

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

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

# When set, enables reverse proxy mode for WAF deployments where the backend
# Container App has internal-only ingress and is not reachable from the internet.
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "")


# Serve static files from build directory
app.mount(
    "/assets", StaticFiles(directory=os.path.join(BUILD_DIR, "assets")), name="assets"
)


@app.get("/")
async def serve_index():
    return FileResponse(INDEX_HTML)


@app.get("/config")
async def get_config():
    # In proxy mode (WAF), return empty API_URL so the browser uses relative
    # paths that are routed through the frontend reverse proxy.
    api_url = "" if BACKEND_API_URL else os.getenv("API_URL", "API_URL not set")
    config = {
        "API_URL": api_url,
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
# Reverse proxy routes – only registered when BACKEND_API_URL is configured
# (WAF deployment with internal-only backend ingress).
# ---------------------------------------------------------------------------
if BACKEND_API_URL:
    import httpx
    import websockets

    _backend_base = BACKEND_API_URL.rstrip("/")

    _HOP_BY_HOP_HEADERS = frozenset(
        {
            "host",
            "connection",
            "keep-alive",
            "transfer-encoding",
            "te",
            "trailer",
            "upgrade",
            "proxy-authorization",
            "proxy-authenticate",
        }
    )

    @app.websocket("/api/{path:path}")
    async def proxy_websocket(websocket: WebSocket, path: str):
        """Proxy WebSocket connections to the internal backend."""
        await websocket.accept()
        ws_url = (
            f"{_backend_base}/api/{path}"
            .replace("https://", "wss://")
            .replace("http://", "ws://")
        )
        try:
            async with websockets.connect(ws_url) as backend_ws:

                async def client_to_backend():
                    try:
                        while True:
                            data = await websocket.receive_text()
                            await backend_ws.send(data)
                    except (WebSocketDisconnect, Exception):
                        pass

                async def backend_to_client():
                    try:
                        async for message in backend_ws:
                            await websocket.send_text(str(message))
                    except Exception:
                        pass

                done, pending = await asyncio.wait(
                    [
                        asyncio.create_task(client_to_backend()),
                        asyncio.create_task(backend_to_client()),
                    ],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
        except Exception as exc:
            logger.error("WebSocket proxy error: %s", exc)
        finally:
            try:
                await websocket.close()
            except Exception:
                pass

    @app.api_route(
        "/api/{path:path}",
        methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
    )
    async def proxy_api(request: Request, path: str):
        """Proxy HTTP API requests to the internal backend."""
        target_url = f"{_backend_base}/api/{path}"
        if request.query_params:
            target_url = f"{target_url}?{request.query_params}"

        headers = {
            k: v
            for k, v in request.headers.items()
            if k.lower() not in _HOP_BY_HOP_HEADERS
        }
        body = await request.body()

        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
            )

        excluded = _HOP_BY_HOP_HEADERS | {"content-encoding", "content-length"}
        resp_headers = {
            k: v for k, v in resp.headers.items() if k.lower() not in excluded
        }
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=resp_headers,
        )

    @app.get("/health")
    async def proxy_health():
        """Proxy health check to the internal backend."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{_backend_base}/health")
            return Response(content=resp.content, status_code=resp.status_code)
        except httpx.RequestError as exc:
            logger.error("Backend health check failed: %s", exc)
            return Response(
                content=b'{"status":"backend_unreachable"}',
                status_code=502,
            )


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
