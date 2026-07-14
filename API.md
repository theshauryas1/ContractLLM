# API Gateway Documentation

This document describes all API endpoints exposed by the backend web server, including payload contracts, headers, and request/response JSON examples.

---

## Headers & Authentication

All API endpoints (except the Copilot endpoints) require authentication when `REQUIRE_AUTH=true` in settings. The gateway accepts two forms of authentication:

1. **Bearer Token (Clerk JWT)**:
   - Header: `Authorization: Bearer <clerk_jwt>`
   - Authenticates user and automatically synchronizes their profile in the database.
2. **Static API Key**:
   - Header: `x-api-key: <backend_api_key>`
   - Bypasses external authentication and authenticates as the static `API Key Agent`.

---

## 1. Compliance Analysis Endpoints

### POST `/api/analyze`
Submits a tender specification (either as raw text or parsed PDF) along with corporate profile evidence and knowledge base documents to generate a compliance matrix.

* **Headers**: `Content-Type: application/json`, auth headers (optional if disabled).
* **Request Schema (`TenderAnalysisRequest`)**:
```json
{
  "tender_title": "Municipal IT Infrastructure",
  "tender_text": "The contractor must deliver ISO 27001 cybersecurity certification. Support must be available 24/7.",
  "tender_document_id": null,
  "company_profile_text": "Our IT systems are ISO 27001 certified. We provide office-hours support.",
  "company_document_id": null,
  "kb_documents": [
    {
      "title": "Corporate Capability Deck",
      "content": "Operating procedures cover strict data protection guidelines."
    }
  ],
  "knowledge_document_ids": [],
  "target_language": "en",
  "top_k": 3
}
```
* **Response Schema (`TenderAnalysisResponse`)**:
```json
{
  "analysis_id": "analysis-1d372e9a2b5c",
  "tender_title": "Municipal IT Infrastructure",
  "tender_language": "en",
  "output_language": "en",
  "parser_source": "text",
  "requirements": [
    {
      "id": "REQ-001",
      "text": "The contractor must deliver ISO 27001 cybersecurity certification.",
      "category": "technical",
      "category_label": "Technical",
      "mandatory": true,
      "evaluation_weight": 1.15
    },
    {
      "id": "REQ-002",
      "text": "Support must be available 24/7.",
      "category": "operational",
      "category_label": "Operational",
      "mandatory": true,
      "evaluation_weight": 1.15
    }
  ],
  "matrix": {
    "rows": [
      {
        "requirement_id": "REQ-001",
        "requirement_text": "The contractor must deliver ISO 27001 cybersecurity certification.",
        "category": "technical",
        "category_label": "Technical",
        "status": "full",
        "status_label": "Full",
        "reasoning": "Company evidence strongly supports this requirement. Best evidence came from company-profile-1.",
        "evidence": [
          {
            "source": "company-profile-1",
            "snippet": "Our IT systems are ISO 27001 certified.",
            "score": 0.95,
            "retrieval_backend": "in-memory"
          }
        ],
        "confidence": 0.88,
        "recommended_action": "Reference the strongest evidence directly in the response matrix.",
        "review_required": false,
        "feedback_examples": [],
        "audit_trail": [
          "Requirement extracted from tender text.",
          "Requirement category: Technical.",
          "Retrieved 1 evidence snippets.",
          "Top evidence source: company-profile-1."
        ]
      },
      {
        "requirement_id": "REQ-002",
        "requirement_text": "Support must be available 24/7.",
        "category": "operational",
        "category_label": "Operational",
        "status": "partial",
        "status_label": "Partial",
        "reasoning": "Company evidence partially addresses this requirement, but important gaps remain. Best evidence came from company-profile-2.",
        "evidence": [
          {
            "source": "company-profile-2",
            "snippet": "We provide office-hours support.",
            "score": 0.52,
            "retrieval_backend": "in-memory"
          }
        ],
        "confidence": 0.61,
        "recommended_action": "Add missing proof, certifications, or delivery detail before submission.",
        "review_required": true,
        "feedback_examples": [],
        "audit_trail": [
          "Requirement extracted from tender text.",
          "Requirement category: Operational.",
          "Retrieved 1 evidence snippets.",
          "Top evidence source: company-profile-2."
        ]
      }
    ],
    "risks": [
      {
        "requirement_id": "REQ-002",
        "severity": "medium",
        "title": "Scoring weakness",
        "rationale": "Evidence is incomplete and may reduce evaluator confidence.",
        "mitigation": "Add missing proof, certifications, or delivery detail before submission."
      }
    ],
    "summary": {
      "full_count": 1,
      "partial_count": 1,
      "missing_count": 0,
      "review_required_count": 1,
      "overall_risk": "medium"
    },
    "executive_summary": "Analysis found 1 full, 1 partial, and 0 missing requirements. Overall risk is Medium.",
    "retrieved_sources": [
      "company-profile-1",
      "company-profile-2"
    ]
  },
  "provider": "heuristic+in-memory",
  "retrieval_backend": "in-memory",
  "reasoning_backend": "heuristic",
  "created_at": "2026-07-14T10:41:00Z"
}
```

