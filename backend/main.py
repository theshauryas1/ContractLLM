import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.api.analysis import router as analysis_router
from backend.api.dashboard import router as dashboard_router
from backend.api.documents import router as documents_router
from backend.api.feedback import router as feedback_router
from backend.api.users import router as users_router
from backend.api.copilot import router as copilot_router
from shared.db.models import init_db
from backend.utils.config import get_settings
from shared.security.guardrails import (
    SecureHeadersMiddleware,
    SimpleRateLimitMiddleware,
    SensitiveDataLoggingFilter,
)

# Apply logging filter to scrub logs of PII and API keys
logging.getLogger().addFilter(SensitiveDataLoggingFilter())


settings = get_settings()


def _parse_cors_origins(raw: str) -> list[str]:
    if raw.strip() == "*":
        return ["*"]
    return [item.strip() for item in raw.split(",") if item.strip()]


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Tender Compliance Engine",
    version="0.1.0",
    description=(
        "Agentic compliance reasoning system for multilingual tenders, "
        "grounded company evidence, risk analysis, and feedback-driven improvement."
    ),
    lifespan=lifespan,
)

# Security gateway middlewares (Secure HTTP headers & API Rate Limiting)
app.add_middleware(SecureHeadersMiddleware)
app.add_middleware(SimpleRateLimitMiddleware, requests_per_minute=120)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(analysis_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(feedback_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(copilot_router, prefix="/api")


@app.get("/")
def read_root() -> Response:
    frontend_index = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist", "index.html")
    if os.path.exists(frontend_index):
        return FileResponse(frontend_index)
    return JSONResponse({
        "message": "Welcome to the AI Legal Intelligence Platform API Gateway.",
        "version": "0.1.0",
        "health": "/health",
        "documentation": "/docs"
    })


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


# Serve React static assets if compiled in the dist folder
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    # SPA Routing Fallback for Client-Side Router
    @app.get("/{fallback_path:path}")
    def serve_frontend_fallback(fallback_path: str):
        if fallback_path.startswith("api/") or fallback_path == "health" or fallback_path == "docs" or fallback_path == "openapi.json":
            return Response(content='{"detail": "Not Found"}', status_code=404, media_type="application/json")
        return FileResponse(os.path.join(frontend_dist, "index.html"))
