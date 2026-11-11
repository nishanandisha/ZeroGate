import json
import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, health
from app.core.config import get_settings

settings = get_settings()
log = logging.getLogger("zerogate.audit")
logging.basicConfig(level=logging.INFO, format="%(message)s")

app = FastAPI(title=settings.app_name, version="1.0.0", docs_url="/api/docs", openapi_url="/api/openapi.json")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["GET"],
                   allow_headers=["Authorization"])


@app.middleware("http")
async def audit(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    if request.url.path != "/api/health/live":
        log.info(json.dumps({"ts": round(time.time(), 3), "client": request.client.host if request.client else None,
                             "method": request.method, "path": request.url.path, "status": response.status_code,
                             "ms": round((time.perf_counter() - start) * 1000, 1)}))
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/auth/config", tags=["auth"])
def auth_config() -> dict:
    """Public: tells the console how to log in."""
    return {"enabled": settings.auth_enabled, "authority": settings.keycloak_issuer,
            "client_id": settings.oidc_client_id, "admin_group": settings.admin_group}


app.include_router(health.router)
app.include_router(admin.router)
