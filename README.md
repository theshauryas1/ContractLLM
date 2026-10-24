# AI Legal Intelligence Platform (Tender Compliance Engine)

https://github.com/user-attachments/assets/9684590b-c105-4ef8-b81d-27f0dc52d57d

> **Your AI Legal Copilot for Contracts, Compliance, Legal Research, and Business Governance.**

The AI Legal Intelligence Platform is a decoupled, agentic system designed to analyze complex procurement documents (tenders, RFP specs), extract requirements, perform multilingual RAG matching against corporate records, and determine compliance status (`full`, `partial`, `missing`) while flagging key disqualification and scoring risks.

---

## Key Features

- **Ingestion & Parsing**: Paste plain text or upload base64-encoded/raw PDFs. Automatically parses documents via `ParserAgent` using PyMuPDF (`fitz`) and normalizes whitespace/character encoding.
- **Multilingual Support**: Real-time language detection via `LanguageDetector` and translation fallbacks via `Translator`. Supports English, German, French, Spanish, Dutch, and Hindi.
- **AI-Powered Requirement Extraction**: Extracts requirement lines, determines if they are mandatory, and categorizes them (`eligibility`, `technical`, `financial`, `legal`, `operational`) using heuristic search and keyword classifiers.
- **Hybrid RAG Matching**: Combines semantic embedding search (via custom embedding providers) with lexical token-overlap retrieval to surface relevant corporate capabilities and documents.
- **Failover LLM Reasoning**: Chains multiple AI providers (Google Gemini, NVIDIA NIM, and xAI Grok) with automated failovers and a rule-based heuristic reasoning fallback as a safety net.
- **Interactive Feedback Loop**: Stores reviewer-corrected compliance decisions and uses them as high-importance evidence in subsequent analyses of similar requirements.
- **Dual-Database Support**: Uses SQLite locally for light footprint development and PostgreSQL with the `pgvector` extension for production-ready, high-speed vector similarity queries.
- **AI Legal Copilot Suite**:
  - **Copilot Chat**: Conversational assistant with context injection.
  - **Contract Drafter**: Template-driven contract generation based on custom terms.
  - **Citation Search**: Precedent, case law, and citation search engine.

---

## System Architecture

The core of the compliance platform is structured as a decoupled multi-agent pipeline coordinated by the `TenderComplianceOrchestrator`:

```
                       +-------------------------------+
                       |           React Frontend      |
                       +---------------+---------------+
                                       | HTTP JSON / REST API
                       +---------------v---------------+
                       |        FastAPI Web Server     |
                       +---------------+---------------+
                                       |
                       +---------------v---------------+
                       |  TenderComplianceOrchestrator |
                       +---------------+---------------+
                                       | (Coordinates execution)
        +---------------+--------------+--------------+---------------+--------------+
        |               |              |              |               |              |
 +------v------+ +------v------+ +------v------+ +------v------+ +------v------+ +------v------+
 | ParserAgent | |ExtractorAgent| |  RAGAgent   | |ComplianceAgnt| |  RiskAgent   | |Translator  |
 +------+------+ +------+------+ +------+------+ +------+------+ +------+------+ +------+------+
        |               |              |              |               |              |
        v               v              v              v               v              v
   Text & PDF      Requirement     Vector &      Status & AI      Compliance     Multilingual
   Extracting     Classification    Lexical       Reasoning       Risk Flags     Localization
                  & Weighting      Retrieval    (Gemini/Grok)
```

