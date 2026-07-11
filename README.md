# AI Legal Intelligence Platform

Agentic compliance reasoning and legal assistant system for contracts, compliance, legal research, and business governance.
Tagline: Your AI Legal Copilot for Contracts, Compliance, Legal Research, and Business Governance.

This project is built for the workflow that matters in procurement:

1. Parse a tender or tender PDF
2. Extract structured requirements
3. Retrieve grounded company evidence with multilingual-friendly matching
4. Classify each requirement as `full`, `partial`, or `missing`
5. Flag legal, eligibility, and scoring risks
6. Store reviewer feedback so later analyses improve

## Core product output

The main output is a compliance matrix, not a draft proposal.

Each requirement includes:

- status
- reasoning
- retrieved evidence
- confidence
- recommended action
- risk flags

## Architecture

Backend agents:

- `ParserAgent`: accepts pasted text or base64 PDF payloads
- `ExtractorAgent`: identifies requirements and categories
- `RAGAgent`: retrieves supporting company evidence and KB notes
- `ComplianceAgent`: decides `full`, `partial`, or `missing`
- `RiskAgent`: flags disqualification and scoring risks

Supporting systems:

- multilingual detection and translation utilities
- feedback loop stored in Postgres/SQLite
- scoped knowledge chunk storage with `pgvector` support on Neon/Postgres
- xAI structured-output reasoning with heuristic fallback
- Render + Neon + Vercel deployment setup

## Quick start

### Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Tests

```bash
python -m pytest -q
```

## Main API endpoints

- `POST /api/analyze` (Run compliance analysis)
- `GET /api/analyses`
- `GET /api/analyses/{analysis_id}`
- `POST /api/documents`
- `GET /api/documents`
- `GET /api/documents/{document_id}/download`
- `GET /api/overview`
- `POST /api/feedback`
- `GET /api/feedback`
- `POST /api/copilot/chat` (Copilot legal chatbot)
- `POST /api/copilot/draft` (Template-based contract drafter)
- `POST /api/copilot/search-citations` (Precedents and court citation researcher)

Example analysis request:

```json
{
  "tender_title": "Municipal Services Tender",
  "tender_text": "The bidder must provide ISO 9001 certification.",
  "company_profile_text": "Our company holds ISO 9001 certification.",
  "target_language": "auto",
  "kb_documents": [
    {
      "title": "Capability Notes",
      "content": "We support public-sector clients."
    }
  ]
}
```

## Environment variables

Important backend values:

```env
ENVIRONMENT=production
DATABASE_URL=your_neon_database_url
API_KEY=your_backend_secret
REQUIRE_AUTH=true

# Multi-Provider Failover LLM configurations
LLM_PROVIDER=gemini
LLM_MODEL=gemini-flash-latest

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-flash-latest
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta

NVIDIA_API_KEY=your_nvidia_api_key
NVIDIA_MODEL=meta/llama-3.3-70b-instruct
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1

XAI_API_KEY=your_xai_key
XAI_BASE_URL=https://api.x.ai/v1

EMBEDDING_PROVIDER=multilingual_vector
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=12
VECTOR_DB=pgvector
MULTILINGUAL_EMBEDDINGS=true

LANGUAGE_MODE=auto
DEFAULT_OUTPUT_LANGUAGE=en
STRICT_LANGUAGE_MATCH=true
ALLOW_LANGUAGE_OVERRIDE=true
LANGUAGE_RETRY_LIMIT=2

ENABLE_FEEDBACK_LOOP=true
FEEDBACK_STORE=postgres
CONFIDENCE_THRESHOLD=0.75

BACKEND_CORS_ORIGINS=https://your-vercel-app.vercel.app
```

Frontend:

```env
VITE_API_BASE=https://your-render-service.onrender.com/api
VITE_API_KEY=
```

### Production Deployment

The project is configured for serverless deployment on **Google Cloud Run** with a unified three-stage build:
- **Python Builder**: Installs and compiles python packages cleanly.
- **Node Compiler**: Packages and builds the React frontend app static assets (`dist/`).
- **Runner**: Copies both built environments and serves them natively under a single domain endpoint.

Deploy command:
```bash
gcloud run deploy contract-llm-backend --source . --project [PROJECT_ID] --region us-central1 --allow-unauthenticated
```

Scaffolding blueprints:
- [docker/Dockerfile](file:///d:/ContractLLM/docker/Dockerfile)
- [terraform/main.tf](file:///d:/ContractLLM/terraform/main.tf)
- [docs/deployment.md](file:///d:/ContractLLM/docs/deployment.md)

## Notes

- The local fallback path is deterministic for testing and development.
- When `XAI_API_KEY` is configured, the project uses xAI structured outputs for per-requirement compliance reasoning.
- When `DATABASE_URL` points to Neon/Postgres, the app enables the `vector` extension and stores knowledge embeddings in `pgvector`.
- `EMBEDDING_DIMENSIONS=12` matches the built-in multilingual vector fallback. If you switch to a hosted embedding model, set this to that model's embedding size.
- Uploaded tender, company, and knowledge PDFs are stored in the database and can be reused across analyses.
- The frontend supports browser-stored API keys and sends them as `x-api-key` on all backend calls.
- Feedback is stored and reused as a correction signal for similar future requirements.

## Agentic Development & Custom Skills

This repository is optimized for agentic development using **Antigravity**. It includes workspace-scoped configurations to assist AI agents in code navigation, context preservation, and codebase documentation.

### Workspace Configurations

All customizations are stored in the `.agents/` customization root:
- **Workspace Rules**: Defined in [.agents/AGENTS.md](file:///d:/ContractLLM/.agents/AGENTS.md). These establish behavioral guidelines, coding principles, and context synchronization rules.
- **Custom Skill**: Defined in [.agents/skills/contract-llm-docs/SKILL.md](file:///d:/ContractLLM/.agents/skills/contract-llm-docs/SKILL.md). This skill provides specialized instructions for documenting the core compliance agents.

### Context Preservation & Documentation Workflows

When working with Antigravity, developers and agents are encouraged to leverage the following capabilities:
1. **Context Restoration**: Use the `context-management-context-restore` skill to automatically rehydrate the semantic memory and project state when resuming a development session.
2. **Context Preservation**: Use the `context-management-context-save` skill to serialize the workspace state, architectural decisions, and current progress.
3. **Structured Documentation**: Use the `wiki-architect` skill alongside the custom `contract-llm-docs` skill to generate structured wikis, zero-to-hero onboarding paths, and principal-level guides referencing real files in this repository.

