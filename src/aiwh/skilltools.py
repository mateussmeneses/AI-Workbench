"""Skill quality lint, context-cost estimates and provenance-tracked local imports.

Imported skills are untrusted text: they are validated, copied only into a
project's agent skill directory through the managed-file manifest (so
``aiwh managed remove`` reverses them), and never executed.
"""
from __future__ import annotations

import hashlib
import json
import re
from itertools import combinations
from pathlib import Path

from .core import now
from .workbench import (AGENTS, ManagedFilePlan, _validate_skill, registry, skill_paths)

TEXT_SUFFIXES = {'.md', '.txt', '.json', '.yaml', '.yml', '.csv', '.toml', '.xml', '.html', '.css'}
SCRIPT_SUFFIXES = {'.sh', '.bash', '.ps1', '.psm1', '.py', '.js', '.mjs', '.cjs', '.ts', '.bat', '.cmd',
                   '.rb', '.pl', '.lua', '.go', '.rs'}
MAX_IMPORT_FILE = 512 * 1024
MAX_IMPORT_SKILLS = 200
RISK_PATTERNS = {
    'pipe-to-shell': r'(curl|wget)[^\n|]*\|\s*(ba|z)?sh\b',
    'powershell-download-exec': r'(iwr|irm|invoke-webrequest|invoke-restmethod)[^\n|]*\|\s*iex\b',
    'invoke-expression': r'\binvoke-expression\b',
    'destructive-delete': r'rm\s+-rf\s+(/|~|\$home)(\s|$)',
    'instruction-override': r'ignore (all )?(previous|prior) instructions',
    'credential-request': r'(paste|send|upload)[^\n]{0,40}(api key|token|password|secret)',
}
GENERIC_DESCRIPTION = re.compile(r'workflows for relevant projects$', re.IGNORECASE)


def _frontmatter_and_body(path):
    text = path.read_text(encoding='utf-8')
    lines = text.splitlines()
    end = lines.index('---', 1)
    meta = '\n'.join(lines[1:end])
    description = ''
    match = re.search(r'^description:\s*(.+)$', meta, re.MULTILINE)
    if match:
        description = match.group(1).strip().strip('"\'')
    return description, '\n'.join(lines[end + 1:])


def estimate_tokens(text):
    """Rough, model-independent estimate (about four characters per token)."""
    return (len(text) + 3) // 4


def _body_lines(body):
    return {re.sub(r'\s+', ' ', line.strip().lower()) for line in body.splitlines()
            if line.strip() and not line.lstrip().startswith('#') and len(line.strip()) > 20}


