# Continue AI Workbench in Codex

This is a standalone repository consolidated from the previous **AI Workbench Starter** and **AI Workbench Hub** projects.

## Current baseline

- Version 0.4.0.dev0. Python CLI (`src/aiwh`) with `init`, `resume`, `audit`, `handoff`, `managed`, `profiles`, `areas`, `recommend`, `capabilities`, `skills`, `mcp`, `game-port`, `inspect`, `spec`, `cleanroom`, `sync`, `curate`, `references`, `catalog`, `attach`, `report`, `doctor` and `global-integration`. Use `aiwh --help` and command-specific `--help` for current options.
- Canonical library in `capabilities/`; use `aiwh capabilities` and `aiwh areas` for current counts and identifiers rather than relying on cached totals.
- CLI installs only relevant project skills; private handoffs and optional bookmark/GitHub catalogs are not committed.
- Project file adapters for Codex, Claude Code, Google Antigravity, Hermes and OpenClaude have synthetic path tests, not real-runtime certification. See [adapter evidence](docs/AGENTS.md).
- Global managed instruction blocks are already implemented for Codex, Claude and Antigravity, with explicit application and removal. They are not automatic startup hooks.
- Tests in `tests/`; run `python -m unittest discover -s tests -v`.

## Instructions for the next coding session

1. Read AGENTS.md, README.md and docs/ARCHITECTURE.md; run `aiwh resume . --dry-run` and inspect the current Git status before changing files.
2. Read [the canonical roadmap](docs/ROADMAP.md), including completion notes. Select the earliest incomplete, unblocked task; do not maintain a second milestone queue here.
3. Establish the task's local behavior and focused check, then implement only that scope. Preserve existing user changes and instructions.
4. Run the focused check, `python -m unittest discover -s tests -v` and `aiwh doctor`; report observed outcomes separately from test indicators or runtime assumptions.
5. Update the roadmap task, sanitized completion note and Unreleased changelog after acceptance checks pass. Record blockers and the next eligible task.
6. Keep documentation in English, tests deterministic and local data gitignored. Commits, branches, tags, publishing and system-wide changes require explicit authorization.

## Current continuity limits

`resume` scans local Git metadata, test/build indicators and documented pending work, then writes `.ai-workbench/CONTEXT.md` and `state.json` unless `--dry-run` is used. It includes up to 60 documented pending items (a scan that hits the limit is flagged as truncated), keeps up to 10 state snapshots with comparisons between sessions, and persists approved decisions and task status in `state.json` (schema v2). It does not execute tests.

The term **continuity** does not imply that AI Workbench can read or export proprietary agent chat histories. It preserves portable, local context and code evidence instead.

## Cross-domain area routing

Use `aiwh areas` to list 27 areas. Use `aiwh recommend . --goal "..." --json` to inspect a read-only contextual plan; use multiple explicit `--area` values or opt in with `--auto-areas` during `aiwh init`. Agent roles are reference templates. MCP/plugin recommendations never activate external connections or require private tokens. See `docs/AREAS.md` and `docs/RESEARCH.md` before extending the catalog.
