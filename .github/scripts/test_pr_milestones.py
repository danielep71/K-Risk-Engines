"""Tests for the Keep milestones issue-only workflow (.github/workflows/pr-milestones.yml).

Adapted from danielep71/MyTemplate's tests/test_workflow_controls.py (see
NOTICE.md). The workflow is read with a real YAML parser; without PyYAML the
tests are skipped locally and fail in GitHub Actions.
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
WORKFLOW = ROOT / ".github/workflows/pr-milestones.yml"


def load() -> dict[str, Any]:
    document: dict[Any, Any] = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    # YAML 1.1 reads the bare key "on" as True.
    if True in document:
        document["on"] = document.pop(True)
    return document


def milestone_script() -> str:
    run: str = load()["jobs"]["reconcile"]["steps"][0]["run"]
    return run.split("<<'PY'\n", 1)[1].rsplit("PY", 1)[0]


class FakeGitHub:
    def __init__(self, pulls: list[dict[str, Any]], issues: tuple[dict[str, Any], ...] = ()) -> None:
        self.items = {pull["number"]: dict(pull, pull_request={}) for pull in pulls}
        self.items.update({issue["number"]: dict(issue) for issue in issues})
        self.patches: list[int] = []

    def __call__(self, method: str, path: str, data: dict[str, Any] | None = None) -> Any:
        if path.startswith("/repos/o/r/pulls?"):
            match = re.search(r"[?&]page=(\d+)", path)
            assert match
            page = int(match.group(1))
            pulls = [item for item in self.items.values() if "pull_request" in item]
            return pulls[(page - 1) * 100:page * 100]
        number = int(path.rsplit("/", 1)[1])
        if method == "PATCH":
            assert data is not None
            self.patches.append(number)
            self.items[number]["milestone"] = data["milestone"]
        return dict(self.items[number])


@unittest.skipIf(yaml is None and not os.environ.get("GITHUB_ACTIONS"),
                 "PyYAML is not installed")
class MilestoneWorkflowTests(unittest.TestCase):
    def test_parser_is_available(self) -> None:
        self.assertIsNotNone(yaml, "install PyYAML before running the tests")

    def test_milestone_workflow_never_runs_pull_request_code(self) -> None:
        document = load()
        self.assertEqual(set(document["on"]),
                         {"push", "pull_request_target", "schedule", "workflow_dispatch"})
        self.assertEqual(document["on"]["pull_request_target"],
                         {"types": ["opened", "reopened", "edited", "milestoned"]})
        self.assertEqual(document["permissions"], {})
        job = document["jobs"]["reconcile"]
        self.assertEqual(job["permissions"], {"issues": "read", "pull-requests": "write"})
        self.assertIn("github.event.repository.default_branch", job["if"])
        self.assertEqual(len(job["steps"]), 1)
        step = job["steps"][0]
        self.assertEqual(set(step), {"name", "env", "run"})
        self.assertEqual(step["env"], {"GH_TOKEN": "${{ github.token }}"})
        self.assertNotIn("${{", step["run"])


@unittest.skipIf(yaml is None and not os.environ.get("GITHUB_ACTIONS"),
                 "PyYAML is not installed")
class MilestoneScriptTests(unittest.TestCase):
    def reconcile(self) -> Any:
        namespace: dict[str, Any] = {"__name__": "milestones"}
        exec(milestone_script(), namespace)  # trusted: the script under test, from this repository
        return namespace["reconcile"]

    def test_pull_request_event_clears_only_that_pull_request(self) -> None:
        api = FakeGitHub([{"number": 1, "milestone": {"title": "v1"}},
                          {"number": 2, "milestone": {"title": "v1"}}])
        self.reconcile()(api, "o/r", {"number": 1, "pull_request": {}})
        self.assertEqual(api.patches, [1])
        self.assertIsNotNone(api.items[2]["milestone"])

    def test_scan_clears_every_pull_request_and_never_touches_issues(self) -> None:
        pulls = [{"number": n, "milestone": {"title": "v1"} if n % 2 else None} for n in range(1, 151)]
        api = FakeGitHub(pulls, issues=({"number": 500, "milestone": {"title": "v1"}},))
        self.reconcile()(api, "o/r", {"schedule": "17 3 * * *"})
        self.assertEqual(api.patches, list(range(1, 151, 2)))
        self.assertIsNotNone(api.items[500]["milestone"])

    def test_an_issue_number_is_refused(self) -> None:
        api = FakeGitHub([], issues=({"number": 7, "milestone": {"title": "v1"}},))
        with self.assertRaisesRegex(ValueError, "Refusing to change an issue"):
            self.reconcile()(api, "o/r", {"number": 7, "pull_request": {}})
        self.assertEqual(api.patches, [])


if __name__ == "__main__":
    unittest.main()
