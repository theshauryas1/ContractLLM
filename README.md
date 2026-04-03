# LLM Contract Eval System

Contract-driven LLM testing & validation platform with failure diagnostics, regression tracking, multilingual translation, and optional RAG grounding.

## What this builds

- Contract engine driven by YAML definitions
- Evaluation pipeline for structural, pattern, semantic, and RAG-grounding checks
- Failure taxonomy with severity and rationale
- Auto-repair suggestion loop for failed contracts
- FastAPI endpoints for trace ingestion, contracts, and reports
- Neon/Postgres-friendly storage layer with SQLite default for local development
- React dashboard shell and Typer CLI

## Quick start

### Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Copy `.env.example` to `.env` and set provider credentials if you want hosted Grok/xAI judging or translation.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### CLI

```bash
python cli/llmtest.py run tests/sample_traces.json
```

## Production-oriented additions

- Optional API-key auth on all mutable/reporting API endpoints
- Provider abstraction for semantic judging and embeddings with local fallback
- Docker, Render, Neon, and Vercel deployment scaffolding
- Environment-based runtime configuration for providers, DB, and CORS

## Provider modes

- `LLM_PROVIDER=heuristic`: local grounding judge without external API calls
- `LLM_PROVIDER=xai`: hosted semantic judge using Grok/xAI when `XAI_API_KEY` is set
- `TRANSLATION_PROVIDER=heuristic`: local phrase-based translation fallback for `fr`, `de`, `es`, and `nl`
- `TRANSLATION_PROVIDER=xai`: hosted translation using Grok/xAI when `XAI_API_KEY` is set
- `EMBEDDING_PROVIDER=lexical`: local ranking for RAG evidence
- `EMBEDDING_PROVIDER=xai`: hosted embeddings if you choose an xAI-compatible embedding model

## Deploy on Render + Neon + Vercel

### Backend on Render

Use [render.yaml](/abs/path/c:/ContractLLM/render.yaml) or create a Render Web Service from this repo.

Set these environment variables on Render:

- `DATABASE_URL`: your Neon pooled Postgres connection string
- `XAI_API_KEY`: your Grok/xAI API key
- `API_KEY`: shared backend API key for protected routes
- `BACKEND_CORS_ORIGINS`: your Vercel frontend URL, for example `https://your-app.vercel.app`
- `LLM_PROVIDER=xai`
- `TRANSLATION_PROVIDER=xai`
- `EMBEDDING_PROVIDER=lexical`
- `REQUIRE_AUTH=true`

### Database on Neon

Create a Neon project and copy its connection string into Render as `DATABASE_URL`.
This app uses SQLAlchemy and `psycopg` in production, so Neon works without code changes.

### Frontend on Vercel

Deploy the `frontend` directory as a Vite project and set:

- `VITE_API_BASE=https://your-render-service.onrender.com/api`

If backend auth is enabled, any frontend write flows you add later will also need to send `x-api-key`.

## Example API flow

1. `POST /api/trace` with a trace payload and a contract file path
2. Evaluation orchestrator routes each contract to the right evaluator
3. Failures are classified and repair suggestions are generated
4. Results are stored and surfaced through `/api/reports/*`

## Deployment readiness notes

1. The backend now reads CORS origins from env instead of always allowing `*`.
2. The Docker image respects Render's `PORT`.
3. Production Postgres connections use `psycopg` and connection health checks.
4. The Vercel config now rewrites routes to `index.html` for SPA navigation.
