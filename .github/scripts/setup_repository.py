#!/usr/bin/env python3
"""Preview, check or apply this repository's settings through an authenticated GitHub CLI.

The settings are docs/repository-settings.json: the general options, the five
security features, the GitHub Pages source, the five GitHub Actions settings and
the five rulesets recorded in docs/REPOSITORY_SETTINGS.md. Preview (the default)
and --check only read: a value the token cannot read is unknown, with its source,
and counts as drift. They print the differences and the plan with its SHA-256.
--apply needs administrator access, writes only the approved plan
(--approve-plan) and journals it (--journal) before the first write and after
each, then reads everything back. The Actions settings are compared, never
written. --check --token-scope workflow is the partial, read-only variant for the
limited GITHUB_TOKEN of a workflow: a value it cannot read is NOT CHECKED, not drift,
the result is PARTIAL (exit 3) when nothing differs, no write is planned and no
record is written. A live ruleset under another name counts for a managed one when it
enforces every rule at least as strictly. Apply runs locally, never in CI.
Adapted from danielep71/MyTemplate's tools/setup_repository.py (see NOTICE.md).
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / 'docs/repository-settings.json'
TOOL = '.github/scripts/setup_repository.py'
EVIDENCE_SCHEMA_VERSION = 1
TOP_KEYS = {'schema_version', 'repository', 'security', 'pages', 'actions', 'rulesets'}
RULE_KEYS = ('name', 'target', 'enforcement', 'conditions', 'rules', 'bypass_actors')
GENERAL_KEYS = ('allow_rebase_merge', 'delete_branch_on_merge', 'allow_update_branch', 'has_projects',
                'has_downloads')
PAGES_KEYS = {'build_type', 'source'}
# Pages values compared, as (label, path in the configuration).
PAGES_FIELDS = (('build_type', ('build_type',)), ('source.branch', ('source', 'branch')),
                ('source.path', ('source', 'path')))
# The merge methods a ruleset may allow, and the repository option each needs.
MERGE_METHODS = {'merge': 'allow_merge_commit', 'squash': 'allow_squash_merge',
                 'rebase': 'allow_rebase_merge'}
# How the note on an unmanaged ruleset describes it, by enforcement.
UNMANAGED_STATE = {'active': 'stays active', 'disabled': 'stays in place but is disabled',
                   'evaluate': 'stays in place in evaluate mode'}
# Security features in write order (alerts before the security updates that need
# them), and whether GitHub offers them only on public repositories (private
# repositories need a paid licence for secret scanning).
SECURITY_PUBLIC_ONLY = {
    'private_vulnerability_reporting': True,
    'vulnerability_alerts': False,
    'automated_security_fixes': False,
    'secret_scanning': True,
    'secret_scanning_push_protection': True,
}
ANALYSIS_KEYS = ('secret_scanning', 'secret_scanning_push_protection')
# Each GitHub Actions setting: the endpoint under actions/permissions that reports
# it, its field there, and whether it applies only to public repositories. This
# tool reads them and never writes them; set them in Settings > Actions > General.
ACTIONS_SOURCES = {
    'sha_pinning_required': ('', 'sha_pinning_required', False),
    'default_workflow_permissions': ('/workflow', 'default_workflow_permissions', False),
    'can_approve_pull_request_reviews': ('/workflow', 'can_approve_pull_request_reviews', False),
    'fork_pr_approval_policy': ('/fork-pr-contributor-approval', 'approval_policy', True),
    'retention_days': ('/artifact-and-log-retention', 'days', False),
}
FORK_POLICIES = ('first_time_contributors_new_to_github', 'first_time_contributors',
                 'all_external_contributors')
REPOSITORY_PATTERN = re.compile(r'[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+')
DIGEST_PATTERN = re.compile(r'[0-9a-fA-F]{64}')
# Ruleset statuses that need no write and are not drift.
SATISFIED = ('matches', 'covered')
NOT_APPLIED = 'not applied (public repositories only)'
# Exit status of a workflow-token check that found no drift but could not observe everything.
PARTIAL_EXIT = 3

# GitHub API values are JSON; a call takes a method, an endpoint and an optional payload.
Json = Any
Call = Callable[..., Json]
Plan = list[tuple[str, str, Json]]
Row = dict[str, Json]


class SetupError(Exception):
    """A refusal or failure; the command exits with status 2."""


class ApiError(SetupError):
    """A GitHub API call that failed, with the HTTP status gh reported, if any."""

    def __init__(self, method: str, endpoint: str, status: str) -> None:
        super().__init__(f'{method} {endpoint} failed (HTTP {status}). Check gh authentication, '
                         'repository access, Administration permissions and plan availability. '
                         'No automatic rollback is performed; rerun preview to inspect partial changes.')
        self.status = status


def api(method: str, endpoint: str, payload: Json = None) -> Json:
    command = ['gh', 'api', '--hostname', 'github.com', '--method', method,
               '-H', 'Accept: application/vnd.github+json',
               '-H', 'X-GitHub-Api-Version: 2022-11-28', endpoint]
    if payload is not None:
        command += ['--input', '-']
    # Never inherit HTTP debug logging: it can expose authentication headers.
    env = dict(os.environ)
    env.pop('GH_DEBUG', None)
    # gh writes UTF-8; never decode with the locale code page (cp1252 on Windows).
    result = subprocess.run(command, input=json.dumps(payload) if payload is not None else None,
                            text=True, encoding='utf-8', capture_output=True, env=env, check=False)
    if result.returncode:
        # Do not print CLI stderr (may contain sensitive server or credential detail).
        match = re.search(r'HTTP (\d{3})', result.stderr)
        raise ApiError(method, endpoint, match.group(1) if match else 'unknown')
    return json.loads(result.stdout) if result.stdout.strip() else None


def read(call: Call, endpoint: str) -> tuple[Json, str | None]:
    """GET an endpoint: its value, or None and the HTTP status of the failure."""
    try:
        return call('GET', endpoint), None
    except ApiError as error:
        return None, error.status


def pages(call: Call, endpoint: str, key: str | None = None) -> list[Json]:
    result: list[Json] = []
    page = 1
    while True:
        separator = '&' if '?' in endpoint else '?'
        value = call('GET', f'{endpoint}{separator}per_page=100&page={page}')
        batch = value[key] if key else value
        result.extend(batch)
        if len(batch) < 100:
            return result
        page += 1


def canonical(value: Json) -> Json:
    """Rule arrays are sets for this baseline; ignore API ordering, not values."""
    if isinstance(value, dict):
        return {k: canonical(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return sorted((canonical(x) for x in value), key=lambda x: json.dumps(x, sort_keys=True))
    return value


def rule_spec(rule: dict[str, Json]) -> Json:
    # Ignore response metadata, but preserve unknown rules/parameters in comparison.
    return canonical({k: rule.get(k) for k in RULE_KEYS})


# Configuration


def check_actions(actions: Json) -> None:
    if not isinstance(actions, dict) or set(actions) != set(ACTIONS_SOURCES):
        raise SetupError('Configuration must contain exactly the documented Actions settings: '
                         + ', '.join(ACTIONS_SOURCES) + '.')
    days = actions['retention_days']
    if (type(actions['sha_pinning_required']) is not bool
            or actions['default_workflow_permissions'] not in ('read', 'write')
            or type(actions['can_approve_pull_request_reviews']) is not bool
            or actions['fork_pr_approval_policy'] not in FORK_POLICIES
            or type(days) is not int or days < 1):
        raise SetupError('Invalid Actions settings: sha_pinning_required and '
                         'can_approve_pull_request_reviews are booleans, default_workflow_permissions '
                         'is read or write, fork_pr_approval_policy is one of '
                         + ', '.join(FORK_POLICIES) + ', and retention_days is a positive integer.')


def check_rulesets(rulesets: Json) -> None:
    names: list[str] = []
    for rule in rulesets:
        if set(rule) != set(RULE_KEYS) or rule['target'] not in ('branch', 'tag') or rule['enforcement'] != 'active':
            raise SetupError('Invalid baseline ruleset.')
        if rule['bypass_actors'] != [] or rule['conditions']['ref_name']['exclude']:
            raise SetupError('Baseline must not contain bypass actors or excluded refs.')
        types = [entry['type'] for entry in rule['rules']]
        if len(types) != len(set(types)):
            raise SetupError(f'Ruleset "{rule["name"]}" repeats a rule type.')
        names.append(rule['name'])
    if len(names) != 5 or len(set(names)) != 5:
        raise SetupError('Expected five uniquely named baseline rulesets.')


def load_config(path: Path) -> dict[str, Json]:
    value = json.loads(path.read_text(encoding='utf-8'))
    if set(value) != TOP_KEYS or value['schema_version'] != 1:
        raise SetupError('Unsupported configuration schema.')
    pages_config = value['pages']
    if set(pages_config) != PAGES_KEYS or set(pages_config['source']) != {'branch', 'path'}:
        raise SetupError('Configuration must give the Pages build type and source branch and path.')
    security = value['security']
    if set(security) != set(SECURITY_PUBLIC_ONLY) or any(type(v) is not bool for v in security.values()):
        raise SetupError('Configuration must contain exactly the five documented boolean security features.')
    if security['secret_scanning_push_protection'] and not security['secret_scanning']:
        raise SetupError('Push protection requires secret scanning.')
    if security['automated_security_fixes'] and not security['vulnerability_alerts']:
        raise SetupError('Dependabot security updates require vulnerability alerts.')
    check_actions(value['actions'])
    if set(value['repository']) != set(GENERAL_KEYS) \
            or any(type(v) is not bool for v in value['repository'].values()):
        raise SetupError('Configuration must contain exactly the five documented boolean repository settings.')
    check_rulesets(value['rulesets'])
    return dict(value)


# Observation: read-only, and tolerant of what a token without administrator access cannot read.


def dependabot_states(call: Call, root: str) -> tuple[Row, Row]:
    """Dependabot alerts and security updates as observed: True, False or None when GitHub does not say."""
    value, failure = read(call, root + '/automated-security-fixes')
    if failure is None:
        value = value or {}
        paused = bool(value.get('enabled')) and bool(value.get('paused'))
        fixes: Row = {'observed': bool(value.get('enabled')), 'paused': paused,
                      'source': 'GET automated-security-fixes enabled' + (', paused' if paused else '')}
    elif failure == '404':
        fixes = {'observed': False, 'paused': False, 'source': 'GET automated-security-fixes (HTTP 404: off)'}
    else:
        fixes = {'observed': None, 'paused': False,
                 'source': f'GET automated-security-fixes (HTTP {failure}: unreadable)'}
    # The endpoint answers without content when the alerts are on and 404 when
    # they are off. Enabled security updates prove them on: GitHub requires them.
    _, failure = read(call, root + '/vulnerability-alerts')
    if failure is None:
        alerts: Row = {'observed': True, 'source': 'GET vulnerability-alerts (on)'}
    elif failure == '404':
        alerts = {'observed': False, 'source': 'GET vulnerability-alerts (HTTP 404: off)'}
    elif fixes['observed'] is True:
        alerts = {'observed': True, 'source': f'GET vulnerability-alerts (HTTP {failure}: unreadable); on, '
                                              'because Dependabot security updates are enabled and require them'}
    else:
        alerts = {'observed': None, 'source': f'GET vulnerability-alerts (HTTP {failure}: unreadable)'}
    return alerts, fixes


def security_states(call: Call, root: str, metadata: dict[str, Json], public: bool) -> dict[str, Row]:
    """Each security feature as observed: True, False or None when GitHub does not say."""
    states: dict[str, Row] = {}
    if public:
        value, failure = read(call, root + '/private-vulnerability-reporting')
        states['private_vulnerability_reporting'] = (
            {'observed': bool((value or {}).get('enabled')), 'source': 'GET private-vulnerability-reporting enabled'}
            if failure is None else
            {'observed': None, 'source': f'GET private-vulnerability-reporting (HTTP {failure}: unreadable)'})
    states['vulnerability_alerts'], states['automated_security_fixes'] = dependabot_states(call, root)
    # GitHub reports this block only to administrators of the repository.
    analysis = metadata.get('security_and_analysis')
    for key in ANALYSIS_KEYS if public else ():
        if not isinstance(analysis, dict):
            states[key] = {'observed': None,
                           'source': f'security_and_analysis.{key} (not reported without administrator access)'}
        else:
            states[key] = {'observed': (analysis.get(key) or {}).get('status') == 'enabled',
                           'source': f'security_and_analysis.{key}'}
    for feature, only in SECURITY_PUBLIC_ONLY.items():
        if only and not public:
            states[feature] = {'observed': None, 'source': NOT_APPLIED, 'applies': False}
    return {feature: states[feature] for feature in SECURITY_PUBLIC_ONLY}


def pages_state(call: Call, root: str) -> Row:
    """The Pages build type and source: published, not published (HTTP 404) or unknown."""
    value, failure = read(call, root + '/pages')
    if failure == '404':
        return {'published': False, 'value': None, 'source': 'GET pages (HTTP 404: not published)'}
    if failure is not None or not isinstance(value, dict):
        return {'published': None, 'value': None,
                'source': f'GET pages (HTTP {failure or "without content"}: unreadable)'}
    source = value.get('source') or {}
    return {'published': True, 'source': 'GET pages',
            'value': {'build_type': value.get('build_type'),
                      'source': {'branch': source.get('branch'), 'path': source.get('path')}}}


def actions_states(call: Call, root: str, public: bool) -> dict[str, Row]:
    """Each Actions setting as observed, or None with the reason it is not known."""
    answers: dict[str, tuple[Json, str | None]] = {}
    states: dict[str, Row] = {}
    for setting, (suffix, field, public_only) in ACTIONS_SOURCES.items():
        if public_only and not public:
            states[setting] = {'observed': None, 'source': NOT_APPLIED, 'applies': False}
            continue
        endpoint = 'actions/permissions' + suffix
        if endpoint not in answers:
            answers[endpoint] = read(call, f'{root}/{endpoint}')
        value, failure = answers[endpoint]
        if failure is not None:
            states[setting] = {'observed': None, 'source': f'GET {endpoint} (HTTP {failure}: unreadable)'}
        elif not isinstance(value, dict) or field not in value:
            states[setting] = {'observed': None, 'source': f'GET {endpoint} (no {field} field)'}
        else:
            states[setting] = {'observed': value[field], 'source': f'GET {endpoint} {field}'}
    return states


def observe(call: Call, repo: str, config: dict[str, Json], scope: str = 'admin') -> dict[str, Json]:
    """Read every value the configuration manages. Read-only.

    With the workflow scope, rulesets the token cannot read are reported as unreadable.
    """
    root = f'repos/{repo}'
    metadata = call('GET', root)
    public = metadata.get('visibility') == 'public'
    unreadable = False
    try:
        listed = pages(call, root + '/rulesets?includes_parents=true')
    except ApiError:
        if scope != 'workflow':
            raise
        listed, unreadable = [], True
    own = [r for r in listed if r.get('source_type', 'Repository') == 'Repository']
    managed = {rule['name'] for rule in config['rulesets']}
    names = [r['name'] for r in own if r['name'] in managed]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise SetupError('Ambiguous duplicate ruleset name: ' + ', '.join(duplicates))
    # A ruleset whose detail cannot be read does not hide the ones that can: only it is unchecked.
    details: list[Json] = []
    unreadable_names: list[str] = []
    for ruleset in own:
        try:
            details.append(call('GET', f'{root}/rulesets/{ruleset["id"]}'))
        except ApiError:
            if scope != 'workflow':
                raise
            unreadable_names.append(ruleset['name'])
    state: dict[str, Json] = {
        'metadata': metadata,
        'public': public,
        'rulesets': details,
        'inherited': [r['name'] for r in listed if r.get('source_type', 'Repository') != 'Repository'],
        'security': security_states(call, root, metadata, public),
        'pages': pages_state(call, root),
        'actions': actions_states(call, root, public),
    }
    if scope == 'workflow':
        state['rulesets_unreadable'] = unreadable
        state['unreadable_rulesets'] = unreadable_names
    return state


# Comparison


_ABSENT = '<absent>'


def keyed(spec: Json) -> Json:
    """A ruleset spec with its rules keyed by type, for readable difference paths."""
    result = dict(spec)
    rules = spec.get('rules') or []
    types = [rule.get('type') for rule in rules]
    if len(types) == len(set(types)):
        result['rules'] = {rule.get('type'): rule.get('parameters', {}) for rule in rules}
    return result


def differences(observed: Json, configured: Json, path: str = '') -> list[str]:
    """Each path where an observed value departs from the configured one."""
    if isinstance(observed, dict) and isinstance(configured, dict):
        found: list[str] = []
        for key in sorted(set(observed) | set(configured), key=str):
            found += differences(observed.get(key, _ABSENT), configured.get(key, _ABSENT),
                                 f'{path}.{key}' if path else str(key))
        return found
    if canonical(observed) == canonical(configured):
        return []
    return [f'{path}: observed {json.dumps(canonical(observed))}, '
            f'configured {json.dumps(canonical(configured))}']


def compare(key: str, name: str, configured: Json, state: Row) -> Row:
    """A row of the record; matches is None for a value that does not apply here."""
    row: Row = {key: name, 'configured': configured, 'observed': state['observed'], 'source': state['source']}
    if 'paused' in state:
        row['paused'] = state['paused']
    if not state.get('applies', True):
        row['matches'] = None
    elif row.get('paused') and configured is True:
        # Paused updates open no pull requests: drift when they should be on, but still
        # enabled, so turning the feature off needs the DELETE.
        row['matches'] = False
    else:
        row['matches'] = state['observed'] is not None and state['observed'] == configured
    return row


def setting_rows(config: dict[str, Json], metadata: dict[str, Json]) -> list[Row]:
    """The general options; a value GitHub does not report to this token is unknown."""
    rows: list[Row] = []
    for key in GENERAL_KEYS:
        reported = key in metadata and metadata[key] is not None
        rows.append({'setting': key, 'configured': config['repository'][key],
                     'observed': metadata.get(key),
                     'source': f'GET repository {key}' if reported
                     else f'GET repository (no {key} field: not reported to this token)',
                     'matches': reported and metadata.get(key) == config['repository'][key]})
    return rows


def pages_rows(config: dict[str, Json], state: Row) -> list[Row]:
    """The Pages build type, source branch and source path as configured and observed."""
    rows: list[Row] = []
    for label, path in PAGES_FIELDS:
        configured: Json = config['pages']
        observed: Json = state['value']
        for part in path:
            configured = configured[part]
            observed = None if observed is None else observed.get(part)
        rows.append({'setting': label, 'configured': configured, 'observed': observed,
                     'published': state['published'], 'source': state['source'],
                     'matches': state['published'] is True and observed == configured})
    return rows


# Coverage: live rulesets that enforce a configured one at least as strictly,
# under any names. Only an active ruleset of the same target with a reported and
# empty bypass list and no excluded refs can count: GitHub applies every active
# ruleset, so its rules hold whatever the configured name's ruleset does.


def parameters(rule: Json) -> dict[str, Json]:
    return dict(rule.get('parameters') or {})


def include_covers(candidate: Json, desired: dict[str, Json], default_branch: str) -> bool:
    """Whether a live ruleset's ref conditions reach every ref the configured one names."""
    conditions = (candidate.get('conditions') or {}).get('ref_name') or {}
    if conditions.get('exclude'):
        return False
    include = set(conditions.get('include') or [])
    if '~ALL' in include:
        return True
    wanted = set(desired['conditions']['ref_name']['include'])
    if desired['target'] == 'branch':
        # ~DEFAULT_BRANCH on either side names the same branch as its full ref.
        for refs in (include, wanted):
            if '~DEFAULT_BRANCH' in refs:
                refs.discard('~DEFAULT_BRANCH')
                refs.add(f'refs/heads/{default_branch}')
    return wanted <= include


