"""Inspect local distributions and smoke-test an offline temporary installation."""
import argparse
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import venv
import zipfile
from pathlib import Path, PurePosixPath


def expected_payload(source):
    files = {f'aiwh/{path.name}': path for path in (source / 'src/aiwh').glob('*.py')}
    files['aiwh/taxonomy.json'] = source / 'src/aiwh/taxonomy.json'
    capabilities = source / 'capabilities'
    patterns = ('__init__.py', 'agents/*.md', 'areas/catalog.json', 'game-porting/*.json', 'mcp/catalog.json',
                'plugins/catalog.json', 'references/catalog.json', 'profiles/*.json', 'routing/*.json',
                'skills/*/*/*', 'skills/*/*/**/*')
    for pattern in patterns:
        for path in capabilities.glob(pattern):
            if path.is_file():
                files[f'aiwh/capabilities/{path.relative_to(capabilities).as_posix()}'] = path
    return files


def check_member(name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
        raise ValueError(f'Unsafe archive member: {name}')
    if any(part in {'.ai-workbench', '.ai-workbench-hub', '.git', '__pycache__'}
           for part in path.parts):
        raise ValueError(f'Private/generated archive member: {name}')


def inspect_distributions(wheel, sdist, source):
    expected = expected_payload(source)
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate wheel members')
        metadata_files = {'METADATA', 'WHEEL', 'RECORD', 'entry_points.txt', 'top_level.txt',
                          'LICENSE', 'licenses/LICENSE'}
        for name in names:
            check_member(name)
            parts = PurePosixPath(name).parts
            metadata = (parts[0].startswith('ai_workbench-') and parts[0].endswith('.dist-info')
                        and '/'.join(parts[1:]) in metadata_files)
            if name not in expected and not metadata:
                raise ValueError(f'Unexpected wheel payload: {name}')
        for name, path in expected.items():
            if name not in names or archive.read(name) != path.read_bytes():
                raise ValueError(f'Missing or stale wheel payload: {name}')
        taxonomy = json.loads(archive.read('aiwh/taxonomy.json'))
        if taxonomy != json.loads((source / 'config/taxonomy.json').read_text(encoding='utf-8')):
            raise ValueError('Packaged taxonomy differs from canonical configuration')
    if sdist:
        with tarfile.open(sdist, 'r:gz') as archive:
            members = archive.getmembers()
            names = [member.name for member in members]
            if len(names) != len(set(names)):
                raise ValueError('Duplicate sdist members')
            roots = {PurePosixPath(name).parts[0] for name in names}
            if len(roots) != 1:
                raise ValueError('Expected a single sdist root')
            root = next(iter(roots))
            allowed = {path.relative_to(source).as_posix() for path in expected.values()}
            support_files = [source / 'config/taxonomy.json', source / 'scripts/Verify-Package.py']
            allowed.update({'pyproject.toml', 'README.md', 'LICENSE', 'PKG-INFO', 'setup.cfg', 'MANIFEST.in'})
            allowed.update(path.relative_to(source).as_posix() for path in support_files)
            allowed.update(path.relative_to(source).as_posix() for path in (source / 'tests').glob('test_*.py'))
            allowed.update(f'src/ai_workbench.egg-info/{name}' for name in
                           ('PKG-INFO', 'SOURCES.txt', 'dependency_links.txt', 'entry_points.txt',
                            'requires.txt', 'top_level.txt'))
            for member in members:
                check_member(member.name)
                if not member.isfile() and not member.isdir():
                    raise ValueError(f'Unsupported sdist member: {member.name}')
                relative = PurePosixPath(member.name).relative_to(root).as_posix()
                if member.isfile() and relative not in allowed:
                    raise ValueError(f'Unexpected sdist payload: {relative}')
            for path in [*expected.values(), *support_files]:
                name = f'{root}/{path.relative_to(source).as_posix()}'
                member = archive.extractfile(name)
                if member is None:
                    raise ValueError(f'Missing sdist payload: {name}')
                with member:
                    if member.read() != path.read_bytes():
                        raise ValueError(f'Stale sdist payload: {name}')
    return len(expected)


def run(command, directory):
    environment = os.environ.copy()
    for name in ('PYTHONPATH', 'PYTHONHOME', 'AIWH_HOME', 'AIWH_TAXONOMY'):
        environment.pop(name, None)
    result = subprocess.run([str(part) for part in command], cwd=directory, env=environment,
                            capture_output=True, text=True, encoding='utf-8', errors='replace',
                            timeout=120)
    if result.returncode:
        raise RuntimeError(f'Command failed ({result.returncode}): {command}\n'
                           f'{result.stdout}\n{result.stderr}')
    return result.stdout


def smoke_install(wheel, wheelhouse=None, reuse_dependencies=False):
    with tempfile.TemporaryDirectory(prefix='aiwh-package-') as temporary:
        directory = Path(temporary)
        runtime = directory / 'runtime'
        venv.EnvBuilder(with_pip=True, system_site_packages=reuse_dependencies).create(runtime)
        executable = runtime / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        install = [executable, '-I', '-m', 'pip', 'install', '--no-index',
                   '--disable-pip-version-check', '--ignore-installed']
        if reuse_dependencies:
            install.append('--no-deps')
        if wheelhouse:
            install.extend(['--find-links', wheelhouse])
        run([*install, wheel], directory)
        probe = ('import json, sys, aiwh, yaml; from pathlib import Path; '
                 'from aiwh.core import load_taxonomy; '
                 'assert Path(aiwh.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()); '
                 'assert load_taxonomy(); '
                 'print(json.dumps({"python":sys.version.split()[0], "pyyaml":yaml.__version__}))')
        evidence = json.loads(run([executable, '-I', '-c', probe], directory))
        private = directory / 'private'
        cli = [executable, '-I', '-m', 'aiwh', '--home', private]
        for command in ('init', 'managed', 'resume', 'audit', 'profiles', 'areas', 'recommend',
                        'capabilities', 'sync', 'attach', 'report', 'doctor', 'global-integration'):
            run([*cli, command, '--help'], directory)
        run([*cli, 'managed', 'remove', '--help'], directory)
        for command in ('profiles', 'areas', 'capabilities', 'report'):
            run([*cli, command], directory)
        project = directory / 'project with spaces'
        options = ['init', project, '--create', '--agent', 'all', '--profile', 'frontend']
        preview = json.loads(run([*cli, *options, '--dry-run'], directory))
        if project.exists() or not preview['operations']:
            raise ValueError('Bootstrap preview changed disk or omitted operations')
        first = json.loads(run([*cli, *options], directory))
        for location in ('.agents/skills', '.claude/skills', '.openclaude/skills'):
            for skill in first['skills']:
                if not (project / location / skill / 'SKILL.md').is_file():
                    raise ValueError(f'Missing installed skill: {location}/{skill}')
        again = json.loads(run([*cli, *options], directory))
        if any(operation['action'] in ('create', 'update', 'copy') for operation in again['operations']):
            raise ValueError('Repeated bootstrap changed managed files')
        run([*cli, 'doctor', '--project', project], directory)
        launcher = runtime / ('Scripts/aiwh.exe' if os.name == 'nt' else 'bin/aiwh')
        run([launcher, '--home', private, 'doctor', '--project', project], directory)
        json.loads(run([*cli, 'audit', project], directory))
        json.loads(run([*cli, 'recommend', project, '--area', 'frontend', '--json'], directory))
        run([*cli, 'resume', project, '--dry-run'], directory)
        if (project / '.ai-workbench/CONTEXT.md').exists():
            raise ValueError('Resume preview wrote a handoff')
        run([*cli, 'resume', project], directory)
        if not (project / '.ai-workbench/CONTEXT.md').is_file():
            raise ValueError('Resume did not write a handoff')
        run([*cli, 'attach', '--project', project, '--dry-run'], directory)
        evidence['dependency_mode'] = 'host reuse' if reuse_dependencies else 'isolated wheelhouse'
        return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheel', type=Path, required=True)
    parser.add_argument('--sdist', type=Path)
    parser.add_argument('--wheelhouse', type=Path, help='local dependency wheels; never downloads')
    parser.add_argument('--reuse-installed-dependencies', action='store_true',
                        help='reuse host dependencies; does not certify a clean dependency install')
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1]
    payload_count = inspect_distributions(args.wheel, args.sdist, source)
    evidence = smoke_install(args.wheel.resolve(),
                             args.wheelhouse.resolve() if args.wheelhouse else None,
                             args.reuse_installed_dependencies)
    evidence.update({'payload_files': payload_count, 'sdist_checked': bool(args.sdist),
                     'status': 'passed'})
    print(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    main()