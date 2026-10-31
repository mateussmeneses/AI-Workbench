# Roadmap

## M0 — Unified starter (delivered)

- [x] Merge the reusable skills/agents/MCP catalog and the private resource Hub without data duplication.
- [x] Implement `aiwh init` with profiles and agent-specific skill directories.
- [x] Implement `aiwh resume` with Git/test/roadmap evidence and private handoff.
- [x] Implement read-only `aiwh audit` plus catalog sync/attach.
- [x] Preserve project instruction files and local edits to installed skills.
- [x] Add deterministic tests and Windows quick-start documentation.

## M1 — Technical stabilization

- [ ] Test Windows installation and CLI operations with actual Codex/Claude/Antigravity/Hermes/OpenClaude runtimes.
- [ ] Evaluate profiles against real projects without changing their source until approved.
- [ ] Create a structural diff for repeated init and clear update/removal of managed capability files.
- [ ] Validate individual skill frontmatter and portability more deeply.
- [ ] Establish CI and first GitHub release after account/repository creation.

## M2 — Continuity engine

- [ ] Store user-approved project decisions and milestone outcomes in a portable schema.
- [ ] Compare snapshots across sessions and detect regressions and unresolved risks.
- [ ] Optional safe test execution with controlled timeouts and explicit commands.
- [ ] Generate task-ready handoffs for multiple runtimes.

## M3 — Capability intelligence

- [ ] Enrich GitHub star metadata and rank tools with provenance and maintenance health.
- [ ] Opt-in semantic recommendation using local or custom models.
- [ ] Optional link to AI Bookmark Organizer's reviewed export without browsing history leakage.
- [ ] Explicit approval and rollback for capability updates, MCP installation and global configuration.

## M4 — Opt-in automation

- [ ] Optional global new-project hook / CLI templates.
- [ ] Optional recurring project audits; disabled by default.
- [ ] Integration tests on Windows, including interruption and upgrade scenarios.

The optional global instruction adapter has been implemented for Codex, Claude Code and Antigravity; automated native execution hooks remain future scope.
