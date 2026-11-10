import contextlib
import copy
import io
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from aiwh.cli import main  # noqa: E402
from aiwh.handoff_checks import handoff_gaps, lint_state  # noqa: E402
from aiwh.handoff_export import export_handoff  # noqa: E402
from aiwh.handoff_plan import (build_plan, check_drift, claim_task, lint_handoff,  # noqa: E402
                               plan_markdown)
from aiwh.references import reference_catalog, references_for, validate_references  # noqa: E402
from aiwh.workbench import resume  # noqa: E402


def git(project, *args):
    subprocess.run(['git', '-C', str(project), *args], check=True, capture_output=True)


def repository(directory, roadmap='- [ ] RM-301 First task\n- [ ] RM-302 Second task\n'):
    project = Path(directory) / 'proj'
    (project / 'docs').mkdir(parents=True)
    (project / 'docs' / 'ROADMAP.md').write_text(roadmap, encoding='utf-8')
    (project / 'AGENTS.md').write_text('Run `python -m unittest discover -s tests` after changes.\n',
                                       encoding='utf-8')
    subprocess.run(['git', 'init', '-q', str(project)], check=True)
    git(project, 'config', 'user.email', 'test@example.org')
    git(project, 'config', 'user.name', 'Test Runner')
    git(project, 'add', '.')
    git(project, 'commit', '-qm', 'Baseline')
    return project


def state_of(project):
    return json.loads((project / '.ai-workbench' / 'state.json').read_text(encoding='utf-8'))


def save_state(project, state):
    (project / '.ai-workbench' / 'state.json').write_text(json.dumps(state), encoding='utf-8')


def run_cli(*argv):
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        code = main([str(arg) for arg in argv])
    return code, stream.getvalue()


