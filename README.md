# AI Workbench

**Portable project bootstrap + continuity for multiple coding agents.** A local-first CLI and capability library: skills, role templates, MCP recommendations, project profiles, and a private catalog of technical references.

AI Workbench is an independent project. It does **not** modify your bookmarks, clone starred repositories, enable MCP servers, or upload project data to AI services.

## What it already does

- **Bootstrap:** `aiwh init` detects a project's technology profile (or accepts overrides), installs the selected skills in agent-specific project directories, preserves existing instructions, and suggests MCP candidates for review.
- **Continuity:** `aiwh resume` reads local Git state, recent commits, test indicators and up to 30 documented pending items, then writes a private handoff and versioned `.ai-workbench/state.json`. It preserves approved decisions, task status and explicit resource choices, retaining up to 10 snapshots with session comparisons.
- **Audit:** `aiwh audit` reports the observed project state in JSON without changing anything.
- **Capability registry:** 46 deduplicated skills, 21 agent role templates, 29 technical profiles, 27 composable areas, and opt-in MCP/plugin catalogs.
- **Resource catalog:** optional read-only ingestion of GitHub stars (`gh` CLI), Chromium bookmarks, and Netscape HTML. Resource suggestions are local and never automatically installed or executed.

## Install (Windows 11)

Requirements: Python 3.10+, PyYAML 6.0.3+ (below 7, declared as a package dependency), optional Git, optional `gh` for GitHub stars. Installing the package also installs its dependencies when needed.

```powershell
# Extract the ZIP and open PowerShell inside AI-Workbench.
py -m pip install -e .
aiwh doctor
aiwh profiles
aiwh capabilities
```

If `aiwh` is not on PATH immediately, reopen the terminal or use `py -m aiwh` after installation.

These instructions use an editable install from the source checkout. Wheel/sdist assets and a clean temporary wheel installation outside the checkout have been verified locally on Windows/Python 3.10.22 using an isolated PyYAML wheelhouse. The CI matrix includes Ubuntu/Windows and Python 3.10, 3.12 and 3.14; hosted CI results were not observed. See the [roadmap](docs/ROADMAP.md) for release gates.

## Distribution checks

The canonical `capabilities/` tree is mapped into `aiwh.capabilities` during packaging; it is not maintained as a second source copy. Build tooling is separate from runtime dependencies and must be available in the selected development environment.

After explicitly preparing the build tools and local dependency wheels, verify the artifacts with:

```powershell
python -m build --outdir dist
$wheel = (Get-ChildItem dist/*.whl).FullName
$sdist = (Get-ChildItem dist/*.tar.gz).FullName
python scripts/Verify-Package.py --wheel $wheel --sdist $sdist --wheelhouse .package-wheels
```

Use a directory containing only the current build's wheel and sdist. The verifier never downloads dependencies: it inspects archive contents, creates a temporary venv, installs from local wheels, and exercises the installed `aiwh` launcher and module outside the checkout. It checks skill installation in all three directories, repeated bootstrap, previews and continuity using synthetic projects and a temporary private catalog.

`--reuse-installed-dependencies` is an explicit offline fallback when dependencies are already installed on the host. Its result is reported as `host reuse`, not a clean dependency-install certification. Temporary verification environments are removed after the check.

CI is configured for Ubuntu and Windows with Python 3.10, 3.12 and 3.14. Other Python 3.10+ releases remain declared-compatible but are not individually covered by that matrix. No hosted run was observed during this local packaging work.

## CLI reference

Use `aiwh --help` and `aiwh <command> --help` for current options. The global `--home` option precedes the command, for example `aiwh --home "C:\private\workbench" report`.

| Command | Current behavior |
| --- | --- |
| `init` | Write or explicitly update selected project skills and managed instructions using the manifest; `--dry-run` reports added, unchanged, changed and conflicting paths |
| `managed remove` | Remove only unchanged manifest-owned files; preserve shared instruction files and report conflicts; `--dry-run` previews |
| `resume` | Write a private handoff and bounded state history; `--dry-run` previews without writes |
| `audit` | Print observed local project state as JSON, without writes |
| `profiles` | List available technical profiles |
| `areas` | List composable capability areas |
| `recommend` | Print an explainable capability proposal; `--json` selects JSON output |
| `capabilities` | List skill and role identifiers plus skill/role/profile counts |
| `sync` | Read explicitly selected sources and update the private catalog; `--dry-run` skips catalog writes |
| `attach` | Write private resource suggestions and may add a managed `AGENTS.md` note plus `.gitignore` entry; `--dry-run` previews without writes |
| `report` | Summarize the private resource catalog, without writes |
| `doctor` | Check registry references and report executable detection; not a runtime compatibility test |
| `global-integration` | Preview a managed global instruction block; only `--apply` writes changes |

