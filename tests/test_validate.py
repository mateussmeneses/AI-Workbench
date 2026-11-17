import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from aiwh.cli import main  # noqa: E402
from aiwh.continuity import resume  # noqa: E402
from aiwh.validate import evaluate_evidence, redact_secrets, run_validation  # noqa: E402


def _git(project, *args):
    subprocess.run(['git', '-C', str(project), *args], check=True, capture_output=True)


def _repo(directory):
    project = Path(directory) / 'proj'
    project.mkdir()
    (project / 'AGENTS.md').write_text('Run `python -c "print(\'ok\')"` to test.\n', encoding='utf-8')
    _git(project, 'init', '-q', str(project))
    _git(project, 'config', 'user.email', 'test@example.org')
    _git(project, 'config', 'user.name', 'Test Runner')
    _git(project, 'add', '.')
    _git(project, 'commit', '-qm', 'Baseline')
    return project


class ValidationTests(unittest.TestCase):
    def test_preview_does_not_execute_or_write_state(self):
        with tempfile.TemporaryDirectory() as d:
            project = _repo(d)
            marker = project / 'ran.txt'
            cmd = f'{sys.executable} -c "open(\'ran.txt\', \'w\').write(\'1\')"'
            res = run_validation(project, command=cmd, approve=False)
            self.assertFalse(res['executed'])
            self.assertEqual(res['status'], 'not_run')
            self.assertFalse(marker.exists())
            self.assertFalse((project / '.ai-workbench' / 'state.json').exists())

    def test_approved_pass_fail_timeout_and_secret_redaction(self):
        cleaned = redact_secrets('Authorization: Bearer secret12345678\nghp_1234567890abcdef12345\npassword=mysecretpass')
        self.assertNotIn('secret12345678', cleaned)
        self.assertNotIn('ghp_1234567890abcdef12345', cleaned)
        self.assertNotIn('mysecretpass', cleaned)
        self.assertEqual(cleaned.count('[REDACTED]'), 3)

        with tempfile.TemporaryDirectory() as d:
            project = _repo(d)
            ok = run_validation(project, command=f'{sys.executable} -c "print(\'ghp_abcdef1234567890\')"', approve=True)
            self.assertTrue(ok['executed'])
            self.assertEqual(ok['status'], 'passed')
            self.assertNotIn('ghp_abcdef1234567890', ok['output'])
            self.assertIn('[REDACTED]', ok['output'])

            state = json.loads((project / '.ai-workbench' / 'state.json').read_text(encoding='utf-8'))
            self.assertEqual(state['validation']['status'], 'passed')

            fail = run_validation(project, command=f'{sys.executable} -c "import sys; sys.exit(2)"', approve=True)
            self.assertEqual(fail['status'], 'failed')
            self.assertEqual(fail['exit_code'], 2)

            timed = run_validation(project, command=f'{sys.executable} -c "import time; time.sleep(5)"',
                                   timeout=1, approve=True)
            self.assertEqual(timed['status'], 'timed_out')

    def test_stale_evidence_after_commit_and_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            project = _repo(d)
            code = main(['validate', str(project), '--command', f'{sys.executable} -c "print(123)"'])
            self.assertEqual(code, 0)
            self.assertFalse((project / '.ai-workbench' / 'state.json').exists())

            code = main(['validate', str(project), '--command', f'{sys.executable} -c "print(123)"', '--approve'])
            self.assertEqual(code, 0)
            state = json.loads((project / '.ai-workbench' / 'state.json').read_text(encoding='utf-8'))
            self.assertEqual(evaluate_evidence(project, state['validation'])['effective_status'], 'passed')

            (project / 'AGENTS.md').write_text('Changed\n', encoding='utf-8')
            _git(project, 'add', '.')
            _git(project, 'commit', '-qm', 'Move HEAD')
            ev = evaluate_evidence(project, state['validation'])
            self.assertEqual(ev['effective_status'], 'stale')
            self.assertTrue(ev['stale'])

            res = resume(project, dry_run=True)
            self.assertIn('## Validation evidence', res['markdown'])
            self.assertIn('**stale**', res['markdown'])


if __name__ == '__main__':
    unittest.main()
