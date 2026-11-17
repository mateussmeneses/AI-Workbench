# AI Workbench

**Local-first project bootstrap, cross-session continuity, and capability intelligence for coding agents.**

AI Workbench (`aiwh`) is an independent, offline-capable CLI and curated capability library. It equips projects with portable skills, role templates, explainable recommendations, revision-bound handoffs, and a private local resource hub—without mandatory paid providers, background daemons, or automatic execution of third-party code.

---

## Key Capabilities

- **Transactional Project Bootstrap (`aiwh init`, `aiwh managed remove`):** Detects project technology or composes explicit `--area` / `--profile` selections, installs validated skills into agent-specific directories, preserves existing instructions (`AGENTS.md` / `CLAUDE.md`), and tracks every owned file in `.ai-workbench/managed-files.json` with SHA-256 hashes and rollback journaling.
- **Durable Cross-Session Continuity (`aiwh resume`, `aiwh handoff ...`):** Scans local Git state, recent commits, test indicators, and up to 60 documented pending items without executing project code. Maintains `.ai-workbench/state.json` (schema v2, up to 10 snapshots with session deltas), `depends_on` task dependencies, single-owner claims (`handoff claim`), drift checks (`handoff check`), state linting (`handoff lint`), self-contained execution plans (`handoff plan`), and exports (`json`, `markdown`, `claude-memory`, `wiki`).
- **Explicit CLI State Management (`aiwh handoff decide | reject | feedback | task`):** Record approved or retracted decisions, rejected findings, resource usefulness feedback, and task status/blockers/dependencies directly from the CLI without hand-editing JSON.
- **Supervised Validation Evidence (`aiwh validate`):** Previews the validation command, working directory, timeout, and revision by default; executes only with `--approve`, redacts common credential patterns, bounds output, and marks evidence `stale` when `HEAD` moves or the working tree changes.
- **Contextual Resource Intelligence (`aiwh recommend`, `aiwh game-port`):** Ranks **27** composable capability areas from bounded project evidence and stated goals, producing a **top-5 contextual shortlist** with reasons/limits, an **MCP Advisor**, and specialized triage across **16** game-porting platforms.
- **Curated Reference & Private Resource Hub (`aiwh sync`, `aiwh curate`, `aiwh search`, `aiwh report`):** Indexes GitHub stars (`gh` CLI), Chromium bookmarks, and Netscape HTML into a private home catalog (`~/.ai-workbench-hub`). Includes **491** curated public references with risk labels, **SQLite FTS5** local search (upgradable to hybrid vector + BM25 RRF via `.[semantic]`), and a paginated offline HTML explorer (`report --html`).
- **Clean-Room & Artifact Triage (`aiwh inspect`, `aiwh spec check`, `aiwh cleanroom init`):** Identifies native/managed/Electron/Web/APK/game binaries, checks behavior-only specs for decompiler/address leaks, and scaffolds a two-room (`lab/` + `clean/`) workspace with firewalled devcontainer templates.
- **Skill Quality & Imports (`aiwh skills lint`, `aiwh skills import`):** Validates **54** canonical skills (passing `--strict` with 0 findings), estimates context-token cost on `init`, and imports local third-party skills with provenance tracking and script exclusion by default.

---

## Quick Start (Windows 11 / Python 3.10+)

Requirements: Python 3.10+, PyYAML 6.0.3+ (`<7`). Optional: `git`, `gh` CLI (for GitHub stars and `catalog check`), and Ollama (for local LLM workflows).

```powershell
# Core installation (local-first, PyYAML only)
py -m pip install -e .

# Optional: enable local hybrid semantic search (sqlite-vec + FastEmbed ONNX)
py -m pip install -e ".[semantic]"

# Verify installation, catalogs, local tools, and hardware/Ollama tiers
aiwh doctor --hardware
```

### Common Workflows

```powershell
# 1. Inspect a project without modifying anything
aiwh audit .
aiwh recommend . --goal "Build a React dashboard with Playwright tests"

# 2. Preview and apply portable skills & instructions
aiwh init . --agent all --area frontend --area qa-testing --dry-run
aiwh init . --agent all --area frontend --area qa-testing

# 3. Generate continuity handoff & pick the next unblocked task
aiwh resume .
aiwh handoff plan . --output .ai-workbench/NEXT_PLAN.md
aiwh handoff claim RM-010 --by codex

# 4. Run explicitly approved validation and store revision-bound evidence
aiwh validate .
aiwh validate . --approve

# 5. Search private catalog & curated public references offline
aiwh search "clean room" --source references
```

---

## CLI Reference

Global option: `--home PATH` (overrides `~/.ai-workbench-hub`) precedes the subcommand.

