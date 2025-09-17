# Refresh Architecture & Data Flow Diagram

**Description:** Update the ONE high-level diagram for docs.

**Prompt:**
Scan the repo and produce a single updated Mermaid diagram that captures:
- User entry points (CLI/UI/API)
- Core services/modules
- Data stores (files, DBs, Neo4j)
- External APIs (auth, CV, weather)
- Primary flows (ingest → process → persist → visualize)

Keep it one screenful. Then insert it into:
- `docs/guide/architecture.md` (replace prior diagram)
- Add a small “Assumptions & Constraints” list below it (≤5 bullets)

**Acceptance:** One diagram, no duplication; page renders; links intact.

