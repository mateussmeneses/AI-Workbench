# Roadmap

## Product direction

Make AI Workbench the portable, local-first preparation and continuity layer for coding agents: a project should receive the right capabilities, retain its decisions and progress, and be understandable by the next agent without losing user control.

Prioritize trustworthy bootstrap and handoffs over catalog size, autonomous orchestration, or a graphical interface. Success means less repeated setup, fewer lost decisions, and explainable recommendations, not more installed tools.

This is the canonical development queue, not a claim that future features exist. The delivered historical baseline is v0.3.0; current `pyproject.toml` declares v0.4.0.dev0, an unreleased development version. Target versions below are provisional release boundaries, not calendar promises or published releases. Reconcile the milestone table with package metadata before tagging. Work proceeds during explicitly requested sessions; this document does not start unattended development.

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
| 0.3.1 | P0 | Trustworthy baseline and distribution; local gates passed, release not issued | 0.3.0 |
| 0.4.0 | P0 | Safe managed capability lifecycle | 0.3.1 |
| 0.5.0 | P0 | Durable decisions, resource choices, tasks and session deltas | 0.4.0 |
| 0.6.0 | P1 | Explicit validation evidence | 0.5.0 |
| 0.7.0 | P1 | Contextual Resource Intelligence and capability comparison | 0.6.0, 0.5.0 |
| 0.8.0 | P1 | Verified adapters and portable onboarding | 0.7.0 |
| 0.9.0 | P1 | Release candidate and upgrade rehearsal | 0.8.0 |
| 1.0.0 | Gate | Stable core contracts | 0.9.0 |

Finish one task and validate it before opening another. Each ID remains stable when work is split; use suffixes such as RM-004a and document the split. Unchecked tasks are planned unless a completion note explicitly records work in progress or a blocker.

## 0.3.1: Stabilize the baseline

Scope: documentation, registry validation, packaging and test automation. No new external integrations.

- [x] RM-001 Reconcile README.md, CODEX_START_HERE.md and docs/AGENTS.md with CLI behavior; distinguish implemented, synthetically tested and runtime-verified support.
- [x] RM-002 Validate skill metadata and registry references in src/aiwh/workbench.py and tests/test_workbench.py; report duplicate IDs, missing files and malformed metadata clearly.
- [x] RM-003 Verify pyproject.toml distribution assets in an isolated install outside this checkout; add Windows/Python 3.10+ CI and installation smoke checks without publishing.
- [x] RM-003a Bundle canonical assets, configure distribution checks in existing CI/release workflows, and verify local offline builds and wheel installation outside the checkout.
- [x] RM-003b Run clean-wheelhouse installation and the mandatory tests on Windows/Python 3.10; obtain prepared local dependencies/runtime or explicit download approval; record hosted CI results separately if observed.

Acceptance: advertised commands work outside the source checkout; required capability assets are included; invalid registry fixtures fail with actionable messages; tests run on Windows and the minimum supported Python. CI is configured for Ubuntu/Windows and Python 3.10/3.12/3.14; hosted runs were not observed locally and are not claimed.

## 0.4.0: Manage installed capabilities safely

Scope: bootstrap ownership in src/aiwh/workbench.py, explicit CLI operations in src/aiwh/cli.py and focused fixtures in tests/test_workbench.py. Manifest-backed `init` is the explicit update action; `managed remove` is a separate previewable command.

- [x] RM-004 Record a versioned, project-local managed-file manifest with content hashes; preview added, unchanged, changed and conflicting files before applying bootstrap changes.
- [x] RM-005 Make `aiwh init` the explicit hash-verified update operation and add `aiwh managed remove`; preserve user edits and refuse to delete files whose ownership or content cannot be verified.
- [x] RM-006 Make managed writes recoverable after interruption; test repeated application, rollback, Unicode/spaced Windows paths and partial failures.

RM-004 acceptance: repeated initialization produces zero effective file changes; preview and apply produce the same path classifications; each owned file has a project-relative SHA-256 hash; modified managed files and differing unmanifested generated-file collisions are preserved and reported. First-time instruction-block and `.gitignore` merges retain their existing content. Legacy files are not adopted based on names or apparent content, and no files are removed by RM-004. Atomic recovery/rollback was delivered in RM-006 below.

