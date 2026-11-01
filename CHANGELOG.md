# Changelog

## Unreleased

- RM-008: Retained up to 10 private continuity snapshots and added session deltas for Git-status paths, pending items, task blockers/status, decisions and resource records; resource outcomes remain unknown until explicit user feedback.
- RM-007: Added private `state.json` schema version 1 for observations, stable tasks, explicitly approved decisions and selected/rejected resources; legacy snapshots migrate without data loss and corrupt/future schemas fail closed.
- RM-006: Added a private transaction journal, per-file backups and atomic replacements for managed writes/removals; the next mutating command rolls back an interrupted transaction without overwriting intervening edits.
- Added failure-injection tests for interrupted init, interrupted removal, interrupted recovery, repeated retry, Unicode/spaced paths and dry-run refusal while a transaction is pending.
- RM-005: Re-running `aiwh init` explicitly updates only hash-verified managed files; added `aiwh managed remove [PROJECT] [--dry-run]`, which deletes unchanged exclusive files and removes only Workbench-owned sections from shared instruction/ignore files. Edited or unverified files are preserved as conflicts.
- RM-004: Added a version-1 project-local managed-file manifest with SHA-256 hashes and dry-run/apply categories for added, unchanged, changed and conflicting files.
- Bootstrap preserves modified managed files and unmanifested generated-file collisions, safely merges first-time instruction and gitignore additions, and rejects invalid manifests; transactional recovery was added in RM-006.
- RM-003: Added `game-porting/catalog.json` to wheel assets after clean Python 3.10 installation exposed the missing runtime file; expanded package verification to require it.
- Verified the v0.4.0.dev0 wheel and sdist on Windows/Python 3.10.22 with a clean temporary PyYAML 6.0.3 wheelhouse; all 49 unit tests and `aiwh doctor` passed. Hosted CI was not observed.
- RM-003a: Bundled canonical capability assets in wheels/sdists, added installed-package asset resolution, and verified an offline wheel build and rebuild from sdist outside the checkout.
- Added an offline temporary-install verifier and four packaging regression tests; the verifier checks the installed launcher, native skill paths, idempotence, previews and handoffs, and rejects missing/private/unexpected artifact contents.
- Updated existing CI/release workflows to install declared dependencies and verify built distributions; retained Python 3.10/3.12 and added 3.14 to the Ubuntu/Windows CI matrix. Hosted CI results remain unverified.
- RM-002: Added safe YAML skill-frontmatter validation, duplicate JSON-key and profile-list checks, contextual file diagnostics, missing skill/role/MCP reference checks and explicit disabled-by-default MCP validation.
- Declared `PyYAML>=6.0.3,<7` as a runtime dependency and added 10 isolated registry tests covering malformed metadata, missing files, duplicates and unsafe YAML tags; user-modified installed skills remain untouched.
- RM-001: Aligned the CLI reference and continuation guide with current commands, replaced the obsolete milestone queue with the canonical roadmap, and documented synthetic adapter coverage separately from unverified runtime support.
- Clarified source-checkout installation, current snapshot limits and the distinction between dry-run writes and explicitly requested GitHub source reads.
- Fixed the generated project guide to recommend `aiwh resume .` instead of the unsupported `--project` option, with regression coverage in the existing bootstrap test.

## v0.3.0 — Multidisciplinary capability routing

- Added 26 composable capability areas, with 28 mapped project profiles and 45 unique skills.
- Added `aiwh areas` and `aiwh recommend` with bounded, explainable local project classification.
- Added explicit `aiwh init --area` and opt-in `--auto-areas` with goal descriptions.
- Preserved MCPs/plugins as opt-in recommendations, not automatically activated services.
- Consolidated duplicated skill folders and added reference validation and new unit tests.
- Documented community research and provided GitHub CLI publication workflow.

## v0.2.0 — Bootstrap and continuation starter

- Portable project bootstrap, agent adapters and local project handoffs.
- Optional read-only favorites/GitHub stars catalog.
