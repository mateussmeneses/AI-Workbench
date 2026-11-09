# MCPs: a catalog, not an installer

MCP wiring varies by client and credential. This kit **does not enable MCPs** and never writes secrets. `aiwh mcp plan` previews a configuration snippet; only `--apply` (Claude Code project `.mcp.json`) writes a manifest-tracked file that `aiwh managed remove` can reverse.

| MCP | Enable when | Lightweight alternative |
|---|---|---|
| GitHub | Remote issues, PRs, branches and reviews | `gh` CLI |
| Azure DevOps | Work items, boards, builds | authorized web UI / REST |
| Playwright | Real browser interaction | local Playwright/Selenium tests |
| Chrome DevTools | Network, traces, console, performance | manual DevTools |
| Context7 | Library/version docs that change | official docs |
| Ghidra (`ghidra-mcp`) | Decompilation and xrefs on native binaries | Ghidra GUI / headless scripts |
| x64dbg (`x64dbg-mcp`) | Dynamic debugging on Windows | x64dbg GUI |
| Apktool (`apktool-mcp`) | Decoding/rebuilding APKs | `apktool` CLI, jadx |
| REA (`rea`) | Evidence from shipped native/managed/web artifacts | plain CLI tools (leanrea approach) |
| IDA Pro (`ida-pro-mcp`) | Decompilation and xrefs when IDA Pro is the engine | IDA GUI |
| mcp-reverse | Runtime memory inspection for modding | ImHex, x64dbg |

REA installs itself with `npx rea-agents@latest setup` (plan, config backup, then changes) and is checked with `npx -y rea-agents@latest doctor --client claude_code --json`; see `setup_note` in the catalog and docs/RE_LEARNING_PATH.md.

Entries with a `server` field have a known launch command; the others require manual setup from the project's README. On native Windows, `npx`-based servers are wrapped as `cmd /c npx ...`.

## Hermes
Documentation: https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp
Catalog: `hermes mcp catalog`. Manage servers with `hermes mcp` or `mcp_servers` in `~/.hermes/config.yaml`. Use `enabled: false` for servers you do not need and `lazy: true` when supported. After changes: `/reload-mcp`. See `hermes-reference.yaml`.

## Official sources
- GitHub MCP: https://github.com/github/github-mcp-server
- Azure DevOps: https://github.com/microsoft/azure-devops-mcp (remote server recommended)
- Playwright: https://github.com/microsoft/playwright-mcp
- Chrome DevTools: https://github.com/ChromeDevTools/chrome-devtools-mcp
- Context7: https://github.com/upstash/context7

Treat credentials as secrets; prefer login/OAuth and environment variables. Never write a PAT or key into AGENTS.md, Git history or skill files.
