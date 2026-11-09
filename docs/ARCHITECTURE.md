# Architecture

## Modules

1. **Capability Registry (`capabilities/`)** — canonical, versioned repository of skills (`SKILL.md`), role templates, MCP recommendations and technology profiles. This is the single source of truth.
2. **Bootstrap (`src/aiwh/workbench.py`)** — selects profiles, copies skills to recognized agent paths, writes an `AI-WORKBENCH.md` guide and updates only a managed instruction block in project files. It never executes copied skill instructions.
3. **Continuity (`src/aiwh/workbench.py`)** — reads only local Git metadata, common build/test indicators and documented roadmap checkboxes, then writes a private, gitignored context snapshot. It does not run tests or claim outcomes.
4. **Resource Hub (`src/aiwh/core.py`)** — optional indexing of user bookmarks and GitHub stars with deduplication and heuristic project recommendations. It only reads input sources; classification is not LLM-based yet.
5. **References (`src/aiwh/references.py`)** — curated public reference catalog (`capabilities/references/catalog.json`) with areas, kinds and risk labels; generates `docs/REFERENCES.md`, feeds `recommend`/`attach`, runs opt-in `gh` freshness checks and lists curation candidates from user-selected sources without editing the catalog.
6. **Skill tools (`src/aiwh/skilltools.py`)** — skill lint (vague/boilerplate/near-duplicate), approximate context-cost estimates and provenance-tracked imports of local skills through the managed-file manifest.
7. **MCP plans (`src/aiwh/mcp_plan.py`)** — per-agent configuration previews from catalog `server` entries; the only write is an explicit, manifest-owned project `.mcp.json` for Claude Code.
8. **Exports (`src/aiwh/handoff_export.py`, `src/aiwh/html_report.py`)** — handoff exports (json, markdown, claude-memory, wiki) and an offline HTML catalog view, written only to explicit or private locations.
9. **Adapters** — Codex (`AGENTS.md`, `.agents/skills`), Claude Code (`CLAUDE.md`, `.claude/skills`), Antigravity (`AGENTS.md`, `.agents/skills`), Hermes (`.agents/skills`, explicit trust), and OpenClaude (`.openclaude/skills`). MCP catalog entries are never activated automatically.

## Registry validation

`registry()` validates canonical source assets before returning the existing profile, skill-path, role-path and MCP mappings. It does not validate or overwrite user-modified installed skills.

- Skills require UTF-8 `SKILL.md` files with opening/closing `---` frontmatter delimiters, non-empty string `name` and `description`, and a non-empty body. Names must match their directory and use lowercase alphanumeric segments separated by single hyphens, at most 64 characters.
- An optional skill `version` must be a string in `major.minor.patch` format. Descriptions may use YAML block scalars. PyYAML's safe loader parses metadata; duplicate fields, non-string keys, malformed YAML and Python-specific object tags are rejected.
- Profiles must be JSON objects with non-empty string descriptions. Optional `skills`, `agents`, `mcps` and `utilities` fields must be lists of unique non-empty strings. Skill, role and MCP references must resolve; utility names are recommendations, not executable availability checks.
- Duplicate JSON keys are rejected, including nested objects. MCP entries must be objects with literal boolean `enabledByDefault: false`; catalog reading never activates them.
- Required capability directories and the MCP catalog file must exist; role files must be readable, non-empty UTF-8 templates. Missing referenced skills or roles are reported as unresolved IDs.

Invalid inputs raise `ValueError` with the source path and failing field or reference. Duplicate skill-directory IDs include both conflicting paths. This is structural validation, not proof that a skill's procedure is correct or compatible with a real agent runtime.

## Distribution assets

`pyproject.toml` maps the canonical `capabilities/` directory to the data package `aiwh.capabilities`, with explicit runtime asset patterns. Wheels include profiles, role templates, skills, area/MCP/plugin catalogs, routing policy and the bundled taxonomy. Source distributions additionally include the canonical taxonomy and verification script through `MANIFEST.in`; no private user catalog is a distribution input.

At runtime, `workbench.py` prefers the capability directory beside the installed package and falls back to the repository's canonical directory for editable/source use. `core.py` retains its packaged taxonomy fallback. No bootstrap command copies or modifies the user's Python installation.

`scripts/Verify-Package.py` checks expected archive paths and source bytes before installing. It rejects missing/stale runtime assets, unexpected payload files, private/generated paths and unsafe archive names. The smoke uses a temporary venv and project, offline pip installation and isolated module execution; an explicit host-dependency reuse option is reported separately from clean-wheelhouse mode.

The existing CI and release workflows now install declared dependencies, build wheel/sdist artifacts and run the clean-wheelhouse verifier. Release publishing remains conditional on an explicitly authorized tag and passing checks; modifying workflow files does not execute or publish them.

The Python floor remains 3.10. CI is configured for Windows and Ubuntu with Python 3.10/3.12/3.14; hosted CI was not observed during local validation. Local evidence: Windows/Python 3.10.22, clean wheelhouse installation of PyYAML 6.0.3, 49 unit tests and `aiwh doctor` passed. The verifier also passed wheel/sdist asset checks and CLI smoke against the installed package outside the checkout. Python 3.13/3.14 porting guidance was consulted; the verifier uses APIs available on 3.10.