RM-005 acceptance: rerunning `aiwh init` updates a file only when its current SHA-256 matches the manifest. `aiwh managed remove PROJECT --dry-run` previews exclusive managed-file deletion and shared-file cleanup; applying it removes only hash-verified files, strips only recognized AIWH/ignore content from shared files, leaves empty directories, and preserves conflicts in the manifest. Files outside the manifest (including handoffs, state, game-port plans and user data) remain untouched. No automatic discovery/adoption of legacy files.

RM-006 acceptance: every managed write/removal and manifest change is journaled with a restorable preimage before mutation; recovery is idempotent and only restores/removes a target when its current state matches the transaction's expected output. Interruption during recovery can be retried. Committed transactions are never rolled back during cleanup. Invalid journals, symlinks and intervening user changes fail closed. Dry-run does not recover or mutate a pending transaction. Repeated init remains idempotent; test paths include Unicode and spaces. Empty directories may remain; hardware/filesystem failure is outside the guarantee.

## 0.5.0: Preserve durable project continuity

Scope: inspect_project, resume and continuation_markdown in src/aiwh/workbench.py; reuse ContinuityTests in tests/test_workbench.py. Extract a separate module only when the implementation needs it. Keep the durable state project-local and private.

- [x] RM-007 Define a versioned private state schema for approved decisions, stable task IDs, status, blockers, risks and milestone outcomes; record selected/rejected resource IDs, decision rationale and user-confirmed usefulness when provided; migrate existing state.json non-destructively.
- [x] RM-008 Retain bounded snapshot history and compare sessions; distinguish observed project changes, user-approved decisions/resource feedback and unknown outcomes without inferring that a recommendation helped or executing project code.
- [ ] RM-009 Generate task-ready handoffs with the next eligible task, dependencies, relevant resources with reasons/known limits and validation evidence; preserve equivalent facts across adapters and report truncated pending-work scans.

RM-007 acceptance: `.ai-workbench/state.json` schema version 2 separates refreshed observations from persistent tasks, explicitly approved decisions and selected/rejected resources. Tasks preserve stable IDs and status plus blockers, risks and milestone outcomes. User-confirmed usefulness is optional and never inferred. Unversioned state is preserved under `legacy_observation`; corrupt or unsupported future schemas fail before either handoff file is written.

RM-008 acceptance: schema v2 keeps at most 10 project-local snapshots and compares consecutive observations, documented pending items, task status/blockers, approved decisions and explicit resource choices/feedback. The handoff identifies baseline vs. comparison, Git-status files added/resolved, and blocker changes. Resources without user-confirmed usefulness are labeled unknown; selection never implies use or success. Dry-run does not append history, resume executes no project code, and v1 state migrates without losing prior records.

Acceptance: two sessions retain task identity, approved decisions and explicitly recorded resource choices/usefulness; deltas distinguish new/resolved blockers and changed files; observed recommendation is not conflated with selected, used or helpful; corrupt or future schemas fail safely; no chat-history access is implied. Private handoffs stay gitignored, and public summaries exclude private project data.

## 0.6.0: Capture validation evidence explicitly

Scope: a separate opt-in validation action exposed through src/aiwh/cli.py; bootstrap, audit and resume remain non-executing.

- [ ] RM-010 Add user-approved validation commands with a visible execution plan, working directory, timeout and cancellation; never execute commands discovered in project text automatically.
- [ ] RM-011 Store private command evidence with exit status, timestamp and source revision; distinguish passed, failed, timed out, not run and stale results with redacted, bounded output.
- [ ] RM-012 Cover command failure, cancellation, secret redaction and stale evidence; keep non-executing flows unchanged in tests/test_workbench.py.

Acceptance: no validation runs without explicit approval; nonzero exit and timeouts never appear as success; changed code invalidates the applicability of earlier evidence; credentials are not persisted. Approval to validate is not approval to install dependencies or execute downloaded code.

## 0.7.0: Improve recommendation quality

