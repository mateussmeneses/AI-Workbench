import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from aiwh.core import (canonical_url, chromelike_bookmarks, merged_index,
                       github_stars, browser_html_export, attach, project_profile)


class CatalogTests(unittest.TestCase):
    def test_dedup_and_tracking_params(self):
        items = merged_index([], [
            {'url': 'https://github.com/Owner/Repo?utm_source=x#readme', 'title': 'Vulkan Renderer', 'source': 'browser'},
            {'url': 'https://github.com/owner/Repo', 'title': 'Vulkan Renderer', 'source': 'github:starred'}])
        self.assertEqual(len(items), 1)
        self.assertEqual(len(items[0]['sources']), 2)
        self.assertIn('game-port', items[0]['categories'])

    def test_bookmark_tree(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / 'Bookmarks'
            f.write_text(json.dumps({'roots': {'bookmark_bar': {'type': 'folder', 'name': 'Bar', 'children': [
                {'type': 'folder', 'name': 'QA', 'children': [
                    {'type': 'url', 'name': 'NUnit', 'url': 'https://nunit.org'}]}]}}}), encoding='utf-8')
            data = chromelike_bookmarks(f, 'chrome', 'Default')
            self.assertEqual(len(data), 1)
            self.assertIn('QA', data[0]['folder'])

    def test_stars_paginated(self):
        got = github_stars([[{'html_url':'https://github.com/a/b','full_name':'a/b', 'topics':['mcp']}],
                           [{'html_url':'https://github.com/a/c','full_name':'a/c'}]])
        self.assertEqual(len(got), 2)

    def test_html_export(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / 'bookmarks.html'
            f.write_text('<!DOCTYPE NETSCAPE-Bookmark-file-1><DL><p><DT><H3>Dev</H3><DL><p><DT><A HREF="https://test.com">Example</A></DL><p></DL>', encoding='utf-8')
            got = browser_html_export(f)
            self.assertEqual(len(got), 1)
            self.assertEqual(got[0]['title'], 'Example')
            self.assertIn('Dev', got[0]['folder'])

    def test_attach_respects_existing_agents(self):
        with tempfile.TemporaryDirectory() as d:
            project = Path(d)
            (project/'AGENTS.md').write_text('# Original\n', encoding='utf-8')
            index = merged_index([], [{'url':'https://github.com/x/vulkan', 'title':'vulkan-shader', 'source':'browser'}])
            result = attach(project, index, profiles=['game-port'])
            self.assertTrue(result['written'])
            self.assertEqual(len(result['plan']['resources']), 1)
            txt = (project/'AGENTS.md').read_text(encoding='utf-8')
            self.assertIn('# Original', txt)
            self.assertEqual(txt.count('<!-- AIWH:BEGIN -->'), 1)
            attach(project, index, profiles=['game-port'])
            self.assertEqual((project/'AGENTS.md').read_text(encoding='utf-8').count('<!-- AIWH:BEGIN -->'), 1)
            self.assertTrue((project/'.ai-workbench/RESOURCES.md').is_file())
            self.assertIn('.ai-workbench/', (project/'.gitignore').read_text(encoding='utf-8'))

    def test_profile_detection(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/'MySolution.sln').write_text('', encoding='utf-8')
            self.assertIn('qa-dotnet', project_profile(d))


if __name__ == '__main__':
    unittest.main()