`sync --github` requests GitHub star metadata through `gh`, even with `--dry-run`; dry-run prevents writes, not explicitly requested source reads or network access.

## Compose any kind of project from capability areas

Areas are **composable**, not exclusive. The catalog currently includes 27 extendable domains: frontend, backend, fullstack, API integration, extensions, mobile, desktop, QA, DevOps, cloud, security, reverse engineering, modding, recompilation, decompilation, game porting, AI automation, data engineering, analytics, UX, marketing, sales, ecommerce, product management, content, operations and quantitative finance.

```powershell
aiwh areas
aiwh recommend "C:\projects\new-product" --goal "Build a SaaS dashboard for sales and marketing"
aiwh recommend "C:\projects\game-port" --area reverse-engineering --area recompilation --json

# Preview the exact project changes; no files are created
aiwh init "C:\projects\new-product" --create --agent all --area frontend --area backend --area marketing --dry-run

# Apply after reviewing, without activating MCP servers or connecting plugins
aiwh init "C:\projects\new-product" --create --agent all --area frontend --area backend --area marketing

# Optional opt-in autodetection using repository files and project mission
aiwh init "C:\projects\game-port" --agent codex --goal "Reverse engineering and game modding" --auto-areas
```

`aiwh recommend` does not change any files or invoke AI APIs. It ranks areas with bounded, explainable keyword/file evidence (heuristics, not an LLM), and generates proposed skills, agent roles, MCP servers, external plugins and utilities. Plugins/MCPs remain **recommendations only**; no credentials are stored or capabilities connected. Use explicit `--area` flags to avoid unwanted automatic category selection.

See [area reference](docs/AREAS.md), [community research](docs/RESEARCH.md), and [architecture](docs/ARCHITECTURE.md).

## Game Reverse Engineering & Porting

`aiwh game-port` examines bounded binary headers, distinguishes **matching decompilation**, **static recompilation** and **compatibility-runtime** work, then recommends platform-specific tools and relevant Workbench skills. The original game is not executed or modified.

```powershell
aiwh game-port "C:\projects\n64-port" --binary "C:\games\sample.z64" --track static-recomp --json
aiwh game-port "C:\projects\ps4-port" --platform ps4 --goal "Fix Vulkan shader stutter"
aiwh game-port "C:\projects\n64-port" --binary "C:\games\sample.z64" --track matching-decomp --save
aiwh init "C:\projects\n64-port" --agent hermes --area reverse-engineering --area decompilation --dry-run
```

`--save` explicitly writes a private `.ai-workbench/GAME_PORT_PLAN.md` handoff; otherwise the assessment is read-only. MCP and plugin activation remain opt-in. See [Game Porting Guide](docs/GAME_PORTING.md).

## Start a new project

```powershell
aiwh init "C:\projetos\my-app" --create --agent codex --profile browser-extension --dry-run
aiwh init "C:\projetos\my-app" --create --agent codex --profile browser-extension
```

`--dry-run` previews file writes without creating directories. Omit `--profile` to autodetect technology for an existing repository. `--agent all` writes the three distinct skill locations: `.agents/skills`, `.claude/skills` and `.openclaude/skills`. Codex, Antigravity and Hermes share the first path in Workbench's adapter mapping; discovery and trust still depend on each runtime.

## Continue an existing project

```powershell
aiwh init "C:\projetos\neverdead-port" --agent codex --dry-run
aiwh init "C:\projetos\neverdead-port" --agent codex
aiwh resume "C:\projetos\neverdead-port" --agent codex
```

Open the project in Codex and ask it to read `AGENTS.md`, `AI-WORKBENCH.md` and `.ai-workbench/CONTEXT.md` before proposing changes. For Claude Code, use `--agent claude`, then read `CLAUDE.md` and the same handoff. The context is available to every runtime; AI Workbench itself does not migrate proprietary agent chat sessions.

## Check a project without changes

```powershell
aiwh audit "C:\projetos\neverdead-port"
aiwh resume "C:\projetos\neverdead-port" --dry-run
```

## Optional technical references

```powershell
gh auth login
aiwh sync --github             # Read GitHub starred repositories
aiwh sync --browser-auto       # Read-only local Chromium bookmark metadata on Windows
aiwh report
aiwh attach --project "C:\projetos\neverdead-port" --dry-run
aiwh attach --project "C:\projetos\neverdead-port"
```

**Bookmark Organizer is a separate product.** It manages browser bookmarks directly; Workbench can optionally index relevant resources, but it must not rearrange folders or duplicate the browser extension's responsibilities.

## Implemented agent file adapters

