# Community and ecosystem research — 30 October 2026

Research was used to guide architecture; community comments are experience reports, not independent benchmarks.

## Verified references

- [Agent Skills specification](https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx): `SKILL.md` plus progressive disclosure; keep metadata compact and load details only for relevant tasks.
- [OpenSpec](https://github.com/Fission-AI/OpenSpec): cross-agent, change-centered specification workflow; works for existing and new projects. Workbench keeps continuity and area routing without copying OpenSpec source.
- [GitHub Spec Kit](https://github.com/github/spec-kit): modular specify/plan/implement/verify workflows; inspires profile-independent lifecycle phases.
- [Reddit: skills overload](https://www.reddit.com/r/ClaudeCode/comments/1t4cy2y/what_do_you_do_when_you_have_too_much_skills/): reports of ignored/conflicting large skills, motivates opt-in per-project scope.
- [Reddit: MCP overload](https://www.reddit.com/r/ClaudeMCP/comments/1wibujg/mcp_is_great_until_you_have_too_many_servers/): reports of performance/context clutter from enabling many MCPs; motivates recommend-only MCP selection.
- [Reddit: persistent context](https://www.reddit.com/r/codex/comments/1wjaaaf/for_those_of_you_that_that_run_out_on_the_plus_do/): independent community project documents Git-derived, selectively loaded project memory; motivates private evidence-based handoffs.
- [Reddit: multi-agent board](https://www.reddit.com/r/ClaudeAI/comments/1rtiqne/a_coding_agent_session_manager_that_manages/): illustrates phase-specific agent choice and delegation rather than a single default agent for all work.
- [Reddit: tool catalog bloat](https://www.reddit.com/r/ClaudeAI/comments/1ofltdr/i_spent_way_too_long_cataloguing_claude_code/): firsthand report of pruning excessive tools and plugins; motivates bounded recommendations.

X/Twitter queries during this research did not yield sufficiently verifiable, relevant primary examples. No claims about community consensus on X are made.

## Decisions adopted

1. Use one canonical registry with 26 composable, extendable areas; do not load every skill.
2. Separate discovery from installation: `recommend` is read-only; `init` explicitly copies skills.
3. Recommend MCPs and third-party plugins but never activate/install without a separate user-authorized workflow.
4. Store private continuity in `.ai-workbench`, with Git as authoritative state.
5. Make explanations and area overrides available to users; never present heuristic scores as calibrated probabilities.
6. Avoid dependency on commercial APIs for project discovery or continuity.
