import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('site', Path(__file__).with_name('check-website.py'))
site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site)

PAGE = ('<!doctype html><html lang="en"><head><title>T</title></head>'
        '<body><a href="docs/guide.md#install">Guide</a></body></html>')


class MarkdownParsingTests(unittest.TestCase):
    def test_github_slugs(self):
        self.assertEqual(site.github_slug('Branches and publication'), 'branches-and-publication')
        self.assertEqual(site.github_slug('🧭 Status'), '-status')
        self.assertEqual(site.github_slug('Run `check-website.py` [now](x.md)'), 'run-check-websitepy-now')

    def test_entities_are_decoded_before_slugging(self):
        self.assertEqual(site.github_slug('Rock &amp; Roll'), 'rock--roll')
        self.assertEqual(site.github_slug('Caf&eacute; &#169; 2026'), 'café--2026')

    def test_setext_headings_get_anchors(self):
        _, anchors = site.markdown_links('Install\n=======\n\nTwo line\nsetext title\n---\n\n- item\n---\n\n---\n')
        self.assertEqual(anchors, {'install', 'two-line-setext-title'})

    def test_duplicate_headings_get_suffixes(self):
        _, anchors = site.markdown_links('# Notes\n\n## Notes\n\n### Notes\n')
        self.assertEqual(anchors, {'notes', 'notes-1', 'notes-2'})

    def test_colliding_slugs_follow_github(self):
        _, anchors = site.markdown_links('# Foo\n# Foo-1\n# Foo\n')
        self.assertEqual(anchors, {'foo', 'foo-1', 'foo-2'})

    def test_destinations_with_parentheses_and_angle_brackets(self):
        links, _ = site.markdown_links('[a](guide_(v2).md "T") [b](<my file.md>) [c](x.md)\n'
                                       '[ref]: <ref file.md>\n')
        self.assertEqual(links, ['guide_(v2).md', 'my file.md', 'x.md', 'ref file.md'])

    def test_html_attributes_in_any_quoting(self):
        links, anchors = site.markdown_links(
            "<a href='single.md' id='one'></a><a name=two href=bare.md></a><img data-src=\"x.png\">\n")
        self.assertEqual(links, ['single.md', 'bare.md'])
        self.assertEqual(anchors, {'one', 'two'})

    def test_links_ignore_code_and_footnotes(self):
        text = ('[a](one.md) and `[b](two.md)`\n'
                '```\n[c](three.md)\n```\n'
                '[ref]: four.md "Title"\n'
                '[^1]: Not a link.\n'
                '<https://example.com/x> <a id="custom"></a> <img src="five.png" alt="">\n')
        links, anchors = site.markdown_links(text)
        self.assertEqual(links, ['one.md', 'four.md', 'https://example.com/x', 'five.png'])
        self.assertIn('custom', anchors)


class CheckTests(unittest.TestCase):
    def run_check(self, files):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            for name, text in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()):
                return site.check(root)

    def test_valid_markdown_links_pass(self):
        errors, external, *_ = self.run_check({
            'index.html': PAGE,
            'README.md': ('# Hub\n\n[Guide](docs/guide.md#install) [Top](#hub) [Docs](docs/)\n'
                          '[Page](index.html) [Site](https://example.com/page#part)\n'
                          "[V2](docs/guide_(v2).md) [Spaced](<docs/my guide.md>) <a href='#here' id='here'></a>\n"),
            'docs/guide.md': '# Guide\n\n## Install\n\n[Back](../README.md)\n',
            'docs/guide_(v2).md': '# V2\n',
            'docs/my guide.md': '# Spaced\n'})
        self.assertEqual(errors, [])
        self.assertEqual(external, {'https://example.com/page'})

    def test_broken_markdown_links_fail(self):
        errors, *_ = self.run_check({
            'index.html': PAGE,
            'README.md': ('[Missing](docs/missing.md) [Anchor](docs/guide.md#nowhere)\n'
                          '[Root](/docs/guide.md) [Outside](../elsewhere.md)\n'
                          "<a href='docs/gone.md'>Gone</a>\n"),
            'docs/guide.md': '# Guide\n\n## Install\n'})
        self.assertEqual(errors, [
            'README.md: missing target docs/missing.md',
            'README.md: missing anchor docs/guide.md#nowhere',
            'README.md: root-relative URL breaks project Pages hosting: /docs/guide.md',
            'README.md: path outside repository: ../elsewhere.md',
            'README.md: missing target docs/gone.md'])

    def test_html_links_to_markdown_anchors_are_checked(self):
        errors, *_ = self.run_check({'index.html': PAGE, 'docs/guide.md': '# Guide\n'})
        self.assertEqual(errors, ['index.html: missing anchor docs/guide.md#install'])


if __name__ == '__main__':
    unittest.main()