class RevisionAndDriftTests(unittest.TestCase):
    def test_repeated_task_id_is_recorded_once_and_resume_repeats(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / 'docs').mkdir()
            (project / 'docs' / 'ROADMAP.md').write_text(
                '- [ ] RM-009 Ship handoffs\n\n## Next-session procedure\n\n1. Current next task: RM-009 handoffs\n',
                encoding='utf-8')
            resume(project)
            resume(project)
            tasks = state_of(project)['tasks']
            self.assertEqual([task['id'] for task in tasks], ['RM-009'])
            self.assertEqual(tasks[0]['title'], 'Ship handoffs')

    def test_handoff_records_revision_and_reports_movement(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = repository(temporary)
            first = resume(project)
            head = first['data']['head_commit']
            self.assertEqual(len(head), 40)
            self.assertIn(f'Source revision: `{head}`', first['markdown'])
            self.assertIsNone(state_of(project)['latest_delta']['observed']['head_change'])
            self.assertEqual(check_drift(project)['status'], 'current')

            (project / 'README.md').write_text('new\n', encoding='utf-8')
            git(project, 'add', 'README.md')
            git(project, 'commit', '-qm', 'Move on')
            drift = check_drift(project)
            self.assertEqual(drift['status'], 'drifted')
            self.assertEqual(drift['commits_since'], 1)
            self.assertEqual(drift['changed_files'], ['README.md'])
            self.assertEqual(run_cli('handoff', 'check', project)[0], 1)

            second = resume(project)
            change = state_of(project)['latest_delta']['observed']['head_change']
            self.assertEqual(change['from'], head)
            self.assertIn('Source revision moved', second['markdown'])
            self.assertEqual(run_cli('handoff', 'check', project)[0], 0)

    def test_drift_is_unknown_without_baseline_or_git(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            self.assertEqual(check_drift(project)['status'], 'unknown')
            self.assertEqual(run_cli('handoff', 'check', project)[0], 2)
            resume(project)
            self.assertIsNone(state_of(project)['observed']['head_commit'])
            self.assertEqual(check_drift(project)['status'], 'unknown')

    def test_snapshot_without_recorded_revision_is_not_reported_as_movement(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = repository(temporary)
            resume(project)
            state = state_of(project)
            for snapshot in state['history']:
                snapshot['observed'].pop('head_commit')
            save_state(project, state)
            resume(project)
            self.assertIsNone(state_of(project)['latest_delta']['observed']['head_change'])


class ExecutionPlanTests(unittest.TestCase):
    def test_plan_is_self_contained_and_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = repository(temporary)
            before = sorted(str(path) for path in project.rglob('*') if '.git' not in path.parts)
            plan = build_plan(project)
            self.assertEqual(plan['task']['id'], 'RM-301')
            self.assertEqual(plan['task_source'], {'path': 'docs/ROADMAP.md', 'line': 1,
                                                   'text': '- [ ] RM-301 First task'})
            text = plan_markdown(plan)
            self.assertIn(f'Source revision: `{plan["source_revision"]}`', text)
            self.assertIn('`docs/ROADMAP.md:1`', text)
            self.assertIn('Run `python -m unittest discover -s tests`. Expected: exit status 0', text)
            self.assertIn('## Stop and report instead of continuing when', text)
            self.assertIn('aiwh handoff claim RM-301', text)
            self.assertIn('## Model routing (recommendation)', text)
            self.assertEqual(before, sorted(str(path) for path in project.rglob('*') if '.git' not in path.parts))

    def test_plan_skips_blocked_and_claimed_tasks_and_honors_records(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = repository(temporary, '- [ ] RM-301 First\n- [ ] RM-302 Second\n- [ ] RM-303 Third\n')
            resume(project)
            state = state_of(project)
            state['tasks'][0].update(status='blocked', blockers=['needs review'])
            state['decisions'] = [
                {'id': 'd-1', 'text': 'Stay local', 'approved': True, 'rationale': 'Privacy'},
                {'id': 'd-2', 'text': 'Use a daemon', 'approved': True, 'rationale': 'Speed',
                 'retracted': True, 'retraction_reason': 'Breaks portability'}]
            state['rejections'] = [{'id': 'r-1', 'text': 'Rename the CLI', 'rationale': 'Compatibility'}]
            state['resources'] = [{'id': 'repo:a/b', 'selection': 'selected', 'rationale': 'Fits'},
                                  {'id': 'repo:c/d', 'selection': 'rejected', 'rationale': 'Paid'}]
            save_state(project, state)
            claim_task(project, 'RM-302', 'codex')
            plan = build_plan(project)
            self.assertEqual(plan['task']['id'], 'RM-303')
            self.assertEqual([item['id'] for item in plan['skipped']], ['RM-301', 'RM-302'])
            self.assertIn('claimed by codex', plan['skipped'][1]['reason'])
            self.assertEqual([d['id'] for d in plan['decisions']], ['d-1'])
            self.assertEqual([r['id'] for r in plan['resources']], ['repo:a/b'])
            text = plan_markdown(plan)
            self.assertIn('r-1: Rename the CLI', text)
            self.assertNotIn('Use a daemon', text)
            explicit = build_plan(project, task_id='RM-301')
            self.assertEqual(explicit['task']['id'], 'RM-301')
            self.assertIn('selected explicitly', explicit['skipped'][0]['reason'])
            with self.assertRaisesRegex(ValueError, 'Unknown task'):
                build_plan(project, task_id='RM-999')

    def test_no_eligible_task_and_missing_test_command(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            code, output = run_cli('handoff', 'plan', project)
            self.assertEqual(code, 1)
            self.assertIn('## No eligible task', output)
            (project / 'TODO.md').write_text('- [ ] Write the parser\n', encoding='utf-8')
            text = plan_markdown(build_plan(project))
            self.assertIn('No test command is documented', text)
            self.assertIn('No Git revision was readable', text)

    def test_cli_writes_plan_and_checks_it_for_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = repository(temporary)
            plan_file = Path(temporary) / 'plan.md'
            self.assertEqual(run_cli('handoff', 'plan', project, '--output', plan_file)[0], 0)
            self.assertEqual(run_cli('handoff', 'check', project, '--plan', plan_file)[0], 0)
            (project / 'docs' / 'ROADMAP.md').write_text('- [ ] RM-301 Reworded\n', encoding='utf-8')
            git(project, 'commit', '-qam', 'Edit roadmap')
            code, output = run_cli('handoff', 'check', project, '--plan', plan_file)
            self.assertEqual(code, 1)
            self.assertIn('Changed: docs/ROADMAP.md', output)
            code, output = run_cli('handoff', 'plan', project, '--json')
            self.assertEqual(json.loads(output)['schema'], 'aiwh-plan/1')


class ClaimTests(unittest.TestCase):
    def test_task_has_one_owner_until_released(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = repository(temporary)
            with self.assertRaisesRegex(ValueError, 'run `aiwh resume` first'):
                claim_task(project, 'RM-301', 'claude')
            resume(project)
            preview = claim_task(project, 'RM-301', 'claude', dry_run=True)
            self.assertEqual((preview['action'], preview['written']), ('claimed', False))
            self.assertNotIn('claimed_by', state_of(project)['tasks'][0])
            self.assertEqual(claim_task(project, 'RM-301', 'claude')['action'], 'claimed')
            self.assertEqual(state_of(project)['tasks'][0]['claimed_by'], 'claude')
            self.assertEqual(claim_task(project, 'RM-301', 'claude')['action'], 'unchanged')
            with self.assertRaisesRegex(ValueError, 'already claimed by claude'):
                claim_task(project, 'RM-301', 'codex')
            with self.assertRaisesRegex(ValueError, 'claimed by claude, not codex'):
                claim_task(project, 'RM-301', 'codex', release=True)
            self.assertEqual(run_cli('handoff', 'claim', 'RM-301', '--by', 'codex', '--project', project)[0], 1)
            handoff = resume(project)['markdown']
            self.assertIn('RM-301: claimed by claude', handoff)
            self.assertEqual(claim_task(project, 'RM-301', 'claude', release=True)['action'], 'released')
            self.assertNotIn('claimed_by', state_of(project)['tasks'][0])
            with self.assertRaisesRegex(ValueError, 'Unknown task'):
                claim_task(project, 'RM-999', 'claude')

    def test_closed_task_cannot_be_claimed(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = repository(temporary)
            resume(project)
            state = state_of(project)
            state['tasks'][0]['status'] = 'completed'
            save_state(project, state)
            with self.assertRaisesRegex(ValueError, 'cannot be claimed'):
                claim_task(project, 'RM-301', 'claude')


class StateRecordTests(unittest.TestCase):
    def test_decision_and_rejection_fields_are_validated_and_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = repository(temporary)
            resume(project)
            base = state_of(project)
            good = {'id': 'd-1', 'text': 'Stay local', 'approved': True, 'rationale': 'Privacy',
                    'source': 'docs/ARCHITECTURE.md', 'last_verified': '2026-11-01', 'confidence': 'high'}
            rejection = {'id': 'r-1', 'text': 'Add a daemon', 'rationale': 'Out of scope'}
            state = copy.deepcopy(base)
            state.update(decisions=[good], rejections=[rejection])
            save_state(project, state)
            markdown = resume(project)['markdown']
            saved = state_of(project)
            self.assertEqual(saved['decisions'], [good])
            self.assertEqual(saved['rejections'], [rejection])
            self.assertIn('d-1: Stay local (source: docs/ARCHITECTURE.md; last verified: 2026-11-01; '
                          'confidence: high)', markdown)
            self.assertIn('## Rejected findings (do not re-raise)', markdown)
            invalid = (
                ({'last_verified': '01/11/2026'}, 'last_verified must be YYYY-MM-DD'),
                ({'confidence': 'certain'}, 'confidence must be one of'),
                ({'retracted': True}, 'requires a retraction_reason'),
                ({'retracted': 'yes'}, 'retracted must be true or false'),
                ({'source': ' '}, 'source must be a non-empty string'),
            )
            for change, message in invalid:
                with self.subTest(change=change):
                    broken = copy.deepcopy(saved)
                    broken['decisions'][0].update(change)
                    save_state(project, broken)
                    with self.assertRaisesRegex(ValueError, message):
                        resume(project)
            broken = copy.deepcopy(saved)
            broken['rejections'] = [{'id': 'r-2', 'text': 'No reason given'}]
            save_state(project, broken)
            with self.assertRaisesRegex(ValueError, 'rejection r-2 requires rationale'):
                resume(project)

    def test_retracted_decision_is_shown_as_retracted(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = repository(temporary)
            resume(project)
            state = state_of(project)
            state['decisions'] = [{'id': 'd-9', 'text': 'Ship weekly', 'approved': True, 'rationale': 'Cadence',
                                   'retracted': True, 'retraction_reason': 'Release gates changed'}]
            save_state(project, state)
            self.assertIn('RETRACTED d-9: Ship weekly (reason: Release gates changed)',
                          resume(project)['markdown'])


class GapsAndLintTests(unittest.TestCase):
    DATA = {'generated_at': '2026-11-10T00:00:00+00:00', 'head_commit': 'a' * 40, 'working_tree_changes': [],
            'test_command': 'make test', 'pending_truncated': False, 'pending_scan_limit': 60,
            'evidence_status': []}
    DOCUMENTS = ('docs/ROADMAP.md',)

    def task(self, identifier, **changes):
        return {'id': identifier, 'title': f'Title {identifier}', 'source': 'docs\\ROADMAP.md', 'status': 'pending',
                'blockers': [], 'risks': [], 'milestone_outcomes': [], **changes}

    def test_clean_state_has_no_gaps_or_findings(self):
        state = {'tasks': [self.task('T-1')], 'decisions': [], 'resources': []}
        self.assertEqual(handoff_gaps(self.DATA, state, {'T-1'}, self.DOCUMENTS), [])
        self.assertEqual(lint_state(self.DATA, state, {'T-1'}, self.DOCUMENTS), [])

    def test_gaps_name_what_is_unknown(self):
        data = {**self.DATA, 'head_commit': None, 'working_tree_changes': [' M a.py'], 'test_command': None,
                'pending_truncated': True,
                'evidence_status': [{'path': 'NOTES.md', 'unknown': 2, 'open_questions': 1,
                                     'verifier': {'wrong': 3, 'crash': 0}}]}
        state = {'tasks': [self.task('T-1', status='blocked', blockers=['x'])],
                 'decisions': [{'id': 'd-old', 'last_verified': '2026-01-01'}, {'id': 'd-new'},
                               {'id': 'd-gone', 'retracted': True}],
                 'resources': [{'id': 'repo:a/b', 'selection': 'selected', 'rationale': 'r'}]}
        text = '\n'.join(handoff_gaps(data, state, {'T-1'}, self.DOCUMENTS, today=date(2026, 11, 10)))
        for expected in ('No Git revision is readable', '1 uncommitted tracked changes',
                         'No documented test command', 'scan stopped at 60', '2 unknowns and 1 open questions',
                         'wrong=3 crash=0', 'Blocked tasks: T-1', 'never re-verified: d-new',
                         'more than 180 days ago: d-old', 'no usefulness feedback: repo:a/b'):
            self.assertIn(expected, text)
        self.assertNotIn('d-gone', text)

    def test_lint_rules(self):
        state = {'tasks': [self.task('T-1'), self.task('T-2', status='blocked'),
                           self.task('T-3', title='Title T-2'),
                           self.task('T-4', status='completed', claimed_by='codex'),
                           self.task('T-5', source='private note')],
                 'decisions': [{'id': 'd-1', 'source': 'README.md', 'last_verified': '2026-11-09'},
                               {'id': 'd-2', 'last_verified': '2025-01-01'}, {'id': 'd-3'}],
                 'resources': [{'id': 'repo:a/b', 'selection': 'selected', 'rationale': 'r'}]}
        findings = lint_state(self.DATA, state, {'T-2', 'T-3'}, self.DOCUMENTS, today=date(2026, 11, 10))
        rules = {(finding['rule'], finding['id']) for finding in findings}
        self.assertEqual(rules, {
            ('orphaned-task', 'T-1'), ('blocked-without-blocker', 'T-2'), ('duplicate-task-title', 'T-2, T-3'),
            ('claimed-closed-task', 'T-4'), ('decision-without-source', 'd-2'), ('decision-stale', 'd-2'),
            ('decision-without-source', 'd-3'), ('decision-unverified', 'd-3'),
            ('resource-unknown-outcome', 'repo:a/b')})
        truncated = lint_state({**self.DATA, 'pending_truncated': True}, state, set(), self.DOCUMENTS)
        self.assertIn('orphan-check-skipped', {finding['rule'] for finding in truncated})
        self.assertNotIn('orphaned-task', {finding['rule'] for finding in truncated})

    def test_removed_document_item_becomes_an_orphan(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = repository(temporary)
            resume(project)
            self.assertEqual(lint_handoff(project)['findings'], [])
            self.assertEqual(run_cli('handoff', 'lint', project, '--strict')[0], 0)
            (project / 'docs' / 'ROADMAP.md').write_text('- [x] RM-301 First task\n- [ ] RM-302 Second task\n',
                                                         encoding='utf-8')
            findings = lint_handoff(project)['findings']
            self.assertEqual([(f['rule'], f['id']) for f in findings], [('orphaned-task', 'RM-301')])
            code, output = run_cli('handoff', 'lint', project, '--strict')
            self.assertEqual(code, 1)
            self.assertIn('orphaned-task', output)
            self.assertIn('1 open tasks are no longer listed', resume(project)['markdown'])
            self.assertEqual(build_plan(project)['task']['id'], 'RM-302')


class WikiExportTests(unittest.TestCase):
    def test_wiki_has_index_gaps_and_append_only_log(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = repository(temporary)
            out = Path(temporary) / 'wiki'
            first = export_handoff(project, 'wiki', output=out)
            self.assertEqual(set(first['files']), {'index.md', 'overview.md', 'open-work.md', 'decisions.md',
                                                   'recent-commits.md', 'gaps.md', 'log.md'})
            index = (out / 'index.md').read_text(encoding='utf-8')
            for page in first['files']:
                if page != 'index.md':
                    self.assertIn(f']({page})', index)
            export_handoff(project, 'wiki', output=out)
            log = (out / 'log.md').read_text(encoding='utf-8')
            self.assertEqual(log.count('# proj: log'), 1)
            entries = [line for line in log.splitlines() if line.startswith('## [')]
            self.assertEqual(len(entries), 2)
            self.assertRegex(entries[0], r'export \| branch \S+ \| revision [0-9a-f]{12} \| 2 open tasks')
            payload = json.loads(export_handoff(project, 'json')['files']['handoff.json'])
            self.assertEqual(payload['rejections'], [])
            self.assertIsInstance(payload['gaps'], list)


class ReferenceReviewTests(unittest.TestCase):
    def test_review_dates_are_validated_listed_and_counted(self):
        stats = validate_references()
        reviewed = [row for row in references_for() if row.get('reviewed')]
        self.assertEqual(stats['reviewed'], len(reviewed))
        self.assertIn('https://github.com/shadcn/improve', [row['url'] for row in reviewed])
        data = reference_catalog()
        key = next(iter(data['references']))
        for change, message in (({'reviewed': '2026-13-40'}, 'reviewed date must be YYYY-MM-DD'),
                                ({'license': ''}, 'license note must be a non-empty string')):
            broken = copy.deepcopy(data)
            broken['references'][key].update(change)
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, message):
                validate_references(broken)
        code, output = run_cli('references', '--unreviewed', '--json')
        self.assertEqual(code, 0)
        self.assertEqual(len(json.loads(output)), stats['references'] - stats['reviewed'])


if __name__ == '__main__':
    unittest.main()