Scope: src/aiwh/areas.py, src/aiwh/core.py, canonical capabilities and tests/test_areas.py/test_core.py. Build on existing read-only bookmark/HTML/GitHub-star imports, project profiles and deterministic category heuristics; do not add another importer as a substitute for recommendation quality. Curate existing entries before expanding them.

- [ ] RM-013 Track public capability provenance, review dates, compatibility claims and licensing notes; keep personal bookmarks, stars and catalog data outside the repository. Partial: the curated reference catalog, risk labels and `aiwh catalog check` (B2-B4) exist; per-entry review dates and licensing notes remain.
- [ ] RM-014 Add synthetic labeled project scenarios and measure relevant-area hits, false positives and scan limits; improve ranking with explainable positive and negative signals.
- [ ] RM-015 Deliver deterministic Contextual Resource Intelligence: rank a small shortlist (target 3-5) of relevant references/tools using project evidence, detected profiles and the user's stated task; explain why each item was selected, known compatibility, limits and a sensible first consultation/action. Add a Skill & MCP Advisor that compares relevant alternatives and flags likely redundancy or scope/approval requirements; suggestions never install or activate anything.

Acceptance: publish reproducible fixture metrics before and after ranking changes; cover mixed-domain and ambiguous projects, explicit goals, irrelevant results and redundant alternatives; preserve explicit overrides; produce explainable reasons and a bounded shortlist; keep unknown maintenance/compatibility/limits unknown. Deterministic results remain available offline; user-selected resource sources and catalog data stay private. External metadata refresh requires authorization and provenance. References are untrusted data; no automatic fetch, install, connection or execution.

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

## Backlog B1-B20 (delivered 2026-11-09)

- [x] B1 `aiwh curate`: read-only comparison of stars/bookmark exports with every URL the repository references, with suggested areas.
- [x] B2 Structured reference catalog `capabilities/references/catalog.json`; `docs/REFERENCES.md` is generated and tested for drift.
- [x] B3 Risk labels (`authorized-only`, `tos-check`, `licensing-check`, `experimental`, `financial-risk`) shown by `recommend`, `attach`, `references` and the HTML report.
- [x] B4 `aiwh catalog check`: opt-in `gh` metadata check for archived, stale, missing, renamed and forked repositories.
- [x] B5 `.gitattributes` normalizes text files to LF.
- [x] B6 Switch NSP/XCI/NRO/NSO signatures; a verified Switch container accepts a `switch2` declaration.
- [x] B7 Android DEX/APK/AAB signatures, `android` platform, reverse-engineering area signals and the `wb-android-reverse-engineering` skill.
- [x] B8 `aiwh skills lint`: vague descriptions, oversized bodies, shared boilerplate and near-duplicate clusters.
- [x] B9 `aiwh init` reports an approximate context cost for the selected skills.
- [x] B10 `aiwh mcp plan`: per-agent previews; `--apply` writes only a manifest-owned Claude `.mcp.json`.
- [x] B11 `first_seen`/`last_sync` in the private catalog; `aiwh sync --show-new` and `aiwh report --since`.
- [x] B12 `wb-ai-pr-review` skill with an opt-in GitHub Actions template.
- [x] B13 `wb-llm-redteam` skill for authorized robustness testing of owned LLM applications.
- [x] B14 `wb-video-pipeline` skill (content-creation).
- [x] B15 `wb-web-api-recon` skill (traffic capture to OpenAPI, bundle/asar inspection).
- [x] B16 Quant-finance backtest report and data-provenance templates.
- [x] B17 `aiwh skills import`: validated, provenance-tracked local skill import; scripts excluded by default; reversible through `aiwh managed remove`.
- [x] B18 `aiwh handoff export`: json, markdown, claude-memory and wiki formats to an explicit output directory.
- [x] B19 `aiwh report --html`: offline catalog view with filters and risk labels.
- [x] B20 Capability catalogs, skills, roles and routing policy standardized in English.

Follow-up found by B8: 22 generic skills share most of their body text and need domain-specific procedures (`aiwh skills lint`).

## Backlog C1-C14: clean-room and oracle method (delivered 2026-11-09)

