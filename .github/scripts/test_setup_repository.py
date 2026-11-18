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
from collections.abc import Callable
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import setup_repository as setup  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 11, 17, 9, 0, tzinfo=timezone.utc)


def configured(name: str) -> dict[str, Any]:
    return copy.deepcopy(next(r for r in setup.load_config(setup.CONFIG)['rulesets'] if r['name'] == name))


class FakeAPI:
    def __init__(self) -> None:
        self.repo: dict[str, Any] = {
            'full_name': 'example/project', 'visibility': 'private', 'default_branch': 'main',
            'permissions': {'admin': True}, 'allow_merge_commit': True, 'allow_squash_merge': True,
            'allow_rebase_merge': True, 'delete_branch_on_merge': False,
            'allow_update_branch': False, 'has_projects': True, 'has_downloads': True}
        self.rules: list[dict[str, Any]] = []
        self.inherited: list[dict[str, Any]] = []
        self.writes: list[tuple[str, str, Any]] = []
        self.green = True
        self.ignore_patch = False
        self.reporting = False
        self.alerts = False
        self.fixes = False
        self.paused = False
        self.pages: dict[str, Any] | None = None
        # GitHub Actions settings by actions/permissions suffix, matching the manifest.
        self.actions: dict[str, dict[str, Any]] = {
            '': {'enabled': True, 'allowed_actions': 'all', 'sha_pinning_required': True},
            '/workflow': {'default_workflow_permissions': 'read',
                          'can_approve_pull_request_reviews': False},
            '/fork-pr-contributor-approval': {'approval_policy': 'all_external_contributors'},
            '/artifact-and-log-retention': {'days': 90, 'maximum_allowed_days': 400}}
        # Endpoint suffixes whose GET fails, with the HTTP status.
        self.refused: dict[str, str] = {}
        self.fail_write: str | None = None
        self.hide_bypass = False

    def failure(self, method: str, endpoint: str, status: str) -> Any:
        raise setup.ApiError(method, endpoint, status)

    def switch(self, method: str, endpoint: str, attribute: str) -> Any:
        if method == 'GET':
            if attribute == 'reporting':
                return {'enabled': self.reporting}
            if attribute == 'alerts':
                return None if self.alerts else self.failure(method, endpoint, '404')
            return ({'enabled': self.fixes, 'paused': self.paused} if self.alerts
                    else self.failure(method, endpoint, '404'))
        self.writes.append((method, endpoint, None))
        setattr(self, attribute, method == 'PUT')
        return None

    def actions_permissions(self, method: str, endpoint: str, payload: Any) -> Any:
        suffix = endpoint.split('/actions/permissions', 1)[1]
        if method != 'GET':
            self.writes.append((method, endpoint, copy.deepcopy(payload)))
            return {}
        return copy.deepcopy(self.actions[suffix])

    def write(self, method: str, endpoint: str, payload: Any) -> Any:
        self.writes.append((method, endpoint, copy.deepcopy(payload)))
        if endpoint.endswith('/pages'):
            self.pages = copy.deepcopy(payload)
            return {}
        if method == 'POST':
            created = dict(copy.deepcopy(payload), id=len(self.rules) + 1, source_type='Repository')
            self.rules.append(created)
            return copy.deepcopy(created)
        if method == 'PUT':
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

    def __call__(self, method: str, endpoint: str, payload: Any = None) -> Any:
        if method != 'GET' and self.fail_write and endpoint.endswith(self.fail_write):
            self.writes.append((method, endpoint, copy.deepcopy(payload)))
            self.failure(method, endpoint, '422')
        if method == 'GET':
            for suffix, status in self.refused.items():
                if endpoint.split('?')[0].endswith(suffix):
                    self.failure(method, endpoint, status)
        if '/actions/permissions' in endpoint:
            return self.actions_permissions(method, endpoint, payload)
        switches = {'/private-vulnerability-reporting': 'reporting',
                    '/vulnerability-alerts': 'alerts', '/automated-security-fixes': 'fixes'}
        for suffix, attribute in switches.items():
            if endpoint.endswith(suffix):
                return self.switch(method, endpoint, attribute)
        if method != 'GET':
            return self.write(method, endpoint, payload)
        return self.get(endpoint)

    def get(self, endpoint: str) -> Any:
        if endpoint.endswith('/pages'):
            if self.pages is None:
                return self.failure('GET', endpoint, '404')
            return copy.deepcopy(dict(self.pages, url='https://example/'))
        if '/check-runs?' in endpoint:
            return {'check_runs': [{'name': 'HTML and links', 'app': {'id': 15368},
                                    'status': 'completed',
                                    'conclusion': 'success' if self.green else 'failure'}]}
        if '/branches/' in endpoint:
            return {'commit': {'sha': 'abc'}}
        if '/rulesets?' in endpoint:
            return [{'id': r['id'], 'name': r['name'], 'source_type': r.get('source_type', 'Repository')}
                    for r in self.rules + self.inherited]
        if '/rulesets/' in endpoint:
            number = int(endpoint.rsplit('/', 1)[1])
            rule = copy.deepcopy(next(r for r in self.rules if r['id'] == number))
            if self.hide_bypass:
                rule.pop('bypass_actors', None)
            return rule
        return copy.deepcopy(self.repo)

    def without_administrator_access(self) -> None:
        """What a token with read access only sees."""
        self.repo['permissions'] = {'admin': False, 'push': False, 'pull': True}
        for key in setup.GENERAL_KEYS:
            self.repo.pop(key, None)
        self.repo.pop('security_and_analysis', None)
        self.refused.update({'/vulnerability-alerts': '403', '/automated-security-fixes': '403',
                             '/private-vulnerability-reporting': '403', '/pages': '403',
                             '/actions/permissions': '403', '/actions/permissions/workflow': '403',
                             '/actions/permissions/artifact-and-log-retention': '403',
                             '/actions/permissions/fork-pr-contributor-approval': '403'})
        self.hide_bypass = True


class SetupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.api = FakeAPI()
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.tmp = Path(self.directory.name)
        self.args = argparse.Namespace(repo='example/project', config=setup.CONFIG, apply=False,
                                       check=False, update_existing=False, report=None, evidence=None,
                                       approve_plan=None, journal=None)

    def run_setup(self) -> int:
        with redirect_stdout(io.StringIO()):
            return setup.run(self.args, self.api, NOW)

    def run_output(self) -> tuple[int, str]:
        output = io.StringIO()
        with redirect_stdout(output):
            status = setup.run(self.args, self.api, NOW)
        return status, output.getvalue()

    def digest(self) -> str:
        """The PLAN SHA-256 that preview prints now."""
        saved = (self.args.apply, self.args.check, self.args.report, self.args.evidence)
        self.args.apply = self.args.check = False
        self.args.report = self.args.evidence = None
        _, output = self.run_output()
        self.args.apply, self.args.check, self.args.report, self.args.evidence = saved
        return next(line.split(': ')[1] for line in output.splitlines() if line.startswith('PLAN SHA-256: '))

    def approve(self, name: str = 'journal.json') -> Path:
        """Set up an apply of the plan that preview prints now, with a new journal path."""
        digest = self.digest()
        journal = self.tmp / name
        self.args.apply, self.args.check = True, False
        self.args.approve_plan, self.args.journal = digest, journal
        return journal

    def apply_baseline(self) -> None:
        self.approve('baseline.json')
        self.assertEqual(self.run_setup(), 0)
        self.api.writes.clear()
        self.args.apply, self.args.approve_plan, self.args.journal = False, None, None

    def write_names(self) -> list[str]:
        return [w[1].rsplit('/', 1)[1] for w in self.api.writes]

    # Preview, check and apply

    def test_preview_never_writes(self) -> None:
        self.assertEqual(self.run_setup(), 0)
        self.assertEqual(self.api.writes, [])

    def test_check_returns_drift_without_writes(self) -> None:
        self.args.check = True
        self.assertEqual(self.run_setup(), 1)
        self.assertEqual(self.api.writes, [])

    def test_apply_verify_and_second_run_is_noop(self) -> None:
        self.approve()
        self.assertEqual(self.run_setup(), 0)
        # Five rulesets, alerts, security updates, the Pages site, general settings.
        self.assertEqual([w[0] for w in self.api.writes], ['POST'] * 5 + ['PUT', 'PUT', 'POST', 'PATCH'])
        self.assertEqual(self.write_names()[5:8], ['vulnerability-alerts', 'automated-security-fixes', 'pages'])
        self.assertEqual(self.api.writes[-1][2], {'allow_rebase_merge': False, 'delete_branch_on_merge': True,
                                                  'allow_update_branch': True, 'has_projects': False,
                                                  'has_downloads': False})
        self.api.writes.clear()
        self.approve('second.json')
        self.assertEqual(self.run_setup(), 0)
        self.assertEqual(self.api.writes, [])

    def test_a_different_pages_source_is_updated(self) -> None:
        self.api.pages = {'build_type': 'legacy', 'source': {'branch': 'gh-pages', 'path': '/'}}
        self.approve()
        self.args.update_existing = True
        self.assertEqual(self.run_setup(), 0)
        self.assertIn(('PUT', 'repos/example/project/pages',
                       {'build_type': 'workflow', 'source': {'branch': 'main', 'path': '/'}}), self.api.writes)

    def test_failed_check_blocks_all_writes(self) -> None:
        self.approve()
        self.api.green = False
        with self.assertRaisesRegex(setup.SetupError, 'has not succeeded'):
            self.run_setup()
        self.assertEqual(self.api.writes, [])

    def test_non_admin_blocks_all_writes(self) -> None:
        self.api.repo['permissions']['admin'] = False
        self.approve()
        with self.assertRaisesRegex(setup.SetupError, 'Administrative'):
            self.run_setup()
        self.assertEqual(self.api.writes, [])

    def test_merge_methods_are_a_prerequisite_of_apply_only(self) -> None:
        self.api.repo['allow_squash_merge'] = False
        self.assertEqual(self.run_setup(), 0)
        self.approve()
        with self.assertRaisesRegex(setup.SetupError, 'Squash merging must be enabled'):
            self.run_setup()
        self.assertEqual(self.api.writes, [])

    def test_existing_rule_changes_require_explicit_flag(self) -> None:
        rule = dict(configured('Protect main'), id=1, source_type='Repository', enforcement='disabled')
        self.api.rules = [rule]
        self.approve()
        with self.assertRaisesRegex(setup.SetupError, 'named ruleset differs'):
            self.run_setup()
        self.assertEqual(self.api.writes, [])
        self.args.update_existing = True
        self.assertEqual(self.run_setup(), 0)

    def test_unmanaged_rulesets_are_named_and_preserved(self) -> None:
        self.api.rules = [{'name': 'Require website checks', 'id': 10, 'source_type': 'Repository',
                           'target': 'branch', 'enforcement': 'disabled', 'rules': [], 'bypass_actors': [],
                           'conditions': {'ref_name': {'include': ['~DEFAULT_BRANCH'], 'exclude': []}}}]
        _, output = self.run_output()
        self.assertIn('unmanaged ruleset "Require website checks" (branch: ~DEFAULT_BRANCH; disabled) '
                      'stays in place but is disabled.', output)
        self.assertNotIn('stays active', output)
        self.approve()
        self.run_setup()
        self.assertEqual(self.api.rules[0]['name'], 'Require website checks')

    def test_an_active_unmanaged_ruleset_is_said_to_stay_active(self) -> None:
        self.api.rules = [{'name': 'Legacy protection', 'id': 11, 'source_type': 'Repository',
                           'target': 'branch', 'enforcement': 'active', 'rules': [], 'bypass_actors': [],
                           'conditions': {'ref_name': {'include': ['~DEFAULT_BRANCH'], 'exclude': []}}}]
        _, output = self.run_output()
        self.assertIn('unmanaged ruleset "Legacy protection" (branch: ~DEFAULT_BRANCH; active) stays active.',
                      output)

    def test_inherited_rulesets_are_noted_not_managed(self) -> None:
        self.api.inherited = [{'id': 90, 'name': 'Organization baseline', 'source_type': 'Organization'}]
        status, output = self.run_output()
        self.assertEqual(status, 0)
        self.assertIn('NOTE: inherited rules also apply', output)
        self.assertNotIn('unmanaged ruleset "Organization baseline"', output)

    def test_public_repository_enables_reporting_and_secret_scanning_once(self) -> None:
        self.api.repo['visibility'] = 'public'
        self.api.repo['security_and_analysis'] = {}
        self.approve()
        self.assertEqual(self.run_setup(), 0)
        self.assertIn(('PUT', 'repos/example/project/private-vulnerability-reporting', None), self.api.writes)
        self.assertIn(('PATCH', 'repos/example/project',
                       {'security_and_analysis': {'secret_scanning': {'status': 'enabled'},
                                                  'secret_scanning_push_protection': {'status': 'enabled'}}}),
                      self.api.writes)
        self.api.writes.clear()
        self.approve('second.json')
        self.assertEqual(self.run_setup(), 0)
        self.assertEqual(self.api.writes, [])

    def test_private_repository_skips_public_only_features_with_a_note(self) -> None:
        self.approve()
        status, output = self.run_output()
        self.assertEqual(status, 0)
        self.assertIn('private_vulnerability_reporting, secret_scanning, '
                      'secret_scanning_push_protection apply only to public repositories', output)
        self.assertFalse(any('private-vulnerability' in endpoint or 'security_and_analysis' in str(payload)
                             for _, endpoint, payload in self.api.writes))

    def test_paused_security_updates_are_drift_not_verified(self) -> None:
        self.apply_baseline()
        self.api.paused = True
        self.args.check = True
        self.args.report = self.tmp / 'settings.md'
        status, output = self.run_output()
        self.assertEqual(status, 1)
        self.assertIn('enabled but paused', output)
        self.assertIn('| `automated_security_fixes` | on | paused |', self.args.report.read_text(encoding='utf-8'))

    def test_readback_detects_ignored_changes(self) -> None:
        self.approve()
        self.api.ignore_patch = True
        with self.assertRaisesRegex(setup.SetupError, 'Read-back'):
            self.run_setup()

    def test_duplicate_names_rejected_before_writes(self) -> None:
        name = 'Protect main'
        self.api.rules = [{'name': name, 'id': 1}, {'name': name, 'id': 2}]
        with self.assertRaisesRegex(setup.SetupError, 'Ambiguous'):
            self.run_setup()
        self.assertFalse(self.api.writes)

    # Records

    def test_report_records_drift_then_verification(self) -> None:
        self.args.report = self.tmp / 'evidence' / 'settings.md'
        self.args.check = True
        self.assertEqual(self.run_setup(), 1)
        drift = self.args.report.read_text(encoding='utf-8')
        self.assertIn('- Result: **DRIFT**', drift)
        self.assertIn(f'- Plan SHA-256: `{self.digest()}`', drift)
        self.assertIn('| Protect main | — | missing |', drift)
        self.assertIn('| `allow_rebase_merge` | off | on |', drift)
        self.assertIn('| source branch | `main` | not published |', drift)
        self.assertIn('| `secret_scanning` | on | not applied (public repositories only) |', drift)
        self.args.check = False
        self.approve()
        self.assertEqual(self.run_setup(), 0)
        verified = self.args.report.read_text(encoding='utf-8')
        self.assertIn('- Result: **VERIFIED**', verified)
        self.assertIn('| Protect main | 1 | matches |', verified)
        self.assertIn('| source branch | `main` | `main` |', verified)
        self.assertIn('| `vulnerability_alerts` | on | on |', verified)

    def test_json_evidence_records_values_sources_and_writes_without_payloads(self) -> None:
        self.args.evidence = self.tmp / 'settings-{date}.json'
        self.args.check = True
        self.assertEqual(self.run_setup(), 1)
        record = json.loads((self.tmp / 'settings-2026-11-17.json').read_text(encoding='utf-8'))
        self.assertEqual(set(record), {
            'schema_version', 'record', 'checked_at', 'tool', 'mode', 'repository', 'visibility',
            'default_branch', 'configuration', 'result', 'settings', 'security', 'pages', 'actions',
            'rulesets', 'unmanaged_rulesets', 'inherited_rulesets', 'planned_changes', 'plan_sha256', 'scope'})
        self.assertEqual((record['schema_version'], record['record'], record['mode'], record['result']),
                         (1, 'repository-settings-evidence', 'check', 'DRIFT'))
        self.assertEqual((record['checked_at'], record['repository'], record['default_branch']),
                         ('2026-11-17T09:00:00Z', 'example/project', 'main'))
        self.assertEqual(record['configuration'], {
            'path': 'docs/repository-settings.json',
            'sha256': __import__('hashlib').sha256(setup.CONFIG.read_bytes()).hexdigest()})
        self.assertEqual(record['plan_sha256'], self.digest())
        row = next(r for r in record['settings'] if r['setting'] == 'allow_rebase_merge')
        self.assertEqual((row['configured'], row['observed'], row['matches'], row['source']),
                         (False, True, False, 'GET repository allow_rebase_merge'))
        self.assertEqual(record['pages'][0]['source'], 'GET pages (HTTP 404: not published)')
        # Writes are named, never their payloads.
        self.assertEqual(record['planned_changes'][0],
                         {'method': 'POST', 'endpoint': 'repos/example/project/rulesets',
                          'ruleset': 'Protect main'})
        for change in record['planned_changes']:
            self.assertLessEqual(set(change), {'method', 'endpoint', 'ruleset'})
        text = json.dumps(record)
        for secret in ('token', 'Authorization', 'payload', 'required_status_checks'):
            self.assertNotIn(secret, text)

    def test_json_evidence_follows_the_configuration_bytes(self) -> None:
        changed = self.tmp / 'settings.json'
        changed.write_text(setup.CONFIG.read_text(encoding='utf-8') + '\n', encoding='utf-8')
        digests = []
        for config in (setup.CONFIG, changed):
            self.args.config = config
            self.args.evidence = self.tmp / f'evidence-{config.stem}.json'
            self.run_setup()
            record = json.loads(self.args.evidence.read_text(encoding='utf-8'))
            self.assertEqual(record['configuration']['sha256'],
                             __import__('hashlib').sha256(config.read_bytes()).hexdigest())
            digests.append((record['configuration']['sha256'], record['plan_sha256']))
        self.assertNotEqual(digests[0][0], digests[1][0])
        self.assertNotEqual(digests[0][1], digests[1][1])

    # Access without administrator rights (S12)

    def test_preview_and_check_run_without_administrator_access(self) -> None:
        self.apply_baseline()
        self.api.without_administrator_access()
        self.args.evidence = self.tmp / 'partial.json'
        status, output = self.run_output()
        self.assertEqual(status, 0)
        self.assertEqual(self.api.writes, [])
        self.args.check = True
        status, output = self.run_output()
        self.assertEqual(status, 1)
        self.assertIn('DIFF setting allow_rebase_merge: observed unknown, configured false '
                      '[GET repository (no allow_rebase_merge field: not reported to this token)].', output)
        self.assertIn('DIFF security vulnerability_alerts: observed unknown, configured true '
                      '[GET vulnerability-alerts (HTTP 403: unreadable)].', output)
        self.assertIn('DIFF pages build_type: observed unknown, configured "workflow" '
                      '[GET pages (HTTP 403: unreadable)].', output)
        self.assertIn('DIFF actions retention_days: observed unknown, configured 90 '
                      '[GET actions/permissions/artifact-and-log-retention (HTTP 403: unreadable)].', output)
        self.assertIn('DIFF ruleset "Protect main" (1) bypass_actors: not reported '
                      '(needs write access to the ruleset)', output)
        self.assertNotIn('VERIFIED', output)
        record = json.loads(self.args.evidence.read_text(encoding='utf-8'))
        self.assertEqual(record['result'], 'DRIFT')
        self.assertEqual({r['status'] for r in record['rulesets']}, {'unknown'})
        self.assertEqual(self.api.writes, [])

    def test_unknown_values_block_apply_before_any_write(self) -> None:
        self.apply_baseline()
        self.api.refused['/vulnerability-alerts'] = '403'
        self.api.refused['/automated-security-fixes'] = '403'
        self.api.hide_bypass = True
        self.approve()
        with self.assertRaisesRegex(setup.SetupError, 'unknown: vulnerability_alerts, automated_security_fixes, '
                                                      'ruleset "Protect main"'):
            self.run_setup()
        self.assertEqual(self.api.writes, [])
        self.assertFalse(self.args.journal.exists())

    def test_a_null_or_malformed_bypass_list_is_unknown(self) -> None:
        values: tuple[Any, ...] = (None, {})
        for value in values:
            with self.subTest(value=value):
                self.setUp()
                self.apply_baseline()
                self.api.rules[0]['bypass_actors'] = value
                self.args.check = True
                status, output = self.run_output()
                self.assertEqual(status, 1)
                self.assertIn(f'bypass_actors: not a list ({json.dumps(value)})', output)
                self.approve()
                self.args.update_existing = True
                with self.assertRaisesRegex(setup.SetupError, 'unknown: ruleset "Protect main"'):
                    self.run_setup()
                self.assertEqual(self.api.writes, [])

    def test_a_server_error_is_unknown_not_a_value(self) -> None:
        self.apply_baseline()
        self.api.refused['/pages'] = '500'
        self.args.check = True
        status, output = self.run_output()
        self.assertEqual(status, 1)
        self.assertIn('[GET pages (HTTP 500: unreadable)]', output)

    # Workflow token scope (S32)

    def workflow_check(self) -> tuple[int, str]:
        self.args.check = True
        self.args.token_scope = 'workflow'
        return self.run_output()

    def test_a_workflow_token_check_is_partial_not_drift(self) -> None:
        self.apply_baseline()
        self.api.without_administrator_access()
        status, output = self.workflow_check()
        self.assertEqual(status, setup.PARTIAL_EXIT)
        self.assertEqual(setup.PARTIAL_EXIT, 3)
        for line in ('NOT CHECKED setting allow_rebase_merge: GET repository (no allow_rebase_merge field',
                     'NOT CHECKED security vulnerability_alerts: GET vulnerability-alerts (HTTP 403: unreadable).',
                     'NOT CHECKED pages build_type: GET pages (HTTP 403: unreadable).',
                     'NOT CHECKED actions retention_days: GET actions/permissions/artifact-and-log-retention '
                     '(HTTP 403: unreadable).',
                     'NOT CHECKED ruleset "Protect main": bypass_actors: not reported (needs write access to the ruleset)',
                     'PARTIAL: no difference was found in the values this token can read',
                     'No plan: a workflow-token check never writes or records anything.'):
            self.assertIn(line, output)
        for absent in ('DIFF', 'VERIFIED', 'PLAN SHA-256', 'PREVIEW ONLY'):
            self.assertNotIn(absent, output)
        self.assertEqual(self.api.writes, [])

    def test_a_workflow_token_check_still_reports_a_difference_it_can_read(self) -> None:
        self.apply_baseline()
        self.api.without_administrator_access()
        self.api.repo['allow_rebase_merge'] = True
        self.api.rules[0]['enforcement'] = 'disabled'
        status, output = self.workflow_check()
        self.assertEqual(status, 1)
        self.assertIn('DIFF setting allow_rebase_merge: observed true, configured false', output)
        self.assertIn('DIFF ruleset "Protect main" (1) enforcement: observed "disabled"', output)
        self.assertNotIn('DIFF ruleset "Protect main" (1) bypass_actors', output)
        self.assertIn('NOT CHECKED ruleset "Protect release tags": bypass_actors: not reported', output)
        self.assertIn('NOT CHECKED security vulnerability_alerts', output)
        self.assertIn('DRIFT: documented settings do not match.', output)
        self.assertNotIn('PARTIAL', output)
        self.assertEqual(self.api.writes, [])

    def test_a_workflow_token_check_that_reads_everything_is_verified(self) -> None:
        self.apply_baseline()
        status, output = self.workflow_check()
        self.assertEqual(status, 0)
        self.assertIn('VERIFIED: all documented settings match.', output)
        self.assertNotIn('NOT CHECKED', output)

    def test_unreadable_rulesets_and_an_unpublished_looking_site_are_not_checked(self) -> None:
        self.apply_baseline()
        self.api.refused['/rulesets'] = '403'
        self.api.pages = None
        status, output = self.workflow_check()
        self.assertEqual(status, setup.PARTIAL_EXIT)
        self.assertIn('NOT CHECKED ruleset "Protect main": rulesets: not readable with this token', output)
        self.assertIn('NOT CHECKED pages build_type: GET pages (HTTP 404: not published).', output)
        self.assertNotIn('DIFF', output)
        # The same answers are errors and drift for an administrator.
        self.args.token_scope = 'admin'
        with self.assertRaises(setup.ApiError):
            self.run_output()
        self.api.refused.clear()
        status, output = self.run_output()
        self.assertEqual(status, 1)
        self.assertIn('DIFF pages build_type: observed not published', output)

    def test_the_workflow_scope_refuses_apply_and_records_on_the_command_line(self) -> None:
        for extra in (['--apply', '--approve-plan', '0' * 64, '--journal', 'journal.json'],
                      ['--report', 'record.md', '--check'], ['--evidence', 'record.json', '--check'], []):
            with self.subTest(extra=extra), patch.object(sys, 'argv', ['setup_repository.py', '--repo',
                                                                       'example/project', '--token-scope',
                                                                       'workflow', *extra]):
                with redirect_stderr(io.StringIO()) as stderr, self.assertRaises(SystemExit) as raised:
                    setup.main()
                self.assertEqual(raised.exception.code, 2)
                self.assertIn('--token-scope workflow', stderr.getvalue())

    # Plan approval (S27)

    def test_plan_digest_is_stable_and_printed(self) -> None:
        first, second = self.digest(), self.digest()
        self.assertEqual(first, second)
        self.assertRegex(first, r'^[0-9a-f]{64}$')
        # Key order and API ordering do not change the digest.
        config = setup.load_config(setup.CONFIG)
        report = setup.assess(config, setup.observe(self.api, 'example/project', config))
        steps = setup.plan(config, report, 'example/project')
        reordered = json.loads(json.dumps(report, sort_keys=True))
        self.assertEqual(setup.plan_digest('example/project', 'x', report, steps),
                         setup.plan_digest('example/project', 'x', reordered, steps))
        self.assertNotEqual(setup.plan_digest('example/project', 'x', report, steps),
                            setup.plan_digest('example/project', 'y', report, steps))

    def test_a_new_default_branch_changes_the_digest(self) -> None:
        self.apply_baseline()
        self.api.repo['has_projects'] = True
        before = self.digest()
        self.api.repo['default_branch'] = 'trunk'
        self.assertNotEqual(self.digest(), before)
        journal = self.tmp / 'journal.json'
        self.args.apply, self.args.approve_plan, self.args.journal = True, before, journal
        with self.assertRaisesRegex(setup.SetupError, 'differs from the approved one'):
            self.run_setup()
        self.assertEqual(self.api.writes, [])

    def test_every_output_expands_the_date(self) -> None:
        self.approve()
        self.args.journal = self.tmp / 'journal-{date}.json'
        self.args.report = self.tmp / 'settings-{date}.md'
        self.args.evidence = self.tmp / 'settings-{date}.json'
        self.assertEqual(self.run_setup(), 0)
        for name in ('journal-2026-11-17.json', 'settings-2026-11-17.md', 'settings-2026-11-17.json'):
            self.assertTrue((self.tmp / name).exists(), name)
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir() if '{date}' in p.name), [])
        # A second dated run refuses the journal it wrote, by its expanded name.
        self.approve()
        self.args.journal = self.tmp / 'journal-{date}.json'
        with self.assertRaisesRegex(setup.SetupError, 'journal-2026-11-17.json exists'):
            self.run_setup()

    def test_outputs_that_name_the_same_file_are_refused_before_any_call(self) -> None:
        cases = {('journal', 'evidence'): ('j.json', 'j.json'),
                 ('journal', 'report'): ('out/j.json', 'out/../out/j.json'),
                 ('report', 'evidence'): ('2026-11-17.md', '{date}.md')}
        for (first, second), (one, two) in cases.items():
            with self.subTest(first=first, second=second):
                self.setUp()
                if 'journal' in (first, second):
                    self.approve()
                setattr(self.args, first, self.tmp / one)
                setattr(self.args, second, self.tmp / two)
                calls = len(self.api.writes)
                with self.assertRaisesRegex(setup.SetupError, f'--{first} and --{second} name the same file'):
                    self.run_setup()
                self.assertEqual(len(self.api.writes), calls)
                self.assertFalse((self.tmp / one).exists())

    def test_a_wrong_digest_is_refused_before_any_write(self) -> None:
        journal = self.approve()
        self.args.approve_plan = '0' * 64
        with self.assertRaisesRegex(setup.SetupError, 'differs from the approved one'):
            self.run_setup()
        self.assertEqual(self.api.writes, [])
        self.assertFalse(journal.exists())

    def test_a_repository_changed_since_the_plan_is_refused_before_any_write(self) -> None:
        journal = self.approve()
        self.api.repo['has_projects'] = False
        with self.assertRaisesRegex(setup.SetupError, 'differs from the approved one'):
            self.run_setup()
        self.assertEqual(self.api.writes, [])
        self.assertFalse(journal.exists())

    def test_apply_requires_an_approved_plan_and_a_journal(self) -> None:
        self.args.apply = True
        with self.assertRaisesRegex(setup.SetupError, '--approve-plan SHA256 and --journal PATH'):
            self.run_setup()
        self.assertEqual(self.api.writes, [])
        for argv in (['--apply'], ['--apply', '--approve-plan', '0' * 64],
                     ['--apply', '--journal', 'j.json'], ['--journal', 'j.json'],
                     ['--apply', '--approve-plan', 'abc', '--journal', 'j.json']):
            with self.subTest(argv=argv), patch.object(sys, 'argv', ['setup', '--repo', 'a/b', *argv]), \
                    redirect_stdout(io.StringIO()), patch('sys.stderr', io.StringIO()), \
                    self.assertRaises(SystemExit):
                setup.main()

    # Journal (S28)

    def test_the_journal_exists_before_a_failing_write_and_records_it(self) -> None:
        journal = self.approve()
        self.api.fail_write = '/vulnerability-alerts'
        with self.assertRaisesRegex(setup.SetupError, 'HTTP 422'):
            self.run_setup()
        record = json.loads(journal.read_text(encoding='utf-8'))
        statuses = [entry['status'] for entry in record['writes']]
        self.assertEqual(statuses, ['done'] * 5 + ['failed', 'pending', 'pending', 'pending'])
        self.assertEqual(record['writes'][0]['ruleset_id'], 1)
        self.assertIn('HTTP 422', record['writes'][5]['error'])
        self.assertIsNone(record['readback'])
        self.assertEqual((record['plan_sha256'], record['record']),
                         (self.args.approve_plan, 'repository-settings-journal'))
        self.assertNotIn('payload', json.dumps(record))
        self.assertEqual(len(self.api.writes), 6)

    def test_the_journal_records_a_failed_readback(self) -> None:
        journal = self.approve()
        self.api.ignore_patch = True
        with self.assertRaisesRegex(setup.SetupError, 'Read-back'):
            self.run_setup()
        record = json.loads(journal.read_text(encoding='utf-8'))
        self.assertEqual(record['readback'], 'DRIFT')
        self.assertEqual({entry['status'] for entry in record['writes']}, {'done'})

    def test_an_existing_or_unwritable_journal_is_refused_before_any_write(self) -> None:
        journal = self.approve()
        journal.write_text('{}', encoding='utf-8')
        with self.assertRaisesRegex(setup.SetupError, 'exists; choose a new path'):
            self.run_setup()
        self.assertEqual(self.api.writes, [])
        self.approve('missing/../blocked/journal.json')
        blocked = self.tmp / 'blocked'
        blocked.write_text('a file, not a folder', encoding='utf-8')
        with self.assertRaises(OSError):
            self.run_setup()
        self.assertEqual(self.api.writes, [])

    def test_an_unchanged_apply_writes_nothing_and_journals_the_readback(self) -> None:
        self.apply_baseline()
        journal = self.approve('again.json')
        self.assertEqual(self.run_setup(), 0)
        self.assertEqual(self.api.writes, [])
        record = json.loads(journal.read_text(encoding='utf-8'))
        self.assertEqual((record['writes'], record['readback']), ([], 'VERIFIED'))

    # Actions settings

    def test_matching_actions_settings_are_verified_and_recorded(self) -> None:
        self.api.repo['visibility'] = 'public'
        self.api.repo['security_and_analysis'] = {}
        self.apply_baseline()
        self.args.report, self.args.check = self.tmp / 'settings.md', True
        self.assertEqual(self.run_setup(), 0)
        record = self.args.report.read_text(encoding='utf-8')
        self.assertIn('- Result: **VERIFIED**', record)
        for row in ('| `sha_pinning_required` | on | on |',
                    '| `default_workflow_permissions` | read | read |',
                    '| `can_approve_pull_request_reviews` | off | off |',
                    '| `fork_pr_approval_policy` | all_external_contributors | all_external_contributors |',
                    '| `retention_days` | 90 | 90 |'):
            self.assertIn(row, record)
        self.assertFalse([w for w in self.api.writes if '/actions/' in w[1]])

    def test_actions_settings_that_differ_or_are_unknown_are_drift(self) -> None:
        cases: dict[str, tuple[Callable[[FakeAPI], Any], str, str]] = {
            'mismatch': (lambda api: api.actions['/workflow'].update(default_workflow_permissions='write'),
                         'default_workflow_permissions: observed "write", configured "read" '
                         '[GET actions/permissions/workflow default_workflow_permissions].',
                         'never writes Actions settings'),
            'omitted': (lambda api: api.actions['/artifact-and-log-retention'].pop('days'),
                        'retention_days: observed unknown, configured 90 '
                        '[GET actions/permissions/artifact-and-log-retention (no days field)].',
                        'unknown: retention_days'),
            'inaccessible': (lambda api: api.refused.update({'/actions/permissions': '403'}),
                             'sha_pinning_required: observed unknown, configured true '
                             '[GET actions/permissions (HTTP 403: unreadable)].', 'unknown: sha_pinning_required'),
        }
        for case, (change, message, refusal) in cases.items():
            with self.subTest(case=case):
                self.setUp()
                self.api.repo['visibility'] = 'public'
                self.api.repo['security_and_analysis'] = {}
                self.apply_baseline()
                change(self.api)
                self.args.check = True
                status, output = self.run_output()
                self.assertEqual(status, 1)
                self.assertIn('DIFF actions ' + message + ' This tool never writes Actions settings.', output)
                self.approve()
                with self.assertRaisesRegex(setup.SetupError, refusal):
                    self.run_setup()
                self.assertFalse([w for w in self.api.writes if '/actions/' in w[1]])

    def test_fork_policy_applies_only_to_public_repositories(self) -> None:
        self.api.actions['/fork-pr-contributor-approval']['approval_policy'] = 'first_time_contributors'
        self.apply_baseline()
        self.args.report, self.args.check = self.tmp / 'settings.md', True
        self.assertEqual(self.run_setup(), 0)
        self.assertIn('| `fork_pr_approval_policy` | all_external_contributors | '
                      'not applied (public repositories only) |', self.args.report.read_text(encoding='utf-8'))
        # Once public, the policy applies: apply sets the rest and names it; check sees only it.
        self.api.repo['visibility'] = 'public'
        self.api.repo['security_and_analysis'] = {}
        self.args.report = None
        self.approve()
        with self.assertRaisesRegex(setup.SetupError,
                                    'fork_pr_approval_policy to "all_external_contributors" '
                                    r'\(observed "first_time_contributors"\)'):
            self.run_setup()
        self.args.apply, self.args.check = False, True
        status, output = self.run_output()
        self.assertEqual(status, 1)
        self.assertEqual([line for line in output.splitlines() if line.startswith('DIFF')],
                         ['DIFF actions fork_pr_approval_policy: observed "first_time_contributors", '
                          'configured "all_external_contributors" [GET actions/permissions/'
                          'fork-pr-contributor-approval approval_policy]. This tool never writes Actions settings.'])

    # Equivalent protection (S29)

    def rename(self, name: str, new: str) -> None:
        rule = next(r for r in self.api.rules if r['name'] == name)
        rule['name'] = new

    def ruleset_row(self, name: str) -> dict[str, Any]:
        config = setup.load_config(setup.CONFIG)
        report = setup.assess(config, setup.observe(self.api, 'example/project', config))
        return next(r for r in report['rulesets'] if r['name'] == name)

    def test_a_differently_named_ruleset_that_covers_a_configured_one_needs_no_write(self) -> None:
        self.apply_baseline()
        self.rename('Protect main', 'Main protection')
        row = self.ruleset_row('Protect main')
        self.assertEqual((row['status'], row['covered_by']), ('covered', ['Main protection']))
        self.args.check = True
        status, output = self.run_output()
        self.assertEqual(status, 0)
        self.assertIn('NOTE: ruleset "Protect main" is covered by "Main protection"', output)
        self.assertEqual(self.api.writes, [])

    def test_a_ruleset_on_the_default_branch_by_name_covers_one_on_default_branch(self) -> None:
        self.apply_baseline()
        rule = next(r for r in self.api.rules if r['name'] == 'Protect main')
        rule.update(name='Main by name', conditions={'ref_name': {'include': ['refs/heads/main'], 'exclude': []}})
        self.assertEqual(self.ruleset_row('Protect main')['status'], 'covered')
        rule['conditions'] = {'ref_name': {'include': ['~ALL'], 'exclude': []}}
        self.assertEqual(self.ruleset_row('Protect main')['status'], 'covered')

    def test_inactive_bypassed_or_excluding_rulesets_never_cover(self) -> None:
        changes: dict[str, Callable[[dict[str, Any]], Any]] = {
            'disabled': lambda r: r.update(enforcement='disabled'),
            'evaluate': lambda r: r.update(enforcement='evaluate'),
            'bypass': lambda r: r.update(bypass_actors=[{'actor_id': 5, 'actor_type': 'RepositoryRole',
                                                         'bypass_mode': 'always'}]),
            'exclusion': lambda r: r.update(conditions={'ref_name': {'include': ['~DEFAULT_BRANCH'],
                                                                     'exclude': ['refs/heads/main']}}),
        }
        for case, change in changes.items():
            with self.subTest(case=case):
                self.setUp()
                self.apply_baseline()
                self.rename('Protect main', 'Main protection')
                change(next(r for r in self.api.rules if r['name'] == 'Main protection'))
                self.assertEqual(self.ruleset_row('Protect main')['status'], 'missing')
                self.assertEqual(self.digest(), self.digest())
                _, output = self.run_output()
                self.assertIn('POST repos/example/project/rulesets', output)

    def test_a_named_ruleset_with_stronger_parameters_is_covered_not_replaced(self) -> None:
        self.apply_baseline()
        rule = next(r for r in self.api.rules if r['name'] == 'Protect main')
        pull = next(r for r in rule['rules'] if r['type'] == 'pull_request')
        pull['parameters']['required_approving_review_count'] = 1
        row = self.ruleset_row('Protect main')
        self.assertEqual((row['status'], row['covered_by']), ('covered', ['Protect main']))
        pull['parameters']['required_approving_review_count'] = 0
        pull['parameters']['allowed_merge_methods'] = ['merge', 'squash']
        self.assertEqual(self.ruleset_row('Protect main')['status'], 'differs')

    def test_a_weaker_ruleset_does_not_cover(self) -> None:
        self.apply_baseline()
        self.rename('Protect main', 'Main protection')
        rule = next(r for r in self.api.rules if r['name'] == 'Main protection')
        checks = next(r for r in rule['rules'] if r['type'] == 'required_status_checks')
        checks['parameters']['strict_required_status_checks_policy'] = False
        self.assertEqual(self.ruleset_row('Protect main')['status'], 'missing')

    def test_coverage_is_judged_against_the_rulesets_the_plan_leaves(self) -> None:
        self.apply_baseline()
        # Without the separate deletion rule, the release rule covers it.
        self.api.rules = [r for r in self.api.rules if r['name'] != 'Prevent release branch deletion']
        self.assertEqual(self.ruleset_row('Prevent release branch deletion')['covered_by'],
                         ['Protect release branches'])
        # A missing release rule is not covered by the separate deletion rule alone.
        self.setUp()
        self.apply_baseline()
        self.api.rules = [r for r in self.api.rules if r['name'] != 'Protect release branches']
        self.assertEqual(self.ruleset_row('Protect release branches')['status'], 'missing')

    def test_a_ruleset_the_plan_replaces_cannot_cover_a_missing_one(self) -> None:
        self.apply_baseline()
        # The live release rule also reaches traffic-history, which would cover the missing
        # traffic rule, but it allows rebase merges: it is weaker than configured and the plan
        # replaces it with the configured definition, which no longer reaches traffic-history.
        self.api.rules = [r for r in self.api.rules if r['name'] != 'Protect traffic history']
        release = next(r for r in self.api.rules if r['name'] == 'Protect release branches')
        release['conditions'] = {'ref_name': {'include': ['refs/heads/release/**',
                                                          'refs/heads/traffic-history'], 'exclude': []}}
        pull = next(r for r in release['rules'] if r['type'] == 'pull_request')
        pull['parameters']['allowed_merge_methods'] = ['squash', 'merge', 'rebase']
        self.assertEqual(self.ruleset_row('Protect release branches')['status'], 'differs')
        self.assertEqual(self.ruleset_row('Protect traffic history')['status'], 'missing')
        # Kept as it is (rebase not allowed), the broader live rule covers it.
        pull['parameters']['allowed_merge_methods'] = ['squash', 'merge']
        self.assertEqual(self.ruleset_row('Protect release branches')['status'], 'covered')
        self.assertEqual(self.ruleset_row('Protect traffic history')['covered_by'], ['Protect release branches'])

    def test_the_digest_binds_the_definition_of_a_covering_ruleset(self) -> None:
        self.apply_baseline()
        self.rename('Protect main', 'Main protection')
        before = self.digest()
        rule = next(r for r in self.api.rules if r['name'] == 'Main protection')
        pull = next(r for r in rule['rules'] if r['type'] == 'pull_request')
        pull['parameters']['required_approving_review_count'] = 2
        self.assertEqual(self.ruleset_row('Protect main')['status'], 'covered')
        self.assertNotEqual(self.digest(), before)


