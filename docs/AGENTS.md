# Agent compatibility and sources

## Evidence levels

Workbench implements file adapters, not a guarantee that every runtime discovers or follows the generated content. Current evidence is limited to the source mapping and synthetic tests in `tests/test_workbench.py`:

| Agent | Implemented skill path | Synthetic path contract | Real-runtime discovery/workflow |
| --- | --- | --- | --- |
| Codex | `.agents/skills/` | Covered by `test_native_paths` | Unverified |
| Claude Code | `.claude/skills/` | Covered by `test_native_paths` | Unverified |
| Google Antigravity | `.agents/skills/` | Covered by `test_native_paths` | Unverified |
| Hermes Agent | `.agents/skills/` | Covered by `test_native_paths` | Unverified |
| OpenClaude | `.openclaude/skills/` | Covered by `test_native_paths` | Unverified |

`test_preserves_custom_agents_and_can_run_twice` checks generated files and idempotence for the three distinct directories through `--agent all`; it does not launch any agent. `test_opt_in_global_activation_is_reversible` exercises the global managed block with a temporary Codex home, not every runtime's configuration.

`aiwh doctor` reports executable detection for Git, GitHub CLI, Codex, Claude and Hermes. It neither launches those agents nor checks their versions, discovery, trust settings or instruction precedence. It does not probe Antigravity or OpenClaude executables.

Real-runtime verification is tracked in RM-016/RM-017 in [the roadmap](ROADMAP.md). When performed, record runtime version, date, scenario and observed result; leave unavailable runtimes explicitly unverified.

## Adapter behavior

`init --agent` accepts `codex`, `claude`, `antigravity`, `hermes`, `openclaude` and `all`. The `all` option writes the three distinct skill paths above, not five independent installations. Claude receives a `CLAUDE.md` managed block plus a shared `AGENTS.md` pointer; the other mappings use `AGENTS.md`.

`global-integration` is implemented only for Codex, Claude and Antigravity. It previews by default; `--apply` writes the managed instruction block and `--disable --apply` removes it. This is an instruction adapter, not an automatic native execution hook. Workbench does not install Antigravity rules or grant Hermes repository trust.

## Reference sources

These references informed the existing mappings. They were not revalidated against current vendor documentation during RM-001; reconfirm paths and runtime requirements before claiming compatibility after an upgrade:

- Codex: `AGENTS.md` and `.agents/skills/<skill>/SKILL.md`; [VS Code Agent Skills](https://code.visualstudio.com/docs/agent-customization/agent-skills).
- Claude Code: `CLAUDE.md` and `.claude/skills/<skill>/SKILL.md`; [Anthropic Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview).
- Google Antigravity: `AGENTS.md`, `.agents/skills/`, `.agents/rules/` with YAML triggers for rules; [Antigravity Rules](https://antigravity.google/docs/rules/). AI Workbench does not install rules yet.
- Hermes Agent: `.agents/skills/`, project discovery and `hermes skills trust` in the project; [Hermes Skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills).
- OpenClaude: `.openclaude/skills/` and optional shared `~/.agents/skills` support; [OpenClaude Skills](https://github.com/Twigpine/openclaude/blob/main/docs/skills.md).

Codex, Claude and other agents may discover different subsets. AI Workbench does not claim that role templates are native subagents; adapters for native subagent definitions are future scope.