def lint_skills(skills=None, *, shared_threshold=None, similarity=0.6):
    """Report vague metadata, oversized bodies and duplicated boilerplate. Warnings only."""
    skills = skills or registry()['skills']
    data = {}
    for name, directory in sorted(skills.items()):
        description, body = _frontmatter_and_body(Path(directory) / 'SKILL.md')
        data[name] = {'description': description, 'body': body, 'lines': _body_lines(body)}
    counts = {}
    for entry in data.values():
        for line in entry['lines']:
            counts[line] = counts.get(line, 0) + 1
    threshold = shared_threshold or max(3, len(data) // 5)
    shared = {line for line, count in counts.items() if count >= threshold}
    findings = []
    for name, entry in data.items():
        desc = entry['description']
        if len(desc) < 40 or GENERIC_DESCRIPTION.search(desc):
            findings.append({'skill': name, 'rule': 'vague-description',
                             'detail': 'Description is short or generic; state when the skill applies.'})
        if len(desc) > 1024:
            findings.append({'skill': name, 'rule': 'long-description', 'detail': f'{len(desc)} characters'})
        tokens = estimate_tokens(entry['body'])
        if tokens > 5000:
            findings.append({'skill': name, 'rule': 'large-body',
                             'detail': f'~{tokens} tokens; move details to referenced files'})
        if entry['lines']:
            ratio = len(entry['lines'] & shared) / len(entry['lines'])
            if ratio >= 0.5:
                findings.append({'skill': name, 'rule': 'boilerplate',
                                 'detail': f'{ratio:.0%} of body lines are shared with {threshold}+ skills; '
                                           'add domain-specific procedure'})
    parent = {name: name for name in data}

    def root(name):
        while parent[name] != name:
            parent[name] = parent[parent[name]]
            name = parent[name]
        return name

    for (left, a), (right, b) in combinations(data.items(), 2):
        if a['lines'] and b['lines']:
            score = len(a['lines'] & b['lines']) / len(a['lines'] | b['lines'])
            if score >= similarity:
                parent[root(left)] = root(right)
    clusters = {}
    for name in data:
        clusters.setdefault(root(name), []).append(name)
    for members in clusters.values():
        if len(members) > 1:
            findings.append({'skill': ', '.join(sorted(members)), 'rule': 'near-duplicate',
                             'detail': f'{len(members)} skills share at least {similarity:.0%} of body lines'})
    summary = {}
    for finding in findings:
        summary[finding['rule']] = summary.get(finding['rule'], 0) + 1
    return {'skills': len(data), 'shared_line_threshold': threshold, 'summary': summary,
            'shared_lines': sorted(shared, key=lambda l: (-counts[l], l))[:10],
            'findings': findings}


def context_estimate(skill_dirs):
    """Approximate context cost: metadata always listed, bodies/resources loaded on demand."""
    skill_dirs = [Path(d) for d in skill_dirs]
    metadata = body = resources = 0
    for directory in skill_dirs:
        directory = Path(directory)
        description, text = _frontmatter_and_body(directory / 'SKILL.md')
        metadata += estimate_tokens(directory.name + ' ' + description)
        body += estimate_tokens(text)
        for extra in directory.rglob('*'):
            if extra.is_file() and extra.name != 'SKILL.md':
                resources += estimate_tokens(extra.read_text(encoding='utf-8', errors='replace'))
    return {'skills': len(skill_dirs), 'metadata_tokens': metadata,
            'body_tokens_if_all_loaded': body, 'resource_tokens_if_all_loaded': resources,
            'method': 'approximate: characters / 4; actual tokenization varies by model'}


def _scan_skill(directory, allow_scripts):
    files, skipped, risks = [], [], []
    for path in sorted(directory.rglob('*')):
        rel = path.relative_to(directory).as_posix()
        if path.is_symlink():
            skipped.append({'file': rel, 'reason': 'symlink'})
            continue
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if path.stat().st_size > MAX_IMPORT_FILE:
            skipped.append({'file': rel, 'reason': 'larger than 512 KiB'})
        elif suffix in SCRIPT_SUFFIXES and not allow_scripts:
            skipped.append({'file': rel, 'reason': 'script excluded (use --allow-scripts after review)'})
        elif suffix not in TEXT_SUFFIXES and suffix not in SCRIPT_SUFFIXES:
            skipped.append({'file': rel, 'reason': 'binary or unsupported file type'})
        else:
            files.append(path)
            text = path.read_text(encoding='utf-8', errors='replace').lower()
            risks += [{'file': rel, 'pattern': key} for key, pattern in RISK_PATTERNS.items()
                      if re.search(pattern, text)]
    return files, skipped, risks


def import_skills(source, project, *, agent='claude', allow_scripts=False, dry_run=False):
    """Copy validated local skills into a project's agent skill directories with provenance."""
    source = Path(source).expanduser().resolve()
    project = Path(project).expanduser().resolve()
    if agent not in (*AGENTS, 'all'):
        raise ValueError(f'Unknown agent: {agent}')
    if not source.is_dir():
        raise ValueError(f'Skill source directory not found: {source}')
    if not project.is_dir():
        raise ValueError(f'Project not found: {project}')
    canonical = registry()['skills']
    found = sorted(p.parent for p in source.rglob('SKILL.md')
                   if len(p.relative_to(source).parts) <= 5)[:MAX_IMPORT_SKILLS]
    plan = ManagedFilePlan(project, dry_run)
    provenance_path = project / '.ai-workbench' / 'imported-skills.json'
    provenance = {}
    if provenance_path.is_file():
        provenance = json.loads(provenance_path.read_text(encoding='utf-8')).get('skills', {})
    imported, rejected = [], []
    for directory in found:
        name = directory.name
        try:
            _validate_skill(directory / 'SKILL.md')
        except ValueError as error:
            rejected.append({'skill': name, 'reason': str(error)})
            continue
        if name in canonical:
            rejected.append({'skill': name, 'reason': 'name collides with a canonical Workbench skill'})
            continue
        files, skipped, risks = _scan_skill(directory, allow_scripts)
        digest = hashlib.sha256()
        for file in files:
            digest.update(file.relative_to(directory).as_posix().encode('utf-8') + b'\0' + file.read_bytes())
        for base in skill_paths(agent):
            for file in files:
                plan.write(project / base / name / file.relative_to(directory), file.read_bytes(), kind='copy')
        record = {'source': str(directory), 'sha256': digest.hexdigest(), 'files': len(files),
                  'skipped': skipped, 'risk_markers': risks, 'agent': agent,
                  'imported_at': provenance.get(name, {}).get('imported_at') if
                  provenance.get(name, {}).get('sha256') == digest.hexdigest() else now()}
        provenance[name] = record
        imported.append({'skill': name, **record})
    if imported:
        payload = {'schema_version': 1, 'skills': dict(sorted(provenance.items()))}
        plan.write(provenance_path, json.dumps(payload, indent=2, ensure_ascii=False) + '\n')
        gitignore = project / '.gitignore'
        current = gitignore.read_text(encoding='utf-8') if gitignore.exists() else ''
        if '.ai-workbench/' not in current.splitlines():
            plan.write(gitignore, current.rstrip() + '\n\n# AI Workbench private local context\n.ai-workbench/\n',
                       allow_unowned_merge=True)
    managed = plan.finish()
    return {'source': str(source), 'project': str(project), 'agent': agent, 'dry_run': dry_run,
            'imported': imported, 'rejected': rejected, 'managed_files': managed,
            'operations': [vars(op) for op in plan.operations],
            'note': 'Imported skills are untrusted text. Review risk_markers before use; '
                    'remove with `aiwh managed remove`.'}
