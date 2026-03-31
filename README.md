# LLM Contract Eval System

Contract-driven LLM testing & validation platform with failure diagnostics, regression tracking, and optional multilingual + RAG grounding.

## What this builds

- Contract engine driven by YAML definitions
- Evaluation pipeline for structural, pattern, semantic, and RAG-grounding checks
- Failure taxonomy with severity and rationale
- Auto-repair suggestion loop for failed contracts
- FastAPI endpoints for trace ingestion, contracts, and reports
- Postgres-friendly storage layer with SQLite default for local development
- React dashboard shell and Typer CLI

## Quick start

### Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Copy `.env.example` to `.env` and set provider credentials if you want hosted judging or embeddings.

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
- Docker, Railway, and Vercel deployment scaffolding
- Environment-based runtime configuration for providers, DB, and CORS

## Provider modes

- `LLM_PROVIDER=heuristic`: local grounding judge without external API calls
- `LLM_PROVIDER=openai`: hosted semantic judge when `OPENAI_API_KEY` is set
- `EMBEDDING_PROVIDER=lexical`: local ranking for RAG evidence
- `EMBEDDING_PROVIDER=openai`: hosted embeddings when `OPENAI_API_KEY` is set

## Example API flow

1. `POST /api/trace` with a trace payload and a contract file path
2. Evaluation orchestrator routes each contract to the right evaluator
3. Failures are classified and repair suggestions are generated
4. Results are stored and surfaced through `/api/reports/*`

## Suggested next steps

1. Replace the stub semantic judge with a LangGraph workflow and provider-backed LLM calls.
2. Swap the lexical RAG retriever for FAISS or Chroma plus real embeddings.
3. Add prompt version diffing and model comparison endpoints for richer regression tracking.
4. Connect the frontend to the backend API and render live report data.
