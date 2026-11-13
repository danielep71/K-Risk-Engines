"""Regression checks for broken-link rejection and project names."""
import tempfile
import unittest
from pathlib import Path

from check import Page, inspect, name_errors


class PortalTests(unittest.TestCase):
    def test_engine_pages_and_menu_use_the_displayed_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'engines/frtb').mkdir(parents=True)
            (root / 'engines/frtb/index.md').write_text('# K-FRTB-ASA\n\nText\n')
            projects = [{'id': 'frtb', 'name': 'K-FRTB-SA', 'repo': 'danielep71/K-FRTB-ASA'}]
            nav = [{'Market Risk': [{'K-FRTB-ASA': 'engines/frtb/index.md'}]}]
            self.assertEqual(len(name_errors(root, projects, nav)), 2)
            (root / 'engines/frtb/index.md').write_text('# K-FRTB-SA\n\nText\n')
            nav = [{'Market Risk': [{'K-FRTB-SA': 'engines/frtb/index.md'}]}]
            self.assertEqual(name_errors(root, projects, nav), [])

    def test_missing_file_and_anchor_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            page = root / 'index.html'
            page.write_text('<a href="missing.html">broken</a>')
            with self.assertRaisesRegex(ValueError, 'missing target'):
                inspect(root)
            page.write_text('<a href="#missing">broken</a>')
            with self.assertRaisesRegex(ValueError, 'missing anchor'):
                inspect(root)

    def test_directory_url_and_encoded_anchor(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'engine').mkdir()
            (root / 'index.html').write_text('<a href="engine/#a%20b">valid</a>')
            (root / 'engine/index.html').write_text('<h1 id="a b">Title</h1>')
            self.assertEqual(len(inspect(root)), 2)

    def test_escape_outside_site_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'index.html').write_text('<a href="../outside.html">escape</a>')
            with self.assertRaisesRegex(ValueError, 'missing target'):
                inspect(root)

    def test_image_sources_are_checked(self):
        self.assertEqual(Page('<img src="missing.png">').links, ['missing.png'])


if __name__ == '__main__':
    unittest.main()