- [x] C1 `wb-clean-room-rebuild` skill: analysis room, behavior-only spec, clean room, verifier loop with a 3-round limit.
- [x] C2 `wb-oracle-testing` skill: byte, behavior, runtime and statistical oracles with three planted failures.
- [x] C3 `aiwh spec check`: blocks addresses, decompiler names/types and assembly before the handoff.
- [x] C4 Native Claude Code subagents (analyst, spec-writer, rebuilder without REA tools, verifier that only reports) via `aiwh cleanroom init`.
- [x] C5 TEARDOWN.md, SPEC.md, evidence.md (confidence 1-10), NOTES.md and planted-failures templates; run-team.ps1/.sh.
- [x] C6 `aiwh inspect`: target identification and method/tool/REA routing for files and app folders.
- [x] C7 Evidence status (observed/inferred/unknown, open questions, verifier RESULT) in `aiwh resume`.
- [x] C8 Suggested `/goal` line for the next documented task, using the project's documented test command.
- [x] C9 Effort per phase and clean-room roles in `routing/model-policy.json`.
- [x] C10 Clean-room devcontainer with default-deny outbound firewall and wall checks.
- [x] C11 Agent-directed text: flagged by `aiwh inspect`, recorded by the analyst, covered in RE skills and `wb-llm-redteam`.
- [x] C12 `wb-behavior-teardown` skill (screens, probes, frame measurement, sanitized HAR, numbered acceptance checks).
- [x] C13 54 new references (identification/analysis tools, rebuild stack, courses, books, papers) with `book`/`paper`/`course` kinds.
- [x] C14 `docs/RE_LEARNING_PATH.md`, REA setup notes, `ida-pro-mcp`, and REA/Ghidra/Java detection in `aiwh doctor`.

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
3. Choose the earliest incomplete, unblocked task in the execution order. Current next task: RM-009 task-ready handoffs with dependencies, resources and validation evidence; hosted CI for RM-003 remains unverified.
4. Confirm the task's local behavior and baseline checks; implement and validate only that scope.
5. Update this queue and the completion note before ending. Suggest the next eligible task and leave version control actions pending unless authorized.

The current resume scan reports at most 60 pending checklist items (`PENDING_SCAN_LIMIT`) and flags truncation in the handoff. This roadmap currently has 66 top-level checklist items, of which 16 are pending; preserve headroom or raise the tested scan limit before adding enough open tasks to truncate the next-step queue. Agents must still read the complete document for dependencies and acceptance criteria.

## Completion notes

Planning baseline: roadmap expanded from the original M0-M4 themes into versioned tasks. The delivered historical baseline was v0.3.0; current package metadata declares unreleased v0.4.0.dev0. No future capability is marked delivered by planning alone.

RM-001 completed: reconciled the 12 CLI commands, adapter evidence levels, current continuity limits and source-checkout installation guidance; replaced the outdated Codex milestone queue with this roadmap. Corrected the generated guide from `aiwh resume --project .` to `aiwh resume .` and added regression assertions to the existing bootstrap test. Evidence: 11 focused tests and 24 full-suite tests passed; `aiwh --help` matches the command reference; `aiwh doctor` completed; no editor errors in the touched Python files. Release status: Unreleased, version 0.3.0 unchanged; no commit, tag or publication. Remaining gates: real-runtime compatibility and standalone distribution are still unverified, not blockers for this documentation task. Next: RM-002 registry validation.

RM-002 completed: canonical registry validation now rejects malformed/duplicate skill metadata, malformed/duplicate JSON, invalid profile lists, empty role templates, missing source directories/catalog files and unresolved skill/role/MCP IDs. MCP entries require explicit disabled-by-default booleans. The registry return structure and preservation of user-modified installed skills remain unchanged. Evidence: reproduced acceptance of a skill without description before the fix; 10 isolated registry tests and 34 full-suite tests passed after it; `aiwh doctor` accepted the real catalog; no editor errors in changed code or pyproject.toml. Dependency: PyYAML 6.0.3 was already available locally and is now declared; no package download or installation was performed. Release status: Unreleased, version 0.3.0 unchanged; no commit, tag or publication. Remaining gates: dependency distribution and minimum-Python installation must be checked in RM-003. Next: RM-003 packaging verification and CI.

