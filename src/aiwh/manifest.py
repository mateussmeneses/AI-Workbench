"""Transactional, hash-verified managed-file manifest and removal."""
from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

BEGIN, END = '<!-- AIWH:BEGIN -->', '<!-- AIWH:END -->'


@dataclass
class Operation:
    action: str
    path: str
    detail: str = ''


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON field: {key}')
        result[key] = value
    return result


class ManagedFileTransaction:
    DIRECTORY = '.ai-workbench/managed-files.transaction'

    def __init__(self, project, dry_run):
        self.project = Path(project).resolve()
        self.dry_run = dry_run
        self.root_relative = PurePosixPath(self.DIRECTORY)
        self.root = self.project / Path(*self.root_relative.parts)
        self.journal_path = self.root / 'journal.json'
        self.data = None
        self._recover()

    def _relative(self, path):
        target = Path(path)
        if not target.is_absolute():
            target = self.project / target
        try:
            relative = target.absolute().relative_to(self.project).as_posix()
        except ValueError as error:
            raise ValueError(f'Transaction path is outside project: {path}') from error
        pure = PurePosixPath(relative)
        if (not relative or pure.is_absolute() or '\\' in relative
                or any(part in ('', '.', '..') for part in pure.parts)
                or pure == self.root_relative or self.root_relative in pure.parents):
            raise ValueError(f'Invalid transaction path: {path}')
        return pure

    def _path(self, relative):
        pure = PurePosixPath(relative)
        if (pure.is_absolute() or '\\' in relative
                or any(part in ('', '.', '..') for part in pure.parts)):
            raise ValueError(f'Invalid transaction path: {relative}')
        return self.project / Path(*pure.parts)

    def _has_symlink_component(self, relative):
        current = self.project
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                return True
        return False

    def _write_journal(self):
        temporary = self.root / 'journal.tmp'
        if temporary.is_symlink() or (temporary.exists() and not temporary.is_file()):
            raise ValueError(f'Invalid transaction journal temporary path: {temporary}')
        encoded = json.dumps(self.data, indent=2, ensure_ascii=False).encode('utf-8')
        with temporary.open('wb') as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, self.journal_path)

    def _read_journal(self):
        try:
            data = json.loads(self.journal_path.read_text(encoding='utf-8'),
                              object_pairs_hook=_unique_json_object)
            if (not isinstance(data, dict)
                    or set(data) != {'schema_version', 'transaction_id', 'committed', 'entries'}
                    or type(data.get('schema_version')) is not int
                    or data['schema_version'] != 1
                    or not isinstance(data.get('transaction_id'), str)
                    or not re.fullmatch(r'[0-9a-f]{32}', data['transaction_id'])
                    or type(data.get('committed')) is not bool
                    or not isinstance(data.get('entries'), list)):
                raise ValueError('unsupported transaction journal schema')
            return data
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError(f'Invalid managed-file transaction {self.journal_path}: {error}') from error

    def _entry_paths(self, entry):
        required = {'path', 'operation', 'existed', 'previous_sha256', 'desired_sha256',
                    'backup', 'backup_ready', 'temporary'}
        if (not isinstance(entry, dict) or set(entry) != required
                or entry['operation'] not in ('write', 'remove')
                or type(entry['existed']) is not bool
                or type(entry['backup_ready']) is not bool):
            raise ValueError('invalid transaction entry')
        relative = self._relative(self.project / entry['path'])
        if relative.as_posix() != entry['path']:
            raise ValueError(f'non-canonical transaction path: {entry["path"]}')
        target = self._path(entry['path'])
        temporary_relative = self._relative(self.project / entry['temporary'])
        if (temporary_relative.as_posix() != entry['temporary']
                or temporary_relative.parent != relative.parent
                or not temporary_relative.name.startswith(relative.name + '.aiwh-')):
            raise ValueError(f'invalid transaction temporary path: {entry["temporary"]}')
        temporary = self._path(entry['temporary'])
        backup = None
        if entry['existed']:
            if (not isinstance(entry['backup'], str)
                    or not re.fullmatch(r'backup-[0-9]{6}\.bin', entry['backup'])):
                raise ValueError('invalid transaction backup name')
            if (not isinstance(entry['previous_sha256'], str)
                    or not re.fullmatch(r'[0-9a-f]{64}', entry['previous_sha256'])):
                raise ValueError('invalid previous content hash in transaction')
            backup = self.root / entry['backup']
        elif entry['backup'] is not None or entry['previous_sha256'] is not None:
            raise ValueError('unexpected backup for a newly created file')
        if entry['operation'] == 'write':
            if (not isinstance(entry['desired_sha256'], str)
                    or not re.fullmatch(r'[0-9a-f]{64}', entry['desired_sha256'])):
                raise ValueError('invalid desired content hash in transaction')
        elif entry['desired_sha256'] is not None:
            raise ValueError('unexpected desired hash for a removed file')
        return target, temporary, backup

    def _remove_artifact(self, path):
        if path is None or not path.exists():
            return
        if path.is_symlink() or not path.is_file():
            raise ValueError(f'Refusing to remove unexpected transaction artifact: {path}')
        path.unlink()

    def _restore_entry(self, entry):
        target, temporary, backup = self._entry_paths(entry)
        if self._has_symlink_component(self._relative(target)):
            raise ValueError(f'Refusing to recover through symlink: {target}')

        if entry['backup_ready']:
            exists = target.exists()
            if exists and (target.is_symlink() or not target.is_file()):
                raise ValueError(f'Refusing to recover non-regular file: {target}')
            current_hash = hashlib.sha256(target.read_bytes()).hexdigest() if exists else None
            old_hash = entry['previous_sha256']
            desired_hash = entry['desired_sha256']
            already_restored = current_hash == old_hash if entry['existed'] else not exists
            if not already_restored:
                expected_after = desired_hash if entry['operation'] == 'write' else None
                if current_hash != expected_after:
                    raise ValueError(f'Cannot safely recover changed file: {target}')
                if entry['existed']:
                    if backup is None or backup.is_symlink() or not backup.is_file():
                        raise ValueError(f'Managed-file backup is missing: {backup}')
                    original = backup.read_bytes()
                    if hashlib.sha256(original).hexdigest() != old_hash:
                        raise ValueError(f'Managed-file backup hash mismatch: {backup}')
                    if temporary.is_symlink() or (temporary.exists() and not temporary.is_file()):
                        raise ValueError(f'Refusing unexpected recovery temporary path: {temporary}')
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with temporary.open('wb') as stream:
                        stream.write(original)
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.replace(temporary, target)
                elif exists:
                    target.unlink()

        self._remove_artifact(temporary)
        self._remove_artifact(backup)

    def _cleanup_committed(self, data):
        for entry in data['entries']:
            _, temporary, backup = self._entry_paths(entry)
            self._remove_artifact(temporary)
            self._remove_artifact(backup)
        journal_temporary = self.root / 'journal.tmp'
        self._remove_artifact(journal_temporary)
        if any(path.name not in {'journal.json'} for path in self.root.iterdir()):
            raise ValueError(f'Unexpected files in transaction directory: {self.root}')
        self.journal_path.unlink(missing_ok=True)
        self.root.rmdir()
        self.data = None

    def _recover(self):
        if self._has_symlink_component(self.root_relative):
            raise ValueError(f'Refusing symlinked transaction directory: {self.root}')
        if not self.root.exists():
            return
        if not self.root.is_dir():
            raise ValueError(f'Invalid transaction directory: {self.root}')
        if self.dry_run:
            raise ValueError(f'Incomplete managed-file transaction; rerun without --dry-run to recover: {self.root}')
        if not self.journal_path.is_file() or self.journal_path.is_symlink():
            journal_temporary = self.root / 'journal.tmp'
            if journal_temporary.is_file() and not journal_temporary.is_symlink():
                journal_temporary.unlink()
            if any(self.root.iterdir()):
                raise ValueError(f'Managed-file transaction journal is missing: {self.root}')
            self.root.rmdir()
            return
        data = self._read_journal()
        self.data = data
        if not data['committed']:
            for entry in reversed(data['entries']):
                self._restore_entry(entry)
        self._cleanup_committed(data)

    def _begin(self):
        if self.data is not None:
            return
        if self.root.exists() or self.root.is_symlink():
            raise ValueError(f'Transaction directory unexpectedly exists: {self.root}')
        self.root.mkdir(parents=True)
        self.data = {'schema_version': 1, 'transaction_id': uuid.uuid4().hex,
                     'committed': False, 'entries': []}
        self._write_journal()

    def _record(self, target, operation, desired):
        target = Path(target)
        relative = self._relative(target)
        if self._has_symlink_component(relative):
            raise ValueError(f'Refusing managed write through symlink: {target}')
        target.parent.mkdir(parents=True, exist_ok=True)
        exists = target.exists()
        if exists and (target.is_symlink() or not target.is_file()):
            raise ValueError(f'Refusing to transact non-regular file: {target}')
        original = target.read_bytes() if exists else None
        index = len(self.data['entries'])
        backup_name = f'backup-{index:06d}.bin' if exists else None
        transaction_id = self.data['transaction_id']
        temporary = target.with_name(f'{target.name}.aiwh-{transaction_id}-{index:06d}.tmp')
        temporary_relative = self._relative(temporary).as_posix()
        entry = {'path': relative.as_posix(), 'operation': operation, 'existed': exists,
                 'previous_sha256': hashlib.sha256(original).hexdigest() if exists else None,
                 'desired_sha256': hashlib.sha256(desired).hexdigest() if operation == 'write' else None,
                 'backup': backup_name, 'backup_ready': False, 'temporary': temporary_relative}
        self.data['entries'].append(entry)
        self._write_journal()
        if exists:
            backup = self.root / backup_name
            with backup.open('xb') as stream:
                stream.write(original)
                stream.flush()
                os.fsync(stream.fileno())
        entry['backup_ready'] = True
        self._write_journal()
        return target, temporary, entry

    def write(self, target, content):
        self._begin()
        target = Path(target)
        data = content if isinstance(content, bytes) else content.encode('utf-8')
        target, temporary, _ = self._record(target, 'write', data)
        with temporary.open('xb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)

    def remove(self, target):
        self._begin()
        target, _, _ = self._record(target, 'remove', None)
        target.unlink()

    def commit(self):
        if self.data is None:
            return
        self.data['committed'] = True
        self._write_journal()
        self._cleanup_committed(self.data)


class ManagedFilePlan:
    MANIFEST = '.ai-workbench/managed-files.json'
    SCHEMA_VERSION = 1

    def __init__(self, project, dry_run):
        self.project = Path(project).resolve()
        self.dry_run = dry_run
        self.transaction = ManagedFileTransaction(self.project, dry_run)
        self.manifest_path = self.project / self.MANIFEST
        self.manifest_relative = PurePosixPath(self.MANIFEST)
        self.previous = self._load_manifest()
        self.manifest_present = self.manifest_path.is_file()
        self.next = dict(self.previous)
        self.categories = {name: [] for name in ('added', 'unchanged', 'changed', 'conflicting')}
        self.operations = []
        self.visited = set()

    def _relative(self, path):
        target = Path(path)
        if not target.is_absolute():
            target = self.project / target
        try:
            relative = target.absolute().relative_to(self.project).as_posix()
        except ValueError as error:
            raise ValueError(f'Managed path is outside project: {path}') from error
        pure = PurePosixPath(relative)
        if (not relative or pure.is_absolute() or '\\' in relative
                or any(part in ('', '.', '..') for part in pure.parts)
                or pure == self.manifest_relative):
            raise ValueError(f'Invalid managed path: {path}')
        return pure

    def _has_symlink_component(self, relative):
        current = self.project
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                return True
        return False

    def _load_manifest(self):
        if self._has_symlink_component(self.manifest_relative):
            raise ValueError(f'Refusing symlinked managed-file manifest: {self.manifest_path}')
        if not self.manifest_path.exists():
            return {}
        try:
            value = json.loads(self.manifest_path.read_text(encoding='utf-8'),
                               object_pairs_hook=_unique_json_object)
            if (not isinstance(value, dict)
                    or type(value.get('schema_version')) is not int
                    or value['schema_version'] != self.SCHEMA_VERSION
                    or set(value) != {'schema_version', 'files'}
                    or not isinstance(value['files'], dict)):
                raise ValueError('unsupported manifest schema')
            files = {}
            for name, digest in value['files'].items():
                relative = self._relative(self.project / name)
                if (relative.as_posix() != name or not isinstance(digest, str)
                        or not re.fullmatch(r'[0-9a-f]{64}', digest)):
                    raise ValueError(f'invalid file entry: {name}')
                files[name] = digest
            return files
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError(f'Invalid managed-file manifest {self.manifest_path}: {error}') from error

    def write(self, path, content, *, kind='write', allow_unowned_merge=False):
        relative = self._relative(path)
        name = relative.as_posix()
        self.visited.add(name)
        target = self.project / Path(*relative.parts)
        desired = content if isinstance(content, bytes) else content.encode('utf-8')
        desired_hash = hashlib.sha256(desired).hexdigest()
        previous_hash = self.previous.get(name)

        if self._has_symlink_component(relative):
            self.categories['conflicting'].append(name)
            self.operations.append(Operation('skip-conflict', str(target), 'Symlinked path is not managed'))
            if previous_hash:
                self.next[name] = previous_hash
            return

        exists = target.exists()
        if exists and not target.is_file():
            self.categories['conflicting'].append(name)
            self.operations.append(Operation('skip-conflict', str(target), 'Existing path is not a regular file'))
            if previous_hash:
                self.next[name] = previous_hash
            return

        current_hash = hashlib.sha256(target.read_bytes()).hexdigest() if exists else None
        if not exists:
            category, action = 'added', 'copy' if kind == 'copy' else 'create'
        elif current_hash == desired_hash:
            self.categories['unchanged'].append(name)
            if previous_hash:
                self.next[name] = desired_hash
            return
        elif previous_hash is not None and current_hash == previous_hash:
            category, action = 'changed', 'update'
        elif allow_unowned_merge and previous_hash is None:
            category, action = 'changed', 'update'
        else:
            self.categories['conflicting'].append(name)
            self.operations.append(Operation('skip-conflict', str(target), 'Existing file has no matching ownership hash'))
            if previous_hash:
                self.next[name] = previous_hash
            return

        self.categories[category].append(name)
        self.next[name] = desired_hash
        self.operations.append(Operation(action, str(target)))
        if not self.dry_run:
            self._transactional_write(target, desired)

    def _transactional_write(self, target, content):
        self.transaction.write(target, content)

    def _transactional_remove(self, target):
        self.transaction.remove(target)

    def finish(self):
        for name, expected_hash in self.previous.items():
            if name in self.visited:
                continue
            relative = PurePosixPath(name)
            target = self.project / Path(*relative.parts)
            if (self._has_symlink_component(relative) or not target.is_file()
                    or hashlib.sha256(target.read_bytes()).hexdigest() != expected_hash):
                self.categories['conflicting'].append(name)
                self.operations.append(Operation('skip-conflict', str(target),
                                                 'Previously managed file changed or is missing'))
            else:
                self.categories['unchanged'].append(name)
        manifest_action = self._save_manifest()
        self.transaction.commit()
        return {**{key: sorted(set(paths)) for key, paths in self.categories.items()},
                'manifest': manifest_action}

    def _save_manifest(self):
        payload = {'schema_version': self.SCHEMA_VERSION,
                   'files': dict(sorted(self.next.items()))}
        encoded = json.dumps(payload, indent=2, ensure_ascii=False) + '\n'
        previous_text = None
        if self.manifest_path.is_file() and not self.manifest_path.is_symlink():
            previous_text = self.manifest_path.read_text(encoding='utf-8')
        if previous_text == encoded:
            manifest_action = 'unchanged'
        else:
            manifest_action = 'create' if previous_text is None else 'update'
            self.operations.append(Operation(manifest_action, str(self.manifest_path),
                                             'Versioned SHA-256 ownership manifest'))
            if not self.dry_run:
                self._transactional_write(self.manifest_path, encoded)
        return manifest_action

    def remove(self):
        if not self.manifest_present:
            return {'removed': [], 'updated': [], 'missing': [], 'conflicting': [],
                    'manifest': 'missing', 'dry_run': self.dry_run, 'operations': []}

        removed, updated, missing, conflicting = [], [], [], []
        planned = []
        for name, expected_hash in sorted(self.previous.items()):
            relative = PurePosixPath(name)
            target = self.project / Path(*relative.parts)
            if self._has_symlink_component(relative):
                conflicting.append(name)
                self.operations.append(Operation('skip-conflict', str(target), 'Symlinked path is not removed'))
                continue
            if not target.exists():
                missing.append(name)
                self.next.pop(name, None)
                self.operations.append(Operation('already-missing', str(target)))
                continue
            if not target.is_file():
                conflicting.append(name)
                self.operations.append(Operation('skip-conflict', str(target), 'Existing path is not a regular file'))
                continue
            try:
                content = target.read_bytes()
            except OSError as error:
                conflicting.append(name)
                self.operations.append(Operation('skip-conflict', str(target), f'Cannot verify file: {error}'))
                continue
            if hashlib.sha256(content).hexdigest() != expected_hash:
                conflicting.append(name)
                self.operations.append(Operation('skip-conflict', str(target), 'Content hash differs from manifest'))
                continue

            text = content.decode('utf-8') if name in ('AGENTS.md', 'CLAUDE.md', '.gitignore') else None
            if name in ('AGENTS.md', 'CLAUDE.md'):
                cleaned = _remove_managed_instruction_block(text)
                if cleaned is None:
                    conflicting.append(name)
                    self.operations.append(Operation('skip-conflict', str(target), 'Managed instruction markers are missing or ambiguous'))
                    continue
                if not cleaned:
                    removed.append(name)
                    planned.append(('remove', target, None))
                    self.operations.append(Operation('remove', str(target), 'Only the managed instruction block remained'))
                else:
                    updated.append(name)
                    planned.append(('write', target, cleaned.encode('utf-8')))
                    self.operations.append(Operation('update', str(target), 'Removed only the managed instruction block'))
            elif name == '.gitignore':
                cleaned = _remove_managed_ignore_block(text)
                if cleaned is None:
                    conflicting.append(name)
                    self.operations.append(Operation('skip-conflict', str(target), 'Managed ignore entry is missing'))
                    continue
                updated.append(name)
                planned.append(('write', target, cleaned.encode('utf-8')))
                self.operations.append(Operation('update', str(target), 'Removed only the managed ignore entry'))
            else:
                removed.append(name)
                planned.append(('remove', target, None))
                self.operations.append(Operation('remove', str(target), 'Manifest hash verified'))
            self.next.pop(name, None)

        if not self.dry_run:
            for action, target, content in planned:
                if action == 'remove':
                    self._transactional_remove(target)
                else:
                    self._transactional_write(target, content)
        manifest_action = self._save_manifest()
        self.transaction.commit()
        if not self.dry_run:
            self._prune_empty_parents(target for action, target, _ in planned if action == 'remove')
        return {'removed': removed, 'updated': updated, 'missing': missing,
                'conflicting': conflicting, 'manifest': manifest_action,
                'dry_run': self.dry_run, 'operations': [vars(op) for op in self.operations]}

    def _prune_empty_parents(self, removed_files):
        """Remove directories left empty by managed removals, never the project root."""
        for path in sorted({p.parent for p in removed_files}, key=lambda p: len(p.parts), reverse=True):
            current = path
            while current != self.project and self.project in current.parents:
                try:
                    current.rmdir()  # fails unless empty
                except OSError:
                    break
                current = current.parent


def _remove_managed_instruction_block(content):
    if content.count(BEGIN) != 1 or content.count(END) != 1:
        return None
    start = content.index(BEGIN)
    end = content.index(END) + len(END)
    prefix, suffix = content[:start], content[end:]
    if not suffix.strip('\n'):
        # Appended block: init wrote original.rstrip() + blank line + block + newline.
        stripped = prefix.rstrip('\n')
        return stripped + '\n' if stripped else ''
    if prefix.endswith('\n\n'):
        prefix = prefix[:-2]
    elif prefix.endswith('\n'):
        prefix = prefix[:-1]
    if suffix.startswith('\n'):
        suffix = suffix[1:]
    return prefix + suffix


def _remove_managed_ignore_block(content):
    suffix = '\n\n# AI Workbench private local context\n.ai-workbench/\n'
    if not content.endswith(suffix):
        return None
    prefix = content[:-len(suffix)]
    return prefix + '\n' if prefix else ''


def remove_managed(project, *, dry_run=False):
    project = Path(project).expanduser().resolve()
    if not project.is_dir():
        raise ValueError(f'Project not found: {project}')
    return ManagedFilePlan(project, dry_run).remove()
