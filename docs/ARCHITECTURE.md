# Architecture

## Modules

1. **Capability Registry (`capabilities/`)** — canonical, versioned repository of skills (`SKILL.md`), role templates, MCP recommendations and technology profiles. This is the single source of truth.
2. **Bootstrap (`src/aiwh/workbench.py`)** — selects profiles, copies skills to recognized agent paths, writes an `AI-WORKBENCH.md` guide and updates only a managed instruction block in project files. It never executes copied skill instructions.
3. **Continuity (`src/aiwh/workbench.py`)** — reads only local Git metadata, common build/test indicators and documented roadmap checkboxes, then writes a private, gitignored context snapshot. It does not run tests or claim outcomes.
4. **Resource Hub (`src/aiwh/core.py`)** — optional indexing of user bookmarks and GitHub stars with deduplication and heuristic project recommendations. It only reads input sources; classification is not LLM-based yet.
5. **Adapters** — Codex (`AGENTS.md`, `.agents/skills`), Claude Code (`CLAUDE.md`, `.claude/skills`), Antigravity (`AGENTS.md`, `.agents/skills`), Hermes (`.agents/skills`, explicit trust), and OpenClaude (`.openclaude/skills`). MCP catalog entries are never activated automatically.

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
