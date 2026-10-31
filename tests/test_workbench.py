import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from aiwh.workbench import (bootstrap, choose_profiles, inspect_project, global_integration, managed_text,
                            registry, resume, skill_paths)
from aiwh.cli import main


class BootstrapTests(unittest.TestCase):
    def test_registry_integrity(self):
        r = registry()
        self.assertEqual(len(r['profiles']), 28)
        self.assertEqual(len(r['skills']), 45)
        self.assertEqual(len(r['agents']), 20)
        self.assertIn('ai-agents', r['profiles'])

    def test_invalid_profile_fails(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, 'Unknown profiles'):
                choose_profiles(Path(d), ['made-up'])

    def test_native_paths(self):
        self.assertEqual(skill_paths('codex'), ('.agents/skills',))
        self.assertEqual(skill_paths('antigravity'), ('.agents/skills',))
        self.assertEqual(skill_paths('hermes'), ('.agents/skills',))
        self.assertEqual(skill_paths('claude'), ('.claude/skills',))
        self.assertEqual(skill_paths('openclaude'), ('.openclaude/skills',))
        self.assertEqual(len(skill_paths('all')), 3)

    def test_dry_run_has_zero_disk_writes_for_missing_project(self):
        with tempfile.TemporaryDirectory() as d:
            project = Path(d) / 'future-project'
            result = bootstrap(project, agent='all', create=True, dry_run=True)
            self.assertFalse(project.exists())
            self.assertTrue(result['operations'])

    def test_preserves_custom_agents_and_can_run_twice(self):
        with tempfile.TemporaryDirectory() as d:
            project = Path(d) / 'qa-dotnet'
            project.mkdir()
            (project / 'App.csproj').write_text('<Project/>', encoding='utf-8')
            (project / 'AGENTS.md').write_text('# User rules\n\nKeep tests green.\n', encoding='utf-8')
            first = bootstrap(project, agent='all', home=Path(d)/'private-catalog')
            self.assertIn('qa-dotnet', first['profiles'])
            self.assertTrue((project / '.agents/skills/wb-api-contract-qa/SKILL.md').exists())
            self.assertTrue((project / '.claude/skills/wb-api-contract-qa/SKILL.md').exists())
            self.assertTrue((project / '.openclaude/skills/wb-api-contract-qa/SKILL.md').exists())
            self.assertTrue((project / 'CLAUDE.md').exists())
            content = (project / 'AGENTS.md').read_text(encoding='utf-8')
            self.assertIn('Keep tests green.', content)
            self.assertEqual(content.count('<!-- AIWH:BEGIN -->'), 1)
            again = bootstrap(project, agent='all', home=Path(d)/'private-catalog')
            self.assertFalse([op for op in again['operations'] if op['action'] in ('create','update','copy')])
            self.assertIn('.ai-workbench/', (project / '.gitignore').read_text(encoding='utf-8'))
            self.assertEqual((project / 'AGENTS.md').read_text(encoding='utf-8'), content)

    def test_never_overwrites_modified_skill(self):
        with tempfile.TemporaryDirectory() as d:
            project = Path(d)
            first = bootstrap(project, agent='codex', profiles=['game-port'], home=Path(d)/'private')
            skill = project / '.agents/skills/wb-vulkan-frame-pacing/SKILL.md'
            skill.write_text('customized locally', encoding='utf-8')
            result = bootstrap(project, agent='codex', profiles=['game-port'], home=Path(d)/'private')
            self.assertEqual(skill.read_text(encoding='utf-8'), 'customized locally')
            self.assertTrue(any(x['action']=='skip-conflict' for x in result['operations']))

    def test_opt_in_global_activation_is_reversible(self):
        with tempfile.TemporaryDirectory() as d:
            home=Path(d)
            global_file=home/'.codex/AGENTS.md'
            global_file.parent.mkdir()
            global_file.write_text('# Personal preference\nKeep answers concise.\n',encoding='utf-8')
            preview=global_integration('codex',user_home=home)
            self.assertTrue(preview['changed'])
            self.assertEqual(global_file.read_text(encoding='utf-8'),'# Personal preference\nKeep answers concise.\n')
            global_integration('codex',user_home=home,dry_run=False)
            content=global_file.read_text(encoding='utf-8')
            self.assertIn('Keep answers concise.',content)
            self.assertEqual(content.count('<!-- AIWH:BEGIN -->'),1)
            self.assertFalse(global_integration('codex',user_home=home,dry_run=False)['changed'])
            global_integration('codex',user_home=home,dry_run=False,disable=True)
            self.assertEqual(global_file.read_text(encoding='utf-8'),'# Personal preference\nKeep answers concise.\n')

    def test_unbalanced_managed_sections_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            managed_text('<!-- AIWH:BEGIN -->', 'hello')

    def test_projects_are_independent(self):
        with tempfile.TemporaryDirectory() as d:
            x, y = Path(d)/'game-port', Path(d)/'browser-extension'
            x.mkdir(); y.mkdir()
            (x/'renderer.vcxproj').write_text('', encoding='utf-8')
            (y/'manifest.json').write_text('{}', encoding='utf-8')
            game = bootstrap(x, agent='codex', profiles=['game-port'], home=Path(d)/'private')
            browser = bootstrap(y, agent='codex', profiles=['browser-extension'], home=Path(d)/'private')
            self.assertIn('wb-shader-cache-triage', game['skills'])
            self.assertNotIn('wb-shader-cache-triage', browser['skills'])
            self.assertIn('wb-extension-mv3', browser['skills'])
            self.assertNotIn('wb-extension-mv3', game['skills'])


class ContinuityTests(unittest.TestCase):
    def test_real_git_state_and_documented_todos_only(self):
        with tempfile.TemporaryDirectory() as d:
            project = Path(d)
            subprocess.run(['git','init','-q',str(project)], check=True)
            subprocess.run(['git','-C',str(project),'config','user.email','test@example.org'],check=True)
            subprocess.run(['git','-C',str(project),'config','user.name','Test Runner'],check=True)
            (project/'README.md').write_text('Synthetic test repository',encoding='utf-8')
            (project/'docs').mkdir()
            (project/'docs/ROADMAP.md').write_text('- [ ] Implement feature A\n- [x] completed B\n',encoding='utf-8')
            subprocess.run(['git','-C',str(project),'add','.'],check=True)
            subprocess.run(['git','-C',str(project),'commit','-qm','Initial test baseline'],check=True)
            state=inspect_project(project)
            self.assertIn('Initial test baseline', ' '.join(state['recent_commits']))
            self.assertEqual(len(state['pending_documented']),1)
            self.assertEqual(state['working_tree_changes'],[])
            preview=resume(project,agent='claude',dry_run=True)
            self.assertFalse((project/'.ai-workbench').exists())
            self.assertIn('Implement feature A',preview['markdown'])
            written=resume(project,agent='claude')
            self.assertTrue(written['written'])
            self.assertTrue((project/'.ai-workbench/CONTEXT.md').exists())
            self.assertEqual(json.loads((project/'.ai-workbench/state.json').read_text())['branch'],state['branch'])

    def test_cli_init_and_resume(self):
        with tempfile.TemporaryDirectory() as d:
            project = Path(d)/'new-project'
            self.assertEqual(main(['--home',str(Path(d)/'private'),'init',str(project),'--create','--agent','codex','--profile','devops']),0)
            self.assertTrue((project/'AGENTS.md').exists())
            self.assertEqual(choose_profiles(project), ['core', 'devops'])
            self.assertEqual(main(['--home',str(Path(d)/'private'),'resume',str(project)]),0)


if __name__ == '__main__':
    unittest.main()