## Data flow

`Repository / project intent -> profile selection -> capability manifests -> native skills + instruction pointer -> local working session -> evidence scan -> .ai-workbench/CONTEXT.md -> next agent/session`

Optional: `browser bookmarks / GitHub stars -> private catalog -> ranked reference list -> local project attachment`.

## Storage and identity

- Portable configuration: checked-in files `AGENTS.md`, `CLAUDE.md`, `AI-WORKBENCH.md` and skill directories.
- Private handoff: project `.ai-workbench/` (added to `.gitignore`).
- Private resource catalog: `~/.ai-workbench-hub/catalog.json` or `--home` override.
- No token stores, global hooks, background daemons, network calls, or automatic execution during bootstrap or resume.

`state.json` schema version 2 wraps the latest observation in `observed` and retains user-maintained `tasks`, `decisions` and `resources`, plus the latest comparison in `latest_delta`. Up to 10 snapshots retain their observations and explicit records. Deltas compare Git-status paths, documented pending items, task blockers/status, approved decisions and resource records. Resource outcomes without an explicit usefulness value are labeled unknown; selection does not imply use or success. Tasks have stable IDs, status, blockers, risks and milestone outcomes; checklist IDs are reused when present, otherwise IDs derive deterministically from source path and title. Decisions must be explicitly approved and include rationale. Resources record a selected/rejected choice and rationale; `usefulness` accepts only explicit `useful`/`not_useful` feedback. Migration from unversioned state or schema v1 preserves legacy data under `legacy_observation`. Corrupt or unsupported schemas fail before either handoff file is written, and state replacement uses a same-directory atomic replace. Resume remains non-executing and does not access agent chat history.

## Changes and conflict policy

- The `<!-- AIWH:BEGIN --> ... <!-- AIWH:END -->` block marks managed instructions.
- Existing material outside the marker is retained.
- `aiwh init` records SHA-256 hashes for project-relative files it creates or safely merges in `.ai-workbench/managed-files.json` (`schema_version: 1`). The manifest excludes itself and is private/gitignored.
- Dry-run results classify managed paths as `added`, `unchanged`, `changed` or `conflicting`, and report whether the manifest would be created, updated or left unchanged. The classification is also used during apply.
- Existing unmanifested files with differing content are treated as conflicts and preserved, except first-time append/merge of the AI Workbench instruction block and `.gitignore` entry, which retain all existing text. Identical unmanifested files are not claimed as owned.
- Re-running `aiwh init` is the explicit update operation: a file is updated only if its current hash matches the manifest. A file whose current hash differs is reported as a conflict and left untouched. Corrupt, unsupported-version or symlinked manifests fail closed.
- `aiwh managed remove PROJECT --dry-run` previews removal; omit `--dry-run` to apply it. Exclusive manifest-owned files are deleted only when their hash matches. For AGENTS/CLAUDE and `.gitignore`, removal strips only the recognizable Workbench block/entry and preserves remaining content. Missing files are forgotten; changed, symlinked or unrecognized content remains a conflict in the manifest.
- Handoffs/state, game-port plans, other unmanifested files and the manifest itself are never deleted by this command; empty parent directories are retained.
- Multi-file writes/removals use a private journal and per-file backups in `.ai-workbench/managed-files.transaction`. The manifest is updated within the same transaction. The next mutating `init` or `managed remove` recovers an interrupted operation before loading the manifest: it restores old bytes only if the target is still the transaction's expected output, and refuses to overwrite an intervening user change. Dry-run with a pending transaction fails without writes and directs the user to run an explicit mutating recovery. Successful transactions mark committed before cleaning backups, so interrupted cleanup does not roll back completed work. This protects against process interruption, not storage/hardware failure.
- Existing project directories are never deleted or recreated.
- Project metadata and MCP suggestions are non-authoritative; verify them during actual work.

## Limitations

- Skills are reusable procedures, not registered native subagents.
- An attached resource is a suggestion, not installed code.
- Auto-detection uses heuristics; use explicit `--profile` overrides when needed.
- Continuity does not automatically mine private conversations, CI services or external issue trackers.
- Hermes needs per-repository trust approval; the CLI cannot grant it.
- Behavioral equivalence across agent models is not guaranteed.

## Cross-domain routing (v0.3)

`src/aiwh/areas.py` interprets `capabilities/areas/catalog.json` through bounded source-tree and project-metadata signals. It produces an explainable ranked proposal with 27 composable areas and six capability kinds: profiles, skills, agent-role templates, MCP candidates, plugin candidates, and CLI utilities. `aiwh recommend` is read-only; `aiwh init --area` and `--auto-areas` are deliberate opt-in installation of project-local skills only. External plugins and MCPs are never connected automatically.

The scan avoids recursive dependency trees and generated folders and does not execute foreign code. Because its classification is deterministic (not a trained model) users should verify ranked suggestions; agents can consume the recommendation plan as grounded context. References are catalogued, never silently fetched or run.
