# Continue AI Workbench in Codex

This is a standalone repository consolidated from the previous **AI Workbench Starter** and **AI Workbench Hub** projects.

## Current baseline

- Python CLI (`src/aiwh`) with `init`, `resume`, `audit`, `profiles`, `capabilities`, `sync`, `attach`, `report` and `doctor`.
- Canonical library in `capabilities/`: 22 skills, 10 agent role templates, 8 project profiles and opt-in MCP catalog.
- CLI installs only relevant project skills; private handoffs and optional bookmark/GitHub catalogs are not committed.
- Adapters for Codex, Claude Code, Google Antigravity, Hermes and OpenClaude.
- Tests in `tests/`; run `python -m unittest discover -s tests -v`.

## Instructions for the next coding session

1. Inspect the code, docs, test suite and current Git status before changing files.
2. Run tests and check the existing CLI behavior before proposing changes.
3. Prioritize reliable project bootstrap and continuity; avoid adding unrelated bookmark-management features.
4. Extend the capability registry with curation, provenance, conflict detection and user-approved updates.
5. Improve runtime adapters by verifying each tool's current documented instruction/skill path. Do not auto-enable MCPs.
6. Design a cross-agent *handoff schema* containing observable project state, decisions and TODOs. Distinguish notes from verifiable evidence.
7. Add a Windows opt-in onboarding flow. Do not install global hooks or modify user machine configuration without explicit approval.
8. Keep documentation in English, tests deterministic, and local data gitignored.

## Suggested next milestones

- M1: Contract tests for all adapter locations and project types; done at starter level.
- M2: Non-destructive CLI updates, project state snapshots, diffing between sessions.
- M3: Searchable curated references with source provenance, ranking and optional AI semantics.
- M4: Optional runtime adapter configuration and opt-in global initialization.
- M5: End-to-end testing on Windows with real Codex/Claude/Antigravity/Hermes/OpenClaude installations.

The term **continuity** does not imply that AI Workbench can read or export proprietary agent chat histories. It preserves portable, local context and code evidence instead.

## New: cross-domain area routing

Use `aiwh areas` to list 26 areas. Use `aiwh recommend . --goal "..." --json` to inspect a read-only contextual plan; use multiple explicit `--area` values or opt in with `--auto-areas` during `aiwh init`. Agent roles are reference templates. MCP/plugin recommendations never activate external connections or require private tokens. See `docs/AREAS.md` and `docs/RESEARCH.md` before extending the catalog.
