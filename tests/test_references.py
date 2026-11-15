import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from aiwh.cli import _utf8_stdout, main  # noqa: E402
from aiwh.references import (CATALOG_PATH, document_is_current, reference_catalog,  # noqa: E402
                             references_markdown, validate_references, write_document)


def _catalog_with(**changes):
    """Copy of the real catalog with the first reference's fields replaced or extended."""
    data = json.loads(CATALOG_PATH.read_text(encoding='utf-8'))
    key = next(iter(data['references']))
    data['references'][key].update(changes)
    return data


def _run(argv):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = main(argv)
    return code, output.getvalue()


class ValidateReferencesTests(unittest.TestCase):
    def test_real_catalog_is_valid(self):
        stats = validate_references(reference_catalog())
        self.assertGreater(stats['references'], 0)

    def test_null_group_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'group must be a non-empty string'):
            validate_references(_catalog_with(group=None))

    def test_blank_group_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'group must be a non-empty string'):
            validate_references(_catalog_with(group='   '))

    def test_string_group_is_accepted(self):
        self.assertTrue(validate_references(_catalog_with(group='Frameworks')))

    def test_string_areas_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'areas must be a list of strings'):
            validate_references(_catalog_with(areas='security'))

    def test_non_string_area_items_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'areas must be a list of strings'):
            validate_references(_catalog_with(areas=[1]))

    def test_non_list_risk_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'risk must be a list of strings'):
            validate_references(_catalog_with(risk='authorized-only'))

    def test_unknown_key_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unknown keys'):
            validate_references(_catalog_with(notes='typo'))

    def test_non_string_url_is_value_error(self):
        with self.assertRaisesRegex(ValueError, 'url must be a string'):
            validate_references(_catalog_with(url=123))

    def test_non_string_title_is_value_error(self):
        with self.assertRaisesRegex(ValueError, 'title must be a string'):
            validate_references(_catalog_with(title=['x']))


class ReferenceDocumentTests(unittest.TestCase):
    def test_write_uses_lf_and_matches_generated_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'REFERENCES.md'
            write_document(target)
            self.assertEqual(target.read_bytes(), references_markdown().encode('utf-8'))
            self.assertNotIn(b'\r', target.read_bytes())

    def test_check_detects_missing_equal_and_changed_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'REFERENCES.md'
            self.assertFalse(document_is_current(target))
            write_document(target)
            self.assertTrue(document_is_current(target))
            target.write_text(references_markdown() + 'drift\n', encoding='utf-8', newline='\n')
            self.assertFalse(document_is_current(target))

    def test_check_is_byte_strict_about_crlf(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'REFERENCES.md'
            target.write_bytes(references_markdown().replace('\n', '\r\n').encode('utf-8'))
            self.assertFalse(document_is_current(target))

    def test_cli_write_then_check(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'REFERENCES.md'
            code, _ = _run(['references', '--write', str(target)])
            self.assertEqual(code, 0)
            self.assertEqual(target.read_bytes(), references_markdown().encode('utf-8'))
            code, out = _run(['references', '--check', str(target)])
            self.assertEqual(code, 0)
            self.assertIn('Current', out)

    def test_cli_check_exits_one_when_out_of_date(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'REFERENCES.md'
            target.write_text('# stale\n', encoding='utf-8', newline='\n')
            code, out = _run(['references', '--check', str(target)])
            self.assertEqual(code, 1)
            self.assertIn('Out of date', out)

    def test_cli_check_exits_one_when_missing(self):
        with tempfile.TemporaryDirectory() as temporary:
            code, _ = _run(['references', '--check', str(Path(temporary) / 'absent.md')])
            self.assertEqual(code, 1)

    def test_cli_write_and_check_together_is_usage_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            code, _ = _run(['references', '--write', str(Path(temporary) / 'a.md'),
                            '--check', str(Path(temporary) / 'a.md')])
            self.assertEqual(code, 2)

    def test_stdout_markdown_uses_lf_newlines(self):
        buffer = io.BytesIO()
        wrapper = io.TextIOWrapper(buffer, encoding='cp1252', newline=None)
        with mock.patch.object(sys, 'stdout', wrapper):
            _utf8_stdout()
            print('line one')
            print('line two')
            wrapper.flush()
        self.assertEqual(buffer.getvalue(), b'line one\nline two\n')


if __name__ == '__main__':
    unittest.main()
