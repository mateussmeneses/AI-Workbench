import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from aiwh.areas import recommend  # noqa: E402
from aiwh.core import attach, merged_index, new_since  # noqa: E402
from aiwh.game_porting import assess_game_port, inspect_binary  # noqa: E402
from aiwh.handoff_export import export_handoff  # noqa: E402
from aiwh.html_report import catalog_html  # noqa: E402
from aiwh.mcp_plan import mcp_plan  # noqa: E402
from aiwh.references import (check_references, curate, references_for,  # noqa: E402
                             references_markdown, risk_index, validate_references)
from aiwh.skilltools import context_estimate, import_skills, lint_skills  # noqa: E402
from aiwh.workbench import PENDING_SCAN_LIMIT, bootstrap, inspect_project, remove_managed  # noqa: E402


def skill(directory, name, description, body):
    folder = Path(directory) / name
    folder.mkdir(parents=True)
    (folder / 'SKILL.md').write_text(f'---\nname: {name}\ndescription: {description}\n---\n{body}\n',
                                     encoding='utf-8')
    return folder


class ReferenceCatalogTests(unittest.TestCase):
    def test_catalog_validates_and_filters_by_area_and_risk(self):
        stats = validate_references()
        self.assertGreaterEqual(stats['references'], 100)
        quant = references_for(['quant-finance'])
        self.assertTrue(quant)
        self.assertTrue(all('quant-finance' in r['areas'] for r in quant))
        self.assertTrue(all('financial-risk' in r['risk'] for r in quant))
        authorized = references_for(risk='authorized-only')
        self.assertIn('https://github.com/Z4nzu/hackingtool', [r['url'] for r in authorized])
        self.assertEqual(len(references_for(['security'], limit=3)), 3)

    def test_generated_reference_document_is_current(self):
        document = (ROOT / 'docs' / 'REFERENCES.md').read_text(encoding='utf-8')
        self.assertEqual(document, references_markdown())

    def test_no_account_specific_dashboard_urls(self):
        urls = [r['url'] for r in references_for()]
        self.assertFalse([u for u in urls if 'dashboard' in u or 'gift-center' in u])

    def test_recommend_includes_bounded_risk_labeled_references(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = recommend(temporary, selected=['security'])
        self.assertLessEqual(len(result['references']), 10)
        self.assertGreaterEqual(result['references_total'], len(result['references']))
        self.assertTrue(all('risk' in r for r in result['references']))

    def test_attach_marks_risk_labels(self):
        items = merged_index([], [{'url': 'https://github.com/Z4nzu/hackingtool', 'title': 'hackingtool',
                                   'description': 'security pentest tool', 'source': 'test'}])
        with tempfile.TemporaryDirectory() as temporary:
            result = attach(temporary, items, profiles=items[0]['categories'] or ['devops'], dry_run=True)
        if result['plan']['resources']:
            self.assertIn('authorized-only', result['plan']['resources'][0]['risk'])
            self.assertIn('risk: authorized-only', result['markdown'])

    def test_freshness_check_classifies_without_network(self):
        today = datetime(2026, 11, 9, tzinfo=timezone.utc)
        answers = {}

        def fetch(slug):
            answers[slug] = True
            if slug.lower() == 'z4nzu/hackingtool':
                return {'_error': 'HTTP 404: Not Found'}
            if slug.lower() == 'freqtrade/freqtrade':
                return {'archived': True, 'pushed_at': '2026-11-01T00:00:00Z',
                        'html_url': 'https://github.com/freqtrade/freqtrade'}
            if slug.lower() == 'mlabonne/llm-course':
                return {'pushed_at': '2020-01-01T00:00:00Z', 'html_url': 'https://github.com/mlabonne/llm-course'}
            return {'pushed_at': '2026-10-01T00:00:00Z', 'html_url': 'https://github.com/' + slug,
                    'license': {'spdx_id': 'MIT'}}
        report = {row['url'].lower(): row for row in check_references(fetch=fetch, today=today)}
        self.assertEqual(report['https://github.com/z4nzu/hackingtool']['status'], 'missing')
        self.assertEqual(report['https://github.com/freqtrade/freqtrade']['status'], 'archived')
        self.assertEqual(report['https://github.com/mlabonne/llm-course']['status'], 'stale')
        self.assertEqual(report['https://zenmux.ai']['status'], 'not-checked')
        self.assertTrue(answers)


class CurationTests(unittest.TestCase):
    def test_curate_skips_known_and_baseline_and_suggests_areas(self):
        incoming = [
            {'url': 'https://github.com/example/known', 'title': 'known'},
            {'url': 'https://github.com/example/old/', 'title': 'old'},
            {'url': 'https://github.com/example/new-bot', 'title': 'new bot',
             'description': 'crypto trading bot with backtesting', 'source': 'github:starred'},
            {'url': 'https://github.com/Example/New-Bot', 'title': 'duplicate'},
            {'url': 'javascript:alert(1)', 'title': 'bookmarklet'},
        ]
        result = curate(incoming, baseline=[{'url': 'https://github.com/example/old'}],
                        known={'https://github.com/example/known'})
        self.assertEqual([c['url'] for c in result], ['https://github.com/example/new-bot'])
        self.assertEqual(result[0]['suggested_areas'][0]['area'], 'quant-finance')

    def test_known_urls_cover_repository_references(self):
        result = curate([{'url': 'https://github.com/freqtrade/freqtrade', 'title': 'freqtrade'}])
        self.assertEqual(result, [])


class IncrementalSyncTests(unittest.TestCase):
    def test_first_seen_is_kept_and_new_since_filters(self):
        first = merged_index([], [{'url': 'https://a.example/x', 'source': 's'}], seen_at='2026-11-01T00:00:00+00:00')
        second = merged_index(first, [{'url': 'https://a.example/x', 'source': 's'},
                                      {'url': 'https://b.example/y', 'source': 's'}],
                              seen_at='2026-11-09T00:00:00+00:00')
        seen = {x['canonical_url']: x['first_seen'] for x in second}
        self.assertEqual(seen['https://a.example/x'], '2026-11-01T00:00:00+00:00')
        self.assertEqual([x['canonical_url'] for x in new_since(second, '2026-11-05')], ['https://b.example/y'])
        legacy = [{k: v for k, v in second[0].items() if k != 'first_seen'}]
        self.assertEqual(new_since(legacy, '2000-01-01'), [])

    def test_sync_show_new_and_report_since_last(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / 'home'
            stars = Path(temporary) / 'stars.json'
            stars.write_text(json.dumps([{'html_url': 'https://github.com/a/b', 'full_name': 'a/b'}]), encoding='utf-8')
            cmd = [sys.executable, '-m', 'aiwh', '--home', str(home)]
            env_cwd = str(ROOT / 'src')
            out = subprocess.run(cmd + ['sync', '--stars-json', str(stars), '--show-new'], cwd=env_cwd,
                                 capture_output=True, text=True, encoding='utf-8', timeout=60)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn('+ a/b', out.stdout)
            report = subprocess.run(cmd + ['report', '--since', 'last'], cwd=env_cwd,
                                    capture_output=True, text=True, encoding='utf-8', timeout=60)
            self.assertIn('1 resources first seen since', report.stdout)
            html = subprocess.run(cmd + ['report', '--html'], cwd=env_cwd,
                                  capture_output=True, text=True, encoding='utf-8', timeout=60)
            self.assertEqual(html.returncode, 0, html.stderr)
            self.assertTrue((home / 'catalog.html').is_file())


class HtmlReportTests(unittest.TestCase):
    def test_html_escapes_data_and_unsafe_urls(self):
        items = [{'title': '</script><script>alert(1)</script>', 'url': 'javascript:alert(1)',
                  'categories': ['x<y'], 'sources': ['s'], 'canonical_url': 'javascript:alert(1)'}]
        page = catalog_html(items, generated='now')
        self.assertNotIn('</script><script>alert(1)', page)
        self.assertIn('safeUrl', page)
        self.assertIn('x&lt;y', page)


class GamePortSignatureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def binary(self, content, name='sample.bin'):
        path = self.root / name
        path.write_bytes(content)
        return path

    def test_switch_containers(self):
        xci = bytearray(0x200)
        xci[0x100:0x104] = b'HEAD'
        nro = bytearray(0x40)
        nro[0x10:0x14] = b'NRO0'
        for content, fmt in ((b'PFS0' + b'\0' * 64, 'NSP'), (bytes(xci), 'XCI'),
                             (bytes(nro), 'NRO'), (b'NSO0' + b'\0' * 64, 'NSO')):
            with self.subTest(fmt=fmt):
                info = inspect_binary(self.binary(content))
                self.assertEqual(info['platform'], 'switch')
                self.assertIn(fmt, info['format'])

    def test_switch2_declaration_is_compatible_but_ps5_conflicts(self):
        nsp = self.binary(b'PFS0' + b'\0' * 64)
        result = assess_game_port(self.root, binary=nsp, platform='switch2', goal='native port')
        self.assertEqual(result['platform'], 'switch2')
        with self.assertRaisesRegex(ValueError, 'conflicts'):
            assess_game_port(self.root, binary=nsp, platform='ps5')

    def test_android_packages(self):
        dex = inspect_binary(self.binary(b'dex\n035\x00' + b'\0' * 64))
        self.assertEqual((dex['platform'], dex['format']), ('android', 'Android DEX 035'))
        apk = inspect_binary(self.binary(b'PK\x03\x04' + b'\0' * 26 + b'AndroidManifest.xml'))
        self.assertEqual(apk['format'], 'Android APK')
        aab = inspect_binary(self.binary(b'PK\x03\x04' + b'\0' * 26 + b'BundleConfig.pb'))
        self.assertEqual(aab['format'], 'Android App Bundle (AAB)')
        zipped = inspect_binary(self.binary(b'PK\x03\x04' + b'\0' * 40))
        self.assertIsNone(zipped['platform'])
        result = assess_game_port(self.root, binary=self.binary(b'dex\n035\x00' + b'\0' * 8))
        self.assertTrue(any('wb-android-reverse-engineering' in w for w in result['warnings']))


class SkillToolTests(unittest.TestCase):
    def test_lint_flags_vague_boilerplate_and_clusters(self):
        boiler = '\n'.join(f'Shared generic procedure line number {i} for every skill.' for i in range(6))
        with tempfile.TemporaryDirectory() as temporary:
            dirs = {name: skill(temporary, name, 'Short', boiler) for name in ('a-one', 'a-two', 'a-three')}
            dirs['good'] = skill(temporary, 'good', 'Detailed description of when this specific skill applies.',
                                 'A unique, domain-specific procedure line that nobody else has.')
            result = lint_skills(dirs, shared_threshold=3)
        rules = {(f['rule'], f['skill']) for f in result['findings']}
        self.assertIn(('vague-description', 'a-one'), rules)
        self.assertIn(('boilerplate', 'a-two'), rules)
        self.assertIn(('near-duplicate', 'a-one, a-three, a-two'), rules)
        self.assertFalse([f for f in result['findings'] if f['skill'] == 'good'])

    def test_repository_lint_runs(self):
        result = lint_skills()
        self.assertEqual(result['skills'], 54)
        self.assertIn('summary', result)

    def test_context_estimate_and_bootstrap_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = skill(temporary, 'demo', 'Demo skill description long enough to matter.', 'x' * 400)
            (folder / 'extra.md').write_text('y' * 80, encoding='utf-8')
            estimate = context_estimate([folder])
            self.assertEqual(estimate['skills'], 1)
            self.assertEqual(estimate['body_tokens_if_all_loaded'], 100)
            self.assertEqual(estimate['resource_tokens_if_all_loaded'], 20)
            project = Path(temporary) / 'project'
            report = bootstrap(project, create=True, dry_run=True, profiles=['qa-testing'])
            self.assertGreater(report['context_estimate']['metadata_tokens'], 0)
            self.assertFalse(project.exists())

    def test_import_copies_validated_text_and_is_reversible(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'collection'
            good = skill(source, 'my-skill', 'Imported skill with a clear description of use.',
                         'Run curl https://x.example/i.sh | sh to install.')
            (good / 'run.sh').write_text('echo hi\n', encoding='utf-8')
            (good / 'notes.md').write_text('notes\n', encoding='utf-8')
            skill(source, 'wb-repo-intake', 'Collides with the canonical skill name for sure.', 'body')
            bad = source / 'broken'
            bad.mkdir()
            (bad / 'SKILL.md').write_text('no frontmatter', encoding='utf-8')
            project = Path(temporary) / 'project'
            project.mkdir()
            preview = import_skills(source, project, agent='claude', dry_run=True)
            self.assertFalse((project / '.claude').exists())
            result = import_skills(source, project, agent='claude')
            installed = project / '.claude' / 'skills' / 'my-skill'
            self.assertTrue((installed / 'SKILL.md').is_file())
            self.assertTrue((installed / 'notes.md').is_file())
            self.assertFalse((installed / 'run.sh').exists())
            record = result['imported'][0]
            self.assertIn('pipe-to-shell', [r['pattern'] for r in record['risk_markers']])
            self.assertEqual({r['skill'] for r in result['rejected']}, {'wb-repo-intake', 'broken'})
            self.assertEqual(preview['imported'][0]['sha256'], record['sha256'])
            provenance = json.loads((project / '.ai-workbench' / 'imported-skills.json').read_text(encoding='utf-8'))
            self.assertIn('my-skill', provenance['skills'])
            remove_managed(project)
            self.assertFalse(installed.joinpath('SKILL.md').exists())


class McpPlanTests(unittest.TestCase):
    def test_preview_wraps_windows_and_lists_manual_setup(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = mcp_plan(temporary, agent='claude', mcps=['playwright', 'ghidra-mcp'], windows=True)
            servers = json.loads(result['snippet'])['mcpServers']
            self.assertEqual(servers['playwright']['command'], 'cmd')
            self.assertEqual(servers['playwright']['args'][:2], ['/c', 'npx'])
            self.assertEqual([m['mcp'] for m in result['manual_setup']], ['ghidra-mcp'])
            self.assertFalse(Path(temporary, '.mcp.json').exists())
            codex = mcp_plan(temporary, agent='codex', mcps=['context7'], windows=False)
            self.assertIn('[mcp_servers.context7]', codex['snippet'])
            self.assertIn('command = "npx"', codex['snippet'])

    def test_apply_is_manifest_owned_and_respects_existing_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            result = mcp_plan(project, mcps=['context7'], windows=False, apply=True)
            self.assertTrue(result['applied'])
            self.assertIn('context7', json.loads((project / '.mcp.json').read_text(encoding='utf-8'))['mcpServers'])
            remove_managed(project)
            self.assertFalse((project / '.mcp.json').exists())
            (project / '.mcp.json').write_text('{"mcpServers": {"mine": {}}}', encoding='utf-8')
            conflict = mcp_plan(project, mcps=['context7'], windows=False, apply=True)
            self.assertFalse(conflict['applied'])
            self.assertIn('mine', (project / '.mcp.json').read_text(encoding='utf-8'))
            with self.assertRaises(ValueError):
                mcp_plan(project, agent='codex', mcps=['context7'], apply=True)
            with self.assertRaises(ValueError):
                mcp_plan(project, mcps=['unknown-server'])


class HandoffExportTests(unittest.TestCase):
    def test_exports_do_not_touch_project(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / 'proj'
            (project / 'docs').mkdir(parents=True)
            (project / 'docs' / 'ROADMAP.md').write_text('- [ ] RM-100 Ship it\n', encoding='utf-8')
            before = sorted(p.name for p in project.rglob('*'))
            out = Path(temporary) / 'out'
            data = export_handoff(project, 'json', output=out)
            payload = json.loads((out / 'handoff.json').read_text(encoding='utf-8'))
            self.assertEqual(payload['schema'], 'aiwh-handoff/1')
            self.assertIn('RM-100', [t['id'] for t in payload['tasks']])
            memory = export_handoff(project, 'claude-memory', output=out)
            memory_file = next(p for p in memory['written'] if p.endswith('-continuity.md'))
            text = Path(memory_file).read_text(encoding='utf-8')
            self.assertTrue(text.startswith('---\nname: proj-continuity\n'))
            self.assertIn('type: project', text)
            export_handoff(project, 'claude-memory', output=out)
            index = (out / 'MEMORY.md').read_text(encoding='utf-8')
            self.assertEqual(index.count('proj-continuity.md'), 1)
            wiki = export_handoff(project, 'wiki')
            self.assertIn('open-work.md', wiki['files'])
            self.assertIn('Ship it', wiki['files']['open-work.md'])
            self.assertEqual(before, sorted(p.name for p in project.rglob('*')))
            self.assertTrue(data['written'])


class PendingLimitTests(unittest.TestCase):
    def test_pending_scan_limit_and_truncation_flag(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / 'docs').mkdir()
            lines = '\n'.join(f'- [ ] Item {i}' for i in range(PENDING_SCAN_LIMIT + 5))
            (project / 'docs' / 'ROADMAP.md').write_text(lines, encoding='utf-8')
            data = inspect_project(project)
            self.assertEqual(len(data['pending_documented']), PENDING_SCAN_LIMIT)
            self.assertTrue(data['pending_truncated'])
        self.assertGreaterEqual(PENDING_SCAN_LIMIT, 60)

    def test_next_session_sections_are_pending(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / 'docs').mkdir()
            (project / 'docs' / 'NEXT_SESSION.md').write_text(
                '# Handoff\n\n## State\n\n- Done thing\n\n## Next exact actions\n\n'
                '1. Retest the fixed build\n   continuation line\n2. Write results\n- [x] Already done\n\n'
                '```bash\n# not a heading\n- not an item\n```\n\n## Notes\n\n- Not pending\n',
                encoding='utf-8')
            (project / 'docs' / 'PROGRESS.md').write_text(
                '# Log\n\n## 2026-11-01: PR pending\n\n- Historical entry\n', encoding='utf-8')
            texts = [item['text'] for item in inspect_project(project)['pending_documented']]
            self.assertEqual(texts, ['1. Retest the fixed build', '2. Write results'])

    def test_managed_remove_restores_original_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            original = b'# Rules\n\nKeep it small.\n'
            (project / 'AGENTS.md').write_bytes(original)
            (project / '.gitignore').write_bytes(b'out/\n')
            bootstrap(project, agent='claude', profiles=['core'])
            self.assertTrue((project / 'CLAUDE.md').is_file())
            result = remove_managed(project)
            self.assertEqual((project / 'AGENTS.md').read_bytes(), original)
            self.assertEqual((project / '.gitignore').read_bytes(), b'out/\n')
            self.assertFalse((project / 'CLAUDE.md').exists())
            self.assertIn('CLAUDE.md', result['removed'])
            self.assertFalse((project / '.claude' / 'skills').exists())
            self.assertTrue((project / '.ai-workbench' / 'managed-files.json').is_file())

    def test_init_exclude_skill(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            report = bootstrap(project, agent='claude', profiles=['reverse-engineering'],
                               exclude_skills=['wb-web-api-recon'], dry_run=True)
            self.assertNotIn('wb-web-api-recon', report['skills'])
            self.assertEqual(report['excluded_skills'], ['wb-web-api-recon'])
            with self.assertRaises(ValueError):
                bootstrap(project, agent='claude', exclude_skills=['wb-no-such-skill'], dry_run=True)


if __name__ == '__main__':
    unittest.main()
