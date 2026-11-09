"""Composable, explainable capability-area selection (offline; no installation)."""
from __future__ import annotations

import fnmatch
import json
import re
from pathlib import Path

from .workbench import CAPABILITIES, registry

IGNORED = {'.git', '.venv', 'venv', 'node_modules', 'dist', 'build', 'coverage',
           '.next', '.idea', '__pycache__', 'vendor', '.gradle', 'bin', 'obj',
           '.ai-workbench', '.agents', '.claude', '.openclaude'}
MAX_FILES = 2500
MAX_TEXT = 40000


def catalog():
    """Versioned cross-domain area catalog, not hardcoded into any one agent."""
    path = CAPABILITIES / 'areas' / 'catalog.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data.get('areas'), dict) or not data['areas']:
        raise ValueError('Area catalog is missing or empty')
    return data['areas']


def validate_catalog():
    """Catch dangling references and malformed area entries early."""
    reg = registry()
    areas = catalog()
    plugins = json.loads((CAPABILITIES / 'plugins' / 'catalog.json').read_text(encoding='utf-8'))
    assert isinstance(plugins, dict)
    for area, entry in areas.items():
        if not entry.get('label') or not isinstance(entry.get('signals'), dict):
            raise ValueError(f'Missing label/signals in area {area}')
        for field, available in [('profiles',reg['profiles']),('skills',reg['skills']),
                                 ('agents',reg['agents']),('mcps',reg['mcps']),('plugins',plugins)]:
            missing = set(entry.get(field,[])) - set(available)
            if missing:
                raise ValueError(f'Area {area} has invalid {field}: {sorted(missing)}')
    return {'areas': len(areas), 'plugins': len(plugins),
            'profiles': len(reg['profiles']), 'skills': len(reg['skills']),
            'agents': len(reg['agents']), 'mcps': len(reg['mcps'])}


def _files(project: Path):
    if not project.is_dir():
        return []
    found = []
    # Use bounded traversal: never parse an entire monorepo or dependency tree.
    for base, dirs, files in __import__('os').walk(project):
        dirs[:] = sorted(d for d in dirs if d not in IGNORED and not d.startswith('.'))
        for name in sorted(files):
            try:
                rel = (Path(base) / name).relative_to(project).as_posix()
                found.append(rel)
                if len(found) >= MAX_FILES:
                    return found
            except ValueError:
                continue
    return found


def _matches(pattern, path):
    return fnmatch.fnmatchcase(path.lower(),pattern.lower()) or (
        pattern.startswith('**/') and fnmatch.fnmatchcase(path.lower(),pattern[3:].lower()))


def _text(project: Path):
    evidence=[]
    # Keep scans limited to human-authored project metadata; not source code, secrets or private handoffs.
    for name in ('README.md', 'README.rst', 'package.json', 'pyproject.toml',
                 'Cargo.toml', 'go.mod', 'pom.xml', 'requirements.txt'):
        f=project / name
        if f.is_file() and not f.is_symlink() and f.stat().st_size < MAX_TEXT:
            evidence.append(f.read_text(encoding='utf-8',errors='replace')[:6000])
    return '\n'.join(evidence)[:MAX_TEXT]


def _word_occurs(term, haystack):
    term=term.lower().strip()
    if not term:
        return False
    return bool(re.search(r'(?<![\w])'+re.escape(term)+r'(?![\w])',haystack))


