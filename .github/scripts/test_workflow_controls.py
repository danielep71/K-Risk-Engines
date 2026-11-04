"""Governance invariants of the workflows and Dependabot, read with a real YAML parser.

Adapted from danielep71/MyTemplate's tests/test_workflow_controls.py (see
NOTICE.md). The parser is pinned in .github/requirements.txt; install it with
``python -m pip install --require-hashes -r .github/requirements.txt``.
Without it the tests are skipped locally and fail in GitHub Actions.
"""

from __future__ import annotations

import os
import re
import unittest
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only without the parser
    yaml = None

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github/workflows"
REQUIRED_JOB = ("website-checks.yml", "website")
REQUIRED_CHECK = "HTML and links"
# The only jobs that may write, and what each may write. An entry for a job
# that does not exist is allowed: it names the intended shape of a pending change.
WRITE_PERMISSIONS = {
    ("labels-sync.yml", "reconcile"): {"issues"},
    ("daily-traffic.yml", "traffic"): {"contents", "issues"},
    ("daily-traffic.yml", "collect"): {"contents"},
    ("daily-traffic.yml", "alert"): {"issues"},
    ("pr-milestones.yml", "reconcile"): {"pull-requests"},
    ("codeql.yml", "analyze"): {"security-events"},
}
# No checkout keeps credentials: the traffic export passes the workflow token
# to its push step only (see test_traffic_credentials_stay_in_their_steps).
PERSISTED_CHECKOUTS: set[tuple[str, str]] = set()
# Exact runtime versions, pinned in every setup step (see website-checks.yml).
NODE_VERSION = "24.22.2"
PYTHON_VERSION = "3.13.18"
PINNED = re.compile(r"^[\w.-]+/[\w.-]+(/[\w./-]+)?@[0-9a-f]{40}$")
# The tests and the issue checker run the label scripts too.
USES_NODE = re.compile(r"\bnode\s|unittest|check_issues\.py")


