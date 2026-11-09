"""Preview (and optionally apply) per-agent MCP configuration from the catalog.

Default behavior is a preview. ``apply`` only writes a project-level Claude Code
``.mcp.json`` that does not exist yet (or that Workbench already owns), through
the managed-file manifest so ``aiwh managed remove`` can reverse it. Global
agent configuration is never modified; credentials are never written.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .workbench import ManagedFilePlan, registry

SUPPORTED = ('claude', 'codex', 'hermes', 'generic')


def _launch(server, windows):
    server = dict(server)
    if windows and server.get('command') == 'npx':
        server['args'] = ['/c', 'npx', *server.get('args', [])]
        server['command'] = 'cmd'
    return server


def resolve_mcps(project=None, *, mcps=None, areas=None):
    catalog = registry()['mcps']
    if mcps:
        unknown = sorted(set(mcps) - set(catalog))
        if unknown:
            raise ValueError('Unknown MCPs: ' + ', '.join(unknown))
        return list(dict.fromkeys(mcps))
    if areas:
        from .areas import recommend
        return recommend(project or Path.cwd(), selected=areas)['mcps']
    raise ValueError('Select MCPs with --mcp or --area')


def _toml_value(value):
    if isinstance(value, list):
        return '[' + ', '.join(json.dumps(v) for v in value) + ']'
    return json.dumps(value)


def mcp_plan(project, *, agent='claude', mcps=None, areas=None, windows=None, apply=False):
    if agent not in SUPPORTED:
        raise ValueError(f'Unsupported agent for MCP plan: {agent}')
    project = Path(project).expanduser().resolve()
    windows = (os.name == 'nt') if windows is None else windows
    catalog = registry()['mcps']
    selected = resolve_mcps(project, mcps=mcps, areas=areas)
    configured, manual = {}, []
    for name in selected:
        entry = catalog[name]
        if 'server' in entry:
            configured[name] = _launch(entry['server'], windows)
        else:
            manual.append({'mcp': name, 'url': entry.get('url'), 'reason': 'no verified launch command in catalog'})
    notes = [catalog[name]['setup_note'] for name in configured if catalog[name].get('setup_note')]
    if agent == 'claude':
        target = '.mcp.json (project scope)'
        snippet = json.dumps({'mcpServers': configured}, indent=2) + '\n'
    elif agent == 'codex':
        target = '~/.codex/config.toml (merge manually; global file is never written)'
        blocks = []
        for name, server in configured.items():
            blocks.append(f'[mcp_servers.{name}]')
            blocks += [f'{key} = {_toml_value(value)}' for key, value in server.items() if key != 'type']
            blocks.append('')
        snippet = '\n'.join(blocks)
    elif agent == 'hermes':
        target = '~/.hermes/config.yaml mcp_servers (merge manually; keep enabled: false until needed)'
        lines = ['mcp_servers:']
        for name, server in configured.items():
            lines.append(f'  {name}:')
            lines += [f'    {key}: {json.dumps(value)}' for key, value in server.items() if key != 'type']
            lines += ['    enabled: false', '    lazy: true']
        snippet = '\n'.join(lines) + '\n'
    else:
        target = 'agent-specific configuration'
        snippet = json.dumps(configured, indent=2) + '\n'
    result = {'project': str(project), 'agent': agent, 'target': target, 'mcps': selected,
              'configured': sorted(configured), 'manual_setup': manual, 'notes': notes,
              'snippet': snippet, 'applied': False}
    if apply:
        if agent != 'claude':
            raise ValueError('--apply is only supported for the Claude Code project .mcp.json')
        if not project.is_dir():
            raise ValueError(f'Project not found: {project}')
        if not configured:
            raise ValueError('No selected MCP has a verified launch command; nothing to apply')
        plan = ManagedFilePlan(project, False)
        plan.write(project / '.mcp.json', snippet)
        managed = plan.finish()
        result['managed_files'] = managed
        result['applied'] = '.mcp.json' in managed['added'] or '.mcp.json' in managed['changed']
        if '.mcp.json' in managed['conflicting']:
            result['notes'].append('Existing .mcp.json is not owned by Workbench; merge the snippet manually.')
    return result