| Command | Purpose |
| --- | --- |
| `init` | Install/update selected skills and managed instructions (`--dry-run`, `--area`, `--auto-areas`, `--exclude-skill`) |
| `managed remove` | Remove only hash-verified Workbench-owned files and blocks; preserves user edits (`--dry-run`) |
| `resume` | Refresh `.ai-workbench/CONTEXT.md` and bounded `state.json` v2 history (`--dry-run`) |
| `audit` | Print observed local project state as JSON without writes |
| `validate` | Preview or (`--approve`) execute a validation command with secret redaction and revision-bound evidence |
| `handoff plan \| check \| lint \| claim \| export` | Execution plans (`depends_on`-aware), HEAD drift checks, state lint, task claims, and exports (`json`, `markdown`, `claude-memory`, `wiki`) |
| `handoff decide \| reject \| feedback \| task` | Record approved/retracted decisions, rejected findings, resource feedback, and task status/blockers/dependencies |
| `areas` / `profiles` / `capabilities` | List the 27 composable areas, 29 technical profiles, 54 skills, and 21 agent role templates |
| `recommend` | Explainable area/skill/MCP/plugin plan with top-5 contextual shortlist and MCP Advisor (`--json`) |
| `search` | Local SQLite FTS5 (or hybrid `sqlite-vec` + `fastembed` RRF) search across private catalog and public references |
| `sync` / `curate` / `attach` / `report` | Read-only ingestion (`gh` stars, Chromium/HTML bookmarks), candidate triage, project attachment, and offline HTML view (`--html`) |
| `references` / `catalog check` | Filter 491 curated public references (`--area`, `--risk`, `--unreviewed`), regenerate `docs/REFERENCES.md` (`--write`/`--check`), or check GitHub freshness |
| `skills lint \| import` | Lint skills (`--strict` exits 1 on findings) or import local skills with provenance (`--dry-run`) |
| `mcp plan` | Preview MCP config for `claude`, `codex`, `hermes`, or `generic` (`--apply` writes manifest-owned Claude `.mcp.json`) |
| `inspect` / `spec check` / `cleanroom init` | Binary/app identification, behavior-only spec leak check, and two-room clean-room scaffolding |
| `game-port` | Triage game binaries/platforms (`--binary`, `--platform`, `--track`, `--save`) |
| `global-integration` | Opt-in managed global instruction block for `codex`, `claude`, or `antigravity` (`--apply`, `--disable`) |
| `doctor` | Validate all catalogs, detect executables (`git`, `gh`, `codex`, `claude`, `hermes`, `rea`, `java`, `Ghidra`), and probe `--hardware` |

---

## Supported Agent Adapters

| Agent | Instruction File | Skill Directory | Notes |
| --- | --- | --- | --- |
| Codex | `AGENTS.md` | `.agents/skills/` | Synthetic contract tested |
| Claude Code | `CLAUDE.md` (+ `AGENTS.md` pointer) | `.claude/skills/` | Supports `mcp plan --apply` |
| Google Antigravity | `AGENTS.md` | `.agents/skills/` | Shared workspace rules + skills |
| Hermes Agent | `AGENTS.md` | `.agents/skills/` | Requires explicit repo trust in Hermes |
| OpenClaude | `AGENTS.md` | `.openclaude/skills/` | Role templates remain reference-only |

> All five skill-path mappings have synthetic contract tests. Real-runtime skill discovery and instruction precedence across external agent CLIs are tracked in RM-016/RM-017.

---

## Safety, Privacy & Architecture

- **Private by default:** `.ai-workbench/` is gitignored by `init`/`attach`; personal catalogs (`~/.ai-workbench-hub/catalog.json` and `catalog.db`) never enter repositories.
- **Untrusted external data:** Bookmarks, starred repositories, and imported skills are treated as untrusted data—never automatically cloned, installed, or executed.
- **Transactional ownership:** `init` and `managed remove` use a preimage backup journal (`.ai-workbench/managed-files.transaction`) and atomic file replacement. Modified files are flagged as conflicts and preserved.
- **Core modules:** [workbench.py](src/aiwh/workbench.py) (bootstrap & registry), [manifest.py](src/aiwh/manifest.py) (SHA-256 transactions), [continuity.py](src/aiwh/continuity.py) (state v2 & snapshots), [handoff_plan.py](src/aiwh/handoff_plan.py) / [handoff_checks.py](src/aiwh/handoff_checks.py) / [handoff_export.py](src/aiwh/handoff_export.py), [validate.py](src/aiwh/validate.py), [areas.py](src/aiwh/areas.py), [core.py](src/aiwh/core.py), [references.py](src/aiwh/references.py), [semantic.py](src/aiwh/semantic.py), [runtime_probe.py](src/aiwh/runtime_probe.py), [skilltools.py](src/aiwh/skilltools.py), [mcp_plan.py](src/aiwh/mcp_plan.py), [cleanroom.py](src/aiwh/cleanroom.py), [artifact.py](src/aiwh/artifact.py), [game_porting.py](src/aiwh/game_porting.py), and [html_report.py](src/aiwh/html_report.py).

---

## Validation & Distribution Checks

```powershell
# Run the full test suite (157 unit tests)
python -m unittest discover -s tests -v

# Strict quality & consistency checks
aiwh skills lint --strict
aiwh references --check
aiwh handoff lint .
```

Build and verify offline wheel/sdist packages:

```powershell
python -m build --outdir dist
$wheel = (Get-ChildItem dist/*.whl).FullName
$sdist = (Get-ChildItem dist/*.tar.gz).FullName
python scripts/Verify-Package.py --wheel $wheel --sdist $sdist --wheelhouse .package-wheels
```

See [Architecture](docs/ARCHITECTURE.md), [Roadmap](docs/ROADMAP.md), [Agent Compatibility](docs/AGENTS.md), [References](docs/REFERENCES.md), [Game Porting](docs/GAME_PORTING.md), [Security](SECURITY.md), and [Contributing](CONTRIBUTING.md).