1. **[ParserAgent](file:///d:/ContractLLM/backend/compliance/parser_agent.py)**: Extracts and cleans plain text from documents. Detects input language.
2. **[ExtractorAgent](file:///d:/ContractLLM/backend/compliance/extractor_agent.py)**: Identifies requirement segments using keyword hints and triggers the classification sub-agent.
3. **[ClassifierAgent](file:///d:/ContractLLM/backend/compliance/classifier_agent.py)**: Maps requirements into categories and evaluates if they represent mandatory criteria.
4. **[RAGAgent](file:///d:/ContractLLM/backend/compliance/rag_agent.py)**: Generates embeddings, syncs document chunks, and queries knowledge base records using hybrid vector-lexical scoring.
5. **[ComplianceAgent](file:///d:/ContractLLM/backend/compliance/compliance_agent.py)**: Resolves compliance status (`full`, `partial`, `missing`) and compiles audit trails.
6. **[RiskAgent](file:///d:/ContractLLM/backend/compliance/risk_agent.py)**: Evaluates the compliance matrix row-by-row to flag disqualification, scoring, or operational risks.

For a detailed look at diagrams, component layouts, and database relations, see [ARCHITECTURE.md](file:///d:/ContractLLM/ARCHITECTURE.md).

---

## Interface Preview (Screenshots)

### 1. Compliance Matrix Dashboard
Displays extracted requirements, categories, status highlights, confidence metrics, and recommended actions.
*Placeholder Link: `/docs/screenshots/dashboard.png`*

### 2. Legal Copilot Interface
Interactive workspace for drafting contracts, searching case precedents, and querying compliance records.
*Placeholder Link: `/docs/screenshots/copilot.png`*

---

## Setup & Running Guide

### 1. Local Development (SQLite)

#### Backend Setup
```bash
# 1. Create a Python 3.12 virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install requirements
pip install -r requirements.txt

# 3. Create a local environment file
cp .env.example .env       # (Or update current .env with your LLM API Keys)

# 4. Run the FastAPI development server
uvicorn backend.main:app --reload
```

#### Frontend Setup
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install Node dependencies
npm install

# 3. Start the Vite server
npm run dev
```

### 2. Containerized Deployment (Docker)

To run the unified frontend and backend inside a single Docker container:
```bash
# Build the image using the three-stage production build
docker build -t contract-llm -f docker/Dockerfile .

# Run the container (injecting environment variables)
docker run -p 8000:8000 --env-file .env contract-llm
```

### 3. Running Tests
Ensure database migrations, endpoints, and security headers are functional:
```bash
python -m pytest -q
```

---

## Main API Gateway Endpoints

Below is a summary of the API endpoints. For detailed JSON structures and request/response payloads, see [API.md](file:///d:/ContractLLM/API.md).

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| **POST** | `/api/analyze` | Initiates requirement extraction and compliance matching | Yes |
| **GET** | `/api/analyses` | Lists summaries of all historical analysis runs | Yes |
| **GET** | `/api/analyses/{id}` | Retrieves full matrix and risk logs of a specific run | Yes |
| **POST** | `/api/documents` | Uploads a PDF or text document asset to the platform | Yes |
| **GET** | `/api/documents` | Lists all stored document assets (Tenders/Company/KB) | Yes |
| **GET** | `/api/documents/{id}/download` | Downloads the raw file bytes of a document asset | Yes |
| **GET** | `/api/overview` | Retrieves aggregate metrics and language stats for dashboard | Yes |
| **POST** | `/api/feedback` | Registers human corrections to retrain RAG/LLM status calls | Yes |
| **GET** | `/api/feedback` | Retrieves historical feedback logs | Yes |
| **GET** | `/api/users/me` | Fetches preferences and organizational settings for current user | Yes (Clerk) |
| **PUT** | `/api/users/me` | Updates user settings (e.g. target language, AI models) | Yes (Clerk) |
| **POST** | `/api/copilot/chat` | AI chatbot assistant with context injection | No |
| **POST** | `/api/copilot/draft` | Template-based contract drafting agent | No |
| **POST** | `/api/copilot/search-citations` | Law Precedents and court case citation searcher | No |

---

## Configuration Variables

The system is configured via environment variables (loaded from `.env`). Core parameters include:

```env
# Server Environment
ENVIRONMENT=development
DATABASE_URL=sqlite:///./llm_eval.db
API_KEY=local-dev-key
REQUIRE_AUTH=false

# LLM Providers Configuration
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-key
GEMINI_MODEL=gemini-flash-latest

# RAG & Embedding Settings
EMBEDDING_PROVIDER=multilingual_vector
EMBEDDING_DIMENSIONS=12
VECTOR_DB=pgvector

# Language Processing
LANGUAGE_MODE=auto
DEFAULT_OUTPUT_LANGUAGE=en
STRICT_LANGUAGE_MATCH=true
```

---

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
