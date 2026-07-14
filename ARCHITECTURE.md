# Platform Architecture: Tender Compliance Engine

This document provides a comprehensive overview of the design patterns, system components, execution flows, and infrastructure models that power the AI Legal Intelligence Platform.

---

## 1. System Component Design

The platform is designed with a decoupled, agentic architecture consisting of an API Gateway, a coordination layer (`TenderComplianceOrchestrator`), specialized functional agents, and a dual storage layer (SQLite for development / PostgreSQL with `pgvector` for production).

```mermaid
graph TD
    %% Frontend
    subgraph Client ["Client Interface"]
        UI["React Dashboard (Vite)"]
    end

    %% API Gateway & Middlewares
    subgraph Gateway ["API Gateway (FastAPI)"]
        RL["Rate Limiter Middleware"]
        SH["Secure Headers Middleware"]
        LF["PII Logging Filter"]
        Routes["API Router (/api/*)"]
        Security["Auth Manager (Clerk JWT / Static Key)"]
        
        UI -->|HTTPS Request| RL
        RL --> SH
        SH --> LF
        LF --> Routes
        Routes -.->|Validate Session| Security
    end

    %% Coordination Layer
    subgraph Core ["Coordination Layer"]
        Orch["TenderComplianceOrchestrator"]
        Routes -->|Trigger Run| Orch
    end

    %% Agentic Sub-system
    subgraph Agents ["Domain Agents"]
        PA["ParserAgent (Text / fitz PDF)"]
        EA["ExtractorAgent"]
        CA["ClassifierAgent"]
        RAG["RAGAgent (Hybrid Search)"]
        Comp["ComplianceAgent (LLM / Heuristic)"]
        Risk["RiskAgent (Risk Auditer)"]
        Trans["Translator (Multilingual support)"]
        LD["LanguageDetector"]

        Orch --> PA
        Orch --> EA
        Orch --> RAG
        Orch --> Comp
        Orch --> Risk

        EA --> CA
        EA --> Trans
        RAG --> Trans
        RAG --> LD
        Comp --> Trans
    end

    %% External & Storage Layers
    subgraph Storage ["Storage Layer"]
        DB[(SQL database: SQLite / Neon Postgres)]
        FS[(Local KB Files .txt)]
        
        Orch -->|Store Analysis Runs| DB
        RAG -->|Read/Write Embeddings| DB
        RAG -->|Read default files| FS
    end

    subgraph Models ["LLM Reasoners (Fallback Chain)"]
        Gemini["Google Gemini API"]
        Nvidia["NVIDIA NIM Gateway"]
        Grok["xAI Grok API"]
        Heur["Rule-based Heuristics"]
        
        Comp --> Gemini
        Gemini -.->|Failover| Nvidia
        Nvidia -.->|Failover| Grok
        Grok -.->|Failover| Heur
    end
```

---

## 2. Request Flow: Compliance Analysis Pipeline

When a client submits a tender text or PDF payload for analysis, the request flows sequentially through the agent pipeline:

