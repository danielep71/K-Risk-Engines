"""Tests for the repository settings tool (.github/scripts/setup_repository.py).

Adapted from danielep71/MyTemplate's tests/test_setup_repository.py (see
NOTICE.md); the hub adds rebase merging and the GitHub Pages source.
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import setup_repository as setup  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


class FakeAPI:
    def __init__(self) -> None:
        self.repo: dict[str, Any] = {
            'full_name': 'example/project', 'visibility': 'private', 'default_branch': 'main',
            'permissions': {'admin': True}, 'allow_merge_commit': True, 'allow_squash_merge': True,
            'allow_rebase_merge': True, 'delete_branch_on_merge': False,
            'allow_update_branch': False, 'has_projects': True, 'has_downloads': True}
        self.rules: list[dict[str, Any]] = []
        self.writes: list[tuple[str, str, Any]] = []
        self.green = True
        self.ignore_patch = False
        self.reporting = False
        self.alerts = False
        self.fixes = False
        self.pages: dict[str, Any] | None = None

    def not_found(self, endpoint: str) -> Any:
        raise setup.SetupError(f'GET {endpoint} failed (HTTP 404). Check gh authentication.')

    def switch(self, method: str, endpoint: str, attribute: str) -> Any:
        if method == 'GET':
            if attribute == 'reporting':
                return {'enabled': self.reporting}
            if attribute == 'alerts':
                return None if self.alerts else self.not_found(endpoint)
            return {'enabled': self.fixes, 'paused': False} if self.alerts else self.not_found(endpoint)
        self.writes.append((method, endpoint, None))
        setattr(self, attribute, method == 'PUT')
        return None

    def __call__(self, method: str, endpoint: str, payload: Any = None) -> Any:
        switches = {'/private-vulnerability-reporting': 'reporting',
                    '/vulnerability-alerts': 'alerts', '/automated-security-fixes': 'fixes'}
        for suffix, attribute in switches.items():
            if endpoint.endswith(suffix):
                return self.switch(method, endpoint, attribute)
        if endpoint.endswith('/pages'):
            if method == 'GET':
                return (copy.deepcopy(dict(self.pages, url='https://example/'))
                        if self.pages else self.not_found(endpoint))
            self.writes.append((method, endpoint, copy.deepcopy(payload)))
            self.pages = copy.deepcopy(payload)
            return {}
        if method != 'GET':
            self.writes.append((method, endpoint, copy.deepcopy(payload)))
            if method == 'POST':
                self.rules.append(dict(copy.deepcopy(payload), id=len(self.rules) + 1,
                                       source_type='Repository'))
            elif method == 'PUT':
                i = int(endpoint.rsplit('/', 1)[1])
                self.rules = [dict(copy.deepcopy(payload), id=i, source_type='Repository')
                              if r['id'] == i else r for r in self.rules]
            elif method == 'PATCH' and not self.ignore_patch:
                changes = copy.deepcopy(payload)
                analysis = changes.pop('security_and_analysis', None)
                if analysis:
                    self.repo.setdefault('security_and_analysis', {}).update(analysis)
                self.repo.update(changes)
            return {}
        if '/check-runs?' in endpoint:
            return {'check_runs': [{'name': 'HTML and links', 'app': {'id': 15368},
                                    'status': 'completed',
                                    'conclusion': 'success' if self.green else 'failure'}]}
        if '/branches/' in endpoint:
            return {'commit': {'sha': 'abc'}}
        if '/rulesets?' in endpoint:
            return copy.deepcopy(self.rules)
        if '/rulesets/' in endpoint:
            number = int(endpoint.rsplit('/', 1)[1])
            return copy.deepcopy(next(r for r in self.rules if r['id'] == number))
        return copy.deepcopy(self.repo)


class SetupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.api = FakeAPI()
        self.args = argparse.Namespace(repo='example/project', config=setup.CONFIG, apply=False,
                                       check=False, update_existing=False, report=None)

    def run_setup(self) -> int:
        with redirect_stdout(io.StringIO()):
            return setup.run(self.args, self.api)

    def test_preview_never_writes(self) -> None:
        self.assertEqual(self.run_setup(), 0)
        self.assertEqual(self.api.writes, [])

    def test_check_returns_drift_without_writes(self) -> None:
        self.args.check = True
        self.assertEqual(self.run_setup(), 1)
        self.assertEqual(self.api.writes, [])

    def test_apply_verify_and_second_run_is_noop(self) -> None:
        self.args.apply = True
        self.assertEqual(self.run_setup(), 0)
        # Five rulesets, alerts, security updates, the Pages site, general settings.
        self.assertEqual([w[0] for w in self.api.writes], ['POST'] * 5 + ['PUT', 'PUT', 'POST', 'PATCH'])
        self.assertEqual([w[1].rsplit('/', 1)[1] for w in self.api.writes[5:8]],
                         ['vulnerability-alerts', 'automated-security-fixes', 'pages'])
        self.assertEqual(self.api.writes[-1][2], {'allow_rebase_merge': False, 'delete_branch_on_merge': True,
                                                  'allow_update_branch': True, 'has_projects': False,
                                                  'has_downloads': False})
        self.api.writes.clear()
        self.assertEqual(self.run_setup(), 0)
        self.assertEqual(self.api.writes, [])

    def test_a_different_pages_source_is_updated(self) -> None:
        self.api.pages = {'build_type': 'legacy', 'source': {'branch': 'gh-pages', 'path': '/'}}
        self.args.apply, self.args.update_existing = True, True
        self.assertEqual(self.run_setup(), 0)
        self.assertIn(('PUT', 'repos/example/project/pages',
                       {'build_type': 'legacy', 'source': {'branch': 'main', 'path': '/'}}), self.api.writes)

    def test_failed_check_blocks_all_writes(self) -> None:
        self.args.apply = True
        self.api.green = False
        with self.assertRaisesRegex(setup.SetupError, 'has not succeeded'):
            self.run_setup()
        self.assertEqual(self.api.writes, [])

    def test_non_admin_blocks_all_writes(self) -> None:
        self.args.apply = True
        self.api.repo['permissions']['admin'] = False
        with self.assertRaisesRegex(setup.SetupError, 'Administrative'):
            self.run_setup()
        self.assertEqual(self.api.writes, [])

    def test_existing_rule_changes_require_explicit_flag(self) -> None:
        rule = copy.deepcopy(setup.load_config(setup.CONFIG)['rulesets'][0])
        rule.update(id=1, source_type='Repository', enforcement='disabled')
        self.api.rules = [rule]
        self.args.apply = True
        with self.assertRaisesRegex(setup.SetupError, 'named ruleset differs'):
            self.run_setup()
        self.assertEqual(self.api.writes, [])
        self.args.update_existing = True
        self.assertEqual(self.run_setup(), 0)

    def test_unmanaged_rulesets_are_named_and_preserved(self) -> None:
        self.api.rules = [{'name': 'Require website checks', 'id': 10, 'source_type': 'Repository',
                           'target': 'branch', 'enforcement': 'disabled',
                           'conditions': {'ref_name': {'include': ['~DEFAULT_BRANCH'], 'exclude': []}}}]
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(setup.run(self.args, self.api), 0)
        self.assertIn('unmanaged ruleset "Require website checks" (branch: ~DEFAULT_BRANCH; disabled)',
                      output.getvalue())
        self.args.apply = True
        self.run_setup()
        self.assertEqual(self.api.rules[0]['name'], 'Require website checks')

    def test_public_repository_enables_reporting_and_secret_scanning_once(self) -> None:
        self.api.repo['visibility'] = 'public'
        self.args.apply = True
        self.assertEqual(self.run_setup(), 0)
        self.assertIn(('PUT', 'repos/example/project/private-vulnerability-reporting', None),
                      self.api.writes)
        self.assertIn(('PATCH', 'repos/example/project',
                       {'security_and_analysis': {'secret_scanning': {'status': 'enabled'},
                                                  'secret_scanning_push_protection': {'status': 'enabled'}}}),
                      self.api.writes)
        self.api.writes.clear()
        self.assertEqual(self.run_setup(), 0)
        self.assertEqual(self.api.writes, [])

    def test_private_repository_skips_public_only_features_with_a_note(self) -> None:
        self.args.apply = True
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(setup.run(self.args, self.api), 0)
        self.assertIn('private_vulnerability_reporting, secret_scanning, '
                      'secret_scanning_push_protection apply only to public repositories',
                      output.getvalue())
        self.assertFalse(any('private-vulnerability' in endpoint or 'security_and_analysis' in str(payload)
                             for _, endpoint, payload in self.api.writes))

    def test_dependent_security_features_are_rejected(self) -> None:
        config = setup.load_config(setup.CONFIG)
        for disabled, needed_by in (('secret_scanning', 'Push protection'),
                                    ('vulnerability_alerts', 'security updates')):
            broken = copy.deepcopy(config)
            broken['security'][disabled] = False
            with patch.object(Path, 'read_text', return_value=json.dumps(broken)), \
                    self.assertRaisesRegex(setup.SetupError, needed_by):
                setup.load_config(Path('settings.json'))

    def test_incomplete_pages_configuration_is_rejected(self) -> None:
        broken = copy.deepcopy(setup.load_config(setup.CONFIG))
        del broken['pages']['source']['path']
        with patch.object(Path, 'read_text', return_value=json.dumps(broken)), \
                self.assertRaisesRegex(setup.SetupError, 'Pages'):
            setup.load_config(Path('settings.json'))

    def test_report_records_drift_then_verification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.args.report = Path(directory) / 'evidence' / 'settings.md'
            self.args.check = True
            self.assertEqual(self.run_setup(), 1)
            drift = self.args.report.read_text(encoding='utf-8')
            self.assertIn('- Result: **DRIFT**', drift)
            self.assertIn('| Protect main | — | missing |', drift)
            self.assertIn('| `allow_rebase_merge` | off | on |', drift)
            self.assertIn('| source branch | `main` | not published |', drift)
            self.assertIn('| `secret_scanning` | on | not applied (public repositories only) |', drift)
            self.args.check, self.args.apply = False, True
            self.assertEqual(self.run_setup(), 0)
            verified = self.args.report.read_text(encoding='utf-8')
            self.assertIn('- Result: **VERIFIED**', verified)
            self.assertIn('| Protect main | 1 | matches |', verified)
            self.assertIn('| source branch | `main` | `main` |', verified)
            self.assertIn('| `vulnerability_alerts` | on | on |', verified)
        self.assertEqual([w for w in self.api.writes if 'evidence' in w[1]], [])

    def test_readback_detects_ignored_changes(self) -> None:
        self.args.apply = True
        self.api.ignore_patch = True
        with self.assertRaisesRegex(setup.SetupError, 'Read-back'):
            self.run_setup()

    def test_duplicate_names_rejected_before_writes(self) -> None:
        name = setup.load_config(setup.CONFIG)['rulesets'][0]['name']
        self.api.rules = [{'name': name, 'id': 1}, {'name': name, 'id': 2}]
        with self.assertRaisesRegex(setup.SetupError, 'Ambiguous'):
            self.run_setup()
        self.assertFalse(self.api.writes)


class ConfigurationTests(unittest.TestCase):
    def test_required_status_check_is_html_and_links(self) -> None:
        from test_workflow_controls import REQUIRED_CHECK
        config = setup.load_config(setup.CONFIG)
        contexts = {check['context'] for ruleset in config['rulesets'] for rule in ruleset['rules']
                    if rule['type'] == 'required_status_checks'
                    for check in rule['parameters']['required_status_checks']}
        self.assertEqual(contexts, {REQUIRED_CHECK})

    def test_every_managed_ruleset_is_documented(self) -> None:
        document = (ROOT / 'docs/REPOSITORY_SETTINGS.md').read_text(encoding='utf-8')
        for ruleset in setup.load_config(setup.CONFIG)['rulesets']:
            with self.subTest(ruleset=ruleset['name']):
                self.assertIn(f"| {ruleset['name']} |", document)

    def test_order_is_not_drift_but_extra_rule_is(self) -> None:
        rule = copy.deepcopy(setup.load_config(setup.CONFIG)['rulesets'][0])
        reordered = copy.deepcopy(rule)
        reordered['rules'].reverse()
        self.assertEqual(setup.rule_spec(rule), setup.rule_spec(reordered))
        reordered['rules'].append({'type': 'creation'})
        self.assertNotEqual(setup.rule_spec(rule), setup.rule_spec(reordered))

    def test_pagination_reads_beyond_first_page(self) -> None:
        calls: list[str] = []

        def call(method: str, endpoint: str) -> Any:
            calls.append(endpoint)
            return list(range(100)) if endpoint.endswith('&page=1') else [100]
        self.assertEqual(len(setup.pages(call, 'repos/x/y/rulesets?includes_parents=false')), 101)
        self.assertEqual(len(calls), 2)

    def test_cli_uses_explicit_method_host_and_stdin(self) -> None:
        result = argparse.Namespace(returncode=0, stdout='{}', stderr='')
        with patch('setup_repository.subprocess.run', return_value=result) as run:
            setup.api('PATCH', 'repos/a/b', {'has_projects': False})
            command = run.call_args.args[0]
            self.assertIn('github.com', command)
            self.assertIn('PATCH', command)
            self.assertEqual(command[-2:], ['--input', '-'])
            self.assertEqual(run.call_args.kwargs['input'], '{"has_projects": false}')

    def test_api_error_does_not_print_server_detail(self) -> None:
        result = argparse.Namespace(returncode=1, stdout='', stderr='secret token HTTP 403')
        with patch('setup_repository.subprocess.run', return_value=result), \
                self.assertRaises(setup.SetupError) as caught:
            setup.api('GET', 'repos/a/b')
        self.assertIn('HTTP 403', str(caught.exception))
        self.assertNotIn('secret token', str(caught.exception))


if __name__ == '__main__':
    unittest.main()
