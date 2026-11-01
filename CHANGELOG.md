# Changelog

## Unreleased

- RM-003a: Bundled canonical capability assets in wheels/sdists, added installed-package asset resolution, and verified an offline wheel build and rebuild from sdist outside the checkout.
- Added an offline temporary-install verifier and four packaging regression tests; the verifier checks the installed launcher, native skill paths, idempotence, previews and handoffs, and rejects missing/private/unexpected artifact contents.
- Updated existing CI/release workflows to install declared dependencies and verify built distributions; retained Python 3.10/3.12 and added 3.14 to the Ubuntu/Windows CI matrix. Clean dependency installation, minimum-runtime execution and hosted CI results remain unverified.
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