RM-003 completed: RM-003a bundled canonical assets and configured CI; RM-003b passed on Windows using temporary Python 3.10.22 and an isolated PyYAML 6.0.3 wheelhouse. Interpreter, build environment, wheels and smoke-test venv were kept under the system temporary directory; no global installation was made. Built wheel and sdist for the current package declaration v0.4.0.dev0, checked their assets (108 runtime payload files), then installed the wheel into a fresh venv with `--no-index` and the local wheelhouse. The installed-package smoke covered CLI help, profiles/areas/capabilities, dry-run and applied bootstrap in a spaced path, idempotence, audit/recommend/resume/attach and `doctor`. The 49-test suite passed on Python 3.10.22 with `DeprecationWarning` visible; `aiwh doctor` also passed. A first smoke exposed omitted `game-porting/catalog.json`; `pyproject.toml` and the verifier were corrected and the clean smoke then passed. Hosted GitHub Actions were not run or observed; only their workflow configuration was checked. Release status: unreleased v0.4.0.dev0; no commit, tag or publication. Next: RM-004. Before any release tag, reconcile provisional milestone targets with the current package version.

RM-004 completed: added `.ai-workbench/managed-files.json` version 1 with project-relative SHA-256 entries; bootstrap returns added/unchanged/changed/conflicting categories and manifest create/update/unchanged status. Preview does not create the target project or write files, and project creation preview matches apply for file classifications, including private resource attachments. Existing manifest-owned edits and differing legacy generated files are reported and preserved; invalid manifests fail before other project writes. First-time instruction and ignore-list additions use preserving merges. No deletion or rollback is claimed. Evidence: six focused manifest tests passed; all 31 `test_workbench.py` tests and all 55 repository tests passed; `aiwh doctor` passed; no code diagnostics remain. The only editor diagnostic is the unchanged README table's MD060 style warning. Release status: Unreleased, package declaration v0.4.0.dev0; no commit, tag or publication. Next: RM-005 capability update/removal.

RM-005 completed: re-running `aiwh init` is the explicit update action and updates only files whose current hash matches the manifest. Added `aiwh managed remove PROJECT [--dry-run]`: hash-verified exclusive files are removed; AGENTS/CLAUDE markers and the appended `.gitignore` block are stripped while remaining user text is retained. Changed, missing-provenance, symlinked or structurally unrecognized paths are preserved/reported; removal keeps conflicting hashes in the manifest, forgets already-missing entries, leaves empty parent directories and never removes handoffs, state, game-port plans or other unmanifested files. Evidence: 10 focused `ManagedManifestTests` and all 59 repository tests passed; `aiwh doctor` passed; no code diagnostics remain. The only editor diagnostic is the unchanged README table's MD060 style warning. Release status: Unreleased v0.4.0.dev0; no commit, tag or publication. Next: RM-006 recoverable writes.
RM-006 completed: managed writes, removals and manifest changes use a private transaction journal with preimage backups and atomic target replacement. A subsequent mutating init/remove rolls back an interrupted transaction; rollback verifies expected/current hashes, is retryable if interrupted, and preserves intervening user changes as a hard failure. Dry-run refuses a pending transaction without mutation; a committed journal only cleans backups. Evidence: two focused failure-injection tests passed for init/remove partial failure, recovery interrupted and retried, Unicode/spaced path and pending-transaction dry-run; all 61 repository tests passed; `aiwh doctor` passed; `aiwh resume . --dry-run` identified RM-007 as next; no code diagnostics remained. The only editor diagnostic was the unchanged README table's MD060 style warning. Release status: Unreleased v0.4.0.dev0; no commit, tag or publication. Next: RM-007 versioned continuity schema.
RM-007 completed: `resume` now writes private `.ai-workbench/state.json` schema version 1, separating refreshed observations from persistent tasks, explicitly approved decisions and selected/rejected resources. Tasks retain stable IDs, status, blockers, risks and milestone outcomes; explicit checklist IDs are reused and other IDs derive deterministically from source path/title. Unversioned state migrates non-destructively under `legacy_observation`; corrupt, malformed and future schemas fail before changing either handoff file. State replacement is atomic. Evidence: four focused continuity-state tests passed, including repeated resume, private-record preservation, legacy snapshot retention, no inferred usefulness and fail-closed corruption/future-schema handling; all 64 repository tests passed; `aiwh doctor` passed; `aiwh resume . --dry-run` identified RM-008 as next; no diagnostics in touched Python files; `git diff --check` passed (Git emitted only LF/CRLF conversion warnings). Risk/limit: records are maintained in the private JSON by the user/agent; no dedicated editing CLI exists, and bounded history is deferred to RM-008. Release status: Unreleased v0.4.0.dev0; no commit, tag or publication. Next: RM-008 bounded snapshot history and session deltas.
RM-008 completed: upgraded private continuity state to schema v2, migrating v1 without dropping records; `resume` keeps at most 10 snapshots and writes the latest delta to both state.json and CONTEXT.md. Comparisons separate observed Git-status path/pending-item changes from blocker/status changes and explicit decision/resource records. Resource outcomes without user-confirmed usefulness remain unknown, selection does not imply use/success, and dry-run leaves history unchanged. Evidence: focused migration and three-session comparison tests passed, including added/resolved file status, blockers, task-status and usefulness changes, unknown outcomes, bounded history and dry-run; all 66 repository tests passed; `aiwh doctor` passed; `aiwh resume . --dry-run` identified RM-009 as next; no diagnostics in touched Python files; `git diff --check` passed with only LF/CRLF warnings. Risk/limit: observed file deltas reflect tracked Git status and do not hash file contents; untracked files remain excluded by the existing scan. Release status: Unreleased v0.4.0.dev0; no commit, tag or publication. Next: RM-009 task-ready handoffs.

