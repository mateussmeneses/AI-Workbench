# AI Workbench

**Portable project bootstrap + continuity for multiple coding agents.** A local-first CLI and capability library: skills, role templates, MCP recommendations, project profiles, and a private catalog of technical references.

AI Workbench is an independent project. It does **not** modify your bookmarks, clone starred repositories, enable MCP servers, or upload project data to AI services.

## What it already does

- **Bootstrap:** `aiwh init` detects a project's technology profile (or accepts overrides), installs the relevant skills in native agent directories, preserves existing instructions, and suggests only the necessary MCPs.
- **Continuity:** `aiwh resume` reads local Git state, recent commits, test indicators and documented TODOs, then creates an evidence-based handoff in the private `.ai-workbench/CONTEXT.md` directory.
- **Audit:** `aiwh audit` reports the observed project state in JSON without changing anything.
- **Capability registry:** 45 deduplicated skills, 20 agent role templates, 28 technical profiles, 26 composable areas, and opt-in MCP/plugin catalogs.
- **Resource catalog:** optional read-only ingestion of GitHub stars (`gh` CLI), Chromium bookmarks, and Netscape HTML. Resource suggestions are local and never automatically installed or executed.

## Install (Windows 11)

Requirements: Python 3.10+, optional Git, optional `gh` for GitHub stars.

```powershell
# Extract the ZIP and open PowerShell inside AI-Workbench.
py -m pip install -e .
aiwh doctor
aiwh profiles
aiwh capabilities
```

If `aiwh` is not on PATH immediately, reopen the terminal or use `py -m aiwh` after installation.

## Compose any kind of project from capability areas

Areas are **composable**, not exclusive. The catalog currently includes 26 extendable domains: frontend, backend, fullstack, API integration, extensions, mobile, desktop, QA, DevOps, cloud, security, reverse engineering, modding, recompilation, decompilation, game porting, AI automation, data engineering, analytics, UX, marketing, sales, ecommerce, product management, content and operations.

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

`--dry-run` previews file writes without creating directories. Omit `--profile` to autodetect technology for an existing repository. Use `--agent all` to install compatible project skills for Codex, Claude Code and OpenClaude simultaneously. Antigravity and Hermes can also consume the shared `.agents/skills` directory, subject to their own runtime trust and configuration rules.

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

## Supported agent adapters

| Agent | Workspace instruction | Skill location | Notes |
|---|---|---|---|
| Codex | `AGENTS.md` | `.agents/skills/` | Native discovery |
| Claude Code | `CLAUDE.md` | `.claude/skills/` | Also writes the shared `AGENTS.md` pointer |
| Google Antigravity | `AGENTS.md` | `.agents/skills/` | Shared repo rules + skills |
| Hermes Agent | Portable `AGENTS.md` pointer | `.agents/skills/` | Trust repository skills explicitly in Hermes |
| OpenClaude | Portable `AGENTS.md` pointer | `.openclaude/skills/` | Role adapters remain templates |

No tool is automatically granted access to GitHub/Azure DevOps, or configured with API keys.

## Security and contributions

See [Security](SECURITY.md) and [Contributing](CONTRIBUTING.md).

## Safety, privacy and portability

- `.ai-workbench/` is local, gitignored context. `AI-WORKBENCH.md` and managed sections of agent instruction files are explicit, reviewable files.
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

Version **0.3.0 starter** — bootstrapping, continuation, local catalog and adapters are implemented and covered with synthetic unit/integration tests. Automatic startup hooks, universal MCP activation, live agent-session migration, background project monitoring and GitHub release automation are future milestones.

## Optional global agent integration

Workbench will **not** modify global settings during installation. To opt in, preview and then apply a managed instruction block:

```powershell
aiwh global-integration --agent codex
aiwh global-integration --agent codex --apply

# Optional uninstall of only Workbench's instructions:
aiwh global-integration --agent codex --disable --apply
```

Available for `codex`, `claude`, and `antigravity`. The block asks the agent to recognize Workbench context and offer bootstrap/continuity commands; it cannot force any coding agent to invoke tools or start background monitoring. Other agents still work via per-project skills.
