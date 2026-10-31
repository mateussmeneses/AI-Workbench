# Agent compatibility and sources

These locations were selected from vendor documentation. Reconfirm on runtime upgrades:

- Codex: `AGENTS.md` and `.agents/skills/<skill>/SKILL.md`; [VS Code Agent Skills](https://code.visualstudio.com/docs/agent-customization/agent-skills).
- Claude Code: `CLAUDE.md` and `.claude/skills/<skill>/SKILL.md`; [Anthropic Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview).
- Google Antigravity: `AGENTS.md`, `.agents/skills/`, `.agents/rules/` with YAML triggers for rules; [Antigravity Rules](https://antigravity.google/docs/rules/). AI Workbench does not install rules yet.
- Hermes Agent: `.agents/skills/`, project discovery and `hermes skills trust` in the project; [Hermes Skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills).
- OpenClaude: `.openclaude/skills/` and optional shared `~/.agents/skills` support; [OpenClaude Skills](https://github.com/Twigpine/openclaude/blob/main/docs/skills.md).

Codex, Claude and other agents may discover different subsets. AI Workbench does not claim that role templates are native subagents; adapters for native subagent definitions are future scope.
