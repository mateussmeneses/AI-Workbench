"""Export the continuity handoff to portable formats without touching the project.

Formats:
- ``json``: ``aiwh-handoff/1`` document (observation, tasks, decisions, resources, delta).
- ``markdown``: the same text written by ``aiwh resume``.
- ``claude-memory``: one Claude Code memory file (frontmatter, ``type: project``)
  plus a ``MEMORY.md`` index line, written to an explicit output directory.
- ``wiki``: plain Markdown pages (overview, pending, decisions, commits) suitable
  for Markdown-based memory stores such as git-backed wikis. Ingestion by a
  specific tool (for example ai-memory) is not verified and stays the user's step.

Nothing is written to the project or to global agent directories unless the user
passes that path explicitly as ``output``.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .workbench import _continuity_state, continuation_markdown, inspect_project

FORMATS = ('json', 'markdown', 'claude-memory', 'wiki')


def _slug(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')[:48] or 'project'


def build_handoff(project):
    data = inspect_project(project)
    state_path = Path(project).expanduser().resolve() / '.ai-workbench' / 'state.json'
    state = _continuity_state(data, state_path)  # read-only: nothing is written here
    return data, state


def _pages(data, state):
    name = Path(data['project']).name
    open_tasks = [t for t in state['tasks'] if t.get('status') not in ('completed', 'cancelled')]
    overview = [f'# {name}: overview', '', f'- Snapshot: {data["generated_at"]}',
                f'- Branch: `{data["branch"]}`', f'- Profiles: {", ".join(data["profiles"])}',
                f'- Test/build indicators: {", ".join(data["test_indicators"]) or "not detected"}',
                f'- Working-tree entries: {len(data["working_tree_changes"])}', '',
                'Observations from local Git and documents, not verified test results.']
    pending = [f'# {name}: open work', '']
    pending += [f'- [{t.get("status", "pending")}] {t.get("title", t.get("id"))}'
                + (f' (blockers: {", ".join(t["blockers"])})' if t.get('blockers') else '')
                for t in open_tasks] or ['- No open tasks recorded.']
    decisions = [f'# {name}: decisions', '']
    decisions += [f'- {d.get("text") or d.get("title") or d.get("id")}: {d.get("rationale", "")}'
                  for d in state['decisions']] or ['- No approved decisions recorded.']
    commits = [f'# {name}: recent commits', '']
    commits += [f'- {c}' for c in data['recent_commits']] or ['- No readable Git history.']
    return {'overview.md': overview, 'open-work.md': pending, 'decisions.md': decisions,
            'recent-commits.md': commits}


def export_handoff(project, fmt, output=None):
    if fmt not in FORMATS:
        raise ValueError('Unknown format: ' + fmt)
    data, state = build_handoff(project)
    name = Path(data['project']).name
    if fmt == 'json':
        payload = {'schema': 'aiwh-handoff/1', 'project': name, 'generated_at': data['generated_at'],
                   'observed': data, 'tasks': state['tasks'], 'decisions': state['decisions'],
                   'resources': state['resources'], 'latest_delta': state['latest_delta']}
        files = {'handoff.json': json.dumps(payload, indent=2, ensure_ascii=False) + '\n'}
    elif fmt == 'markdown':
        files = {'CONTEXT.md': continuation_markdown(data, delta=state['latest_delta'])}
    elif fmt == 'claude-memory':
        slug = f'{_slug(name)}-continuity'
        pages = _pages(data, state)
        body = '\n'.join(pages['overview.md'][2:] + [''] + pages['open-work.md'][2:])
        memory = ('---\n'
                  f'name: {slug}\n'
                  f'description: Continuity snapshot for {name} exported by AI Workbench on {data["generated_at"][:10]}\n'
                  'metadata:\n  type: project\n'
                  '---\n\n'
                  f'{body}\n\n'
                  '**Why:** carries project state across agent sessions.\n'
                  '**How to apply:** verify against the repository before acting; it may be stale.\n')
        files = {f'{slug}.md': memory,
                 'MEMORY.md': f'- [{name} continuity]({slug}.md) — exported AI Workbench handoff\n'}
    else:
        files = {page: '\n'.join(lines) + '\n' for page, lines in _pages(data, state).items()}
    written = []
    if output is not None:
        target = Path(output).expanduser().resolve()
        target.mkdir(parents=True, exist_ok=True)
        for filename, content in files.items():
            path = target / filename
            if filename == 'MEMORY.md' and path.exists():
                existing = path.read_text(encoding='utf-8')
                if content.strip() in existing:
                    continue
                content = existing.rstrip('\n') + '\n' + content
            path.write_text(content, encoding='utf-8')
            written.append(str(path))
    return {'format': fmt, 'files': files, 'written': written}
