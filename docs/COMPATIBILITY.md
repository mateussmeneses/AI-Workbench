# Compatibility, Schema, and Migration Contract

## CLI & Python Floor
- **Python:** `>=3.10` (tested on Windows Python 3.10+ and 3.14; CI configured for Windows and Ubuntu across 3.10, 3.12, 3.14).
- **Mandatory runtime dependency:** `PyYAML>=6.0.3,<7`.
- **Optional extras:** `ai-workbench[semantic]` (`sqlite-vec`, `fastembed`) is strictly opt-in; core commands fall back to stdlib `sqlite3` FTS5 or deterministic heuristics when absent.

## Private State Schema (`.ai-workbench/state.json`)
- **Current version:** `schema_version: 2`.
- **Backward migration:** Unversioned legacy state files migrate non-destructively into `legacy_observation`; `schema_version: 1` migrates to `2` preserving `tasks`, `decisions`, `resources`, and `rejections`.
- **Forward safety:** Corrupt JSON, symlinked state files, or unsupported future `schema_version` values fail closed before overwriting `state.json` or `CONTEXT.md`.
- **Bounded history:** `history` retains at most 10 snapshots; `validation_history` retains at most 10 runs.

## Managed-File Manifest (`.ai-workbench/managed-files.json`)
- **Current version:** `schema_version: 1`.
- **Ownership & rollback:** Every `init` and `managed remove` operation is journaled in `.ai-workbench/managed-files.transaction` with preimage backups. Modified user files and conflicting unmanifested files are preserved, never overwritten or deleted.

## Deprecation Policy
- Pre-1.0 (`0.x.y`): additive CLI flags and optional schema fields are introduced without breaking existing consumers; breaking schema changes require an explicit migration path.
- Post-1.0: incompatible CLI, schema, or manifest changes require a major version increment.
