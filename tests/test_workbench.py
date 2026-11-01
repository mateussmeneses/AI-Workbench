import json
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from aiwh.workbench import (bootstrap, choose_profiles, inspect_project, global_integration, managed_text,
                            registry, resume, skill_paths)
from aiwh.cli import main


class PackageVerificationTests(unittest.TestCase):
    def setUp(self):
        self.source = Path(__file__).resolve().parents[1]
        self.verifier = runpy.run_path(str(self.source / 'scripts/Verify-Package.py'))

    def test_rejects_unsafe_and_private_archive_paths(self):
        for name in ('../catalog.json', 'C:/catalog.json', 'root\\catalog.json',
                     'root/.ai-workbench/CONTEXT.md', 'root/.git/config'):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    self.verifier['check_member'](name)

    def test_rejects_missing_wheel_assets(self):
        with tempfile.TemporaryDirectory() as temporary:
            wheel = Path(temporary) / 'example.whl'
            with zipfile.ZipFile(wheel, 'w'):
                pass
            with self.assertRaisesRegex(ValueError, 'Missing or stale wheel payload'):
                self.verifier['inspect_distributions'](wheel, None, self.source)

    def test_rejects_unexpected_wheel_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            wheel = Path(temporary) / 'example.whl'
            with zipfile.ZipFile(wheel, 'w') as archive:
                archive.writestr('catalog.json', '{}')
            with self.assertRaisesRegex(ValueError, 'Unexpected wheel payload: catalog.json'):
                self.verifier['inspect_distributions'](wheel, None, self.source)


class RegistryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for directory in ('profiles', 'skills', 'agents', 'mcp'):
            (self.root / directory).mkdir()
        self.skill = self.root / 'skills' / 'wb-example' / 'SKILL.md'
        self.skill.parent.mkdir()
        self.skill.write_text('---\nname: wb-example\ndescription: Example workflow\n---\n# Example\n',
                              encoding='utf-8')
        self.profile = self.root / 'profiles' / 'core.json'
        self.profile.write_text(json.dumps({'description': 'Core', 'skills': ['wb-example']}),
                                encoding='utf-8')
        (self.root / 'mcp' / 'catalog.json').write_text('{}', encoding='utf-8')
        patcher = patch('aiwh.workbench.CAPABILITIES', self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_skill_requires_description(self):
        self.skill.write_text('---\nname: wb-example\n---\n# Example\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'SKILL.md.*description'):
            registry()

    def test_valid_metadata_and_optional_version(self):
        self.assertIn('wb-example', registry()['skills'])
        self.skill.write_text('---\nname: wb-example\ndescription: |\n  Multi-line workflow\n'
                              'version: 1.0.0\n---\n# Example\n', encoding='utf-8')
        self.assertIn('wb-example', registry()['skills'])

    def test_invalid_skill_metadata(self):
        cases = (
            ('# No header\n', 'opening frontmatter'),
            ('---\nname: wb-example\n', 'closing frontmatter'),
            ('---\n- name\n---\nBody\n', 'mapping'),
            ('---\nname: wb-example\ndescription: [broken\n---\nBody\n', 'Invalid skill'),
            ('---\nname: wb-other\ndescription: Example\n---\nBody\n', 'match skill directory'),
            ('---\nname: wb-example\ndescription: true\n---\nBody\n', 'description'),
            ('---\nname: wb-example\ndescription: ""\n---\nBody\n', 'description'),
            ('---\nname: wb-example\nname: wb-example\ndescription: Example\n---\nBody\n',
             'duplicate metadata field: name'),
            ('---\nname: wb-example\ndescription: Example\nversion: 1\n---\nBody\n', 'version'),
            ('---\nname: wb-example\ndescription: Example\n---\n', 'body'),
            ('---\nname: wb-example\ndescription: !!python/name:os.system\n---\nBody\n',
             'Invalid skill'),
        )
        for content, message in cases:
            with self.subTest(message=message, content=content):
                self.skill.write_text(content, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, message) as caught:
                    registry()
                self.assertIn(str(self.skill), str(caught.exception))

    def test_duplicate_skill_directory_names(self):
        duplicate = self.root / 'skills' / 'another-area' / 'wb-example' / 'SKILL.md'
        duplicate.parent.mkdir(parents=True)
        duplicate.write_text(self.skill.read_text(encoding='utf-8'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Duplicate skill name: wb-example') as caught:
            registry()
        self.assertIn(str(self.skill.parent), str(caught.exception))
        self.assertIn(str(duplicate.parent), str(caught.exception))

    def test_invalid_profile_json_and_fields(self):
        cases = (
            ('{', 'Invalid registry JSON'),
            ('[]', 'JSON object'),
            ('{"description":"Core","description":"Duplicate"}', 'duplicate JSON field'),
            ('{}', 'description'),
            ('{"description":"Core","skills":"wb-example"}', 'skills must be a list'),
            ('{"description":"Core","skills":[1]}', 'skills must be a list'),
            ('{"description":"Core","skills":["wb-example","wb-example"]}', 'duplicate IDs'),
        )
        for content, message in cases:
            with self.subTest(content=content):
                self.profile.write_text(content, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, message) as caught:
                    registry()
                self.assertIn(str(self.profile), str(caught.exception))

    def test_missing_profile_references(self):
        for field, label in (('skills', 'skill'), ('agents', 'agent'), ('mcps', 'MCP')):
            with self.subTest(field=field):
                self.profile.write_text(json.dumps({'description': 'Core', field: ['missing']}),
                                        encoding='utf-8')
                with self.assertRaisesRegex(ValueError, f'missing {label} missing') as caught:
                    registry()
                self.assertIn(str(self.profile), str(caught.exception))

    def test_missing_capability_directory(self):
        (self.root / 'agents').rmdir()
        with self.assertRaisesRegex(ValueError, 'Missing capability directory'):
            registry()

    def test_missing_skill_file(self):
        self.skill.unlink()
        with self.assertRaisesRegex(ValueError, 'missing skill wb-example'):
            registry()

    def test_empty_role_template(self):
        role = self.root / 'agents' / 'example.md'
        role.write_text('', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'example.md.*must not be empty'):
            registry()

    def test_mcp_catalog_validation(self):
        path = self.root / 'mcp' / 'catalog.json'
        cases = (
            ('[]', 'JSON object'),
            ('{"example":{},"example":{}}', 'duplicate JSON field'),
            ('{"example":[]}', 'expected an object'),
            ('{"example":{"enabledByDefault":true}}', 'enabledByDefault must be false'),
            ('{"example":{"enabledByDefault":0}}', 'enabledByDefault must be false'),
        )
        for content, message in cases:
            with self.subTest(content=content):
                path.write_text(content, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, message) as caught:
                    registry()
                self.assertIn(str(path), str(caught.exception))
        path.unlink()
        with self.assertRaisesRegex(ValueError, 'catalog.json'):
            registry()


class BootstrapTests(unittest.TestCase):
    def test_bundled_assets_outside_checkout(self):
        source = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            installed = Path(temporary) / 'site-packages'
            package = installed / 'aiwh'
            shutil.copytree(source / 'src' / 'aiwh', package, ignore=shutil.ignore_patterns('__pycache__'))
            shutil.copytree(source / 'capabilities', package / 'capabilities')
            script = ('import sys; from pathlib import Path; '
                      'sys.path.insert(0, sys.argv[1]); '
                      'from aiwh.workbench import CAPABILITIES, registry; '
                      'from aiwh.areas import validate_catalog; '
                      'assert CAPABILITIES == Path(sys.argv[1]) / "aiwh" / "capabilities"; '
                      'assert len(registry()["skills"]) == 45; '
                      'assert validate_catalog()["areas"] == 26')
            result = subprocess.run([sys.executable, '-I', '-c', script, str(installed)],
                                    cwd=temporary, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

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
            guide = (project / 'AI-WORKBENCH.md').read_text(encoding='utf-8')
            self.assertIn('`aiwh resume .`', guide)
            self.assertNotIn('aiwh resume --project', guide)
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
