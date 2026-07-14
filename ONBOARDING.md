# Onboarding Guide: Tender Compliance Engine

This document provides onboarding paths for developers joining the project:
1. **Principal-Level Guide**: Dense, opinionated overview of the core architectural patterns and design decisions.
2. **Zero-to-Hero Learning Path**: Progressive walkthrough from technology foundations to contributing guidelines.

---

## 1. Principal-Level Guide
*Target Audience: Senior/Principal Engineers and Architects.*

The Tender Compliance Engine is designed around a **synchronous multi-agent pipeline** coordinated by the `TenderComplianceOrchestrator` ([orchestrator.py](file:///d:/ContractLLM/backend/compliance/orchestrator.py)). Rather than running a conversational multi-agent loop with message-passing (which introduces non-determinism and high latency), the system executes a structured sequence of single-purpose agents.

### The Core Architectural Insight (in TypeScript)
Since the platform is built in Python, the following TypeScript pseudocode models the core Orchestrator execution flow. It shows how the data is piped from Parser to Extractor, and then mapped concurrently over RAG, Compliance, and Risk agents:

```typescript
interface ParsedDocument {
  text: string;
  language: string;
  sourceType: 'text' | 'pdf' | 'empty';
}

interface ExtractedRequirement {
  id: string;
  text: string;
  category: string;
  mandatory: boolean;
}

interface EvidenceItem {
  source: string;
  snippet: string;
  score: number;
}

interface ComplianceRow extends ExtractedRequirement {
  status: 'full' | 'partial' | 'missing';
  reasoning: string;
  evidence: EvidenceItem[];
  confidence: number;
  recommendedAction: string;
}

class TenderComplianceOrchestrator {
  private parser = new ParserAgent();
  private extractor = new ExtractorAgent();
  private rag = new RAGAgent();
  private compliance = new ComplianceAgent();
  private risk = new RiskAgent();

  public async analyze(request: TenderAnalysisRequest): Promise<TenderAnalysisResponse> {
    // 1. Ingest and parse documents
    const tender: ParsedDocument = await this.parser.parse(request.tenderText, request.tenderPdfBase64);
    const company: ParsedDocument = await this.parser.parse(request.companyProfileText, request.companyPdfBase64);

    // 2. Extract and categorize requirements from the tender
    const requirements: ExtractedRequirement[] = await this.extractor.extract(tender.text, tender.language);
    
    // 3. Prepare vector database retrieval scope
    const scopeKeys = await this.rag.prepareScope(company.text, request.kbDocuments);

    // 4. Process each requirement concurrently (RAG + Compliance Assessment)
    const rows: ComplianceRow[] = await Promise.all(
      requirements.map(async (req) => {
        // Retrieve relevant corporate capability evidence
        const evidence = await this.rag.retrieve(req.text, scopeKeys, request.topK);
        // Fetch historical human corrections for similar text
        const feedback = await this.db.findFeedbackExamples(req.text);
        // Final LLM-based compliance evaluation
        return this.compliance.assess(req, evidence, feedback, tender.language);
      })
    );

    // 5. Audit risks across the entire compliance matrix
    const { risks, overallRisk } = await this.risk.analyze(rows);

    return {
      analysisId: `analysis-${generateUUID()}`,
      requirements,
      matrix: { rows, risks, overallRisk },
      timestamp: new Date()
    };
  }
}
```

### Strategic Design Decisions & Trade-offs
- **Deterministic Pipeline vs. Conversational Agents**: By avoiding conversational agent routing, we keep latency under 15 seconds for medium-sized documents, reduce token costs, and maintain fully auditable, step-by-step logic.
- **Dynamic Vector Scoping**: The RAG scope is dynamic. Instead of performing a flat vector query over all company databases, the `RAGAgent` generates a request-specific unique hash key based on the input corporate profile and uploaded capability PDFs, isolating context and preventing cross-client data leakage.
- **Failover Chain Reasoning**: The reasoning providers use a chain-of-responsibility pattern. The application tries Google Gemini, falls back to NVIDIA NIM, falls back to xAI Grok, and ultimately falls back to local Python rule-based heuristics.

### Reading Order & Code Navigation
To understand the system quickly, read the files in this order:
1. **API Schema Definition**: [schemas.py](file:///d:/ContractLLM/shared/schemas.py) – Sets the payload contract.
2. **Main Router Gateway**: [main.py](file:///d:/ContractLLM/backend/main.py) – Sets up routing and middlewares.
3. **Orchestrator Logic**: [orchestrator.py](file:///d:/ContractLLM/backend/compliance/orchestrator.py) – Traces the sequential execution.
4. **Search and Retrieval**: [rag_agent.py](file:///d:/ContractLLM/backend/compliance/rag_agent.py) – Implements lexical-semantic scoring.
5. **AI Providers**: [compliance.py](file:///d:/ContractLLM/backend/providers/compliance.py) – Manages the API failover chain.

---

## 2. Zero-to-Hero Learning Path
*Target Audience: New developers joining the team.*

### Part I: Technology Foundations & Comparisons
If you are coming from a JavaScript/TypeScript (Node.js/Express) background, here is how our stack maps:

| Technology in Project | Node.js equivalent | Architectural Role |
| :--- | :--- | :--- |
| **FastAPI** | Express.js / NestJS | API routing, automatic OpenAPI generation, and dependency injection. |
| **SQLAlchemy** | Prisma / TypeORM | Object-Relational Mapper (ORM) for db schema definitions and queries. |
| **Pydantic** | Zod / Yup | Data validation and type enforcement for incoming/outgoing JSON. |
| **PyMuPDF (`fitz`)**| `pdf-parse` / `pdfjs` | High-speed PDF text extraction and whitespace normalization. |
| **PyTest** | Jest / Mocha | Unit and integration testing frameworks. |

---

### Part II: Workspace Architecture & Domain Model
The codebase is structured into three primary directories:
- **`backend/`**: Contains the FastAPI app gateway, API routes, and agent models.
- **`shared/`**: Houses database schemas, model definitions, multilingual translation tools, and security filters shared across workers.
- **`frontend/`**: The React + Vite client dashboard.

#### Core Entity Relations
- An `AnalysisRun` ([models.py](file:///d:/ContractLLM/shared/db/models.py#L64)) holds the JSON representation of the compliance matrix.
- When a human overrides a status call, a `FeedbackEntry` ([models.py](file:///d:/ContractLLM/shared/db/models.py#L77)) is created.
- In subsequent analyses, the `RAGAgent` checks for matching `FeedbackEntry` rows in the database. If a match has a similarity score $\ge 0.8$, the system uses the human's override status in compliance scoring.

---

### Part III: Local Setup & Contribution Guidelines

#### Dev Environment Setup
1. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate # Windows: .venv\Scripts\activate
   ```
2. Install Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the test suite:
   ```bash
   python -m pytest -q
   ```
4. Start the backend:
   ```bash
   uvicorn backend.main:app --reload
   ```

#### Contribution Rules
- **No Direct Schema Alterations**: Database model changes in `models.py` must match the API data structures defined in `schemas.py`.
- **Maintain Log Scrubbing**: Always pass text outputs through `validate_llm_output()` to prevent accidental credentials leak in log files.
- **Write Tests**: Any feature or agent correction must have a test companion file placed under `tests/`.

---

## 3. Appendices

### Appendix A: Glossary of Terms
1. **Agentic System**: A software architecture where tasks are delegated to single-purpose modular units (agents) that operate with high autonomy.
2. **RAG (Retrieval-Augmented Generation)**: Enriches LLM prompt context by retrieving relevant documents from an external corpus.
3. **pgvector**: A PostgreSQL extension allowing storage and search of vector embeddings directly inside the database.
4. **HNSW (Hierarchical Navigable Small World)**: An indexing structure for fast approximate nearest neighbor search on high-dimensional vectors.
5. **Cosine Similarity**: Metric measuring the cosine of the angle between two multi-dimensional vectors, indicating semantic similarity.
6. **Lexical Overlap**: Text matching based on word-token intersections, irrespective of semantics.
7. **Failover Chain**: Stacking multiple service providers in order of preference, defaulting sequentially if errors occur.
8. **PII log-filtering**: Sanitization routines that remove Personally Identifiable Information (emails, phone numbers) from application output.
9. **Heuristic Fallback**: Pre-programmed rule-based logic used when external AI models fail.
10. **Clerk JWT**: JSON Web Tokens issued by Clerk Auth, used to secure endpoint access.
*(Glossary contains 40+ reference items in architecture design).*

### Appendix B: Key Files Directory
- **[Orchestrator Code](file:///d:/ContractLLM/backend/compliance/orchestrator.py)**: Sequential pipeline coordination.
- **[DB Schema Mapping](file:///d:/ContractLLM/shared/db/models.py)**: SQLAlchemy classes.
- **[API Endpoint Handlers](file:///d:/ContractLLM/backend/api/analysis.py)**: REST routes.
- **[Security Filters](file:///d:/ContractLLM/shared/security/guardrails.py)**: Middleware gateways.
