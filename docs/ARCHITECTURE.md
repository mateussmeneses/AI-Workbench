# Architecture

## Modules

1. **Capability Registry (`capabilities/`)** — canonical, versioned repository of skills (`SKILL.md`), role templates, MCP recommendations and technology profiles. This is the single source of truth.
2. **Bootstrap (`src/aiwh/workbench.py`)** — selects profiles, copies skills to recognized agent paths, writes an `AI-WORKBENCH.md` guide and updates only a managed instruction block in project files. It never executes copied skill instructions.
3. **Continuity (`src/aiwh/workbench.py`)** — reads only local Git metadata, common build/test indicators and documented roadmap checkboxes, then writes a private, gitignored context snapshot. It does not run tests or claim outcomes.
4. **Resource Hub (`src/aiwh/core.py`)** — optional indexing of user bookmarks and GitHub stars with deduplication and heuristic project recommendations. It only reads input sources; classification is not LLM-based yet.
5. **Adapters** — Codex (`AGENTS.md`, `.agents/skills`), Claude Code (`CLAUDE.md`, `.claude/skills`), Antigravity (`AGENTS.md`, `.agents/skills`), Hermes (`.agents/skills`, explicit trust), and OpenClaude (`.openclaude/skills`). MCP catalog entries are never activated automatically.

## Data flow

`Repository / project intent -> profile selection -> capability manifests -> native skills + instruction pointer -> local working session -> evidence scan -> .ai-workbench/CONTEXT.md -> next agent/session`

Optional: `browser bookmarks / GitHub stars -> private catalog -> ranked reference list -> local project attachment`.

## Storage and identity

- Portable configuration: checked-in files `AGENTS.md`, `CLAUDE.md`, `AI-WORKBENCH.md` and skill directories.
- Private handoff: project `.ai-workbench/` (added to `.gitignore`).
- Private resource catalog: `~/.ai-workbench-hub/catalog.json` or `--home` override.
- No token stores, global hooks, background daemons, network calls, or automatic execution during bootstrap or resume.

## Changes and conflict policy

- The `<!-- AIWH:BEGIN --> ... <!-- AIWH:END -->` block marks managed instructions.
- Existing material outside the marker is retained.
- Skills that already exist with different bytes are left untouched and reported as conflicts.
- Dry runs perform no writes. Existing project directories are never deleted or recreated.
- Project metadata and MCP suggestions are non-authoritative; verify them during actual work.

## Limitations

- Skills are reusable procedures, not registered native subagents.
- An attached resource is a suggestion, not installed code.
- Auto-detection uses heuristics; use explicit `--profile` overrides when needed.
- Continuity does not automatically mine private conversations, CI services or external issue trackers.
- Hermes needs per-repository trust approval; the CLI cannot grant it.
- Behavioral equivalence across agent models is not guaranteed.

## Cross-domain routing (v0.3)

`src/aiwh/areas.py` interprets `capabilities/areas/catalog.json` through bounded source-tree and project-metadata signals. It produces an explainable ranked proposal with 26 composable areas and six capability kinds: profiles, skills, agent-role templates, MCP candidates, plugin candidates, and CLI utilities. `aiwh recommend` is read-only; `aiwh init --area` and `--auto-areas` are deliberate opt-in installation of project-local skills only. External plugins and MCPs are never connected automatically.

The scan avoids recursive dependency trees and generated folders and does not execute foreign code. Because its classification is deterministic (not a trained model) users should verify ranked suggestions; agents can consume the recommendation plan as grounded context. References are catalogued, never silently fetched or run.