def candidates(desired: dict[str, Json], rulesets: list[Json], default_branch: str) -> list[Json]:
    """The live rulesets whose scope can stand in for the configured one, the named one first."""
    found = [r for r in rulesets
             if r.get('enforcement') == 'active' and r.get('target') == desired['target']
             and r.get('bypass_actors') == [] and include_covers(r, desired, default_branch)]
    return sorted(found, key=lambda r: r.get('name') != desired['name'])


def covers_pull_request(configured: dict[str, Json], actual: dict[str, Json]) -> bool:
    """More approvals, a true option, fewer merge methods or more reviewers are stricter."""
    for key, value in configured.items():
        if key == 'allowed_merge_methods':
            if not set(actual.get(key, tuple(MERGE_METHODS))) <= set(value):
                return False
        elif key == 'required_approving_review_count':
            if actual.get(key, 0) < value:
                return False
        elif type(value) is bool:
            if actual.get(key, False) not in (True, value):
                return False
        elif isinstance(value, list):
            dumped = {json.dumps(canonical(item), sort_keys=True) for item in actual.get(key) or []}
            if not {json.dumps(canonical(item), sort_keys=True) for item in value} <= dumped:
                return False
        elif actual.get(key) != value:
            return False
    return True


def covers_status_checks(configured: dict[str, Json], actual: dict[str, Json]) -> bool:
    """A strict policy, more checks or enforcement on creation are stricter."""
    def checks(found: dict[str, Json]) -> set[tuple[Json, Json]]:
        return {(c.get('context'), c.get('integration_id')) for c in found.get('required_status_checks') or []}
    strict, on_create = 'strict_required_status_checks_policy', 'do_not_enforce_on_create'
    return (actual.get(strict, False) in (True, configured.get(strict, False))
            and checks(configured) <= checks(actual)
            and actual.get(on_create, False) in (False, configured.get(on_create, False)))


