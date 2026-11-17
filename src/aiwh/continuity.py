"""Project continuity inspection, versioned private state, session deltas and handoff markdown."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from .core import now
from .handoff_checks import CONFIDENCE_LEVELS, handoff_gaps, open_tasks, parse_day

PENDING_SCAN_LIMIT = 60


def _git(project: Path, *args):
    try:
        p = subprocess.run(['git', '-C', str(project), *args], capture_output=True,
                           text=True, encoding='utf-8', timeout=12, check=False)
        return p.stdout.rstrip('\r\n') if p.returncode == 0 else ''
    except (OSError, subprocess.TimeoutExpired):
        return ''


EVIDENCE_FILES = ('NOTES.md', 'analysis/evidence.md', 'lab/NOTES.md', 'lab/analysis/evidence.md',
                  'handoff/SPEC.md', 'lab/handoff/SPEC.md', 'report.md', 'lab/report.md', 'TEARDOWN.md')
TEST_COMMAND = re.compile(r'`((?:python|py|pytest|npm|pnpm|yarn|dotnet|cargo|go|gradle|\./gradlew|mvn|make|bun|deno)'
                          r'\b[^`\n]{0,110}\btest[^`\n]{0,60})`')


def _evidence_status(project):
    """Count observation/inference/unknown tags, open questions and verifier results in known files."""
    files = []
    for name in EVIDENCE_FILES:
        path = project / name
        if not path.is_file() or path.stat().st_size > 2_000_000:
            continue
        text = path.read_text(encoding='utf-8', errors='replace')
        counts = {tag: len(re.findall(rf'^\s*(?:[-*]\s*)?{tag}\b', text, re.IGNORECASE | re.MULTILINE))
                  for tag in ('observation', 'inference', 'unknown')}
        for tag, label in (('observation', 'Observed'), ('inference', 'Inferred'), ('unknown', 'Unknown')):
            counts[tag] += len(re.findall(rf'^\s*[-*]\s*{label}:\s*\S', text, re.MULTILINE))
        questions = 0
        section = re.search(r'^#+\s*(?:\d+\.\s*)?Open questions\s*$(.*?)(?=^#|\Z)', text,
                            re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if section:
            questions = len(re.findall(r'^\s*(?:[-*]|\d+\.|\|)\s*\S', section.group(1), re.MULTILINE))
        result = re.findall(r'^RESULT wrong=(\d+) crash=(\d+)\s*$', text, re.MULTILINE)
        entry = {'path': name, **counts, 'open_questions': questions}
        if result:
            entry['verifier'] = {'wrong': int(result[-1][0]), 'crash': int(result[-1][1])}
        if any(entry[k] for k in ('observation', 'inference', 'unknown', 'open_questions')) or result:
            files.append(entry)
    return files


def _test_command(project):
    for name in ('AGENTS.md', 'CLAUDE.md', 'README.md', 'CONTRIBUTING.md'):
        path = project / name
        if path.is_file() and path.stat().st_size <= 1_000_000:
            match = TEST_COMMAND.search(path.read_text(encoding='utf-8', errors='replace'))
            if match:
                return match.group(1).strip()
    return None


def suggested_goal(data):
    """A Claude Code /goal line for the next documented task: measurable, checked and turn-limited."""
    tasks = data.get('pending_documented') or []
    if not tasks:
        return None
    title = re.sub(r'^\s*[-*]\s*\[\s\]\s*', '', tasks[0]['text']).strip()
    title = title[:160] + ('...' if len(title) > 160 else '')
    check = f'`{data["test_command"]}` passes with no failures' if data.get('test_command') \
        else 'the project test suite passes with no failures'
    return f'/goal {title} is done, {check}, and no unrelated files changed. or stop after 25 turns.'


PENDING_DOCUMENTS = ('NEXT_SESSION.md', 'docs/NEXT_SESSION.md', 'TODO.md', 'docs/TODO.md',
                     'docs/ROADMAP.md', 'docs/PROGRESS.md')
_PENDING_HEADING = re.compile(r'^#{1,6}\s+(next\b|pending\b|todo\b|to do\b|open items\b|remaining\b)',
                              re.IGNORECASE)
_LIST_ITEM = re.compile(r'^(?:[-*]|\d+[.)])\s+(.*\S)')


def _pending_lines(text):
    """Unchecked boxes and TODO markers anywhere, plus top-level list items under a
    heading that starts with Next/Pending/TODO/Open items/Remaining."""
    in_section = in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith(('```', '~~~')):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if re.match(r'^#{1,6}\s', line):
            in_section = bool(_PENDING_HEADING.match(line))
            continue
        if re.search(r'^\s*[-*]\s*\[\s\]|\bTODO\b', line, flags=re.IGNORECASE):
            yield line.strip()
        elif in_section:
            item = _LIST_ITEM.match(line)
            if item and not re.match(r'\[[xX]\]', item.group(1)):
                yield line.strip()


def inspect_project(project):
    from .workbench import choose_profiles
    project = Path(project).expanduser().resolve()
    if not project.is_dir():
        raise ValueError(f'Project not found: {project}')
    branch = _git(project, 'branch', '--show-current') or '(unknown or detached)'
    changes = _git(project, 'status', '--porcelain=v1', '-uno').splitlines()[:30]
    commits = _git(project, 'log', '-5', '--pretty=format:%h %s').splitlines()
    tracked = _git(project, 'ls-files').splitlines()
    common_tests = ('pytest.ini', 'pyproject.toml', 'package.json', 'Cargo.toml',
                    'build.gradle', 'build.gradle.kts', 'gradlew', 'Makefile')
    test_evidence = sorted({name for name in common_tests if (project / name).exists()})
    test_evidence += [name for name in ('tests', 'test', '__tests__') if (project / name).is_dir()]
    instructions = [name for name in ('AGENTS.md','CLAUDE.md','GEMINI.md','README.md','AI-WORKBENCH.md') if (project / name).is_file()]
    todo = []
    for path in (project / relative for relative in PENDING_DOCUMENTS):
        if len(todo) >= PENDING_SCAN_LIMIT:
            break
        if path.is_file() and path.stat().st_size <= 1_000_000:
            for text in _pending_lines(path.read_text(encoding='utf-8', errors='replace')):
                todo.append({'path': str(path.relative_to(project)), 'text': text[:220]})
                if len(todo) >= PENDING_SCAN_LIMIT:
                    break
    return {'project': str(project), 'generated_at': now(), 'profiles': choose_profiles(project),
            'branch': branch, 'head_commit': _git(project, 'rev-parse', '--verify', 'HEAD') or None,
            'working_tree_changes': changes, 'recent_commits': commits,
            'tracked_files': len(tracked), 'test_indicators': test_evidence,
            'instructions': instructions, 'pending_documented': todo[:PENDING_SCAN_LIMIT],
            'pending_scan_limit': PENDING_SCAN_LIMIT,
            'pending_truncated': len(todo) >= PENDING_SCAN_LIMIT,
            'test_command': _test_command(project), 'evidence_status': _evidence_status(project)}


def documented_task_ids(data):
    return {task['id'] for task in _documented_tasks(data)}


def state_gaps(data, state):
    """What the handoff does not know; see ``handoff_checks.handoff_gaps``."""
    return handoff_gaps(data, state, documented_task_ids(data), PENDING_DOCUMENTS)


def _record_sections(data, state):
    """Handoff sections derived from private state records (claims, decisions, rejections, gaps)."""
    lines = []
    claimed = [task for task in open_tasks(state) if task.get('claimed_by')]
    if claimed:
        lines += ['', '## Claimed tasks (do not start these)', '']
        lines += [f'- {task["id"]}: claimed by {task["claimed_by"]}'
                  + (f' at {task["claimed_at"]}' if task.get('claimed_at') else '') for task in claimed]
    if state.get('decisions'):
        lines += ['', '## Approved decisions', '']
        for decision in state['decisions']:
            if decision.get('retracted'):
                lines.append(f'- RETRACTED {decision["id"]}: {decision["text"]} '
                             f'(reason: {decision["retraction_reason"]})')
                continue
            notes = [f'source: {decision["source"]}' if decision.get('source') else 'source: not recorded',
                     f'last verified: {decision.get("last_verified") or "never"}']
            if decision.get('confidence'):
                notes.append(f'confidence: {decision["confidence"]}')
            lines.append(f'- {decision["id"]}: {decision["text"]} ({"; ".join(notes)})')
    if state.get('rejections'):
        lines += ['', '## Rejected findings (do not re-raise)', '']
        lines += [f'- {item["id"]}: {item["text"]} (why: {item["rationale"]})' for item in state['rejections']]
    if state.get('hypotheses'):
        lines += ['', '## Hypotheses', '']
        for h in state['hypotheses']:
            ev = f' — evidence: {h["evidence"]}' if h.get('evidence') else ''
            lines.append(f'- [{h["status"]}] {h["id"]}: {h["text"]}{ev}')
    lines += ['', '## Known gaps', '']
    lines += [f'- {gap}' for gap in state_gaps(data, state)] or ['- No gaps detected by the local scan.']
    return lines


def compact_markdown(text, max_tokens):
    """Deterministically compact Markdown to fit an approximate ``max_tokens`` budget (chars / 4)."""
    if max_tokens is None:
        return text
    if max_tokens < 1:
        raise ValueError('max_tokens must be >= 1')
    char_limit = max_tokens * 4
    if len(text) <= char_limit:
        return text

    sections = []
    current_title = ''
    current_lines = []
    for line in text.splitlines():
        if line.startswith('## '):
            sections.append((current_title, current_lines))
            current_title = line
            current_lines = []
        else:
            current_lines.append(line)
    sections.append((current_title, current_lines))

    low_priority = {
        '## Cautions', '## Next-session procedure', '## Model routing (recommendation)',
        '## Recent commits', '## Tasks passed over', '## Selected resources',
    }

    def _render(secs):
        out = []
        for title, body in secs:
            if title:
                out.append(title)
            out.extend(body)
        return '\n'.join(out).rstrip() + '\n'

    compacted = []
    for title, body in sections:
        if title in low_priority and len(_render(sections)) > char_limit:
            kept = [ln for ln in body if ln.strip()][:2]
            if len([ln for ln in body if ln.strip()]) > 2:
                kept.append('- ... [compacted for token budget]')
            compacted.append((title, ['', *kept] if kept else []))
        else:
            compacted.append((title, body))

    rendered = _render(compacted)
    if len(rendered) <= char_limit:
        return rendered

    note = f'\n... [compacted to ~{max_tokens} tokens]\n'
    cutoff = max(0, char_limit - len(note))
    clipped = rendered[:cutoff].rsplit('\n', 1)[0].rstrip()
    return clipped + '\n' + note


def continuation_markdown(data, agent='codex', delta=None, state=None, *, max_tokens=None):
    lines = ['# AI Workbench — Project Continuity', '',
             f'Generated: {data["generated_at"]}',
             f'Agent: {agent}',
             f'Profiles: {", ".join(data["profiles"])}',
             f'Git branch: `{data["branch"]}`',
             f'Source revision: `{data.get("head_commit") or "unknown"}`',
             f'Git tracked files: {data["tracked_files"]}', '',
             '## Local evidence', '',
             'These are observations from the local repository, not verified test results.',
             f'- Working-tree entries: {len(data["working_tree_changes"])}',
             f'- Test/build indicators: {", ".join(data["test_indicators"]) or "not detected"}',
             f'- Instruction files: {", ".join(data["instructions"]) or "none"}', '',
             '## Recent commits', '']
    lines += [f'- {x}' for x in data['recent_commits']] or ['- No readable Git history.']
    lines += ['', '## Pending work explicitly documented', '']
    lines += [f'- [{x["path"]}] {x["text"]}' for x in data['pending_documented']] or ['- No TODO items located in standard documents.']
    if data.get('pending_truncated'):
        lines.append(f'- Scan stopped at {data.get("pending_scan_limit")} items; read the full documents for remaining work.')
    goal = suggested_goal(data)
    if goal:
        lines += ['', '## Suggested goal for the next task', '', '```', goal, '```']
    if data.get('evidence_status'):
        lines += ['', '## Evidence status (Observed / Inferred / Unknown)', '']
        for entry in data['evidence_status']:
            line = (f'- {entry["path"]}: {entry["observation"]} observed, {entry["inference"]} inferred, '
                    f'{entry["unknown"]} unknown, {entry["open_questions"]} open questions')
            if 'verifier' in entry:
                line += f'; verifier wrong={entry["verifier"]["wrong"]} crash={entry["verifier"]["crash"]}'
            lines.append(line)
    if delta:
        lines += ['', '## Since previous handoff', '']
        if delta['baseline']:
            lines.append('- Baseline snapshot; no earlier session is available for comparison.')
        else:
            observed = delta['observed']
            for label, field in (('Git-status files added', 'files_added'),
                                 ('Git-status files resolved', 'files_resolved'),
                                 ('Git-status changes updated', 'files_status_changed')):
                lines.extend(f'- {label}: {path}' for path in observed[field])
            for label, field in (('Newly documented pending items', 'pending_added'),
                                 ('No-longer-pending documented items', 'pending_resolved')):
                lines.extend(f'- {label}: [{item["path"]}] {item["text"]}' for item in observed[field])
            if observed['branch_change']:
                lines.append(f'- Branch changed: `{observed["branch_change"]["from"]}` to `{observed["branch_change"]["to"]}`')
            if observed.get('head_change'):
                lines.append(f'- Source revision moved: `{observed["head_change"]["from"][:12]}` to '
                             f'`{observed["head_change"]["to"][:12]}`; earlier plans and evidence may be stale.')
            tasks = delta['tasks']
            for label, field in (('New blockers', 'blockers_added'), ('Resolved blockers', 'blockers_resolved')):
                lines.extend(f'- {label} for {item["task_id"]}: {item["blocker"]}' for item in tasks[field])
            lines.extend(f'- Task {item["task_id"]} status: {item["from"]} -> {item["to"]}'
                         for item in tasks['status_changed'])
            for category in ('decisions', 'resources'):
                changes = delta[category]
                for field in ('added', 'removed', 'changed'):
                    if changes[field]:
                        lines.append(f'- Explicit {category} {field}: {", ".join(changes[field])}')
            if delta['resources']['usefulness_changed']:
                lines.append('- Explicit resource usefulness feedback: '
                             + ', '.join(delta['resources']['usefulness_changed']))
            has_changes = (
                any(observed[field] for field in ('files_added', 'files_resolved', 'files_status_changed',
                                                   'pending_added', 'pending_resolved'))
                or observed['branch_change'] is not None
                or observed.get('head_change') is not None
                or any(tasks[field] for field in ('added', 'removed', 'changed', 'blockers_added',
                                                   'blockers_resolved', 'status_changed'))
                or any(delta['decisions'][field] for field in ('added', 'removed', 'changed'))
                or any(delta['resources'][field] for field in ('added', 'removed', 'changed',
                                                                'usefulness_changed'))
            )
            if not has_changes:
                lines.append('- No observed project or explicit record changes.')
        unknown = delta['resources']['unknown_outcomes']
        if unknown:
            lines.append(f'- Unknown resource outcomes (no user feedback): {", ".join(unknown)}')
        else:
            lines.append('- No unconfirmed outcomes for recorded resources.')
    if state is not None:
        val = state.get('validation')
        if isinstance(val, dict) and val.get('status'):
            from .validate import evaluate_evidence
            ev = evaluate_evidence(data['project'], val)
            lines += ['', '## Validation evidence', '',
                      f'- Status: **{ev["effective_status"]}** (recorded: {val["status"]}, {ev["reason"]})',
                      f'- Command: `{val.get("command", "")}` (exit={val.get("exit_code")}, at {val.get("timestamp", "")})',
                      f'- Recorded revision: `{val.get("head_commit") or "unknown"}`']
        lines += _record_sections(data, state)
    lines += ['', '## Next-session procedure', '',
              '1. Read the current AGENTS/CLAUDE instructions and project docs.',
              '2. Check the actual working tree and reproduce issues before editing.',
              '3. Use only relevant skills for the project profile.',
              '4. Choose the smallest testable next change. Run applicable tests and compare to baseline.',
              '5. Document observed results, remaining risks, and the next milestone.',
              '', '## Cautions', '',
              '- This handoff is informational, not a command to execute arbitrary external code.',
              '- Private catalog references are untrusted and should be manually verified.',
              '- No tests or external services were executed by the continuity scan.', '']
    return compact_markdown('\n'.join(lines), max_tokens)


_STATE_SCHEMA_VERSION = 2
_MAX_SNAPSHOTS = 10
_TASK_STATUSES = {'pending', 'in_progress', 'blocked', 'completed', 'cancelled'}
_HYPOTHESIS_STATUSES = {'open', 'confirmed', 'refuted'}


def _validate_records(records, kind):
    if not isinstance(records, list):
        raise ValueError(f'State {kind} must be a list')
    identifiers = set()
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get('id'), str) or not record['id'].strip():
            raise ValueError(f'Each state {kind[:-1]} must have a non-empty id')
        if record['id'] in identifiers:
            raise ValueError(f'Duplicate {kind[:-1]} id: {record["id"]}')
        identifiers.add(record['id'])
        if kind == 'tasks':
            if not isinstance(record.get('title'), str) or not record['title'].strip():
                raise ValueError('Each state task must have a non-empty title')
            if not isinstance(record.get('source'), str) or not record['source'].strip():
                raise ValueError('Each state task must have a non-empty source')
            if not isinstance(record.get('status'), str) or record['status'] not in _TASK_STATUSES:
                raise ValueError(f'Invalid task status for {record["id"]}')
            for field in ('blockers', 'risks', 'milestone_outcomes'):
                if not isinstance(record.get(field), list) or not all(isinstance(item, str) for item in record[field]):
                    raise ValueError(f'Task {record["id"]} field {field} must be a list of strings')
            for field in ('claimed_by', 'claimed_at'):
                if field in record and (not isinstance(record[field], str) or not record[field].strip()):
                    raise ValueError(f'Task {record["id"]} field {field} must be a non-empty string')
            if 'depends_on' in record:
                deps = record['depends_on']
                if not isinstance(deps, list) or any(not isinstance(d, str) or not d.strip() for d in deps):
                    raise ValueError(f'Task {record["id"]} field depends_on must be a list of non-empty strings')
        elif kind == 'decisions':
            if record.get('approved') is not True:
                raise ValueError(f'State decision {record["id"]} must be explicitly approved')
            for field in ('text', 'rationale'):
                if not isinstance(record.get(field), str) or not record[field].strip():
                    raise ValueError(f'State decision {record["id"]} requires {field}')
            if 'source' in record and (not isinstance(record['source'], str) or not record['source'].strip()):
                raise ValueError(f'State decision {record["id"]} source must be a non-empty string')
            if 'last_verified' in record and parse_day(record['last_verified']) is None:
                raise ValueError(f'State decision {record["id"]} last_verified must be YYYY-MM-DD')
            if 'confidence' in record and record['confidence'] not in CONFIDENCE_LEVELS:
                raise ValueError(f'State decision {record["id"]} confidence must be one of {CONFIDENCE_LEVELS}')
            if 'retracted' in record and type(record['retracted']) is not bool:
                raise ValueError(f'State decision {record["id"]} retracted must be true or false')
            if record.get('retracted') and (not isinstance(record.get('retraction_reason'), str)
                                            or not record['retraction_reason'].strip()):
                raise ValueError(f'Retracted decision {record["id"]} requires a retraction_reason')
        elif kind == 'rejections':
            for field in ('text', 'rationale'):
                if not isinstance(record.get(field), str) or not record[field].strip():
                    raise ValueError(f'State rejection {record["id"]} requires {field}')
        elif kind == 'hypotheses':
            if not isinstance(record.get('text'), str) or not record['text'].strip():
                raise ValueError(f'State hypothesis {record["id"]} requires text')
            if record.get('status') not in _HYPOTHESIS_STATUSES:
                raise ValueError(f'State hypothesis {record["id"]} status must be one of {sorted(_HYPOTHESIS_STATUSES)}')
            if 'evidence' in record and (not isinstance(record['evidence'], str) or not record['evidence'].strip()):
                raise ValueError(f'State hypothesis {record["id"]} evidence must be a non-empty string')
        else:
            if not isinstance(record.get('selection'), str) or record['selection'] not in ('selected', 'rejected'):
                raise ValueError(f'Invalid resource selection for {record["id"]}')
            if not isinstance(record.get('rationale'), str) or not record['rationale'].strip():
                raise ValueError(f'State resource {record["id"]} requires a rationale')
            if 'usefulness' in record and (not isinstance(record['usefulness'], str)
                                           or record['usefulness'] not in ('useful', 'not_useful')):
                raise ValueError(f'Invalid user-confirmed usefulness for {record["id"]}')


def _documented_tasks(data):
    return [task for task, _ in _documented_pairs(data)]


def _documented_pairs(data):
    """(task, pending item) per documented task; a repeated ID keeps its first mention."""
    tasks, seen = [], set()
    for item in data['pending_documented']:
        path, text = item['path'], item['text']
        title = re.sub(r'^\s*[-*]\s*\[\s\]\s*', '', text).strip()
        match = re.search(r'\b[A-Z][A-Z0-9]+-\d{3,}\b', title)
        task_id = match.group(0) if match else 'task-' + hashlib.sha256(
            f'{path}\0{title}'.encode('utf-8')).hexdigest()[:16]
        if match:
            title = title[match.end():].strip(' :-') or title
        if task_id in seen:
            continue
        seen.add(task_id)
        tasks.append(({
            'id': task_id, 'title': title, 'source': path, 'status': 'pending',
            'blockers': [], 'risks': [], 'milestone_outcomes': [],
        }, item))
    return tasks


def _record_delta(previous, current):
    old = {record['id']: record for record in previous}
    new = {record['id']: record for record in current}
    return {
        'added': sorted(new.keys() - old.keys()),
        'removed': sorted(old.keys() - new.keys()),
        'changed': sorted(identifier for identifier in old.keys() & new.keys()
                          if old[identifier] != new[identifier]),
    }


def _working_tree_paths(observed):
    return {entry[3:]: entry[:2] for entry in observed.get('working_tree_changes', [])
            if isinstance(entry, str) and len(entry) >= 4}


def _pending_delta(previous, current):
    old = {json.dumps(item, sort_keys=True, ensure_ascii=False): item for item in previous}
    new = {json.dumps(item, sort_keys=True, ensure_ascii=False): item for item in current}
    return ([new[key] for key in sorted(new.keys() - old.keys())],
            [old[key] for key in sorted(old.keys() - new.keys())])


def _task_delta(previous, current):
    old = {task['id']: task for task in previous}
    new = {task['id']: task for task in current}
    added_blockers, resolved_blockers, status_changed = [], [], []
    for identifier in sorted(old.keys() & new.keys()):
        if old[identifier]['status'] != new[identifier]['status']:
            status_changed.append({
                'task_id': identifier, 'from': old[identifier]['status'],
                'to': new[identifier]['status'],
            })
        old_blockers = set(old[identifier]['blockers'])
        new_blockers = set(new[identifier]['blockers'])
        added_blockers.extend({'task_id': identifier, 'blocker': blocker}
                              for blocker in sorted(new_blockers - old_blockers))
        resolved_blockers.extend({'task_id': identifier, 'blocker': blocker}
                                  for blocker in sorted(old_blockers - new_blockers))
    return {
        **_record_delta(previous, current),
        'blockers_added': added_blockers,
        'blockers_resolved': resolved_blockers,
        'status_changed': status_changed,
    }


def _compare_snapshots(previous, current):
    if previous is None:
        observed_delta = {
            'files_added': [], 'files_resolved': [], 'files_status_changed': [],
            'pending_added': [], 'pending_resolved': [], 'branch_change': None, 'head_change': None,
        }
        task_delta = {**_record_delta([], []), 'blockers_added': [], 'blockers_resolved': [],
                  'status_changed': []}
        decisions_delta = _record_delta([], [])
        resources_delta = _record_delta([], [])
    else:
        old_observed = previous['observed']
        new_observed = current['observed']
        old_files = _working_tree_paths(old_observed)
        new_files = _working_tree_paths(new_observed)
        pending_added, pending_resolved = _pending_delta(
            old_observed.get('pending_documented', []),
            new_observed.get('pending_documented', []))
        branch_change = None
        if old_observed.get('branch') != new_observed.get('branch'):
            branch_change = {'from': old_observed.get('branch'), 'to': new_observed.get('branch')}
        head_change = None
        old_head, new_head = old_observed.get('head_commit'), new_observed.get('head_commit')
        if old_head and new_head and old_head != new_head:
            head_change = {'from': old_head, 'to': new_head}
        observed_delta = {
            'head_change': head_change,
            'files_added': sorted(new_files.keys() - old_files.keys()),
            'files_resolved': sorted(old_files.keys() - new_files.keys()),
            'files_status_changed': sorted(path for path in old_files.keys() & new_files.keys()
                                           if old_files[path] != new_files[path]),
            'pending_added': pending_added,
            'pending_resolved': pending_resolved,
            'branch_change': branch_change,
        }
        task_delta = _task_delta(previous['tasks'], current['tasks'])
        decisions_delta = _record_delta(previous['decisions'], current['decisions'])
        resources_delta = _record_delta(previous['resources'], current['resources'])
        old_resources = {resource['id']: resource for resource in previous['resources']}
        new_resources = {resource['id']: resource for resource in current['resources']}
        resources_delta['usefulness_changed'] = sorted(
            identifier for identifier in old_resources.keys() & new_resources.keys()
            if old_resources[identifier].get('usefulness') != new_resources[identifier].get('usefulness')
            and ('usefulness' in old_resources[identifier] or 'usefulness' in new_resources[identifier]))
    if previous is None:
        resources_delta['usefulness_changed'] = []
    resources_delta['unknown_outcomes'] = sorted(
        resource['id'] for resource in current['resources'] if 'usefulness' not in resource)
    return {
        'baseline': previous is None,
        'from': previous['generated_at'] if previous else None,
        'to': current['generated_at'],
        'observed': observed_delta,
        'tasks': task_delta,
        'decisions': decisions_delta,
        'resources': resources_delta,
    }


def _continuity_state(data, state_path):
    previous = None
    if state_path.is_symlink():
        raise ValueError(f'Refusing symlinked state file: {state_path}')
    if state_path.exists():
        try:
            previous = json.loads(state_path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f'Cannot read private state file: {state_path}') from exc
        if not isinstance(previous, dict):
            raise ValueError(f'Private state must be a JSON object: {state_path}')

    legacy_observation = None
    extras = {}
    history = []
    rejections = []
    hypotheses = []
    if previous is None:
        tasks, decisions, resources = [], [], []
    else:
        rejections = previous.get('rejections', [])
        hypotheses = previous.get('hypotheses', [])
        version = previous.get('schema_version')
        if 'schema_version' not in previous:
            legacy_observation = {key: value for key, value in previous.items()
                                  if key not in ('tasks', 'decisions', 'resources', 'rejections')}
            tasks = previous.get('tasks', [])
            decisions = previous.get('decisions', [])
            resources = previous.get('resources', [])
        else:
            if type(version) is not int or version not in (1, _STATE_SCHEMA_VERSION):
                raise ValueError(f'Unsupported state schema version: {version}')
            if not isinstance(previous.get('updated_at'), str) or not isinstance(previous.get('observed'), dict):
                raise ValueError('State requires a string updated_at and an observed object')
            legacy_observation = previous.get('legacy_observation')
            if legacy_observation is not None and not isinstance(legacy_observation, dict):
                raise ValueError('State legacy_observation must be an object')
            tasks = previous.get('tasks')
            decisions = previous.get('decisions')
            resources = previous.get('resources')
            if version == _STATE_SCHEMA_VERSION:
                history = previous.get('history')
                if not isinstance(history, list):
                    raise ValueError('State history must be a list')
                for snapshot in history:
                    if (not isinstance(snapshot, dict)
                            or not isinstance(snapshot.get('generated_at'), str)
                            or not isinstance(snapshot.get('observed'), dict)):
                        raise ValueError('Invalid continuity snapshot')
                    for kind in ('tasks', 'decisions', 'resources'):
                        _validate_records(snapshot.get(kind), kind)
                latest_delta = previous.get('latest_delta')
                if not isinstance(latest_delta, dict):
                    raise ValueError('State latest_delta must be an object')
            extras = {key: value for key, value in previous.items() if key not in {
                'schema_version', 'updated_at', 'observed', 'legacy_observation',
                'tasks', 'decisions', 'resources', 'rejections', 'hypotheses', 'history', 'latest_delta'}}

    _validate_records(tasks, 'tasks')
    _validate_records(decisions, 'decisions')
    _validate_records(resources, 'resources')
    _validate_records(rejections, 'rejections')
    _validate_records(hypotheses, 'hypotheses')
    task_ids = {task['id'] for task in tasks}
    tasks = list(tasks) + [task for task in _documented_tasks(data) if task['id'] not in task_ids]
    snapshot = {
        'generated_at': data['generated_at'], 'observed': data,
        'tasks': tasks, 'decisions': decisions, 'resources': resources,
    }
    latest_delta = _compare_snapshots(history[-1] if history else None, snapshot)
    history = (history + [snapshot])[-_MAX_SNAPSHOTS:]
    state = {
        **extras,
        'schema_version': _STATE_SCHEMA_VERSION,
        'updated_at': data['generated_at'],
        'observed': data,
        'tasks': tasks,
        'decisions': decisions,
        'resources': resources,
        'rejections': rejections,
        'hypotheses': hypotheses,
        'history': history,
        'latest_delta': latest_delta,
    }
    if legacy_observation is not None:
        state['legacy_observation'] = legacy_observation
    return state


def _write_private_state(path, state):
    descriptor, temporary = tempfile.mkstemp(prefix='.state-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(json.dumps(state, indent=2, ensure_ascii=False) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def resume(project, *, agent='codex', dry_run=False, max_tokens=None):
    from .workbench import AGENTS
    if agent not in (*AGENTS, 'all'):
        raise ValueError(f'Unknown agent: {agent}')
    data = inspect_project(project)
    folder = Path(project).expanduser().resolve() / '.ai-workbench'
    state_path = folder / 'state.json'
    state = _continuity_state(data, state_path)
    content = continuation_markdown(data, agent=agent, delta=state['latest_delta'], state=state,
                                    max_tokens=max_tokens)
    if not dry_run:
        folder.mkdir(exist_ok=True)
        (folder / 'CONTEXT.md').write_text(content, encoding='utf-8')
        _write_private_state(state_path, state)
    return {'data': data, 'markdown': content, 'written': not dry_run}