---

### GET `/api/analyses`
Lists summaries of all historical analysis runs.

* **Response Schema (`AnalysisListResponse`)**:
```json
{
  "analyses": [
    {
      "analysis_id": "analysis-1d372e9a2b5c",
      "tender_title": "Municipal IT Infrastructure",
      "tender_language": "en",
      "output_language": "en",
      "overall_risk": "medium",
      "missing_count": 0,
      "created_at": "2026-07-14T10:41:00Z"
    }
  ]
}
```

---

### GET `/api/analyses/{analysis_id}`
Retrieves the full analysis matrix and risk details of a specific analysis run.

* **Response Schema (`TenderAnalysisResponse`)**: Same schema as `POST /api/analyze`.

---

## 2. Document Library Endpoints

### POST `/api/documents`
Uploads a text or PDF file to extract its content and persist it as a document asset in the database.

* **Request Content-Type**: `multipart/form-data`
* **Form Fields**:
  - `kind` (string): Options are `tender`, `company`, `knowledge_base`.
  - `file` (binary): The file to upload (PDF, TXT, etc.).
* **Response Schema (`DocumentUploadResponse`)**:
```json
{
  "id": 4,
  "filename": "iso_certification_evidence.pdf",
  "kind": "company",
  "content_type": "application/pdf",
  "size_bytes": 102344,
  "extracted_text_preview": "ISO 27001 Certification. Holds certification valid until 2028...",
  "source_language": "en",
  "created_at": "2026-07-14T10:41:00Z"
}
```

---

### GET `/api/documents`
Lists metadata for all uploaded document assets.

* **Response Schema (`DocumentListResponse`)**:
```json
{
  "items": [
    {
      "id": 4,
      "filename": "iso_certification_evidence.pdf",
      "kind": "company",
      "content_type": "application/pdf",
      "size_bytes": 102344,
      "extracted_text_preview": "ISO 27001 Certification. Holds certification valid until 2028...",
      "source_language": "en",
      "created_at": "2026-07-14T10:41:00Z"
    }
  ]
}
```

---

### GET `/api/documents/{document_id}/download`
Downloads the raw uploaded file bytes.

* **Response**: Binary stream containing file contents, with header `Content-Disposition: attachment; filename="<filename>"`.

---

## 3. Reviewer Feedback Loop Endpoints

### POST `/api/feedback`
Saves a reviewer override or comment for a specific requirement analysis.

* **Request Schema (`FeedbackRequest`)**:
```json
{
  "analysis_id": "analysis-1d372e9a2b5c",
  "requirement_id": "REQ-002",
  "requirement_text": "Support must be available 24/7.",
  "original_status": "partial",
  "corrected_status": "full",
  "comments": "We signed an agreement with an external NOC provider for 24/7 coverage last week."
}
```
* **Response Schema (`FeedbackRecord`)**:
```json
{
  "id": 1,
  "analysis_id": "analysis-1d372e9a2b5c",
  "requirement_id": "REQ-002",
  "requirement_text": "Support must be available 24/7.",
  "original_status": "partial",
  "corrected_status": "full",
  "comments": "We signed an agreement with an external NOC provider for 24/7 coverage last week.",
  "created_at": "2026-07-14T10:41:00Z"
}
```

---

### GET `/api/feedback`
Retrieves all historical feedback overrides.

* **Response Schema (`FeedbackListResponse`)**:
```json
{
  "items": [
    {
      "id": 1,
      "analysis_id": "analysis-1d372e9a2b5c",
      "requirement_id": "REQ-002",
      "requirement_text": "Support must be available 24/7.",
      "original_status": "partial",
      "corrected_status": "full",
      "comments": "We signed an agreement with an external NOC provider for 24/7 coverage last week.",
      "created_at": "2026-07-14T10:41:00Z"
    }
  ]
}
```

---

## 4. User Profile & Preference Endpoints

### GET `/api/users/me`
Retrieves settings, preferences, and profile details for the authenticated user (synced from Clerk JWT metadata).

