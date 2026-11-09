"""Regression checks for deployment isolation and broken-link rejection."""
import tempfile
import unittest
from pathlib import Path

from check import Page, inspect


class PortalTests(unittest.TestCase):
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