def covers_rule(rule: Json, candidate: Json) -> bool:
    """Whether a live rule of the configured rule's type is at least as strict as it."""
    configured, actual = parameters(rule), parameters(candidate)
    kind = rule['type']
    if kind in ('deletion', 'non_fast_forward'):
        return True
    if kind == 'update':
        allows = 'update_allows_fetch_and_merge'
        return actual.get(allows, False) in (False, configured.get(allows, False))
    if kind == 'required_status_checks':
        return covers_status_checks(configured, actual)
    if kind == 'pull_request':
        return covers_pull_request(configured, actual)
    return bool(canonical(actual) == canonical(configured))


def covered_by(desired: dict[str, Json], rulesets: list[Json], default_branch: str) -> list[str]:
    """The names of the live rulesets that together enforce every configured rule, or none."""
    possible = candidates(desired, rulesets, default_branch)
    names: list[str] = []
    for rule in desired['rules']:
        covering = next((c for c in possible if any(r.get('type') == rule['type'] and covers_rule(rule, r)
                                                    for r in c.get('rules') or [])), None)
        if covering is None:
            return []
        names.append(covering['name'])
    return sorted(set(names))


def assess_ruleset(desired: dict[str, Json], state: dict[str, Json]) -> Row:
    """The status of one configured ruleset: matches, covered, differs, missing or unknown."""
    actual = next((r for r in state['rulesets'] if r.get('name') == desired['name']), None)
    row: Row = {'name': desired['name'], 'id': None if actual is None else actual.get('id'),
                'status': 'missing', 'differences': [], 'covered_by': []}
    if actual is not None and not isinstance(actual.get('bypass_actors'), list):
        # GitHub omits the bypass list unless the token can write the ruleset. An
        # omitted, null or malformed list is not an empty one: the ruleset is unknown.
        visible = dict(actual, bypass_actors=desired['bypass_actors'])
        found = differences(keyed(rule_spec(visible)), keyed(rule_spec(desired)))
        found.append('bypass_actors: not reported (needs write access to the ruleset)'
                     if 'bypass_actors' not in actual
                     else f'bypass_actors: not a list ({json.dumps(actual["bypass_actors"])})')
        row.update(status='unknown', differences=found)
        return row
    if actual is not None:
        found = differences(keyed(rule_spec(actual)), keyed(rule_spec(desired)))
        if rule_spec(actual) != rule_spec(desired) and not found:
            found = ['rules: observed and configured differ']
        row.update(status='differs' if found else 'matches', differences=found)
    if row['status'] == 'differs' and actual is not None:
        # The named ruleset counts for itself: stronger parameters cover the configured ones.
        # A weaker one is replaced, whatever other rulesets enforce; a missing one is judged
        # in assess() against the rulesets as the plan leaves them.
        names = covered_by(desired, [actual], str(state['metadata'].get('default_branch', '')))
        if names:
            row.update(status='covered', covered_by=names)
    return row


