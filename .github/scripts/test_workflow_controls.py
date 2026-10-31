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
}
# The traffic export pushes the CSV history, so its checkout keeps credentials.
PERSISTED_CHECKOUTS = {("daily-traffic.yml", "traffic"), ("daily-traffic.yml", "collect")}
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
        self.assertEqual(versions, {"24"}, f"Node.js 24 everywhere, found {versions}")

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
