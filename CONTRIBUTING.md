# Contributing

AI Workbench is an open, provider-independent project. Contributions should maintain local-first behavior, cross-agent portability and project-data privacy.

1. Choose an area in `capabilities/areas/catalog.json` or add a new one with descriptive signals.
2. Reuse existing skills and agent roles when possible; avoid duplicate skill names and long instruction dumps. Follow the [registry validation contract](docs/ARCHITECTURE.md#registry-validation) for frontmatter, profile fields and MCP entries.
3. Reference only validated catalog identifiers; never enable MCPs or external plugins as a side effect of discovery.
4. Add unit tests for area matching, incremental bootstrap, explicit user choices and privacy boundaries.
5. Run `python -m unittest discover -s tests -v` and `aiwh doctor` before sending a pull request.
6. Keep public docs and code comments in English; do not commit user bookmarks, credentials, API keys or private handoffs.

Source templates are role suggestions, not automatic agent installations. External tools must be user-selected separately.