* **Response Schema (`UserProfileResponse`)**:
```json
{
  "user_id": "usr_test_default",
  "email": "guest@legalaip.com",
  "full_name": "Guest User",
  "preferred_language": "en",
  "country": "US",
  "state": "California",
  "timezone": "America/Los_Angeles",
  "legal_profession": "Contract Manager",
  "industry": "IT Procurement",
  "org_id": "org_123",
  "default_jurisdiction": "federal",
  "preferred_ai_model": "gemini-flash-latest",
  "created_at": "2026-07-14T10:41:00Z"
}
```

---

### PUT `/api/users/me`
Updates preferences (e.g. default target language or choice of model models).

* **Request Schema (`UserProfileUpdateRequest`)**:
```json
{
  "full_name": "Senior Bid Specialist",
  "preferred_language": "de",
  "preferred_ai_model": "meta/llama-3.3-70b-instruct",
  "default_jurisdiction": "EU"
}
```
* **Response Schema (`UserProfileResponse`)**:
```json
{
  "user_id": "usr_test_default",
  "email": "guest@legalaip.com",
  "full_name": "Senior Bid Specialist",
  "preferred_language": "de",
  "country": "US",
  "state": "California",
  "timezone": "America/Los_Angeles",
  "legal_profession": "Contract Manager",
  "industry": "IT Procurement",
  "org_id": "org_123",
  "default_jurisdiction": "EU",
  "preferred_ai_model": "meta/llama-3.3-70b-instruct",
  "created_at": "2026-07-14T10:41:00Z"
}
```

---

## 5. Dashboard Metrics Endpoints

### GET `/api/overview`
Retrieves dashboard summary counters and lists recent analyses.

* **Response Schema (`DashboardOverview`)**:
```json
{
  "total_analyses": 1,
  "total_requirements": 2,
  "high_risk_analyses": 0,
  "feedback_items": 1,
  "average_confidence": 0.745,
  "languages": ["en"],
  "recent_analyses": [
    {
      "analysis_id": "analysis-1d372e9a2b5c",
      "tender_title": "Municipal IT Infrastructure",
      "tender_language": "en",
      "output_language": "en",
      "overall_risk": "medium",
      "missing_count": 0,
      "created_at": "2026-07-14T10:41:00Z"
    }
  ]
}
```

---

## 6. AI Legal Copilot Endpoints

### POST `/api/copilot/chat`
Conversational chat interface targeting legal compliance, supporting user-defined custom context.

* **Request Schema (`ChatRequest`)**:
```json
{
  "message": "Do we satisfy requirement REQ-002?",
  "context": "Requirement REQ-002 states that we must support 24/7 operations, but we only have office hours support in our company profile."
}
```
* **Response**:
```json
{
  "reply": "Based on the provided context, the company does not fully satisfy requirement REQ-002. Your profile states support is available only during standard office hours, creating a compliance gap for the requested 24/7 availability. It is recommended to partner with an external NOC provider or request an amendment."
}
```

---

### POST `/api/copilot/draft`
Drafts a legally binding agreement template using context parameters.

* **Request Schema (`DraftRequest`)**:
```json
{
  "template_name": "Non-Disclosure Agreement",
  "party_details": "Party A: Acme Corp (Delaware)\nParty B: Innovate Inc (California)",
  "custom_terms": "Mutual confidentiality obligations, duration of 3 years, governed by Delaware law."
}
```
* **Response**:
```json
{
  "draft": "MUTUAL NON-DISCLOSURE AGREEMENT\n\nThis Mutual Non-Disclosure Agreement (the 'Agreement') is entered into as of this day by and between:\n- Acme Corp, a Delaware corporation ('Party A')...\n- Innovate Inc, a California corporation ('Party B')...\n\n1. Purpose...\n2. Confidentiality Obligation...\n3. Duration: This Agreement shall remain in effect for three (3) years...\n4. Governing Law: This Agreement shall be governed by Delaware law..."
}
```

---

### POST `/api/copilot/search-citations`
Finds legal cases, precedents, and citations matching query keywords.

* **Request Schema (`CitationSearchRequest`)**:
```json
{
  "keywords": "Material adverse effect Delaware corporate law"
}
```
* **Response**:
```json
{
  "results": " Delaware Court of Chancery Case Law Precedents:\n\n1. Akorn, Inc. v. Fresenius Kabi AG (Del. Ch. 2018)\n   - Summary: Landmark ruling finding a Material Adverse Effect (MAE) occurred, justifying the buyer's termination of the merger agreement.\n   - Citation: Akorn, Inc. v. Fresenius Kabi AG, C.A. No. 2018-0300-JTL (Del. Ch. Oct. 1, 2018)\n\n2. IBP, Inc. v. Tyson Foods, Inc. (Del. Ch. 2001)\n   - Summary: Established that an MAE must be durationally significant, rather than a short-term blip in earnings.\n   - Citation: 789 A.2d 14 (Del. Ch. 2001)"
}
```