```mermaid
sequenceDiagram
    autonumber
    actor Client as React Client
    participant Router as API Router (/api/analyze)
    participant Orch as TenderComplianceOrchestrator
    participant Parser as ParserAgent
    participant Extractor as ExtractorAgent
    participant RAG as RAGAgent
    participant Comp as ComplianceAgent
    participant Provider as LLM Provider Chain
    participant Risk as RiskAgent
    participant DB as SQL Database

    Client->>Router: POST /api/analyze (Tender payload)
    Note over Router: Auth & Input Sanitization
    Router->>Orch: analyze(payload)
    
    %% Ingestion
    Orch->>Parser: parse(tender_text / base64_pdf)
    Parser-->>Orch: ParsedDocument (text, language)

    %% Extraction
    Orch->>Extractor: extract(tender_text, source_lang, target_lang)
    Note over Extractor: Split segments & Classify Categories
    Extractor-->>Orch: list[ExtractedRequirement], dict[req_id, normalized_eng_text]

    %% Retrieval & Assessment Loop
    Note over Orch: Begin loop for each requirement
    Orch->>RAG: retrieve(req_text, company_evidence, db)
    Note over RAG: Lexical token match + Cosine similarity (hybrid)
    RAG-->>Orch: list[EvidenceItem]
    
    Orch->>DB: find_feedback_examples(req_text)
    DB-->>Orch: list[FeedbackExample] (historical human corrections)

    Orch->>Comp: assess(req_text, evidence, feedback_examples)
    Comp->>Provider: assess(prompt)
    Note over Provider: Chain: Gemini -> NIM -> Grok -> Heuristics
    Provider-->>Comp: ComplianceDecisionPayload (status, reasoning, confidence)
    Comp-->>Orch: ComplianceMatrixRow
    Note over Orch: End loop

    %% Risk Audit
    Orch->>Risk: analyze(ComplianceMatrixRows)
    Risk-->>Orch: list[RiskFlag], overall_risk

    %% Output Generation & Persistence
    Orch->>DB: create_analysis_run(input, output)
    DB-->>Orch: Saved Analysis ID
    Orch-->>Router: TenderAnalysisResponse
    Router-->>Client: 200 OK (Compliance Matrix JSON)
```

---

## 3. Database Entity-Relationship (ER) Design

The system relies on five main tables to manage analyses, documents, users, feedback corrections, and vector embeddings.

```mermaid
erDiagram
    users {
        int id PK
        string user_id UK "Clerk sub ID"
        string email UK
        string full_name
        string preferred_language
        string preferred_ai_model
        datetime created_at
    }

    document_assets {
        int id PK
        string kind "tender | company | knowledge_base"
        string filename
        string content_type
        int size_bytes
        string content_hash UK
        largebinary file_bytes
        string extracted_text
        string source_language
        datetime created_at
    }

    knowledge_chunks {
        int id PK
        string content_hash UK
        string scope "global | request-id"
        string source
        string language
        string content
        string normalized_content
        vector_or_json embedding "pgvector dim 12 / JSON"
        json metadata "source_kind"
        datetime created_at
    }

    analysis_runs {
        int id PK
        string analysis_id UK
        string tender_title
        string tender_language
        string output_language
        json input_payload
        json output_payload
        datetime created_at
    }

    feedback_entries {
        int id PK
        string analysis_id FK
        string requirement_id
        string requirement_text
        string original_status
        string corrected_status
        string comments
        datetime created_at
    }

    users ||--o. document_assets : "uploads"
    analysis_runs ||--o{ feedback_entries : "has human corrections"
```

---

## 4. Deployment Topologies

The codebase supports two deployment workflows detailed below:

### Topology A: PaaS Deployment (Render + Vercel)
Ideal for staging, quick previews, and testing.

```
       [ Client Browser ]
               | (HTTPS)
               v
     +-------------------+
     |   Vercel Edge     | <--- Serves React + Vite Static Bundle (dist/)
     +-------------------+
               | (REST API Calls)
               v
     +-------------------+
     |   Render Web      | <--- Runs FastAPI Backend in Docker Container
     +-------------------+
               |
               v
     +-------------------+
     |  Render Postgres  | <--- Stores Runs, Feedback & Vector Chunks
     +-------------------+
```

### Topology B: Serverless IaC (GCP Cloud Run + Cloud SQL)
Production architecture managed using Terraform.

```
                                [ Client Browser ]
                                        | (HTTPS Gateway)
                                        v
                            +-----------------------+
                            |     Cloud Run         | <--- Serves Python App + Embedded Frontend
                            |  (Backend & Assets)   |      Scales instance count (0 - 10)
                            +-----------+-----------+
                                        |
               +------------------------+------------------------+
               | (Secure VPC Connection via Connector)           | (Fetch API Keys)
               v                                                 v
  +--------------------------+                      +--------------------------+
  |      Cloud SQL           |                      |     Secret Manager       |
  |  (PostgreSQL + pgvector) |                      | (GEMINI_API_KEY, DB_PWD) |
  +--------------------------+                      +--------------------------+
```