def load(path: Path) -> dict[str, Any]:
    document: dict[Any, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    # YAML 1.1 reads the bare key "on" as True.
    if True in document:
        document["on"] = document.pop(True)
    return document


def workflows() -> dict[str, dict[str, Any]]:
    return {path.name: load(path) for path in sorted(WORKFLOWS.glob("*.yml"))}


def writes(permissions: Any) -> set[str]:
    if permissions in ("write-all", "read-all"):
        return {str(permissions)}
    return {scope for scope, level in (permissions or {}).items() if level == "write"}


@unittest.skipIf(yaml is None and not os.environ.get("GITHUB_ACTIONS"),
                 "PyYAML is not installed: python -m pip install -r .github/requirements.txt")
class WorkflowControlTests(unittest.TestCase):
    def test_parser_is_available(self) -> None:
        self.assertIsNotNone(yaml, "install .github/requirements.txt before running the tests")

    def test_actions_are_pinned_and_checkouts_drop_credentials(self) -> None:
        for name, document in workflows().items():
            for job_id, job in document["jobs"].items():
                for step in job.get("steps", []):
                    if "uses" not in step:
                        continue
                    with self.subTest(workflow=name, job=job_id, uses=step["uses"]):
                        self.assertRegex(step["uses"], PINNED)
                        if step["uses"].startswith("actions/checkout@"):
                            persisted = (step.get("with") or {}).get("persist-credentials")
                            expected = (name, job_id) in PERSISTED_CHECKOUTS
                            self.assertIs(persisted, expected)

    def test_every_job_has_a_timeout_and_permissions_are_explicit(self) -> None:
        for name, document in workflows().items():
            with self.subTest(workflow=name):
                self.assertIn("permissions", document)
            for job_id, job in document["jobs"].items():
                with self.subTest(workflow=name, job=job_id):
                    self.assertIsInstance(job.get("timeout-minutes"), int)
                    self.assertIn("permissions", job)

    def test_only_the_listed_jobs_write(self) -> None:
        for name, document in workflows().items():
            with self.subTest(workflow=name, level="workflow"):
                self.assertEqual(writes(document["permissions"]), set())
            for job_id, job in document["jobs"].items():
                with self.subTest(workflow=name, job=job_id):
                    self.assertEqual(writes(job.get("permissions")),
                                     WRITE_PERMISSIONS.get((name, job_id), set()))

    def test_required_check_runs_unconditionally_on_every_branch(self) -> None:
        name, job_id = REQUIRED_JOB
        document = workflows()[name]
        for event in ("pull_request", "push"):
            with self.subTest(event=event):
                self.assertIn(event, document["on"])
                self.assertFalse(document["on"][event],
                                 f"{event} must have no branch or path filters")
        job = document["jobs"][job_id]
        self.assertNotIn("if", job)
        self.assertNotIn("strategy", job)
        # The rulesets in docs/REPOSITORY_SETTINGS.md require this name.
        self.assertEqual(job["name"], REQUIRED_CHECK)

    def test_live_label_reconciliation_runs_only_on_the_default_branch(self) -> None:
        # A manual dispatch on another branch must not apply an unintegrated manifest.
        condition = workflows()["labels-sync.yml"]["jobs"]["reconcile"]["if"]
        self.assertIn("github.event_name != 'pull_request'", condition)
        self.assertIn("github.event.repository.default_branch", condition)

    def test_traffic_credentials_stay_in_their_steps(self) -> None:
        steps = workflows()["daily-traffic.yml"]["jobs"]["collect"]["steps"]
        with_key = [step for step in steps if "TRAFFIC_APP_PRIVATE_KEY" in str(step)]
        self.assertEqual([step["name"] for step in with_key],
                         ["Check the traffic App configuration", "Create traffic App token"])
        # The configuration check sees only whether the key is set.
        self.assertEqual(with_key[0]["env"]["HAS_KEY"],
                         "${{ secrets.TRAFFIC_APP_PRIVATE_KEY != '' }}")
        with_app_token = [step for step in steps if "steps.app-token.outputs.token" in str(step)]
        self.assertEqual([step["name"] for step in with_app_token], ["Fetch GitHub traffic API data"])
        self.assertNotRegex(with_app_token[0]["run"], r"\bpython|\.py\b")
        with_workflow_token = [step for step in steps if "github.token" in str(step)]
        self.assertEqual([step["name"] for step in with_workflow_token],
                         ["Commit and push traffic history"])
        push = with_workflow_token[0]["run"]
        self.assertNotIn("--force", push)
        self.assertIn("fetch origin traffic-history", push)
        fetch = with_app_token[0]["run"]
        self.assertIn("--retry 5", fetch)
        self.assertIn("--max-time 60", fetch)

    def test_code_scanning_covers_each_language_and_pull_requests_upload_nothing(self) -> None:
        document = workflows()["codeql.yml"]
        self.assertEqual(document["on"]["push"], document["on"]["pull_request"])
        self.assertEqual(set(document["on"]["push"]["branches"]), {"main", "release/**"})
        self.assertIn("schedule", document["on"])
        jobs = document["jobs"]
        gate = jobs["availability"]["steps"][0]
        self.assertIn(".visibility", gate["run"])
        self.assertEqual(gate["env"]["CODE_SCANNING"], "${{ vars.CODE_SCANNING }}")
        expected = {
            "analyze": ("needs.availability.outputs.enabled == 'true' && "
                        "github.event_name != 'pull_request'",
                        ["actions/checkout", "github/codeql-action/init",
                         "github/codeql-action/analyze"]),
            "analyze-pr": ("needs.availability.outputs.enabled == 'true' && "
                           "github.event_name == 'pull_request'",
                           ["actions/checkout", "github/codeql-action/init",
                            "github/codeql-action/analyze", "actions/upload-artifact"]),
        }
        for job_id, (condition, sequence) in expected.items():
            with self.subTest(job=job_id):
                job = jobs[job_id]
                self.assertEqual(job["needs"], "availability")
                self.assertEqual(job["if"], condition)
                self.assertEqual(sorted(job["strategy"]["matrix"]["language"]),
                                 ["actions", "javascript-typescript", "python"])
                steps = [step for step in job["steps"] if "uses" in step]
                self.assertEqual([step["uses"].split("@")[0] for step in steps], sequence)
                self.assertEqual(steps[1]["with"]["queries"], "security-extended")
        # Pull request analysis writes nothing to code scanning.
        self.assertEqual(jobs["analyze-pr"]["permissions"], {"contents": "read"})
        pr_analyze = jobs["analyze-pr"]["steps"][2]["with"]
        self.assertEqual(pr_analyze["upload"], "never")
        self.assertIs(pr_analyze["upload-database"], False)

    def test_every_pip_install_is_hash_locked(self) -> None:
        installs = 0
        for name, document in workflows().items():
            for job_id, job in document["jobs"].items():
                for step in job.get("steps", []):
                    run = step.get("run") or ""
                    if "pip install" not in run:
                        continue
                    installs += 1
                    with self.subTest(workflow=name, job=job_id, step=step.get("name")):
                        self.assertIn("--require-hashes", run)
                        self.assertIn("--only-binary=:all:", run)
                        self.assertRegex(run, r"-r \S+requirements[\w.-]*\.txt")
        self.assertGreater(installs, 0)
        for path in (".github/requirements.txt", "tools/requirements-quality-ci.txt"):
            text = (ROOT / path).read_text(encoding="utf-8")
            for requirement in re.split(r"\n(?=\S)", re.sub(r"(?m)^#.*\n?", "", text).strip()):
                with self.subTest(file=path, requirement=requirement.split()[0]):
                    self.assertRegex(requirement.split()[0], r"^[\w.-]+==[\w.]+$")
                    self.assertRegex(requirement, r"--hash=sha256:[0-9a-f]{64}")

    def test_jobs_that_run_node_set_it_up_first(self) -> None:
        versions, jobs = set(), 0
        for name, document in workflows().items():
            for job_id, job in document["jobs"].items():
                steps = job.get("steps", [])
                runs = [i for i, step in enumerate(steps) if USES_NODE.search(step.get("run") or "")]
                if not runs:
                    continue
                jobs += 1
                setups = [i for i, step in enumerate(steps)
                          if str(step.get("uses", "")).startswith("actions/setup-node@")]
                with self.subTest(workflow=name, job=job_id):
                    self.assertTrue(setups and setups[0] < runs[0], "set up Node.js before using it")
                    versions.add(str(steps[setups[0]]["with"]["node-version"]))
        self.assertGreater(jobs, 0)
        self.assertEqual(versions, {NODE_VERSION}, f"Node.js {NODE_VERSION} everywhere, found {versions}")

    def test_python_setups_pin_one_exact_version(self) -> None:
        versions = {str(step["with"]["python-version"])
                    for document in workflows().values()
                    for job in document["jobs"].values()
                    for step in job.get("steps", [])
                    if str(step.get("uses", "")).startswith("actions/setup-python@")}
        self.assertEqual(versions, {PYTHON_VERSION})

    def test_pull_request_runs_are_replaced_and_push_runs_kept(self) -> None:
        concurrency = workflows()["website-checks.yml"]["concurrency"]
        self.assertIn("github.event.pull_request.number", concurrency["group"])
        self.assertIn("github.run_id", concurrency["group"])
        self.assertEqual(concurrency["cancel-in-progress"],
                         "${{ github.event_name == 'pull_request' }}")

    def test_milestone_events_queue_per_pull_request(self) -> None:
        concurrency = workflows()["pr-milestones.yml"]["concurrency"]
        self.assertIn("github.event.pull_request.number", concurrency["group"])
        self.assertIs(concurrency["cancel-in-progress"], False)

    def test_dependabot_covers_each_pinned_dependency_once(self) -> None:
        document = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text(encoding="utf-8"))
        self.assertEqual(document["version"], 2)
        updates = document["updates"]
        self.assertEqual(sorted((u["package-ecosystem"], u["directory"]) for u in updates),
                         [("github-actions", "/"), ("pip", "/.github"), ("pip", "/tools")])
        release = "release/" + (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        for update in updates:
            with self.subTest(ecosystem=update["package-ecosystem"], directory=update["directory"]):
                self.assertEqual(update["target-branch"], release)
                self.assertNotIn("milestone", update)
                self.assertEqual([label for label in update["labels"]
                                  if label in {"P1", "P2", "P3"}], ["P3"])


if __name__ == "__main__":
    unittest.main()