class ConfigurationTests(unittest.TestCase):
    def broken(self, change: Callable[[dict[str, Any]], Any], message: str) -> None:
        config = copy.deepcopy(setup.load_config(setup.CONFIG))
        change(config)
        with patch.object(Path, 'read_text', return_value=json.dumps(config)), \
                self.assertRaisesRegex(setup.SetupError, message):
            setup.load_config(Path('settings.json'))

    def test_dependent_security_features_are_rejected(self) -> None:
        self.broken(lambda c: c['security'].update(secret_scanning=False), 'Push protection')
        self.broken(lambda c: c['security'].update(vulnerability_alerts=False), 'security updates')

    def test_incomplete_pages_configuration_is_rejected(self) -> None:
        self.broken(lambda c: c['pages']['source'].pop('path'), 'Pages')

    def test_invalid_actions_configuration_is_rejected(self) -> None:
        for key, value in (('sha_pinning_required', 'yes'), ('default_workflow_permissions', 'admin'),
                           ('can_approve_pull_request_reviews', 0), ('fork_pr_approval_policy', 'nobody'),
                           ('retention_days', 0), ('retention_days', True)):
            with self.subTest(key=key, value=value):
                self.broken(lambda c: c['actions'].update({key: value}), 'Invalid Actions settings')
        self.broken(lambda c: c['actions'].pop('retention_days'), 'exactly the documented Actions settings')

    def test_invalid_rulesets_are_rejected(self) -> None:
        self.broken(lambda c: c['rulesets'][0].update(bypass_actors=None), 'bypass actors')
        self.broken(lambda c: c['rulesets'][0]['rules'].append({'type': 'deletion'}), 'repeats a rule type')
        self.broken(lambda c: c['rulesets'].pop(), 'five uniquely named')

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
        rule = configured('Protect main')
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
                self.assertRaises(setup.ApiError) as caught:
            setup.api('GET', 'repos/a/b')
        self.assertIn('HTTP 403', str(caught.exception))
        self.assertEqual(caught.exception.status, '403')
        self.assertNotIn('secret token', str(caught.exception))


if __name__ == '__main__':
    unittest.main()
