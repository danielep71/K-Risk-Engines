import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('refresh', Path(__file__).with_name('portfolio-refresh.py'))
refresh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refresh)


class PortfolioTests(unittest.TestCase):
    def test_status_preserves_negative_evidence(self):
        source = '> [!IMPORTANT]\n> **Version 1 is a prototype.**\n> Not run in Excel. No result is validated.\n\n## More\n'
        result = refresh.status_excerpt(source, 'important')
        self.assertIn('Not run in Excel. No result is validated.', result)

    def test_status_section_keeps_draft_caveats(self):
        source = '## 🧭 Status\n\n**In progress.**\n\n- Decay draft, not validated.\n- No Excel evidence.\n\n## Next\n'
        self.assertIn('No Excel evidence.', refresh.status_excerpt(source, 'status'))

    def test_missing_or_ambiguous_status_fails(self):
        for source in ['no status here', '> [!IMPORTANT]\n> One status is not sufficient.\n\n> [!IMPORTANT]\n> Another status has appeared.\n']:
            with self.assertRaises(ValueError):
                refresh.status_excerpt(source, 'important')

    def test_latest_closed_uses_closure_date_not_number(self):
        milestones = [
            {'number': 12, 'state': 'closed', 'closed_at': '2026-01-01T00:00:00Z'},
            {'number': 2, 'state': 'closed', 'closed_at': '2026-10-20T00:00:00Z'},
            {'number': 19, 'state': 'open', 'closed_at': None}]
        self.assertEqual(refresh.latest_closed(milestones)['number'], 2)
        milestones[1]['state'] = 'open'
        self.assertEqual(refresh.latest_closed(milestones)['number'], 12)
        self.assertIsNone(refresh.latest_closed([]))

    def test_unrelated_commit_does_not_change_snapshot(self):
        project = {'id': 'test', 'repo': 'owner/repo', 'selector': 'current', 'evidence': []}
        metadata = {'private': False, 'full_name': 'owner/repo', 'default_branch': 'main'}
        source = '**Current status: repository setup only.** No model is delivered.'
        with patch.object(refresh, 'api', side_effect=[metadata, {'sha': 'a' * 40}, metadata, {'sha': 'b' * 40}]), patch.object(refresh, 'pages', return_value=[]), patch.object(refresh, 'file_at', return_value=source):
            first = refresh.collect(project)
            second = refresh.collect(project, first)
        self.assertEqual(first, second)
        self.assertIs(first, second)

    def test_private_source_is_rejected(self):
        with patch.object(refresh, 'api', return_value={'private': True}):
            with self.assertRaises(ValueError):
                refresh.collect({'repo': 'owner/private'})

    def test_marker_loss_fails_instead_of_overwriting(self):
        with self.assertRaises(ValueError):
            refresh.replace_block('handwritten document', 'table', 'generated')

    def test_source_text_cannot_inject_html(self):
        project = {'id': 'one', 'name': 'One', 'purpose': 'Purpose'}
        data = {'id': 'one', 'repo': 'owner/repo', 'status': '<script>bad()</script> & caveat',
                'sources': [{'path': 'README.md', 'url': 'https://github.com/owner/repo/blob/abc/README.md', 'sha256': 'abc'}],
                'release': None, 'milestones': []}
        readme, website, report = refresh.render([project], [data],
            '<!-- portfolio:table:start --><!-- portfolio:table:end -->',
            '<!-- portfolio:one:start --><!-- portfolio:one:end -->')
        self.assertNotIn('<script>', website)
        self.assertIn('&lt;script&gt;', website)
        self.assertIn('none recorded', website)


if __name__ == '__main__':
    unittest.main()
