# Areas and context routing

The catalog in `capabilities/areas/catalog.json` has 27 independent, composable disciplines. They can describe a software product, a business workflow, a media campaign, a game-porting project, or combinations of all of these.

| Example | Areas | Activated artifacts |
|---|---|---|
| SaaS product | `frontend` + `backend` + `ux-design` + `sales` | Only selected skill/profile templates are copied at `init` |
| Game reverse engineering | `reverse-engineering` + `decompilation` + `recompilation` + `game-modding` | Disassembly, evidence, compilation and validation guidance |
| Go-to-market | `marketing` + `content-creation` + `data-analytics` + `sales` | Messaging, funnel, KPI and content roles |
| QA platform | `qa-testing` + `api-integration` + `devops` | Testing, integration and release guidance |

The matching engine reads filenames plus a bounded set of project metadata files. Explicit `--goal` terms carry more weight than filename matches. A lack of evidence returns no inferred areas, not a fictitious diagnosis. `aiwh recommend --json` explains signals and returns a list of proposed skills, agents, MCPs, plugins and utilities. No external service is contacted.

**Scope:** `--area` choices map to version-controlled profiles; `--auto-areas` is an opt-in to inferred areas. A project can retain multiple profiles. MCP and plugin identifiers are catalog candidates, not proof they are available or installed in the user's agent. Do not auto-enable them.

**Adding a discipline:** edit `capabilities/areas/catalog.json`, create/reuse skills under `capabilities/skills/<area>`, create a profile under `capabilities/profiles`, reference the appropriate role templates, run `aiwh doctor`, and run tests. Duplicate skills and invalid catalog references fail validation.