Roadmap proposal incorporated: user-provided analysis identifies the next product opportunity as Contextual Resource Intelligence, not another bookmark/star importer. Local source confirms existing read-only imports, profile detection and deterministic keyword/category ranking; learning from feedback, comparing alternatives, and durable resource decisions are not implemented yet. RM-015 now prioritizes explainable task/project ranking and a non-activating Skill/MCP comparison; RM-007/RM-009 preserve decisions, selected resources, user-confirmed usefulness, reasons and limits for cross-session handoff. Project Knowledge Packs and structured Knowledge Feedback remain a later P2, gated on the core state schema and evidence that recommendations are useful. Local Semantic Search remains P3 and optional, after deterministic baselines; no paid provider or external content execution is assumed. The proposal's personal bookmark/star inventory and counts are intentionally not copied into this repository. This was a planning-only update; the next task at that point remained RM-003b.

When completing implementation work, append a short sanitized entry using: task ID; implemented behavior; checks and observed outcome; release status; blockers/risks; next task. Do not store raw private handoffs here.

## Deferred opportunities

Reassess these after the core pilot, rather than automatically adding them to the critical path:

- P2 Project Knowledge Packs: generate a small, user-approved project-local collection of relevant references and approved skills after RM-015 ranking and RM-007/RM-009 state/ownership contracts are stable. Keep it private, inspectable, refreshable and removable; never copy external repository code or silently install MCPs.
- P2 Knowledge Feedback: let users record whether a recommendation was selected, used, useful or rejected and why. Persist only explicit feedback, keep it local and reversible, and measure recommendation changes against RM-014 fixtures before allowing it to affect rankings.
- P3 Local Semantic Search: evaluate an optional local/custom embedding or model only after deterministic Resource Intelligence has measured baselines and a defined privacy/resource budget. Maintain offline deterministic fallback; no mandatory paid provider.
- Explicit native MCP/plugin configuration with plan, approval, health check and reversible ownership; no automatic credential management.
- Optional recurring audits and native startup hooks, disabled by default, with cancellation and uninstall tests.
- Native subagent definitions only where documented runtime support exists; role templates remain templates until verified.
- Optional read-only project dashboard or graph navigation driven by demonstrated user needs, not a replacement for the portable CLI.

Do not turn Workbench into a bookmark organizer, agent-chat exporter, cloud control plane or automatic executor of third-party code.
