# MkDocs Portfolio (Material) — Generate/Refresh

**Description:** Create or update a polished MkDocs site (Material theme) with friendly CTAs, tags, and one high-level diagram.

**Prompt:**
You are a senior dev-writer. Inspect the repo and produce/refresh:
- `mkdocs.yml` (Material theme; search, tags; optional blog; emoji + Mermaid enabled)
- `docs/index.md` (hero, 2–3 highlights, **Launch App →** button if available)
- `docs/get-started.md` (5-minute quickstart)
- `docs/guide/architecture.md` (one Mermaid overview)
- `docs/guide/how-it-works.md`, `docs/guide/faq.md`, `docs/guide/troubleshooting.md`
- `docs/tags.md`
Reuse existing markdown where possible; **link don’t duplicate**. Keep portfolio tone (concise, visual). If notebooks exist, add notes for `mkdocs-jupyter` usage (do not break builds if not installed).

**Acceptance:**
- `mkdocs serve` would succeed with only search+tags enabled.
- Exactly one architecture Mermaid diagram.
- Buttons/links resolve; no hardcoded secrets.

