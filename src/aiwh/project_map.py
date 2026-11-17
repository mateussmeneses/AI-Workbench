"""Deterministic AST and manifest project mapper (offline, non-executing).

Builds a structural map of modules, symbols, entrypoints and internal edges
without running project code or calling external LLMs.
"""
from __future__ import annotations

import ast
import json
import os
from pathlib import Path

from .areas import IGNORED
from .core import now

MAX_MAP_FILES = 1000
MAX_SOURCE_BYTES = 512 * 1024


def _walk_files(project: Path):
    found = []
    for base, dirs, files in os.walk(project):
        dirs[:] = sorted(d for d in dirs if d not in IGNORED and not d.startswith('.'))
        for name in sorted(files):
            path = Path(base) / name
            try:
                rel = path.relative_to(project).as_posix()
            except ValueError:
                continue
            found.append((rel, path))
            if len(found) >= MAX_MAP_FILES:
                return found, True
    return found, False


def _parse_python(rel: str, path: Path):
    try:
        if path.stat().st_size > MAX_SOURCE_BYTES:
            return None
        source = path.read_text(encoding='utf-8', errors='replace')
        tree = ast.parse(source, filename=rel)
    except (OSError, SyntaxError):
        return None
    classes = [n.name for n in tree.body if isinstance(n, ast.ClassDef)]
    functions = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    imports = []
    has_main = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = ('.' * node.level) + (node.module or '')
            if mod:
                imports.append(mod)
        elif isinstance(node, ast.If):
            test = ast.unparse(node.test) if hasattr(ast, 'unparse') else ''
            if '__name__' in test and '__main__' in test:
                has_main = True
    return {
        'path': rel,
        'language': 'python',
        'lines': len(source.splitlines()),
        'classes': classes[:20],
        'functions': functions[:30],
        'imports': list(dict.fromkeys(imports))[:30],
        'entrypoint': has_main,
    }


def _manifest_summary(project: Path):
    manifests = {}
    pkg = project / 'package.json'
    if pkg.is_file() and not pkg.is_symlink() and pkg.stat().st_size <= MAX_SOURCE_BYTES:
        try:
            data = json.loads(pkg.read_text(encoding='utf-8'))
            manifests['package.json'] = {
                'name': data.get('name'),
                'scripts': sorted((data.get('scripts') or {}).keys())[:20],
                'dependencies': sorted((data.get('dependencies') or {}).keys())[:30],
            }
        except (OSError, ValueError):
            pass
    pyproj = project / 'pyproject.toml'
    if pyproj.is_file() and not pyproj.is_symlink() and pyproj.stat().st_size <= MAX_SOURCE_BYTES:
        try:
            import tomllib
            data = tomllib.loads(pyproj.read_text(encoding='utf-8'))
            proj = data.get('project', {})
            manifests['pyproject.toml'] = {
                'name': proj.get('name'),
                'scripts': dict(proj.get('scripts', {})),
                'dependencies': list(proj.get('dependencies', []))[:30],
            }
        except (OSError, ValueError, ImportError):
            pass
    return manifests


def _internal_edges(modules):
    by_stem = {}
    for mod in modules:
        stem = Path(mod['path']).stem
        by_stem.setdefault(stem, []).append(mod['path'])
    edges = []
    for mod in modules:
        src_pkg = Path(mod['path']).parent.as_posix()
        for imp in mod.get('imports', []):
            target_name = imp.lstrip('.').split('.')[-1] if imp.startswith('.') else imp.split('.')[0]
            if not target_name or target_name == Path(mod['path']).stem:
                continue
            for target_path in by_stem.get(target_name, []):
                if imp.startswith('.') and Path(target_path).parent.as_posix() != src_pkg:
                    continue
                edge = {'from': mod['path'], 'to': target_path, 'import': imp}
                if edge not in edges:
                    edges.append(edge)
    return edges[:200]


def map_project(project):
    """Build a deterministic structural map of ``project`` without executing code."""
    root = Path(project).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f'Project not found: {root}')
    files, truncated = _walk_files(root)
    modules = []
    entrypoints = []
    for rel, path in files:
        if path.suffix == '.py':
            parsed = _parse_python(rel, path)
            if parsed:
                modules.append(parsed)
                if parsed['entrypoint']:
                    entrypoints.append(rel)
    manifests = _manifest_summary(root)
    if 'pyproject.toml' in manifests:
        for script_name, target in manifests['pyproject.toml'].get('scripts', {}).items():
            entrypoints.append(f'{script_name} -> {target}')
    edges = _internal_edges(modules)
    return {
        'schema': 'aiwh-map/1',
        'project': str(root),
        'generated_at': now(),
        'files_scanned': len(files),
        'truncated': truncated,
        'entrypoints': sorted(dict.fromkeys(entrypoints)),
        'manifests': manifests,
        'modules': modules,
        'edges': edges,
    }


def project_map_markdown(mapping):
    """Render a compact Markdown summary of the project map."""
    lines = [
        f'# Project Map — {Path(mapping["project"]).name}',
        '',
        f'Generated: {mapping["generated_at"]}',
        f'Files scanned: {mapping["files_scanned"]}' + (' (truncated)' if mapping['truncated'] else ''),
        f'Python modules: {len(mapping["modules"])} | Internal edges: {len(mapping["edges"])}',
        '',
        '## Entrypoints',
        '',
    ]
    lines += [f'- `{ep}`' for ep in mapping['entrypoints']] or ['- None detected.']
    lines += ['', '## Modules', '']
    for mod in mapping['modules'][:80]:
        symbols = mod['classes'] + mod['functions']
        preview = ', '.join(symbols[:6]) + ('...' if len(symbols) > 6 else '')
        lines.append(f'- `{mod["path"]}` ({mod["lines"]}L)' + (f': {preview}' if preview else ''))
    if not mapping['modules']:
        lines.append('- No Python AST modules parsed.')
    if mapping['edges']:
        lines += ['', '## Internal dependencies', '']
        lines += [f'- `{e["from"]}` -> `{e["to"]}` (`{e["import"]}`)' for e in mapping['edges'][:50]]
    return '\n'.join(lines) + '\n'


def save_project_map(project, mapping):
    """Persist ``PROJECT_MAP.json`` and ``PROJECT_MAP.md`` inside ``.ai-workbench/``."""
    folder = Path(project).expanduser().resolve() / '.ai-workbench'
    folder.mkdir(exist_ok=True)
    json_path = folder / 'PROJECT_MAP.json'
    md_path = folder / 'PROJECT_MAP.md'
    json_path.write_text(json.dumps(mapping, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    md_path.write_text(project_map_markdown(mapping), encoding='utf-8', newline='\n')
    return {'json': str(json_path), 'markdown': str(md_path)}
