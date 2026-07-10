# AI Legal Intelligence Platform - Project Context

Your AI Legal Copilot for Contracts, Compliance, Legal Research, and Business Governance.

---

## 1. System Architecture (Decoupled Services & Agents)
The platform is transitioning from a linear compliance engine to a service-agent model:

```
                           Web / Mobile
                                 │
                     Authentication Gateway
                                 │
         ┌───────────────────────┼────────────────────────┐
         │                       │                        │
     Chat Service          Document Service        Admin Service
         │                       │                        │
         └─────────────── Planner Agent ──────────────────┘
                                 │
       ┌───────────────┬──────────────┬───────────────┐
       │               │              │               │
 Legal Research   Contract AI   Tender AI      Compliance AI
       │               │              │               │
       └───────────────────────┬──────────────────────┘
                               │
                     Knowledge/RAG Layer
                               │
      PostgreSQL + pgvector + Object Storage + Cache
```

- **Authentication Gateway**: Single point of ingress, authenticating users and enforcing workspace/role boundaries.
- **Chat, Document, and Admin Services**: Core business logic handlers.
- **Planner Agent**: Cognitive router routing user requests to specialized sub-agents based on detected intent.
- **Specialized AI Agents**: Decoupled agents (Legal Research, Contract AI, Tender AI, Compliance AI) running task-specific actions.
- **RAG & Storage Layer**: PostgreSQL + pgvector, object storage (S3), and Redis cache.

---

## 2. Directory Layout (Phase 0 Transition)
The repository is transitioning to the following structure:
- **`frontend/`**: React + Vite client.
- **`backend/`**: FastAPI endpoints and core agent services.
- **`workers/`**: Background processors (Celery/RabbitMQ) for legal corpus ingestion and RAG chunking.
- **`shared/`**: Database models, schemas, and common utility packages.
- **`infrastructure/`**: Configuration configurations for deployment.
- **`docs/`**: API specifications and developer onboarding wikis.
- **`terraform/`**: Cloud resource definitions (AWS/Azure/Google Cloud).
- **`docker/`**: Multi-container Docker compose setups.
- **`sdk/`**: Client wrappers for REST API integration (JS/Python).

---

## 3. Gap Analysis: Roadmap & Implementation Status
This analysis maps the 21 development phases of the blueprint to the current codebase:

| Phase | Requirement Module | Current Status | codebase files / details |
|---|---|---|---|
| **Phase 0** | **Foundation** | **Implemented** | Repository restructured, multi-provider secret managers integration, config profiles, and GitHub Actions templates created. |
| **Phase 1** | **Authentication** | **Implemented** | User profiles schema added, Clerk JWT token verification middleware integrated, and frontend UserProfilePanel built. |
| **Phase 2** | **Organization** | **Partially Implemented** | Database models in [models.py](file:///d:/ContractLLM/shared/db/models.py) support `scope` but need Org ➔ Dept ➔ Team ➔ Project tables. |
| **Phase 3** | **AI Chat** | **Partially Implemented** | Currently has single-turn requirements evaluation. Multi-turn chat session routing, folders, and rich rendering are planned. |
| **Phase 4** | **Planner Agent** | **Planned** | Needs a coordinator that detects intent (Legal Research vs Contract vs Tender) and invokes sub-agents. |
| **Phase 5** | **Memory** | **Partially Implemented** | Feedback corrections stored in `FeedbackEntry`. Real short-term (chat threads) and long-term (user profiles) are planned. |
| **Phase 6** | **RAG** | **Partially Implemented** | Cosine similarity embeddings matching is live in [rag_agent.py](file:///d:/ContractLLM/backend/compliance/rag_agent.py). Query rewrite, BM25, and reranker are planned. |
| **Phase 7** | **Legal Corpus** | **Planned** | Crucial missing foundation. Need dedicated workers to ingest, version, and index legal databases (India, Germany, EU, US). |
| **Phase 8** | **Explainability** | **Implemented** | Agent answers return structured reasoning, sources, and recommended actions. |
| **Phase 9** | **Contract AI** | **Partially Implemented** | Base review and risk calculations exist. Drafting, version diffing, and negotiation templates are planned. |
| **Phase 10** | **Tender AI** | **Implemented** | Tender extraction, compliance grading, and risk matrices are fully functional. Win probability is planned. |
| **Phase 11** | **Company Knowledge** | **Implemented** | Knowledge base uploads of custom documents (`kb_documents`) are supported in RAG retrievals. |
| **Phase 12** | **AI Agents** | **Partially Implemented** | Parser, Extractor, Compliance, and Risk agents exist. Needs decoupled critic, citation validator, and audit agents. |
| **Phase 13** | **Human Review** | **Planned** | Needs confidence routing and a reviewer verification portal in the UI. |
| **Phase 14** | **Security** | **Implemented** | Enforces static API keys, Clerk JWTs, path traversal filename blocking, input prompt injection checks, and PII redactor. |
| **Phase 15** | **Enterprise Dashboard** | **Implemented** | Core dashboard panels and aggregate analytics exist in [dashboard.py](file:///d:/ContractLLM/backend/api/dashboard.py). |
| **Phase 16** | **AI Operations** | **Planned** | Evaluation metrics, prompt testing harness, and model registries are planned. |
| **Phase 17** | **Infrastructure** | **Partially Implemented** | Basic Dockerfile, render.yaml, and vercel.json configurations exist. Redis and RabbitMQ are planned. |
| **Phase 18** | **APIs** | **Partially Implemented** | FastAPI REST endpoints are fully functional. SDKs and webhooks are planned. |
| **Phase 19** | **Mobile** | **Planned** | React Native mobile wrappers and offline doc viewers are planned. |
| **Phase 20** | **Future Capabilities** | **Planned** | GraphRAG legal graph and e-signatures are planned. |

---

## 4. Active Session State
- **Goal**: Setting up the project context and planning the transition towards a full-featured AI Legal Intelligence Platform.
- **Recent Actions**:
  - Restructured the repository directories, placing database models, schemas, and multilingual systems into `shared/`.
  - Integrated Clerk JWT token decoding, User Profile entities, and preferences REST endpoints.
  - Built the `UserProfilePanel` settings view in React.
  - Implemented the Security Gateway (`shared/security/guardrails.py`) adding prompt injection screening, PII redaction, filename traversal sanitization, and output credentials scrubbing.
  - Integrated support for Google Gemini and NVIDIA NIM compliance reasoning providers.
  - Executed full test suite (16 tests passed in 1.44s).
- **Verification Commands**:
  - Run pytest tests: `python -m pytest -q`
  - Start local FastAPI server: `uvicorn backend.main:app --reload`
  - Start frontend dev: `npm run dev --prefix frontend`
