"""Explicit, user-approved validation execution with redacted, revision-bound evidence.

Bootstrap, audit and resume remain strictly non-executing. ``aiwh validate``
previews the execution plan by default and only runs a command when ``--approve``
is explicitly passed.
"""
from __future__ import annotations

import os
import re
import shlex
import subprocess
import time
from pathlib import Path

from .continuity import _continuity_state, _git, _write_private_state, inspect_project
from .core import now

MAX_OUTPUT_CHARS = 4000
MAX_VALIDATION_HISTORY = 10

_SECRET_PATTERNS = (
    (re.compile(r'(?i)(bearer\s+)[A-Za-z0-9._\-+/=]{8,}'), r'\1[REDACTED]'),
    (re.compile(r'\b(gh[pousr]_[A-Za-z0-9_]{12,}|github_pat_[A-Za-z0-9_]{16,})'), '[REDACTED]'),
    (re.compile(r'\b(sk-[A-Za-z0-9_\-]{12,}|AIza[0-9A-Za-z_\-]{20,}|AKIA[0-9A-Z]{16})'), '[REDACTED]'),
    (re.compile(r'(?i)(\b(?:api[_-]?key|token|secret|password|passwd|pwd)\s*[:=]\s*["\']?)([^\s"\';,]{4,})'),
     r'\1[REDACTED]'),
)


def redact_secrets(text, *, limit=MAX_OUTPUT_CHARS):
    """Redact common credential patterns and bound output length."""
    cleaned = str(text or '')
    for pattern, replacement in _SECRET_PATTERNS:
        cleaned = pattern.sub(replacement, cleaned)
    if len(cleaned) > limit:
        half = (limit - 40) // 2
        cleaned = cleaned[:half] + '\n... [output truncated] ...\n' + cleaned[-half:]
    return cleaned


def _split_command(command):
    if isinstance(command, (list, tuple)):
        parts = [str(x) for x in command if str(x)]
    else:
        parts = [part.strip('"\'') for part in shlex.split(str(command or ''), posix=(os.name != 'nt'))]
    if not parts:
        raise ValueError('Validation command must not be empty')
    return parts


def validation_plan(project, command=None, *, timeout=120):
    """Build a read-only execution plan without running any command."""
    if timeout < 1:
        raise ValueError('Timeout must be >= 1 second')
    root = Path(project).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f'Project not found: {root}')
    data = inspect_project(root)
    chosen = command or data.get('test_command')
    if not chosen:
        raise ValueError('No command specified and no documented test command found')
    return {
        'project': str(root),
        'command': chosen,
        'argv': _split_command(chosen),
        'cwd': str(root),
        'timeout': timeout,
        'head_commit': data.get('head_commit'),
        'working_tree_dirty': bool(data.get('working_tree_changes')),
        'approved': False,
        'status': 'not_run',
        'executed': False,
    }


def evaluate_evidence(project, evidence):
    """Evaluate whether recorded validation evidence is still current or stale."""
    if not isinstance(evidence, dict) or evidence.get('status') in (None, 'not_run'):
        return {'effective_status': 'not_run', 'stale': False, 'reason': 'No validation run recorded.'}
    root = Path(project).expanduser().resolve()
    current_head = _git(root, 'rev-parse', '--verify', 'HEAD') or None
    dirty = bool(_git(root, 'status', '--porcelain=v1', '-uno').splitlines())
    recorded_head = evidence.get('head_commit')
    reasons = []
    if recorded_head and current_head and recorded_head != current_head:
        reasons.append(f'HEAD moved from {recorded_head[:12]} to {current_head[:12]}')
    elif recorded_head and not current_head:
        reasons.append('Git revision is no longer readable')
    if dirty and not evidence.get('working_tree_dirty'):
        reasons.append('working tree has uncommitted changes since validation')
    elif dirty and evidence.get('working_tree_dirty'):
        reasons.append('working tree was dirty during or after validation')
    return {
        'effective_status': 'stale' if reasons else evidence['status'],
        'recorded_status': evidence['status'],
        'stale': bool(reasons),
        'reason': '; '.join(reasons) if reasons else 'Matches recorded revision.',
    }


def run_validation(project, command=None, *, timeout=120, approve=False):
    """Preview or (when ``approve=True``) execute a validation command and store private evidence."""
    plan = validation_plan(project, command=command, timeout=timeout)
    if not approve:
        return plan
    root = Path(plan['project'])
    started = time.monotonic()
    exit_code = None
    try:
        proc = subprocess.run(
            plan['argv'], cwd=root, shell=False, capture_output=True,
            text=True, encoding='utf-8', errors='replace', timeout=timeout, check=False,
        )
        exit_code = proc.returncode
        status = 'passed' if exit_code == 0 else 'failed'
        raw_output = (proc.stdout or '') + (('\n' + proc.stderr) if proc.stderr else '')
    except subprocess.TimeoutExpired as exc:
        status = 'timed_out'
        raw_output = ((exc.stdout or '') if isinstance(exc.stdout, str) else '') + \
                     (('\n' + exc.stderr) if isinstance(exc.stderr, str) and exc.stderr else '')
        if not raw_output.strip():
            raw_output = f'Command timed out after {timeout}s'
    except KeyboardInterrupt:
        status = 'cancelled'
        raw_output = 'Validation cancelled by user.'
    except OSError as exc:
        status = 'failed'
        raw_output = f'Failed to launch command: {exc}'

    duration = round(time.monotonic() - started, 3)
    evidence = {
        'command': plan['command'],
        'cwd': plan['cwd'],
        'timeout': timeout,
        'status': status,
        'exit_code': exit_code,
        'timestamp': now(),
        'duration_seconds': duration,
        'head_commit': plan['head_commit'],
        'working_tree_dirty': plan['working_tree_dirty'],
        'output': redact_secrets(raw_output),
    }

    folder = root / '.ai-workbench'
    folder.mkdir(exist_ok=True)
    state_path = folder / 'state.json'
    state = _continuity_state(inspect_project(root), state_path)
    history = list(state.get('validation_history', []))
    history.append(evidence)
    state['validation'] = evidence
    state['validation_history'] = history[-MAX_VALIDATION_HISTORY:]
    _write_private_state(state_path, state)
    return {**evidence, 'approved': True, 'executed': True}
