"""Non-executing workspace security gate for AI Workbench artifacts and agent configs."""
from __future__ import annotations

import re
from pathlib import Path

from .skilltools import RISK_PATTERNS
from .validate import _SECRET_PATTERNS

MAX_AUDIT_FILES = 200
MAX_AUDIT_BYTES = 512 * 1024


def security_audit(project):
    """Scan Workbench, MCP and agent-skill files for secrets, symlinks and risky patterns."""
    root = Path(project).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f'Project not found: {root}')

    findings = []
    checked = 0

    def add(rule, path, detail):
        findings.append({'rule': rule, 'path': str(path), 'detail': detail})

    targets = [root / 'AGENTS.md', root / 'CLAUDE.md', root / '.mcp.json']
    for folder in ('.ai-workbench', '.agents/skills', '.claude/skills', '.openclaude/skills'):
        base = root / folder
        if base.is_symlink():
            add('symlink-risk', folder, 'Agent/Workbench directory is a symlink.')
            continue
        if base.is_dir():
            for item in sorted(base.rglob('*')):
                if checked >= MAX_AUDIT_FILES:
                    break
                if item.is_symlink():
                    add('symlink-risk', item.relative_to(root).as_posix(), 'Symlinked file inside agent directory.')
                    continue
                if item.is_file():
                    targets.append(item)

    for path in targets:
        if checked >= MAX_AUDIT_FILES:
            break
        if path.is_symlink():
            add('symlink-risk', path.relative_to(root).as_posix(), 'Config file is a symlink.')
            continue
        if not path.is_file() or path.stat().st_size > MAX_AUDIT_BYTES:
            continue
        checked += 1
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding='utf-8', errors='replace')
        for pattern, _ in _SECRET_PATTERNS:
            if pattern.search(text):
                add('secret-exposure', rel, 'Potential credential or token literal detected.')
                break
        if not rel.startswith('.ai-workbench/'):
            for rule, raw_pat in RISK_PATTERNS.items():
                if re.search(raw_pat, text, re.IGNORECASE):
                    add(f'risky-pattern:{rule}', rel, f'Matched {rule} pattern.')

    wb_dir = root / '.ai-workbench'
    gitignore = root / '.gitignore'
    if wb_dir.is_dir():
        ignored = gitignore.is_file() and '.ai-workbench/' in gitignore.read_text(
            encoding='utf-8', errors='replace').splitlines()
        if not ignored:
            add('unignored-private-state', '.gitignore', '.ai-workbench/ exists without a .gitignore entry.')

    return {'project': str(root), 'ok': not findings, 'files_checked': checked, 'findings': findings}
