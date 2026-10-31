# Security and privacy

No secret, browser bookmark or private handoff is required for project area discovery. `aiwh recommend` reads bounded local filenames and selected project metadata. It does not access the network or execute project code.

External integrations (MCP servers and plugin candidates) are never activated by `recommend`, `init` or `resume`. User must configure credentials and permissions explicitly in each agent.

GitHub star import uses an already authenticated `gh` installation and stores the resulting catalog outside the repository. Browser bookmark import is read-only and optional. Do not publish `~/.ai-workbench-hub/catalog.json`, `.ai-workbench` handoffs, `.env` files or tokens.

Report suspected vulnerabilities through the security reporting mechanism of the repository after it is published. Avoid public issue descriptions that include exploitable secrets.
