# Craft Commit Message (Conventional Commits)

**Description:** Propose a clear, single-line commit message + optional body using Conventional Commits. Do NOT mention AI or Claude.

**Prompt:**
Given the staged changes and recent discussion, output:
- `type(scope): concise title`
- Body (wrap at ~72 chars): what/why, notable trade-offs
- Footer: issue/PR refs (e.g., `Refs #123`), BREAKING CHANGE if needed

Types: feat, fix, docs, refactor, test, chore, build, ci, perf.
Prefer “what changed + why” over restating filenames.

**Example Output:**
feat(exif): add timestamp/GPS unit tests and parser fallback

- Add happy-path+edge-case EXIF tests (no GPS, malformed date)
- Fallback to file mtime when EXIF missing; log warning
- Improves weather join reliability

Refs #42

