# Roadmap

## Product direction

Make AI Workbench the portable, local-first preparation and continuity layer for coding agents: a project should receive the right capabilities, retain its decisions and progress, and be understandable by the next agent without losing user control.

Prioritize trustworthy bootstrap and handoffs over catalog size, autonomous orchestration, or a graphical interface. Success means less repeated setup, fewer lost decisions, and explainable recommendations, not more installed tools.

This is the canonical development queue, not a claim that future features exist. Baseline: v0.3.0. Target versions below are provisional release boundaries, not calendar promises. Work proceeds during explicitly requested sessions; this document does not start unattended development.

## Delivered baseline: v0.3.0

- [x] Unified bootstrap, continuity, read-only audit and optional private resource catalog.
- [x] Profile selection and native project skill paths for five agent adapters.
- [x] Preservation of existing instructions, modified skills and dry-run behavior.
- [x] Composable area routing with explainable local recommendations.
- [x] Opt-in, reversible global instruction blocks for Codex, Claude and Antigravity.
- [x] Synthetic unit/integration tests and Windows quick-start documentation.

These checks describe implemented behavior and synthetic coverage. They do not certify real agent runtimes, clean-machine installation, published distributions or unattended hooks.

## Execution order

| Target | Priority | Outcome | Depends on |
| --- | --- | --- | --- |
| 0.3.1 | P0 | Trustworthy baseline and distribution | 0.3.0 |
| 0.4.0 | P0 | Safe managed capability lifecycle | 0.3.1 |
| 0.5.0 | P0 | Durable decisions, tasks and session deltas | 0.4.0 |
| 0.6.0 | P1 | Explicit validation evidence | 0.5.0 |
| 0.7.0 | P1 | Curated, measurable recommendations | 0.6.0 |
| 0.8.0 | P1 | Verified adapters and portable onboarding | 0.7.0 |
| 0.9.0 | P1 | Release candidate and upgrade rehearsal | 0.8.0 |
| 1.0.0 | Gate | Stable core contracts | 0.9.0 |

Finish one task and validate it before opening another. Each ID remains stable when work is split; use suffixes such as RM-004a and document the split. Unchecked tasks are planned unless a completion note explicitly records work in progress or a blocker.

## 0.3.1: Stabilize the baseline

Scope: documentation, registry validation, packaging and test automation. No new external integrations.

- [x] RM-001 Reconcile README.md, CODEX_START_HERE.md and docs/AGENTS.md with CLI behavior; distinguish implemented, synthetically tested and runtime-verified support.
- [x] RM-002 Validate skill metadata and registry references in src/aiwh/workbench.py and tests/test_workbench.py; report duplicate IDs, missing files and malformed metadata clearly.
- [ ] RM-003 Verify pyproject.toml distribution assets in an isolated install outside this checkout; add Windows/Python 3.10+ CI and installation smoke checks without publishing.
- [x] RM-003a Bundle canonical assets, configure distribution checks in existing CI/release workflows, and verify local offline builds and wheel installation outside the checkout.
- [ ] RM-003b Run clean-wheelhouse installation and the mandatory tests on Windows/Python 3.10; obtain prepared local dependencies/runtime or explicit download approval; record hosted CI results separately if observed.

Acceptance: advertised commands work outside the source checkout; required capability assets are included; invalid registry fixtures fail with actionable messages; tests run on Windows and the minimum supported Python. Configure CI in-repo, but do not claim hosted runs until observed. Select a current Python version when implementing the matrix.

## 0.4.0: Manage installed capabilities safely

Scope: bootstrap ownership in src/aiwh/workbench.py, explicit CLI operations and focused fixtures in tests/test_workbench.py. Decide public command names at implementation time.

- [ ] RM-004 Record a versioned, project-local managed-file manifest with content hashes; preview added, unchanged, changed and conflicting files before applying bootstrap changes.
- [ ] RM-005 Add explicit capability update/removal using the manifest; preserve user edits and refuse to delete files whose ownership or content cannot be verified.
- [ ] RM-006 Make managed writes recoverable after interruption; test repeated application, rollback, Unicode/spaced Windows paths and partial failures.

Acceptance: repeated initialization produces zero effective changes; preview matches application; modified user files survive updates/removal; interrupted work can recover without deleting unrelated content. Legacy projects without a manifest require an explicit adoption plan, not inferred ownership.

## 0.5.0: Preserve durable project continuity

Scope: inspect_project, resume and continuation_markdown in src/aiwh/workbench.py; reuse ContinuityTests in tests/test_workbench.py. Extract a separate module only when the implementation needs it.

- [ ] RM-007 Define a versioned private state schema for approved decisions, stable task IDs, status, blockers, risks and milestone outcomes; migrate existing state.json non-destructively.
- [ ] RM-008 Retain bounded snapshot history and compare sessions; separate observed changes, user-approved notes and unknown results without executing project code.
- [ ] RM-009 Generate task-ready handoffs with the next eligible task, dependencies and evidence; preserve equivalent facts across adapters and report truncated pending-work scans.

