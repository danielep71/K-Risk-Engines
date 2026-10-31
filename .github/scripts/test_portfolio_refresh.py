import importlib.util
import json
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

    def test_deleted_milestone_becomes_dated_history(self):
        project = {'id': 'one', 'name': 'One', 'purpose': 'Purpose', 'repo': 'owner/repo', 'selector': 'current', 'evidence': []}
        metadata = {'private': False, 'full_name': 'owner/repo', 'default_branch': 'main'}
        source = '**Current status: repository setup only.** No model is delivered.'
        kept = {'number': 1, 'title': 'v0.1.0', 'state': 'closed', 'open_issues': 0, 'closed_issues': 4,
                'closed_at': '2026-10-01T00:00:00Z', 'html_url': 'https://github.com/owner/repo/milestone/1'}
        deleted = {'number': 2, 'title': 'v0.2.0', 'state': 'closed', 'open_issues': 1, 'closed_issues': 2,
                   'closed_at': '2026-10-20T00:00:00Z', 'html_url': 'https://github.com/owner/repo/milestone/2'}
        api = [metadata, {'sha': 'a' * 40}] * 3
        pages = [[], [kept, deleted], [], [kept], [], [kept]]
        with patch.object(refresh, 'api', side_effect=api), patch.object(refresh, 'pages', side_effect=pages), \
                patch.object(refresh, 'file_at', return_value=source), patch.object(refresh, 'today', side_effect=['2026-10-27', '2026-10-28']):
            first = refresh.collect(project)
            second = refresh.collect(project, first)
            third = refresh.collect(project, second)
        self.assertEqual(second['milestones'][1], dict(deleted, html_url=None, removed_on='2026-10-27'))
        self.assertIs(third, second)
        readme, website, report = refresh.render([project], [second],
            '<!-- portfolio:table:start --><!-- portfolio:table:end -->',
            '<!-- portfolio:one:start --><!-- portfolio:one:end -->')
        self.assertIn('- v0.2.0: historical snapshot recorded closed; 2 closed / 1 open issues. '
                      'Milestone URL no longer available as of 2026-10-27.', report)
        self.assertNotIn('milestone/2', report + readme + website)
        self.assertIn('Last closed milestone: v0.1.0 (2026-10-01).', website)

    def test_only_significant_changes_replace_a_record(self):
        old = {'id': 'one', 'repo': 'owner/repo', 'status': 'Prototype.',
               'sources': [{'path': 'README.md', 'url': 'https://github.com/owner/repo/blob/a/README.md', 'sha256': 'a'}],
               'release': None,
               'milestones': [{'number': 1, 'title': 'v0.1.0', 'state': 'closed', 'open_issues': 0, 'closed_issues': 4,
                               'closed_at': '2026-10-01T00:00:00Z', 'html_url': 'https://github.com/owner/repo/milestone/1'},
                              {'number': 2, 'title': 'v0.2.0', 'state': 'open', 'open_issues': 5, 'closed_issues': 1,
                               'closed_at': None, 'html_url': 'https://github.com/owner/repo/milestone/2'}]}
        self.assertTrue(refresh.significant(old, None))
        counts = json.loads(json.dumps(old))
        counts['milestones'][1].update(open_issues=3, closed_issues=3)
        counts['sources'][0].update(url='https://github.com/owner/repo/blob/b/README.md', sha256='b')
        counts['milestones'].append({'number': 3, 'title': 'v0.3.0', 'state': 'open', 'open_issues': 1,
                                     'closed_issues': 0, 'closed_at': None, 'html_url': 'https://github.com/owner/repo/milestone/3'})
        self.assertFalse(refresh.significant(counts, old))
        status = dict(counts, status='Working prototype.')
        self.assertTrue(refresh.significant(status, old))
        release = dict(counts, release={'tag': 'v0.2.0', 'url': 'u', 'published_at': '2026-10-30T00:00:00Z', 'notes_sha256': 'x'})
        self.assertTrue(refresh.significant(release, old))
        closed = json.loads(json.dumps(counts))
        closed['milestones'][1].update(state='closed', closed_at='2026-10-30T00:00:00Z')
        self.assertTrue(refresh.significant(closed, old))
        removed = json.loads(json.dumps(counts))
        removed['milestones'][1].update(html_url=None, removed_on='2026-10-30')
        self.assertTrue(refresh.significant(removed, old))

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

    def test_website_status_has_no_links(self):
        project = {'id': 'one', 'name': 'One', 'purpose': 'Purpose'}
        data = {'id': 'one', 'repo': 'owner/repo', 'status': 'Prototype.',
                'sources': [{'path': 'README.md', 'url': 'https://github.com/owner/repo/blob/abc/README.md', 'sha256': 'abc'}],
                'release': None, 'milestones': [{'number': 1, 'state': 'closed', 'title': 'v0.1.0',
                'closed_at': '2026-10-01T00:00:00Z', 'html_url': 'https://github.com/owner/repo/milestone/1',
                'closed_issues': 3, 'open_issues': 0}]}
        readme, website, report = refresh.render([project], [data],
            '<!-- portfolio:table:start --><!-- portfolio:table:end -->',
            '<!-- portfolio:one:start --><!-- portfolio:one:end -->')
        self.assertNotIn('<a ', website)
        self.assertIn('Last closed milestone: v0.1.0 (2026-10-01).', website)
        self.assertIn('https://github.com/owner/repo/milestone/1', readme)


if __name__ == '__main__':
    unittest.main()