| Agent | Workspace instruction | Skill location | Notes |
|---|---|---|---|
| Codex | `AGENTS.md` | `.agents/skills/` | Project path mapping |
| Claude Code | `CLAUDE.md` | `.claude/skills/` | Also writes the shared `AGENTS.md` pointer |
| Google Antigravity | `AGENTS.md` | `.agents/skills/` | Shared repo rules + skills |
| Hermes Agent | Portable `AGENTS.md` pointer | `.agents/skills/` | Trust repository skills explicitly in Hermes |
| OpenClaude | Portable `AGENTS.md` pointer | `.openclaude/skills/` | Role adapters remain templates |

No tool is automatically granted access to GitHub/Azure DevOps, or configured with API keys.

All five skill-path mappings have synthetic contract tests. Real-runtime skill discovery, instruction precedence and end-to-end workflows are not yet verified for any adapter. See [adapter evidence and sources](docs/AGENTS.md); `doctor` finding an executable does not certify support.

## Security and contributions

See [Security](SECURITY.md) and [Contributing](CONTRIBUTING.md).

## Safety, privacy and portability

- `.ai-workbench/` is project-local context. Applying `aiwh init` or `aiwh attach` adds it to `.gitignore`; `attach` may also add a managed note to `AGENTS.md`. Standalone `aiwh resume` and `aiwh game-port --save` do not ensure the ignore entry, so verify/add it before committing their output. `AI-WORKBENCH.md` and managed instruction sections are explicit, reviewable files.
- `aiwh init` records project-relative paths and SHA-256 hashes for files it creates or safely merges in `.ai-workbench/managed-files.json`. Existing unmanifested generated files with different content are reported as conflicts and preserved; legacy files are not silently adopted. Removal is a separate, hash-verified `aiwh managed remove` operation.
- Re-running `aiwh init` is the explicit update operation: it updates a file only while its current bytes match the recorded hash. Use `aiwh managed remove PROJECT --dry-run` to preview removal and omit `--dry-run` to apply it. Removal deletes only hash-verified exclusive files; for AGENTS/CLAUDE and `.gitignore` it removes only the recognizable Workbench block/entry. Edited or unverified files remain and are reported as conflicts. Handoffs, state, game-port plans and unmanifested files are not removed.
- Managed writes/removals use a private transaction journal and backups under `.ai-workbench/`; the next mutating `init`/`managed remove` rolls back an interrupted transaction before continuing. A dry-run refuses a pending transaction rather than changing files. Transactional recovery is not a guarantee against storage/hardware failure.
- `.ai-workbench/state.json` schema version 2 separates refreshed observations from persistent tasks, explicitly approved decisions and selected/rejected resources, retaining up to 10 snapshots. Only user-confirmed usefulness is recorded; absent feedback is labeled unknown. Corrupt or unsupported future state is preserved and causes `resume` to fail before replacing the handoff.
- Existing `AGENTS.md`/`CLAUDE.md` content is preserved. Re-running setup is idempotent; collisions with user-modified skills are reported, not overwritten.
- Existing project code is never reformatted, built, committed, pushed, deleted or executed by bootstrap or continuity.
- The continuation scan reports **test indicators**, not fake test results; it never runs project test commands.
- Catalog files are stored outside repositories in the user's home (default `~/.ai-workbench-hub/catalog.json`, configurable with `--home`).
- Profiles and technical recommendations may be imperfect; review before using in a production repository.

## Validation

```powershell
py -m unittest discover -s tests -v
```

See [architecture](docs/ARCHITECTURE.md), [roadmap](docs/ROADMAP.md), [agents](docs/AGENTS.md), [publishing tutorial](docs/PUBLISHING.md), and [Codex handoff](CODEX_START_HERE.md).

## Project status

Package version **0.4.0.dev0** is an unreleased development build; the latest documented stable changelog entry is **0.3.0**. Bootstrapping, continuation, local catalog and agent file adapters have synthetic test coverage. The distribution also passed a clean local wheelhouse install and 49 unit tests on Windows/Python 3.10.22. This does not certify real agent runtimes or hosted CI. See the [versioned roadmap](docs/ROADMAP.md) for acceptance gates and the next task.

Managed capability updates/removal, versioned private state and bounded session history/deltas are available. Native startup hooks and recurring monitoring are deferred opt-in opportunities. MCPs/plugins remain recommendations; proprietary chat-session migration is not supported.

## Optional global agent integration

Workbench will **not** modify global settings during installation. To opt in, preview and then apply a managed instruction block:

```powershell
aiwh global-integration --agent codex
aiwh global-integration --agent codex --apply

# Optional uninstall of only Workbench's instructions:
aiwh global-integration --agent codex --disable --apply
```

Available for `codex`, `claude`, and `antigravity`. The block asks the agent to recognize Workbench context and offer bootstrap/continuity commands; it cannot force any coding agent to invoke tools or start background monitoring. Other agents still work via per-project skills.