def effective_rulesets(config: dict[str, Json], state: dict[str, Json], rows: list[Row]) -> list[Json]:
    """The live rulesets as the plan leaves them.

    A named ruleset that the plan replaces counts with its configured definition, not
    the live one: what the live definition enforces beyond the configuration is gone
    once it is replaced, so it cannot cover a missing ruleset.
    """
    replaced = {row['name'] for row in rows if row['status'] == 'differs'}
    desired = {r['name']: r for r in config['rulesets']}
    return [dict(desired[live['name']], id=live.get('id')) if live.get('name') in replaced else live
            for live in state['rulesets']]


NOT_CHECKED = 'not checked'


def mark_unobserved(rows: list[Row]) -> list[Row]:
    """Workflow scope: a value GitHub did not report to this token is NOT CHECKED, not drift."""
    unobserved = [row for row in rows if row['matches'] is False and row['observed'] is None]
    for row in unobserved:
        row.update(matches=None, not_checked=True)
    return unobserved


def mark_unobserved_rulesets(rows: list[Row], state: dict[str, Json], config: dict[str, Json]) -> None:
    """Workflow scope: a ruleset the token cannot fully read is NOT CHECKED unless it already differs.

    A ruleset whose bypass list is not reported is judged on what is visible, with the
    coverage rules of an administrator's check: a definition that enforces every configured
    rule at least as strictly, or differs in nothing visible, leaves only the bypass list
    unverified.
    """
    desired_by_name = {r['name']: r for r in config['rulesets']}
    for row in rows:
        if state.get('rulesets_unreadable'):
            row.update(status=NOT_CHECKED, differences=['rulesets: not readable with this token'])
        elif row['name'] in state.get('unreadable_rulesets', ()):
            row.update(status=NOT_CHECKED, differences=['ruleset: its definition could not be read'])
        elif row['status'] == 'unknown':
            # The last difference is the omitted bypass list; any other one is judged below.
            visible_differences = row['differences'][:-1]
            desired = desired_by_name[row['name']]
            actual = next(r for r in state['rulesets'] if r.get('name') == row['name'])
            visible = dict(actual, bypass_actors=desired['bypass_actors'])
            names = covered_by(desired, [visible], str(state['metadata'].get('default_branch', '')))
            if visible_differences and not names:
                row.update(status='differs', differences=visible_differences)
            else:
                row.update(status=NOT_CHECKED, differences=row['differences'][-1:])


