import json
import tempfile
import unittest
from pathlib import Path

from aiwh.areas import catalog, validate_catalog, recommend, resolve_areas
from aiwh.workbench import bootstrap, choose_profiles
from aiwh.cli import main


class AreaTests(unittest.TestCase):
    def test_references_and_catalog(self):
        info = validate_catalog()
        self.assertEqual(info['areas'], 27)
        self.assertEqual(info['skills'], 54)
        self.assertIn('marketing', catalog())
        self.assertIn('sales', catalog())
        self.assertIn('reverse-engineering', catalog())

    def test_explicit_composable_business_and_technical_areas(self):
        with tempfile.TemporaryDirectory() as d:
            r = recommend(d,selected=['frontend','backend','marketing','sales'])
            self.assertEqual(set(r['areas']), {'frontend','backend','marketing','sales'})
            self.assertIn('wb-frontend-engineering',r['skills'])
            self.assertIn('wb-marketing-strategy',r['skills'])
            self.assertIn('sales-strategist',r['agents'])
            self.assertIn('figma',r['plugins'])
            self.assertIn('playwright',r['mcps'])
            self.assertEqual(r['execution']['plugins'], 'suggest-only; connection requires explicit user action')

    def test_game_and_reverse_engineering_composition(self):
        with tempfile.TemporaryDirectory() as d:
            r = recommend(d,selected=['reverse-engineering','decompilation','recompilation','game-modding'])
            for name in ('reverse-engineering','decompilation','recompilation','game-modding'):
                self.assertIn(name,r['areas'])
            self.assertGreaterEqual(len(r['skills']),4)

    def test_auto_detect_from_readme_and_files(self):
        with tempfile.TemporaryDirectory() as d:
            repo=Path(d)
            (repo/'README.md').write_text('A React frontend and FastAPI backend for ecommerce sales.')
            (repo/'src').mkdir()
            (repo/'src/App.tsx').write_text('export default function App() {}')
            r=recommend(repo,goal='Build a sales analytics dashboard')
            self.assertIn('frontend',r['areas'])
            self.assertTrue(all(x['evidence'] for x in r['ranked']))
            self.assertLessEqual(len(r['areas']),4)

    def test_unknowns_do_not_guess(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(resolve_areas(d)['areas'],[])
            with self.assertRaisesRegex(ValueError,'Unknown areas'):
                recommend(d,selected=['not-a-real-area'])

    def test_init_dry_run_is_read_only_and_install_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            project=Path(d)/'new'
            before=bootstrap(project,create=True,agent='all',areas=['frontend','marketing'],dry_run=True)
            self.assertFalse(project.exists())
            self.assertIn('frontend',before['areas'])
            first=bootstrap(project,create=True,agent='all',areas=['frontend','marketing'],home=Path(d)/'secret')
            self.assertTrue((project/'.ai-workbench/CAPABILITY_PLAN.md').exists())
            self.assertTrue((project/'.agents/skills/wb-frontend-engineering/SKILL.md').is_file())
            self.assertTrue((project/'.claude/skills/wb-marketing-strategy/SKILL.md').is_file())
            self.assertEqual(choose_profiles(project),['core','frontend','marketing'])
            second=bootstrap(project,create=True,agent='all',areas=['frontend','marketing'],home=Path(d)/'secret')
            self.assertFalse([op for op in second['operations'] if op['action'] in ('copy','create','update')])
            self.assertNotIn('key', (project/'.ai-workbench/CAPABILITY_PLAN.md').read_text().lower())

    def test_auto_areas_cli_and_goal(self):
        with tempfile.TemporaryDirectory() as d:
            project=Path(d)/'web-project'
            self.assertEqual(main(['--home',str(Path(d)/'private'),'init',str(project),
                                   '--create','--goal','Build a React frontend dashboard',
                                   '--auto-areas','--agent','codex']),0)
            self.assertIn('frontend',choose_profiles(project))
            self.assertEqual(main(['recommend',str(project),'--area','marketing','--json']),0)


class AreaBenchmarkTests(unittest.TestCase):
    def test_synthetic_labeled_scenarios_hit_rate_and_advisor(self):
        scenarios = [
            ('saas', {'README.md': 'FastAPI backend and React frontend with Playwright tests'},
             ['src/App.tsx', 'api/main.py', 'playwright.config.ts'],
             'Build a SaaS dashboard', {'frontend', 'backend'}, set()),
            ('quant', {'README.md': 'Quantitative finance backtest engine with Sharpe ratio and drawdown'},
             ['strategies/momentum.py'], 'Run backtest', {'quant-finance'}, {'game-port'}),
            ('android-re', {'README.md': 'Android APK reverse engineering with jadx and frida'},
             ['AndroidManifest.xml'], 'Analyze APK', {'reverse-engineering', 'mobile-app'}, {'quant-finance'}),
            ('empty', {}, [], '', set(), {'frontend', 'backend', 'game-port', 'security'}),
        ]
        hits = total_expected = false_positives = 0
        with tempfile.TemporaryDirectory() as d:
            for name, files, tree_files, goal, expected, forbidden in scenarios:
                repo = Path(d) / name
                repo.mkdir()
                for rel, content in files.items():
                    (repo / rel).write_text(content, encoding='utf-8')
                for rel in tree_files:
                    p = repo / rel
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text('', encoding='utf-8')
                rec = recommend(repo, goal=goal)
                got = set(rec['areas'])
                hits += len(expected & got)
                total_expected += len(expected)
                false_positives += len(forbidden & got)
                if not expected:
                    self.assertEqual(got, set())

            self.assertGreaterEqual(hits / total_expected, 0.85)
            self.assertEqual(false_positives, 0)

            overlap_rec = recommend(Path(d) / 'saas', selected=['frontend', 'qa-testing'])
            self.assertTrue(overlap_rec['skill_advisor']['overlaps'])


if __name__=='__main__':
    unittest.main()
