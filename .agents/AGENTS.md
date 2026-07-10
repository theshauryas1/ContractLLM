# Workspace Rules: Tender Compliance Engine

This file defines style guidelines, behavioral constraints, and instructions for AI agents working in this workspace.

## 1. Core Codebase Principles

- **Architecture**: Always respect the decoupled agentic architecture. The backend uses FastAPI, SQLAlchemy, and a set of domain-specific agents (`ParserAgent`, `ExtractorAgent`, `RAGAgent`, `ComplianceAgent`, `RiskAgent`).
- **Data Layer**: Use SQLite for local development and PostgreSQL with `pgvector` for production (Neon). Ensure all DB queries are executed through SQLAlchemy sessions.
- **Multilingual Support**: Ensure text normalization, translation fallbacks, and detection match the configuration in `LanguageDetector` and `Translator`.
- **Frontend**: The frontend is built with React, Vite, and vanilla CSS for rich aesthetics. Avoid ad-hoc utility classes; use the design tokens defined in index.css.

## 2. Documentation and Context-Preservation Rules

- **Documentation Sync**: Any time a new backend API, database schema, environment variable, or core agent behavior is added/modified, update [README.md](file:///d:/ContractLLM/README.md) and the corresponding API schemas.
- **Context Preservation**: At the end of every significant task or session, document the changes, tests run, and state updates. Recommend or use context-management skills (`context-management-context-save`) to store progress.
- **File References**: When referencing codebase files or components, always use absolute file URLs (`file:///d:/ContractLLM/...`) to maintain clickable context.

## 3. Testing Constraints

- All functional changes to backend APIs or agents MUST be accompanied by unit or integration tests under [tests/](file:///d:/ContractLLM/tests).
- Run `python -m pytest -q` to verify the codebase remains stable after changes.