def assess(config: dict[str, Json], state: dict[str, Json], scope: str = 'admin') -> dict[str, Json]:
    """Compare every managed value with what GitHub reports; an unknown value is drift.

    With the workflow scope an unreadable value is NOT CHECKED instead, and a result without
    drift but with such values is PARTIAL.
    """
    metadata = state['metadata']
    settings = setting_rows(config, metadata)
    security = [compare('feature', key, config['security'][key], state['security'][key])
                for key in SECURITY_PUBLIC_ONLY]
    pages_report = pages_rows(config, state['pages'])
    actions = [compare('setting', key, config['actions'][key], state['actions'][key])
               for key in ACTIONS_SOURCES]
    rulesets = [assess_ruleset(desired, state) for desired in config['rulesets']]
    if scope == 'workflow':
        for rows in (settings, security, pages_report, actions):
            mark_unobserved(rows)
        mark_unobserved_rulesets(rulesets, state, config)
    effective = effective_rulesets(config, state, rulesets)
    for row, desired in zip(rulesets, config['rulesets']):
        if row['status'] == 'missing':
            names = covered_by(desired, effective, str(metadata.get('default_branch', '')))
            if names:
                row.update(status='covered', covered_by=names)
    managed = {r['name'] for r in config['rulesets']}
    drift = (any(row['matches'] is False for row in settings + security + pages_report + actions)
             or any(row['status'] not in SATISFIED + (NOT_CHECKED,) for row in rulesets))
    partial = (any(row.get('not_checked') for row in settings + security + pages_report + actions)
               or any(row['status'] == NOT_CHECKED for row in rulesets))
    return {
        'result': 'DRIFT' if drift else 'PARTIAL' if partial else 'VERIFIED',
        'settings': settings, 'security': security, 'pages': pages_report, 'actions': actions,
        'rulesets': rulesets,
        'unmanaged_rulesets': [r['name'] for r in state['rulesets'] if r.get('name') not in managed],
        'inherited_rulesets': sorted(state['inherited'])}


# Plan


def plan(config: dict[str, Json], report: dict[str, Json], repo: str) -> Plan:
    """The writes that would make the repository match. Actions settings are never written.

    Missing rulesets are created before differing ones are replaced, so that a
    replacement never narrows protection that only the replaced definition gave. The
    general options come last: automatic deletion of merged branches must not start
    before the deletion rulesets protect the retained branches.
    """
    root = f'repos/{repo}'
    steps: Plan = []
    desired = {r['name']: r for r in config['rulesets']}
    for row in report['rulesets']:
        if row['status'] == 'missing':
            steps.append(('POST', root + '/rulesets', desired[row['name']]))
    for row in report['rulesets']:
        if row['status'] == 'differs':
            steps.append(('PUT', f'{root}/rulesets/{row["id"]}', desired[row['name']]))
    analysis: dict[str, dict[str, str]] = {}
    for row in report['security']:
        if row['matches'] is not False:
            continue
        if row['feature'] in ANALYSIS_KEYS:
            analysis[row['feature']] = {'status': 'enabled' if row['configured'] else 'disabled'}
        else:
            endpoint = root + '/' + row['feature'].replace('_', '-')
            steps.append(('PUT' if row['configured'] else 'DELETE', endpoint, None))
    if analysis:
        steps.append(('PATCH', root, {'security_and_analysis': analysis}))
    if any(row['matches'] is False for row in report['pages']):
        # With build type "workflow" a GitHub Actions workflow publishes; the source
        # branch and folder are only recorded. Apply refuses an unknown site.
        published = report['pages'][0]['published']
        steps.append(('PUT' if published else 'POST', root + '/pages', config['pages']))
    differing = {row['setting']: row['configured'] for row in report['settings'] if row['matches'] is False}
    if differing:
        steps.append(('PATCH', root, differing))
    return steps


