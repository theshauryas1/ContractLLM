---
name: contract-llm-docs
description: "Guidelines and instructions for generating documentation, onboarding guides, and wikis for the ContractLLM repository using Antigravity skills."
---

# ContractLLM Custom Documentation Skill

Use this skill when you are asked to generate or update documentation, wikis, onboarding guides, or README files for the ContractLLM (Tender Compliance Engine) codebase.

## Codebase Architecture Reference

When generating guides or wiki pages, trace the flow through the core agent components:

1. **ParserAgent** ([parser_agent.py](file:///d:/ContractLLM/backend/compliance/parser_agent.py))
   - Parses pasted text or base64 PDF payloads.
2. **ExtractorAgent** ([extractor_agent.py](file:///d:/ContractLLM/backend/compliance/extractor_agent.py))
   - Extracts individual requirements and categorizes them.
3. **RAGAgent** ([rag_agent.py](file:///d:/ContractLLM/backend/compliance/rag_agent.py))
   - Performs hybrid vector/lexical search to fetch supporting evidence.
4. **ComplianceAgent** ([compliance_agent.py](file:///d:/ContractLLM/backend/compliance/compliance_agent.py))
   - Classifies requirements into `full`, `partial`, or `missing`.
5. **RiskAgent** ([risk_agent.py](file:///d:/ContractLLM/backend/compliance/risk_agent.py))
   - Scans output rows and flags eligibility, disqualification, or scoring risks.
6. **Orchestrator** ([orchestrator.py](file:///d:/ContractLLM/backend/compliance/orchestrator.py))
   - Coordinates the entire pipeline execution from input ingestion to finalized risk matrix output.

## Documentation Guidelines

### 1. Zero-to-Hero & Onboarding Docs
When using the built-in `wiki-architect` skill:
- **Principal-Level Guide**: Explain the core orchestrator flow where the user request passes from extraction through retrieval, compliance mapping, and risk checks.
- **Zero-to-Hero Path**: Explain the interaction between the FastAPI endpoints ([api](file:///d:/ContractLLM/backend/api)) and the react dashboard ([frontend/src](file:///d:/ContractLLM/frontend/src)).
- **Comparison Language**: Since this codebase is Python-based, use JavaScript/TypeScript as the comparison language.

### 2. Precise File Citations
- Always cite specific implementation files using clickable absolute paths (e.g., `file:///d:/ContractLLM/...`).
- Ensure code block snippets map exactly to the current codebase versions of the agents.

### 3. Synchronization Checklists
Before finishing a documentation task, verify that:
- Core environment variables in the documentation match those in [config.py](file:///d:/ContractLLM/backend/core/config.py) (if applicable) or [README.md](file:///d:/ContractLLM/README.md).
- Any newly added FastAPI routes are documented with payload formats.
