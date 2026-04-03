from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.contracts import router as contracts_router
from backend.api.ingest import router as ingest_router
from backend.api.reports import router as reports_router
from backend.db.models import init_db
from backend.utils.config import get_settings


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
    title="LLM Contract Eval System",
    version="0.1.0",
    description=(
        "Contract-driven LLM testing & validation platform with failure diagnostics, "
        "regression tracking, and optional multilingual + RAG grounding."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(ingest_router, prefix="/api")
app.include_router(contracts_router, prefix="/api")
app.include_router(reports_router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}