def plan_digest(repo: str, config_sha256: str, report: dict[str, Json], steps: Plan,
                rulesets: list[Json] | None = None, default_branch: str | None = None) -> str:
    """SHA-256 of the plan: repository, default branch, configuration, observed values and exact writes.

    The default branch is included because a ruleset on ~DEFAULT_BRANCH protects
    whichever branch it is: a new default branch needs a new approval.

    The observed definitions of the live rulesets that cover a managed one are
    included, so an approval goes stale when the covering protection changes.
    Sources and timestamps are left out, so the same unchanged repository and
    configuration give the same digest, and any change to either changes it.
    """
    def stable(rows: list[Row]) -> list[Row]:
        return [{key: value for key, value in row.items() if key != 'source'} for row in rows]
    observed: dict[str, Json] = {
        'settings': stable(report['settings']), 'security': stable(report['security']),
        'pages': stable(report['pages']), 'actions': stable(report['actions']),
        'rulesets': report['rulesets'],
        'unmanaged_rulesets': sorted(report['unmanaged_rulesets']),
        'inherited_rulesets': sorted(report['inherited_rulesets'])}
    covering = sorted({name for row in report['rulesets'] for name in row['covered_by']})
    if covering:
        observed['covering_rulesets'] = {name: [rule_spec(r) for r in rulesets or [] if r.get('name') == name]
                                         for name in covering}
    document = {
        'repository': repo, 'default_branch': default_branch, 'configuration_sha256': config_sha256,
        'observed': observed,
        'writes': [{'method': method, 'endpoint': endpoint, 'payload': payload}
                   for method, endpoint, payload in steps],
    }
    text = json.dumps(document, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def step_record(method: str, endpoint: str, payload: Json) -> dict[str, Json]:
    """A write as the records show it: method and endpoint, never the payload.

    A ruleset write also names its ruleset, so that the journal and the evidence
    tell apart writes that share the endpoint ``repos/OWNER/REPO/rulesets``.
    """
    record: dict[str, Json] = {'method': method, 'endpoint': endpoint}
    if endpoint.split('/')[3:4] == ['rulesets'] and isinstance(payload, dict) and payload.get('name'):
        record['ruleset'] = payload['name']
    return record


# Output


def shown(row: Row) -> str:
    if row.get('published') is False:
        return 'not published'
    if row['observed'] is None:
        return 'unknown'
    return json.dumps(row['observed']) + (' (paused)' if row.get('paused') else '')


def print_notes(config: dict[str, Json], state: dict[str, Json], report: dict[str, Json]) -> None:
    metadata = state['metadata']
    print(f'Destination: {metadata["full_name"]}; visibility: {metadata["visibility"]}; '
          f'default branch: {metadata["default_branch"]}')
    if state['inherited']:
        print('NOTE: inherited rules also apply; they are not modified or certified by this script.')
    for detail in state['rulesets']:
        if detail.get('name') not in report['unmanaged_rulesets']:
            continue
        refs = ', '.join(((detail.get('conditions') or {}).get('ref_name') or {}).get('include') or [])
        enforcement = detail.get('enforcement', 'unknown enforcement')
        print(f'NOTE: unmanaged ruleset "{detail["name"]}" '
              f'({detail.get("target", "unknown target")}: {refs or "no ref conditions"}; '
              f'{enforcement}) {UNMANAGED_STATE.get(enforcement, "stays in place")}. This script '
              'never changes or deletes it; delete it in the repository settings if a managed '
              'ruleset replaces it.')
    skipped = [row['feature'] for row in report['security']
               if row['source'] == NOT_APPLIED and row['configured']]
    if skipped:
        print(f'NOTE: {", ".join(skipped)} apply only to public repositories here; they are not '
              f'applied while the destination is {metadata.get("visibility")}. Rerun the check '
              'after making the repository public.')
    if not state['public']:
        print(f'NOTE: fork_pr_approval_policy applies only to public repositories; it is not '
              f'checked while the destination is {metadata.get("visibility")}.')
    fixes = state['security']['automated_security_fixes']
    if fixes.get('paused') and config['security']['automated_security_fixes']:
        print('NOTE: Dependabot security updates are enabled but paused; they count as drift until '
              'GitHub resumes them, and an apply that cannot resume them fails its read-back.')


def difference_lines(report: dict[str, Json]) -> list[str]:
    """One line per managed value that differs from the configuration, and one per covered ruleset."""
    lines: list[str] = []
    for group, key in (('setting', 'settings'), ('security', 'security'), ('pages', 'pages'),
                       ('actions', 'actions')):
        for row in report[key]:
            if row['matches'] is False:
                name = row.get('setting', row.get('feature'))
                suffix = ' This tool never writes Actions settings.' if group == 'actions' else ''
                lines.append(f'DIFF {group} {name}: observed {shown(row)}, '
                             f'configured {json.dumps(row["configured"])} [{row["source"]}].{suffix}')
    for group, key in (('setting', 'settings'), ('security', 'security'), ('pages', 'pages'),
                       ('actions', 'actions')):
        lines += [f'NOT CHECKED {group} {row.get("setting", row.get("feature"))}: {row["source"]}.'
                  for row in report[key] if row.get('not_checked')]
    for row in report['rulesets']:
        if row['status'] == NOT_CHECKED:
            lines.append(f'NOT CHECKED ruleset "{row["name"]}": '
                         + (row['differences'][0] if row['differences'] else
                            'the bypass list is not reported without write access to the ruleset.'))
            continue
        if row['status'] == 'covered':
            names = ', '.join(f'"{name}"' for name in row['covered_by'])
            lines.append(f'NOTE: ruleset "{row["name"]}" is covered by {names}: every configured rule '
                         'is enforced at least as strictly there, so no write is planned for it.')
            continue
        if row['status'] == 'missing':
            lines.append(f'DIFF ruleset "{row["name"]}": missing')
        lines += [f'DIFF ruleset "{row["name"]}" ({row["id"]}) {line}' for line in row['differences']]
    return lines


def print_plan(steps: Plan) -> None:
    for method, endpoint, payload in steps:
        print(f'{method} {endpoint}')
        if payload is not None:
            print(json.dumps(payload, indent=2))


# Records


def markdown_record(state: dict[str, Json], report: dict[str, Json], plan_sha256: str, mode: str,
                    now: datetime) -> str:
    """A dated Markdown record of the managed settings as GitHub reports them."""
    metadata = state['metadata']

    def cell(value: Json) -> str:
        return 'on' if value is True else 'off' if value is False else str(value)

    def observed(row: Row) -> str:
        if row['matches'] is None:
            return NOT_APPLIED
        if row.get('paused'):
            return 'paused'
        return 'unknown' if row['observed'] is None else cell(row['observed'])

    def page(row: Row) -> str:
        if row['published'] is False:
            return 'not published'
        return 'unknown' if row['published'] is None else f'`{row["observed"]}`'

    def status(row: Row) -> str:
        if row['status'] == 'covered':
            return 'covered by ' + ', '.join(f'"{name}"' for name in row['covered_by'])
        return str(row['status'])

    lines = ['# Repository settings evidence', '',
             f'- Checked: **{now.strftime("%Y-%m-%dT%H:%M:%SZ")}** with `{TOOL}` ({mode})',
             f'- Destination: `{metadata["full_name"]}`; visibility: {metadata["visibility"]}; '
             f'default branch: `{metadata["default_branch"]}`',
             f'- Result: **{report["result"]}**',
             f'- Plan SHA-256: `{plan_sha256}`', '',
             '## General settings', '', '| Setting | Configured | Observed |', '| --- | --- | --- |']
    lines += [f'| `{row["setting"]}` | {cell(row["configured"])} | {observed(row)} |'
              for row in report['settings']]
    lines += ['', '## Security features', '', '| Feature | Configured | Observed |', '| --- | --- | --- |']
    lines += [f'| `{row["feature"]}` | {cell(row["configured"])} | {observed(row)} |'
              for row in report['security']]
    labels = {'build_type': 'build type', 'source.branch': 'source branch', 'source.path': 'source path'}
    lines += ['', '## GitHub Pages', '', '| Setting | Configured | Observed |', '| --- | --- | --- |']
    lines += [f'| {labels[row["setting"]]} | `{row["configured"]}` | {page(row)} |' for row in report['pages']]
    lines += ['', '## GitHub Actions settings', '',
              'Read from `actions/permissions` and compared; this tool never writes them.', '',
              '| Setting | Configured | Observed |', '| --- | --- | --- |']
    lines += [f'| `{row["setting"]}` | {cell(row["configured"])} | {observed(row)} |'
              for row in report['actions']]
    lines += ['', '## Managed rulesets', '', '| Ruleset | ID | Status |', '| --- | --- | --- |']
    lines += [f'| {row["name"]} | {"—" if row["id"] is None else row["id"]} | {status(row)} |'
              for row in report['rulesets']]
    lines += ['', '## Other rules', '',
              f'- Unmanaged repository rulesets: {", ".join(report["unmanaged_rulesets"]) or "none"}',
              f'- Inherited rulesets: {", ".join(report["inherited_rulesets"]) or "none"}',
              '', 'Unmanaged settings are outside this record.']
    return '\n'.join(lines) + '\n'


def evidence_record(config_path: Path, config_sha256: str, repo: str, state: dict[str, Json],
                    report: dict[str, Json], steps: Plan, plan_sha256: str, mode: str,
                    now: datetime) -> dict[str, Json]:
    """A dated JSON record of the managed settings as GitHub reports them; no write payloads."""
    try:
        shown_path = config_path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        shown_path = config_path.name
    metadata = state['metadata']
    return {
        'schema_version': EVIDENCE_SCHEMA_VERSION,
        'record': 'repository-settings-evidence',
        'checked_at': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'tool': TOOL,
        'mode': mode,
        'repository': metadata.get('full_name', repo),
        'visibility': metadata.get('visibility'),
        'default_branch': metadata.get('default_branch'),
        'configuration': {'path': shown_path, 'sha256': config_sha256},
        'result': report['result'],
        'settings': report['settings'],
        'security': report['security'],
        'pages': report['pages'],
        'actions': report['actions'],
        'rulesets': report['rulesets'],
        'unmanaged_rulesets': report['unmanaged_rulesets'],
        'inherited_rulesets': report['inherited_rulesets'],
        'planned_changes': [step_record(*step) for step in steps],
        'plan_sha256': plan_sha256,
        'scope': 'Only the settings that the configuration manages are recorded; '
                 'everything else is outside this record.',
    }


def write_text(path: Path, text: str, what: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='\n')
    print(f'{what} written to {path}')


def write_json_atomically(path: Path, record: dict[str, Json]) -> None:
    """Write the record to a temporary file beside the path, then replace the path with it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=path.name + '.', suffix='.tmp')
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as handle:
            handle.write(json.dumps(record, indent=2) + '\n')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


# Apply


def check_prerequisites(state: dict[str, Json], report: dict[str, Json]) -> None:
    """Refuse to apply anything that cannot be written safely, before any write."""
    metadata = state['metadata']
    if metadata.get('archived') or metadata.get('disabled'):
        raise SetupError('Destination is archived or disabled.')
    if not (metadata.get('permissions') or {}).get('admin'):
        raise SetupError('Administrative access to the destination is required to apply the settings.')
    unknown = [row['setting'] for row in report['settings'] if row['observed'] is None]
    unknown += [row['feature'] for row in report['security']
                if row['matches'] is not None and row['observed'] is None]
    if report['pages'][0]['published'] is None:
        unknown.append('pages')
    # Actions settings are never written, but an unread one would only fail the
    # read-back after every other write; refuse before any write instead.
    unknown += [row['setting'] for row in report['actions']
                if row['matches'] is not None and row['observed'] is None]
    unknown += [f'ruleset "{row["name"]}"' for row in report['rulesets'] if row['status'] == 'unknown']
    if unknown:
        raise SetupError('Cannot apply while these managed values are unknown: ' + ', '.join(unknown)
                         + '. Rerun preview to see why GitHub did not report them.')
    # The release rulesets allow squash and merge commits, which this tool does not manage.
    if not metadata.get('allow_merge_commit'):
        raise SetupError('Merge commits must be enabled before applying these rules.')
    if not metadata.get('allow_squash_merge'):
        raise SetupError('Squash merging must be enabled for the release-branch baseline.')


def check_required_checks(call: Call, repo: str, config: dict[str, Json], metadata: dict[str, Json]) -> None:
    root = f'repos/{repo}'
    branch = call('GET', root + '/branches/' + quote(metadata['default_branch'], safe=''))
    checks = pages(call, root + '/commits/' + branch['commit']['sha'] + '/check-runs?filter=latest', 'check_runs')
    required = [check for r in config['rulesets'] for rule in r['rules']
                if rule['type'] == 'required_status_checks'
                for check in rule['parameters']['required_status_checks']]
    for required_check in required:
        if not any(c['name'] == required_check['context'] and
                   c.get('app', {}).get('id') == required_check['integration_id'] and
                   c.get('conclusion') == 'success' and c.get('status') == 'completed' for c in checks):
            raise SetupError('Required GitHub Actions check has not succeeded on the current default-branch '
                             'HEAD. Enable Actions and run Website checks (HTML and links) before '
                             'applying protection.')


def readback_error(report: dict[str, Json]) -> SetupError:
    """The read-back failure, naming each Actions setting to set by hand."""
    actions = [row for row in report['actions'] if row['matches'] is False]
    rest = (any(row['matches'] is False for row in report['settings'] + report['security'] + report['pages'])
            or any(row['status'] not in SATISFIED for row in report['rulesets']))
    message = 'Read-back verification failed'
    message += ('; the differences above remain. Rerun preview to inspect them.' if rest
                else ': the other settings match, but this tool never writes Actions settings.')
    if actions:
        message += (' Set ' + ', '.join(f'{row["setting"]} to {json.dumps(row["configured"])} '
                                        f'(observed {shown(row)})' for row in actions)
                    + " in the repository's Settings > Actions > General, then rerun --check.")
    return SetupError(message)


def check_approval(args: argparse.Namespace, digest: str) -> None:
    """Refuse an apply that is not bound to the plan just printed, before any write."""
    approved, journal = getattr(args, 'approve_plan', None), getattr(args, 'journal', None)
    if not approved or journal is None:
        raise SetupError('--apply requires --approve-plan SHA256 and --journal PATH.')
    if approved.lower() != digest:
        raise SetupError('The plan differs from the approved one: the repository or the configuration '
                         'changed since the reviewed plan, or the digest is not the one preview printed. '
                         'Nothing was written. Run preview again, review the plan above and approve '
                         'its PLAN SHA-256.')
    if Path(journal).exists():
        raise SetupError(f'Journal {journal} exists; choose a new path. Nothing was written.')


def apply(call: Call, args: argparse.Namespace, config: dict[str, Json], state: dict[str, Json],
          steps: Plan, digest: str, config_sha256: str,
          started: datetime) -> tuple[dict[str, Json], dict[str, Json], Plan]:
    """Write the approved plan, journaling before the first write and after each result.

    A failing write stops the sequence; the journal records it and the error
    propagates. Nothing is retried or rolled back. The read-back state is returned.
    """
    if any(method == 'PUT' and '/rulesets/' in endpoint for method, endpoint, _ in steps) \
            and not args.update_existing:
        raise SetupError('A named ruleset differs. Review the preview, then use --update-existing '
                         'to replace that entire named ruleset. Additional rules in it will be removed.')
    if steps:
        check_required_checks(call, args.repo, config, state['metadata'])
    journal: dict[str, Json] = {
        'record': 'repository-settings-journal',
        'tool': TOOL,
        'plan_sha256': digest,
        'repository': state['metadata'].get('full_name', args.repo),
        'configuration_sha256': config_sha256,
        'started_at': started.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'writes': [{**step_record(*step), 'status': 'pending'} for step in steps],
        'readback': None,
    }
    write_json_atomically(args.journal, journal)
    for entry, (method, endpoint, payload) in zip(journal['writes'], steps):
        try:
            response = call(method, endpoint, payload)
        except Exception as error:
            entry.update(status='failed', error=str(error))
            write_json_atomically(args.journal, journal)
            raise
        entry['status'] = 'done'
        # A ruleset write records the ID GitHub answers with, so that a created
        # ruleset can be found again even when a later write fails.
        if 'ruleset' in entry and isinstance(response, dict) and isinstance(response.get('id'), int):
            entry['ruleset_id'] = response['id']
        write_json_atomically(args.journal, journal)
        print(f'Applied {method} {endpoint}')
    # Read back after every apply, an empty one included, so that the journal
    # records a fresh observation, never the one the plan was built from.
    state = observe(call, args.repo, config)
    report = assess(config, state)
    steps = plan(config, report, args.repo)
    journal['readback'] = report['result']
    write_json_atomically(args.journal, journal)
    print(f'Journal written to {args.journal}')
    return state, report, steps


def output_paths(args: argparse.Namespace, started: datetime) -> dict[str, Path]:
    """The files this run writes, with {date} expanded to the UTC start date; each must be a different file.

    Checked before any API call, so that a record can never replace the journal
    an apply needs for recovery, or another record.
    """
    paths: dict[str, Path] = {}
    for option in ('journal', 'report', 'evidence'):
        value = getattr(args, option, None)
        if value is not None:
            paths[option] = Path(str(value).replace('{date}', started.strftime('%Y-%m-%d')))
    seen: dict[Path, str] = {}
    for option, path in paths.items():
        resolved = path.resolve()
        if resolved in seen:
            raise SetupError(f'--{seen[resolved]} and --{option} name the same file ({path}); '
                             'give each output its own path. Nothing was read or written.')
        seen[resolved] = option
    return paths


def workflow_verdict(report: dict[str, Json]) -> int:
    """The outcome of a workflow-token check: no plan, no record. 0 verified, 1 drift, 3 partial."""
    print('No plan: a workflow-token check never writes or records anything.')
    if report['result'] == 'DRIFT':
        print('DRIFT: documented settings do not match.')
        return 1
    if report['result'] == 'PARTIAL':
        print('PARTIAL: no difference was found in the values this token can read; the values listed '
              'as NOT CHECKED were not observed and are neither matches nor drift. Run --check with '
              'administrator access to verify them.')
        return PARTIAL_EXIT
    print('VERIFIED: all documented settings match. Unmanaged settings are outside this verification.')
    return 0


def run(args: argparse.Namespace, call: Call = api, now: datetime | None = None) -> int:
    if not REPOSITORY_PATTERN.fullmatch(args.repo) or args.repo.split('/')[1] in ('.', '..'):
        raise SetupError('Destination must be an explicit owner/repository on github.com.')
    config = load_config(args.config)
    config_sha256 = hashlib.sha256(args.config.read_bytes()).hexdigest()
    mode = 'apply' if args.apply else 'check' if args.check else 'preview'
    started = now or datetime.now(timezone.utc)
    outputs = output_paths(args, started)
    # Every later check, write and message uses the expanded paths.
    args = argparse.Namespace(**{**vars(args), **outputs})
    scope = getattr(args, 'token_scope', 'admin')
    state = observe(call, args.repo, config, scope)
    report = assess(config, state, scope)
    print_notes(config, state, report)
    for line in difference_lines(report):
        print(line)
    if scope == 'workflow':
        return workflow_verdict(report)
    steps = plan(config, report, args.repo)
    digest = plan_digest(state['metadata'].get('full_name', args.repo), config_sha256, report, steps,
                         state['rulesets'], state['metadata'].get('default_branch'))
    print_plan(steps)
    print(f'PLAN SHA-256: {digest}')
    if args.apply:
        check_approval(args, digest)
        check_prerequisites(state, report)
        state, report, steps = apply(call, args, config, state, steps, digest, config_sha256, started)
        digest = plan_digest(state['metadata'].get('full_name', args.repo), config_sha256, report, steps,
                             state['rulesets'], state['metadata'].get('default_branch'))
    stamp = now or datetime.now(timezone.utc)
    if getattr(args, 'report', None):
        write_text(args.report, markdown_record(state, report, digest, mode, stamp), 'Evidence')
    if getattr(args, 'evidence', None):
        record = evidence_record(args.config, config_sha256, args.repo, state, report, steps, digest, mode, stamp)
        write_text(args.evidence, json.dumps(record, indent=2) + '\n', 'Evidence')
    if report['result'] == 'VERIFIED':
        print('VERIFIED: all documented settings match' + (' after apply' if args.apply else '')
              + '. Unmanaged settings are outside this verification.')
        return 0
    if args.apply:
        for line in difference_lines(report):
            print(line)
        raise readback_error(report)
    if args.check:
        print('DRIFT: documented settings do not match.')
        return 1
    print('PREVIEW ONLY: no changes made. To apply this plan, rerun with --apply --approve-plan '
          f'{digest} --journal PATH; set any differing Actions setting by hand in '
          'Settings > Actions > General.')
    return 0


def main() -> int:
    if sys.version_info < (3, 11):
        print('ERROR: Python 3.11 or later is required.', file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, help='Explicit destination owner/repository')
    parser.add_argument('--config', type=Path, default=CONFIG)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true',
                      help='Apply the approved plan, then verify (needs --approve-plan and --journal)')
    mode.add_argument('--check', action='store_true', help='Read-only verification; exit 1 for drift')
    parser.add_argument('--approve-plan', metavar='SHA256',
                        help='The PLAN SHA-256 that preview printed for the plan to apply')
    parser.add_argument('--journal', type=Path,
                        help='Write a JSON journal of the apply to this new path, before the first '
                             'write and after each ({date} becomes the start date, YYYY-MM-DD, UTC)')
    parser.add_argument('--token-scope', choices=('admin', 'workflow'), default='admin',
                        help='workflow: the limited GITHUB_TOKEN of a workflow, with --check only; a value it '
                             'cannot read is NOT CHECKED (neither match nor drift), the result is PARTIAL '
                             f'(exit {PARTIAL_EXIT}) without drift, and nothing is planned, applied or recorded')
    parser.add_argument('--update-existing', action='store_true', help='Allow replacement of differing named rulesets')
    parser.add_argument('--report', type=Path,
                        help='Write a dated Markdown evidence record of the managed settings ({date} becomes '
                             'the start date, YYYY-MM-DD, UTC)')
    parser.add_argument('--evidence', type=Path,
                        help='Write a JSON evidence record of the managed settings ({date} becomes the '
                             'start date, YYYY-MM-DD, UTC)')
    args = parser.parse_args()
    for option in ('approve_plan', 'journal', 'update_existing'):
        if getattr(args, option) and not args.apply:
            parser.error(f'--{option.replace("_", "-")} requires --apply')
    if args.token_scope == 'workflow':
        if not args.check:
            parser.error('--token-scope workflow requires --check')
        for option in ('report', 'evidence'):
            if getattr(args, option) is not None:
                parser.error(f'--token-scope workflow cannot write --{option}: its values are partial')
    if args.apply and (args.approve_plan is None or args.journal is None):
        parser.error('--apply requires --approve-plan SHA256 and --journal PATH')
    if args.approve_plan is not None and not DIGEST_PATTERN.fullmatch(args.approve_plan):
        parser.error('--approve-plan takes the 64 hexadecimal digits of the PLAN SHA-256 line that preview printed')
    try:
        return run(args)
    except (SetupError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