def resolve_areas(project, *, goal='', selected=None, max_auto=4):
    """Rank areas from bounded project evidence and user's goal.

    Explicit areas are always selected; automatic signals are suggestions, not truth.
    When no signals match, this returns an empty selection rather than inventing a domain.
    """
    path=Path(project).expanduser().resolve()
    areas=catalog()
    requested=list(dict.fromkeys(selected or []))
    unknown=set(requested)-set(areas)
    if unknown:
        raise ValueError('Unknown areas: '+', '.join(sorted(unknown)))
    paths=_files(path)
    goal_text=goal.lower()[:4000]
    metadata_text=_text(path).lower()
    results=[]
    for key,entry in areas.items():
        signals=entry.get('signals',{})
        file_matches=[p for p in paths if any(_matches(pat,p) for pat in signals.get('files',[]))]
        goal_matches=[term for term in signals.get('keywords',[]) if _word_occurs(term,goal_text)]
        meta_matches=[term for term in signals.get('keywords',[]) if _word_occurs(term,metadata_text)]
        # More weight to intentional user goals. Saturate evidence to stop giant repos dominating.
        score=6*min(len(goal_matches),4)+3*min(len(file_matches),4)+min(len(meta_matches),3)
        if key in requested:
            score+=100
        if score:
            results.append({'id':key,'label':entry['label'],'score':score,
                            'explicit':key in requested,
                            'evidence':{'goal_terms':goal_matches[:8],
                                        'files':file_matches[:6],
                                        'metadata_terms':meta_matches[:6]}})
    results.sort(key=lambda x:(0, requested.index(x['id'])) if x['explicit'] else (1,-x['score'],x['id']))
    auto=[r for r in results if not r['explicit']]
    # Ensure explicit manual choices don't silently recruit unrelated areas.
    chosen=[r for r in results if r['explicit']]+(auto[:max_auto] if not requested else [])
    return {'project':str(path),'goal':goal,'areas':[r['id'] for r in chosen],
            'ranked':results,'limited_scan':len(paths)>=MAX_FILES,'files_examined':len(paths)}


def recommend(project, *, goal='', selected=None, max_auto=4):
    match=resolve_areas(project,goal=goal,selected=selected,max_auto=max_auto)
    areas=catalog()
    def union(field):
        return list(dict.fromkeys(value for area in match['areas']
                                  for value in areas[area].get(field,[])))
    result={**match,'profiles':union('profiles'), 'skills':union('skills'),
            'agents':union('agents'), 'mcps':union('mcps'),
            'plugins':union('plugins'), 'utilities':union('utilities')}
    from .references import references_for
    refs=references_for(match['areas'],limit=None) if match['areas'] else []
    result['references_total']=len(refs)
    result['references']=[{'title':r['title'],'url':r['url'],'kind':r['kind'],'risk':r.get('risk',[])}
                          for r in refs[:10]]
    if any(area in ('game-port','reverse-engineering','decompilation',
                    'recompilation','game-modding') for area in result['areas']):
        from .game_porting import assess_game_port
        result['game_porting'] = assess_game_port(project, goal=goal)
    result['execution']={
        'plugins':'suggest-only; connection requires explicit user action',
        'mcps':'recommend-only; no server enabled or credentials stored',
        'skills':'copy only with explicit aiwh init; conflicts never overwritten',
        'agents':'role templates, not automatically registered subagents',
        'unknown_goal':'choose explicit --area when no evidence is found',
        'references':'curated links with risk labels; read-only suggestions',
    }
    return result


def markdown_plan(result):
    lines=['# AI Workbench recommendation', '',
           'Selected areas: '+(', '.join(result['areas']) if result['areas'] else '(none; choose --area)'),
           '']
    # The persisted plan records active selections only: generated AGENTS.md
    # must not alter an explicitly chosen area's explanation on re-run.
    for r in [row for row in result['ranked'] if row['id'] in result['areas']][:12]:
        why=[]
        for k,v in r['evidence'].items():
            if v: why.append(k+': '+', '.join(v[:4]))
        lines.append(f"- {r['id']} ({r['score']} points): "+('; '.join(why) or 'explicit selection'))
    for field in ('profiles','skills','agents','mcps','plugins','utilities'):
        lines.extend(['',field.title()+': '+(', '.join(result[field]) if result[field] else '(none)')])
    if result.get('references'):
        lines.extend(['',f"References ({len(result['references'])} of {result['references_total']}; suggestions, never installed):"])
        for ref in result['references']:
            risk=f" (risk: {', '.join(ref['risk'])})" if ref['risk'] else ''
            lines.append(f"- [{ref['title']}]({ref['url']}){risk}")
    if 'game_porting' in result:
        gp=result['game_porting']
        lines.extend(['', 'Game-porting triage: '+gp['workflow']['name']+'; platform: '+str(gp['platform'] or 'unverified'),
                      'Run aiwh game-port <project> --binary <file> --track <mode> for evidence-based tool selection.'])
    lines.extend(['','Capabilities are proposed, not activated. Use aiwh init --area <name> for selected areas.'])
    return '\n'.join(lines)+'\n'
