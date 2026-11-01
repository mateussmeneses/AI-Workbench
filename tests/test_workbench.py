import json
import runpy
import shutil
import subprocess
import sys
import tempfile
import hashlib
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from aiwh.workbench import (ManagedFilePlan, ManagedFileTransaction, bootstrap, choose_profiles, inspect_project,
                            global_integration, managed_text, registry, remove_managed,
                            resume, skill_paths)
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


class ManagedManifestTests(unittest.TestCase):
    def test_preview_and_apply_record_versioned_content_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / 'project'
            project.mkdir()
            private = root / 'private'
            manifest_path = project / '.ai-workbench' / 'managed-files.json'

            preview = bootstrap(project, agent='codex', profiles=['devops'],
                                home=private, dry_run=True)
            plan = preview['managed_files']
            self.assertTrue(plan['added'])
            self.assertEqual(plan['manifest'], 'create')
            self.assertFalse(manifest_path.exists())

            applied = bootstrap(project, agent='codex', profiles=['devops'], home=private)
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            self.assertEqual(manifest['schema_version'], 1)
            self.assertEqual(set(manifest['files']), set(plan['added']))
            for relative, expected_hash in manifest['files'].items():
                content = (project / relative).read_bytes()
                self.assertEqual(hashlib.sha256(content).hexdigest(), expected_hash)
            self.assertEqual(applied['managed_files']['added'], plan['added'])

            next_preview = bootstrap(project, agent='codex', profiles=['devops'],
                                     home=private, dry_run=True)
            self.assertEqual(next_preview['managed_files']['manifest'], 'unchanged')
            self.assertEqual(next_preview['managed_files']['unchanged'], plan['added'])
            self.assertFalse(next_preview['managed_files']['added'])
            self.assertFalse(next_preview['managed_files']['changed'])
            self.assertFalse(next_preview['managed_files']['conflicting'])

    def test_modified_managed_file_is_previewed_as_conflict_and_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / 'project'
            project.mkdir()
            private = root / 'private'
            bootstrap(project, agent='codex', profiles=['devops'], home=private)
            managed_file = project / '.agents/skills/wb-project-bootstrap/SKILL.md'
            managed_file.write_text('user customization', encoding='utf-8')

            preview = bootstrap(project, agent='codex', profiles=['devops'],
                                home=private, dry_run=True)

            self.assertIn('.agents/skills/wb-project-bootstrap/SKILL.md',
                          preview['managed_files']['conflicting'])
            self.assertEqual(managed_file.read_text(encoding='utf-8'), 'user customization')

    def test_modified_previously_managed_file_is_conflict_even_when_not_replanned(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / 'project'
            project.mkdir()
            private = root / 'private'
            bootstrap(project, agent='codex', profiles=['devops'], home=private)
            ignore = project / '.gitignore'
            ignore.write_text(ignore.read_text(encoding='utf-8') + '# User change\n', encoding='utf-8')

            preview = bootstrap(project, agent='codex', profiles=['devops'],
                                home=private, dry_run=True)

            self.assertIn('.gitignore', preview['managed_files']['conflicting'])
            self.assertIn('# User change', ignore.read_text(encoding='utf-8'))

    def test_changed_managed_file_is_previewed_and_updated(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / 'project'
            project.mkdir()
            private = root / 'private'
            bootstrap(project, agent='codex', profiles=['devops'], home=private)
            old_guide = (project / 'AI-WORKBENCH.md').read_bytes()

            preview = bootstrap(project, agent='codex', profiles=['frontend'],
                                home=private, dry_run=True)

            self.assertIn('AI-WORKBENCH.md', preview['managed_files']['changed'])
            self.assertEqual((project / 'AI-WORKBENCH.md').read_bytes(), old_guide)
            applied = bootstrap(project, agent='codex', profiles=['frontend'], home=private)
            self.assertEqual(applied['managed_files']['changed'], preview['managed_files']['changed'])
            self.assertIn('frontend', (project / 'AI-WORKBENCH.md').read_text(encoding='utf-8'))

    def test_invalid_manifest_fails_closed_before_project_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / 'project'
            project.mkdir()
            private = Path(temporary) / 'private'
            metadata = project / '.ai-workbench'
            metadata.mkdir()
            (metadata / 'managed-files.json').write_text(
                '{"schema_version": 99, "files": {}}', encoding='utf-8')

            with self.assertRaisesRegex(ValueError, 'Invalid managed-file manifest'):
                bootstrap(project, agent='codex', profiles=['devops'], home=private)

            self.assertFalse((project / 'AI-WORKBENCH.md').exists())

    def test_unmanifested_generated_file_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / 'project'
            project.mkdir()
            private = root / 'private'
            guide = project / 'AI-WORKBENCH.md'
            guide.write_text('user-owned guide', encoding='utf-8')

            result = bootstrap(project, agent='codex', profiles=['devops'],
                               home=private, dry_run=False)

            self.assertEqual(guide.read_text(encoding='utf-8'), 'user-owned guide')
            self.assertIn('AI-WORKBENCH.md', result['managed_files']['conflicting'])
            manifest = json.loads((project / '.ai-workbench/managed-files.json').read_text(encoding='utf-8'))
            self.assertNotIn('AI-WORKBENCH.md', manifest['files'])

    def test_remove_preview_and_apply_preserve_shared_user_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / 'project'
            project.mkdir()
            private = root / 'private'
            agents = project / 'AGENTS.md'
            ignore = project / '.gitignore'
            agents.write_text('# User rules\n\nPreserve these.\n', encoding='utf-8')
            ignore.write_text('# User ignores\n*.cache\n', encoding='utf-8')
            bootstrap(project, agent='claude', profiles=['devops'], home=private)

            preview = remove_managed(project, dry_run=True)

            self.assertTrue(preview['removed'])
            self.assertEqual(preview['manifest'], 'update')
            self.assertIn('AGENTS.md', preview['updated'])
            self.assertIn('.gitignore', preview['updated'])
            self.assertTrue((project / 'AI-WORKBENCH.md').is_file())
            self.assertIn('AIWH:BEGIN', agents.read_text(encoding='utf-8'))

            applied = remove_managed(project)

            self.assertEqual(applied['removed'], preview['removed'])
            self.assertEqual(applied['updated'], preview['updated'])
            self.assertEqual(applied['conflicting'], preview['conflicting'])
            self.assertFalse((project / 'AI-WORKBENCH.md').exists())
            self.assertTrue((project / '.agents/skills/wb-project-bootstrap/SKILL.md').is_file() is False)
            self.assertIn('# User rules', agents.read_text(encoding='utf-8'))
            self.assertNotIn('AIWH:BEGIN', agents.read_text(encoding='utf-8'))
            self.assertIn('*.cache', ignore.read_text(encoding='utf-8'))
            self.assertNotIn('.ai-workbench/', ignore.read_text(encoding='utf-8'))
            manifest = json.loads((project / '.ai-workbench/managed-files.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['files'], {})

    def test_remove_refuses_modified_files_and_keeps_them_in_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / 'project'
            project.mkdir()
            private = root / 'private'
            bootstrap(project, agent='codex', profiles=['devops'], home=private)
            skill = project / '.agents/skills/wb-project-bootstrap/SKILL.md'
            skill.write_text('user customization', encoding='utf-8')
            untracked = project / 'user-owned.txt'
            untracked.write_text('leave me alone', encoding='utf-8')

            preview = remove_managed(project, dry_run=True)
            self.assertIn('.agents/skills/wb-project-bootstrap/SKILL.md', preview['conflicting'])
            self.assertEqual(skill.read_text(encoding='utf-8'), 'user customization')
            self.assertTrue(untracked.is_file())

            result = remove_managed(project)
            self.assertIn('.agents/skills/wb-project-bootstrap/SKILL.md', result['conflicting'])
            self.assertEqual(skill.read_text(encoding='utf-8'), 'user customization')
            self.assertEqual(untracked.read_text(encoding='utf-8'), 'leave me alone')
            manifest = json.loads((project / '.ai-workbench/managed-files.json').read_text(encoding='utf-8'))
            self.assertEqual(list(manifest['files']), ['.agents/skills/wb-project-bootstrap/SKILL.md'])

    def test_remove_without_manifest_does_not_touch_project_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            user_file = project / 'AGENTS.md'
            user_file.write_text('user-owned', encoding='utf-8')

            result = remove_managed(project)

            self.assertEqual(result['manifest'], 'missing')
            self.assertEqual(user_file.read_text(encoding='utf-8'), 'user-owned')

    def test_managed_remove_cli_supports_dry_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / 'project'
            private = root / 'private'
            bootstrap(project, agent='codex', profiles=['devops'], home=private, create=True)

            self.assertEqual(main(['--home', str(private), 'managed', 'remove', str(project), '--dry-run']), 0)
            self.assertTrue((project / 'AI-WORKBENCH.md').exists())


class ManagedTransactionTests(unittest.TestCase):
    def test_interrupted_init_rolls_back_before_next_operation(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / 'projeto unicode Ω with spaces'
            project.mkdir()
            private = Path(temporary) / 'private'
            bootstrap(project, agent='codex', profiles=['devops'], home=private)
            guide = project / 'AI-WORKBENCH.md'
            original_guide = guide.read_bytes()
            manifest_path = project / '.ai-workbench/managed-files.json'
            original_manifest = manifest_path.read_bytes()
            original_write = ManagedFilePlan._transactional_write
            writes = 0

            def fail_after_first_write(plan, path, content):
                nonlocal writes
                original_write(plan, path, content)
                writes += 1
                if writes == 1:
                    raise OSError('injected partial write')

            with patch.object(ManagedFilePlan, '_transactional_write', fail_after_first_write):
                with self.assertRaisesRegex(OSError, 'injected partial write'):
                    bootstrap(project, agent='codex', profiles=['frontend'], home=private)

            transaction_dir = project / '.ai-workbench/managed-files.transaction'
            self.assertTrue(transaction_dir.is_dir())
            with self.assertRaisesRegex(ValueError, 'rerun without --dry-run'):
                bootstrap(project, agent='codex', profiles=['devops'], home=private, dry_run=True)
            self.assertTrue(transaction_dir.is_dir())
            original_restore = ManagedFileTransaction._restore_entry
            recoveries = 0

            def fail_after_first_restore(transaction, entry):
                nonlocal recoveries
                original_restore(transaction, entry)
                recoveries += 1
                if recoveries == 1:
                    raise OSError('injected recovery interruption')

            with patch.object(ManagedFileTransaction, '_restore_entry', fail_after_first_restore):
                with self.assertRaisesRegex(OSError, 'injected recovery interruption'):
                    bootstrap(project, agent='codex', profiles=['devops'], home=private)

            recovered = bootstrap(project, agent='codex', profiles=['devops'], home=private)

            self.assertEqual(guide.read_bytes(), original_guide)
            self.assertEqual(manifest_path.read_bytes(), original_manifest)
            self.assertFalse((project / '.ai-workbench/managed-files.transaction').exists())
            self.assertFalse(recovered['managed_files']['added'])
            self.assertFalse(recovered['managed_files']['changed'])

    def test_interrupted_remove_rolls_back_before_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / 'project'
            project.mkdir()
            private = Path(temporary) / 'private'
            bootstrap(project, agent='codex', profiles=['devops'], home=private)
            guide = project / 'AI-WORKBENCH.md'
            original_guide = guide.read_bytes()
            first_removed = project / '.agents/skills/wb-capability-curation/SKILL.md'
            original_remove = ManagedFilePlan._transactional_remove
            removals = 0

            def fail_after_first_remove(plan, path):
                nonlocal removals
                original_remove(plan, path)
                removals += 1
                if removals == 1:
                    raise OSError('injected partial removal')

            with patch.object(ManagedFilePlan, '_transactional_remove', fail_after_first_remove):
                with self.assertRaisesRegex(OSError, 'injected partial removal'):
                    remove_managed(project)

            self.assertFalse(first_removed.exists())
            recovered = bootstrap(project, agent='codex', profiles=['devops'], home=private)
            self.assertTrue(first_removed.is_file())
            self.assertEqual(guide.read_bytes(), original_guide)
            self.assertFalse(recovered['managed_files']['added'])
            result = remove_managed(project)

            self.assertFalse(guide.exists())
            self.assertFalse((project / '.ai-workbench/managed-files.transaction').exists())
            self.assertIn('AI-WORKBENCH.md', result['removed'])


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
            private = Path(d) / 'private'
            result = bootstrap(project, agent='all', create=True, home=private, dry_run=True)
            self.assertFalse(project.exists())
            self.assertTrue(result['operations'])
            applied = bootstrap(project, agent='all', create=True, home=private)
            self.assertEqual(result['managed_files'], applied['managed_files'])
            self.assertTrue(any(path.endswith('.ai-workbench/RESOURCES.md')
                                for path in result['managed_files']['added']))

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
    def test_resume_migrates_legacy_state_and_preserves_private_records(self):
        with tempfile.TemporaryDirectory() as d:
            project = Path(d)
            (project / 'docs').mkdir()
            (project / 'docs/ROADMAP.md').write_text(
                '- [ ] RM-007 Keep task identity\n', encoding='utf-8')
            state_path = project / '.ai-workbench/state.json'
            legacy_state = resume(project)['data']
            task = {
                'id': 'RM-007', 'title': 'Keep task identity',
                'source': 'docs/ROADMAP.md', 'status': 'blocked',
                'blockers': ['waiting for approval'], 'risks': [],
                'milestone_outcomes': [],
            }
            decision = {
                'id': 'decision-001', 'text': 'Keep state local',
                'approved': True, 'rationale': 'Privacy',
            }
            resource = {
                'id': 'repo:example/tool', 'selection': 'rejected',
                'rationale': 'Not relevant',
            }
            legacy_state.update(tasks=[task], decisions=[decision], resources=[resource])
            state_path.write_text(json.dumps(legacy_state), encoding='utf-8')

            resume(project)
            migrated = json.loads(state_path.read_text(encoding='utf-8'))
            self.assertEqual(migrated['schema_version'], 2)
            self.assertIn('branch', migrated['observed'])
            self.assertEqual(migrated['tasks'], [task])
            self.assertEqual(migrated['decisions'], [decision])
            self.assertEqual(migrated['resources'], [resource])
            self.assertEqual(migrated['legacy_observation']['generated_at'], legacy_state['generated_at'])
            self.assertNotIn('usefulness', migrated['resources'][0])

            resume(project)
            repeated = json.loads(state_path.read_text(encoding='utf-8'))
            self.assertEqual(repeated['tasks'][0]['id'], 'RM-007')
            self.assertEqual(repeated['tasks'][0]['status'], 'blocked')

    def test_resume_migrates_schema_v1_into_bounded_history(self):
        with tempfile.TemporaryDirectory() as d:
            project = Path(d)
            folder = project / '.ai-workbench'
            folder.mkdir()
            state_path = folder / 'state.json'
            legacy_observation = {'project': str(project), 'branch': 'old-branch'}
            decision = {
                'id': 'decision-v1', 'text': 'Keep existing decision',
                'approved': True, 'rationale': 'Compatibility',
            }
            version_one = {
                'schema_version': 1, 'updated_at': '2026-10-31T12:00:00+00:00',
                'observed': legacy_observation, 'legacy_observation': legacy_observation,
                'tasks': [], 'decisions': [decision], 'resources': [],
            }
            state_path.write_text(json.dumps(version_one), encoding='utf-8')

            resume(project)

            migrated = json.loads(state_path.read_text(encoding='utf-8'))
            self.assertEqual(migrated['schema_version'], 2)
            self.assertEqual(migrated['legacy_observation'], legacy_observation)
            self.assertEqual(migrated['decisions'], [decision])
            self.assertEqual(len(migrated['history']), 1)
            self.assertTrue(migrated['latest_delta']['baseline'])

    def test_resume_compares_sessions_and_bounds_snapshot_history(self):
        with tempfile.TemporaryDirectory() as d:
            project = Path(d)
            subprocess.run(['git', 'init', '-q', str(project)], check=True)
            subprocess.run(['git', '-C', str(project), 'config', 'user.email', 'test@example.org'], check=True)
            subprocess.run(['git', '-C', str(project), 'config', 'user.name', 'Test Runner'], check=True)
            (project / 'README.md').write_text('baseline\n', encoding='utf-8')
            (project / 'docs').mkdir()
            (project / 'docs/ROADMAP.md').write_text('- [ ] RM-101 Example task\n', encoding='utf-8')
            subprocess.run(['git', '-C', str(project), 'add', '.'], check=True)
            subprocess.run(['git', '-C', str(project), 'commit', '-qm', 'Baseline'], check=True)

            resume(project)
            state_path = project / '.ai-workbench/state.json'
            state = json.loads(state_path.read_text(encoding='utf-8'))
            state['tasks'][0]['blockers'] = ['waiting for review']
            state['tasks'][0]['status'] = 'blocked'
            state['decisions'] = [{
                'id': 'decision-101', 'text': 'Keep the change local',
                'approved': True, 'rationale': 'Privacy',
            }]
            state['resources'] = [{
                'id': 'repo:example/tool', 'selection': 'selected',
                'rationale': 'Matches the task',
            }]
            state_path.write_text(json.dumps(state), encoding='utf-8')
            (project / 'README.md').write_text('observed change\n', encoding='utf-8')

            second = resume(project)
            second_state = json.loads(state_path.read_text(encoding='utf-8'))
            delta = second_state['latest_delta']
            self.assertEqual(second_state['schema_version'], 2)
            self.assertEqual(len(second_state['history']), 2)
            self.assertIn('README.md', delta['observed']['files_added'])
            self.assertEqual(delta['tasks']['blockers_added'], [
                {'task_id': 'RM-101', 'blocker': 'waiting for review'},
            ])
            self.assertEqual(delta['tasks']['status_changed'], [
                {'task_id': 'RM-101', 'from': 'pending', 'to': 'blocked'},
            ])
            self.assertEqual(delta['decisions']['added'], ['decision-101'])
            self.assertEqual(delta['resources']['added'], ['repo:example/tool'])
            self.assertEqual(delta['resources']['unknown_outcomes'], ['repo:example/tool'])
            self.assertIn('Unknown resource outcomes', second['markdown'])

            second_state['tasks'][0]['blockers'] = []
            second_state['tasks'][0]['status'] = 'in_progress'
            second_state['resources'][0]['usefulness'] = 'useful'
            state_path.write_text(json.dumps(second_state), encoding='utf-8')
            subprocess.run(['git', '-C', str(project), 'add', 'README.md'], check=True)
            subprocess.run(['git', '-C', str(project), 'commit', '-qm', 'Record observed change'], check=True)
            resume(project)
            third_state = json.loads(state_path.read_text(encoding='utf-8'))
            third_delta = third_state['latest_delta']
            self.assertIn('README.md', third_delta['observed']['files_resolved'])
            self.assertEqual(third_delta['tasks']['blockers_resolved'], [
                {'task_id': 'RM-101', 'blocker': 'waiting for review'},
            ])
            self.assertEqual(third_delta['tasks']['status_changed'], [
                {'task_id': 'RM-101', 'from': 'blocked', 'to': 'in_progress'},
            ])
            self.assertEqual(third_delta['resources']['changed'], ['repo:example/tool'])
            self.assertEqual(third_delta['resources']['usefulness_changed'], ['repo:example/tool'])
            self.assertEqual(third_delta['resources']['unknown_outcomes'], [])

            for _ in range(10):
                resume(project)
            before_preview = state_path.read_bytes()
            preview = resume(project, dry_run=True)
            self.assertFalse(preview['written'])
            self.assertEqual(state_path.read_bytes(), before_preview)
            self.assertEqual(len(json.loads(before_preview)['history']), 10)

    def test_resume_refuses_future_state_schema_without_overwriting(self):
        with tempfile.TemporaryDirectory() as d:
            project = Path(d)
            folder = project / '.ai-workbench'
            folder.mkdir()
            state_path = folder / 'state.json'
            future_state = {'schema_version': 999, 'private': 'preserve me'}
            state_path.write_text(json.dumps(future_state), encoding='utf-8')

            with self.assertRaisesRegex(ValueError, 'Unsupported state schema version'):
                resume(project)

            self.assertEqual(json.loads(state_path.read_text(encoding='utf-8')), future_state)
            self.assertFalse((folder / 'CONTEXT.md').exists())

    def test_resume_refuses_corrupt_state_without_changing_existing_files(self):
        invalid_states = ('{', json.dumps({
            'schema_version': 1, 'updated_at': 'now', 'observed': [],
            'tasks': [], 'decisions': [], 'resources': [],
        }), json.dumps({'schema_version': None}))
        for invalid_state in invalid_states:
            with self.subTest(invalid_state=invalid_state), tempfile.TemporaryDirectory() as d:
                project = Path(d)
                folder = project / '.ai-workbench'
                folder.mkdir()
                state_path = folder / 'state.json'
                context_path = folder / 'CONTEXT.md'
                state_path.write_text(invalid_state, encoding='utf-8')
                context_path.write_text('existing handoff', encoding='utf-8')

                with self.assertRaises(ValueError):
                    resume(project)

                self.assertEqual(state_path.read_text(encoding='utf-8'), invalid_state)
                self.assertEqual(context_path.read_text(encoding='utf-8'), 'existing handoff')

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
            self.assertEqual(json.loads((project/'.ai-workbench/state.json').read_text())['observed']['branch'],state['branch'])

    def test_cli_init_and_resume(self):
        with tempfile.TemporaryDirectory() as d:
            project = Path(d)/'new-project'
            self.assertEqual(main(['--home',str(Path(d)/'private'),'init',str(project),'--create','--agent','codex','--profile','devops']),0)
            self.assertTrue((project/'AGENTS.md').exists())
            self.assertEqual(choose_profiles(project), ['core', 'devops'])
            self.assertEqual(main(['--home',str(Path(d)/'private'),'resume',str(project)]),0)


if __name__ == '__main__':
    unittest.main()