Acceptance: two sessions retain task identity and approved decisions; deltas distinguish new/resolved blockers and changed files; corrupt or future schemas fail safely; no chat-history access is implied. Private handoffs stay gitignored, and public summaries exclude private project data.

## 0.6.0: Capture validation evidence explicitly

Scope: a separate opt-in validation action exposed through src/aiwh/cli.py; bootstrap, audit and resume remain non-executing.

- [ ] RM-010 Add user-approved validation commands with a visible execution plan, working directory, timeout and cancellation; never execute commands discovered in project text automatically.
- [ ] RM-011 Store private command evidence with exit status, timestamp and source revision; distinguish passed, failed, timed out, not run and stale results with redacted, bounded output.
- [ ] RM-012 Cover command failure, cancellation, secret redaction and stale evidence; keep non-executing flows unchanged in tests/test_workbench.py.

Acceptance: no validation runs without explicit approval; nonzero exit and timeouts never appear as success; changed code invalidates the applicability of earlier evidence; credentials are not persisted. Approval to validate is not approval to install dependencies or execute downloaded code.

## 0.7.0: Improve recommendation quality

Scope: src/aiwh/areas.py, src/aiwh/core.py, canonical capabilities and tests/test_areas.py/test_core.py. Curate existing entries before expanding them.

- [ ] RM-013 Track public capability provenance, review dates, compatibility claims and licensing notes; keep personal bookmarks, stars and catalog data outside the repository.
- [ ] RM-014 Add synthetic labeled project scenarios and measure relevant-area hits, false positives and scan limits; improve ranking with explainable positive and negative signals.
- [ ] RM-015 Improve private resource deduplication and relevance; support a user-selected reviewed bookmark export without reading browsing history or modifying bookmarks.

Acceptance: publish reproducible fixture metrics before and after ranking changes; include mixed-domain and ambiguous projects; preserve explicit overrides; unknown maintenance/compatibility remains unknown. External metadata refresh requires authorization and provenance, never automatic installation.

## 0.8.0: Verify portability and onboarding

Scope: existing agent paths, scripts/Install-Windows.ps1, scripts/New-Project.ps1, docs/AGENTS.md and adapter contract tests.

- [ ] RM-016 Maintain an adapter compatibility matrix with runtime version, documented paths, synthetic checks and separately recorded real-runtime evidence for all five adapters.
- [ ] RM-017 Rehearse init, resume, update and removal on representative user-approved Windows projects; compare handoff facts across agents without claiming identical model behavior.
- [ ] RM-018 Refine explicit Windows onboarding and reversible global instructions; offer minimal/composed presets without granting native tool access or silently installing hooks.

Acceptance: every advertised support level has dated evidence or is marked unverified; custom instructions survive the lifecycle; users can reproduce setup and removal. Missing runtimes are recorded as validation blockers, not simulated successes.

## 0.9.0: Rehearse release and upgrades

Scope: packaging, security boundaries, user documentation and docs/PUBLISHING.md. Repository creation and publishing require separate authorization.

- [ ] RM-019 Test upgrades from retained baseline fixtures through current schemas and managed-file versions; rehearse interruption and recovery without private production projects.
- [ ] RM-020 Audit release contents for private data and document installation, migration, rollback and known limitations; build an offline-reviewable release candidate.
- [ ] RM-021 Record a real-user pilot of setup and cross-session continuation; resolve core failures and measure friction before authorizing any release publication.

Acceptance: candidate artifacts install cleanly, contain required assets and no private catalogs/handoffs; migration fixtures pass; no unresolved core data-loss or privacy defects. First GitHub release can occur earlier once its version's gates pass and publishing is explicitly authorized.

## 1.0.0: Stabilize the core contract

- [ ] RM-022 Document supported CLI, schema and managed-file compatibility guarantees, deprecation policy and upgrade behavior in public documentation.
- [ ] RM-023 Confirm bootstrap, continuity and capability lifecycle gates on supported Windows/Python versions; disclose optional adapter or integration limitations.
- [ ] RM-024 Complete the release checklist and obtain explicit approval for commits, tags and publication; release only after all mandatory gates are evidenced.

Acceptance: reliable core workflows, reproducible installation, documented migrations, no known destructive overwrite/privacy failures and no unsupported compatibility claims. Optional semantic models, recurring monitoring and native hooks are not prerequisites for 1.0.

## Definition of done

For each task:

1. State the intended behavior, scope and a focused check before editing.
2. Implement the smallest coherent change and run that focused check.
3. Run `python -m unittest discover -s tests -v` and `aiwh doctor`; record actual outcomes, not inferred success.
4. Update relevant public documentation and the Unreleased changelog for implemented changes.
5. Mark the task complete only after its acceptance criteria pass; record blockers instead of silently skipping requirements.
6. Record the task ID, evidence, unresolved risks and next task in a sanitized completion note below. Keep full handoffs and command logs private.

Documentation-only planning does not increment the product version. Release gates supplement task checks: package installation, runtime compatibility and pilot evidence must be executed when their milestone requires them.

## Versioning and source control

