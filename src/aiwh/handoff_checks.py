"""Pure checks over continuity observations and private state records.

Nothing here reads the project, the network or Git: every function receives the
observation (``inspect_project`` output) and the state mapping and returns plain
data. That keeps the checks testable and lets ``workbench`` import this module
without a cycle.
"""
from __future__ import annotations

from datetime import date, datetime

STALE_DECISION_DAYS = 180
OPEN_STATUSES = ('pending', 'in_progress', 'blocked')
CONFIDENCE_LEVELS = ('high', 'medium', 'low')


def parse_day(value):
    """Return a date for a strict ``YYYY-MM-DD`` string, otherwise None."""
    if not isinstance(value, str) or len(value) != 10:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


def _today(data, today=None):
    if today is not None:
        return today
    return parse_day(str(data.get('generated_at', ''))[:10]) or date.today()


def _posix(path):
    return str(path).replace('\\', '/')


def open_tasks(state):
    return [task for task in state.get('tasks', []) if task.get('status') in OPEN_STATUSES]


def active_decisions(state):
    return [decision for decision in state.get('decisions', []) if not decision.get('retracted')]


def orphaned_tasks(data, state, documented_ids, scanned_documents):
    """Open tasks that came from a scanned document but are no longer listed there.

    Returns None when the pending scan was truncated: a task beyond the scan limit
    would look orphaned, so the rule is not evaluated.
    """
    if data.get('pending_truncated'):
        return None
    scanned = {_posix(path) for path in scanned_documents}
    return [task for task in open_tasks(state)
            if _posix(task.get('source', '')) in scanned and task['id'] not in documented_ids]


def decision_age(decision, today):
    """Days since ``last_verified``; None when the decision was never verified."""
    day = parse_day(decision.get('last_verified'))
    return (today - day).days if day else None


def handoff_gaps(data, state, documented_ids, scanned_documents, today=None):
    """What this handoff does not know, as short sentences for the next agent."""
    today = _today(data, today)
    gaps = []
    if not data.get('head_commit'):
        gaps.append('No Git revision is readable; drift since this handoff cannot be checked.')
    changes = len(data.get('working_tree_changes', []))
    if changes:
        gaps.append(f'{changes} uncommitted tracked changes: the recorded revision does not describe the working tree.')
    if not data.get('test_command'):
        gaps.append('No documented test command was found; how to verify a change is unknown.')
    if data.get('pending_truncated'):
        gaps.append(f'Pending-work scan stopped at {data.get("pending_scan_limit")} items; later items are unseen.')
    unknown = sum(entry.get('unknown', 0) for entry in data.get('evidence_status', []))
    questions = sum(entry.get('open_questions', 0) for entry in data.get('evidence_status', []))
    if unknown or questions:
        gaps.append(f'Evidence files record {unknown} unknowns and {questions} open questions.')
    for entry in data.get('evidence_status', []):
        verifier = entry.get('verifier')
        if verifier and (verifier['wrong'] or verifier['crash']):
            gaps.append(f'Last recorded verifier result in {entry["path"]}: wrong={verifier["wrong"]} '
                        f'crash={verifier["crash"]}.')
    blocked = [task['id'] for task in open_tasks(state) if task.get('status') == 'blocked' or task.get('blockers')]
    if blocked:
        gaps.append(f'Blocked tasks: {", ".join(blocked)}.')
    orphans = orphaned_tasks(data, state, documented_ids, scanned_documents)
    if orphans:
        gaps.append(f'{len(orphans)} open tasks are no longer listed in their source document '
                    '(run `aiwh handoff lint`).')
    unverified = [d['id'] for d in active_decisions(state) if decision_age(d, today) is None]
    stale = [d['id'] for d in active_decisions(state)
             if (decision_age(d, today) or 0) > STALE_DECISION_DAYS]
    if unverified:
        gaps.append(f'Decisions never re-verified: {", ".join(unverified)}.')
    if stale:
        gaps.append(f'Decisions last verified more than {STALE_DECISION_DAYS} days ago: {", ".join(stale)}.')
    outcomes = [r['id'] for r in state.get('resources', []) if 'usefulness' not in r]
    if outcomes:
        gaps.append(f'Resources with no usefulness feedback: {", ".join(outcomes)}.')
    return gaps


def lint_state(data, state, documented_ids, scanned_documents, today=None):
    """Findings about stale or inconsistent state records. Warnings only."""
    today = _today(data, today)
    findings = []

    def add(rule, identifier, detail):
        findings.append({'rule': rule, 'id': identifier, 'detail': detail})

    orphans = orphaned_tasks(data, state, documented_ids, scanned_documents)
    if orphans is None:
        add('orphan-check-skipped', '-', 'Pending scan was truncated; orphaned tasks were not evaluated.')
    for task in orphans or []:
        add('orphaned-task', task['id'],
            f'Still {task["status"]} but no longer listed in {_posix(task["source"])}; '
            'mark it completed/cancelled or restore the item.')
    titles = {}
    for task in open_tasks(state):
        titles.setdefault(task['title'].strip().lower(), []).append(task['id'])
        if task['status'] == 'blocked' and not task['blockers']:
            add('blocked-without-blocker', task['id'], 'Status is blocked but no blocker is recorded.')
    for identifiers in titles.values():
        if len(identifiers) > 1:
            add('duplicate-task-title', ', '.join(identifiers), 'Open tasks share the same title.')
    for task in state.get('tasks', []):
        if task.get('claimed_by') and task.get('status') not in OPEN_STATUSES:
            add('claimed-closed-task', task['id'],
                f'Claimed by {task["claimed_by"]} but status is {task["status"]}; release the claim.')
    for decision in active_decisions(state):
        if not decision.get('source'):
            add('decision-without-source', decision['id'], 'No source (file, commit or discussion) is recorded.')
        age = decision_age(decision, today)
        if age is None:
            add('decision-unverified', decision['id'], 'No last_verified date; recheck it against the repository.')
        elif age > STALE_DECISION_DAYS:
            add('decision-stale', decision['id'], f'Last verified {age} days ago.')
    for resource in state.get('resources', []):
        if 'usefulness' not in resource:
            add('resource-unknown-outcome', resource['id'], 'Selected/rejected without usefulness feedback.')
    return findings