- Use semantic versioning. Before 1.0, minor releases may change contracts only with explicit migration notes; patch releases must remain backward compatible.
- Use `0.x.y` patch releases for fixes, packaging corrections and compatible maintenance; use the planned minor releases for coherent feature increments.
- After 1.0, incompatible CLI/schema/ownership changes require a major release; additive features use a minor release.
- Keep pyproject.toml, README.md and CHANGELOG.md aligned when preparing a release. Planning targets are not release announcements.
- Add implemented changes under Unreleased first; move them to a dated release section only after release verification.
- Propose small commits with task IDs, such as `fix(packaging): include capability assets (RM-003)`. Create branches, commits and tags only when explicitly requested.
- Before staging, inspect the exact diff and file list; never stage private catalogs, stars, bookmarks, tokens or live project handoffs. Avoid blanket staging.
- Create a `vX.Y.Z` tag and publish only with explicit authorization. Existing unrelated changes must not be reverted or bundled into a release.

## Next-session procedure

1. Read AGENTS.md, README.md, docs/ARCHITECTURE.md and this roadmap.
2. Run `aiwh resume . --dry-run`, inspect Git status and review the latest completion note.
3. Choose the earliest incomplete, unblocked task in the execution order. Current next task: RM-003b clean dependency installation and minimum-Python verification; RM-004 remains gated on RM-003 acceptance.
4. Confirm the task's local behavior and baseline checks; implement and validate only that scope.
5. Update this queue and the completion note before ending. Suggest the next eligible task and leave version control actions pending unless authorized.

The current resume scan includes only the first 30 pending items, so this roadmap intentionally has 24 top-level tasks. Agents must still read the complete document for dependencies and acceptance criteria.

## Completion notes

Planning baseline: roadmap expanded from the original M0-M4 themes into versioned tasks. No future capability is marked delivered, and the product version remains 0.3.0.

RM-001 completed: reconciled the 12 CLI commands, adapter evidence levels, current continuity limits and source-checkout installation guidance; replaced the outdated Codex milestone queue with this roadmap. Corrected the generated guide from `aiwh resume --project .` to `aiwh resume .` and added regression assertions to the existing bootstrap test. Evidence: 11 focused tests and 24 full-suite tests passed; `aiwh --help` matches the command reference; `aiwh doctor` completed; no editor errors in the touched Python files. Release status: Unreleased, version 0.3.0 unchanged; no commit, tag or publication. Remaining gates: real-runtime compatibility and standalone distribution are still unverified, not blockers for this documentation task. Next: RM-002 registry validation.

RM-002 completed: canonical registry validation now rejects malformed/duplicate skill metadata, malformed/duplicate JSON, invalid profile lists, empty role templates, missing source directories/catalog files and unresolved skill/role/MCP IDs. MCP entries require explicit disabled-by-default booleans. The registry return structure and preservation of user-modified installed skills remain unchanged. Evidence: reproduced acceptance of a skill without description before the fix; 10 isolated registry tests and 34 full-suite tests passed after it; `aiwh doctor` accepted the real catalog; no editor errors in changed code or pyproject.toml. Dependency: PyYAML 6.0.3 was already available locally and is now declared; no package download or installation was performed. Release status: Unreleased, version 0.3.0 unchanged; no commit, tag or publication. Remaining gates: dependency distribution and minimum-Python installation must be checked in RM-003. Next: RM-003 packaging verification and CI.

RM-003 split: RM-003a is delivered; RM-003b is pending, so the parent task remains unchecked. Evidence: cached setuptools 84.0.0 built a wheel and sdist offline; a wheel was rebuilt from extracted source distribution; the final verifier checked 106 runtime payload files plus source-support files and exercised a temporary installed package/launcher outside the checkout. Dependency mode was explicit host reuse of PyYAML 6.0.3, not a clean dependency installation. Four packaging tests were added to the existing test file; all 38 tests passed on Windows/Python 3.14.6, including a run with deprecation warnings visible; `aiwh doctor` passed and no editor errors remained. Existing CI/release workflows were updated, not executed. Only Python 3.14 is locally available, and required dependency wheels are absent from the cache. No download approval was received; no network package downloads, global installs, commit, tag or publication occurred. Release status: Unreleased, version 0.3.0 unchanged. Next: supply an offline wheelhouse and Python 3.10 or authorize temporary downloads for RM-003b before declaring RM-003 complete or preparing v0.3.1.

When completing implementation work, append a short sanitized entry using: task ID; implemented behavior; checks and observed outcome; release status; blockers/risks; next task. Do not store raw private handoffs here.

## Deferred opportunities

Reassess these after the core pilot, rather than automatically adding them to the critical path:

- Optional local/custom semantic ranking with deterministic fallback, explicit data policy and measurable benefit over heuristics; no mandatory paid provider.
- Explicit native MCP/plugin configuration with plan, approval, health check and reversible ownership; no automatic credential management.
- Optional recurring audits and native startup hooks, disabled by default, with cancellation and uninstall tests.
- Native subagent definitions only where documented runtime support exists; role templates remain templates until verified.
- Optional read-only project dashboard or graph navigation driven by demonstrated user needs, not a replacement for the portable CLI.

Do not turn Workbench into a bookmark organizer, agent-chat exporter, cloud control plane or automatic executor of third-party code.
