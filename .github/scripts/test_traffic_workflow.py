"""Behaviour of the traffic workflow's push and alert-guard steps, run with bash.

The steps' scripts are read from .github/workflows/daily-traffic.yml and run
against local repositories: the history branch's origin is a bare repository
on disk, so a concurrent writer, a rejected push and a retry can be exercised
without the network. The tests are skipped where bash, git or base64 is not on
the path, and on Windows; the required check runs them on Linux.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import traffic_history as traffic  # noqa: E402
from test_traffic_history import moment, responses  # noqa: E402
from test_workflow_controls import ROOT, workflows  # noqa: E402

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only without the parser
    yaml = None

SCRIPT = ROOT / ".github/scripts/traffic_history.py"
TOOLS = all(shutil.which(tool) for tool in ("bash", "git", "base64")) and sys.platform != "win32"


def step_script(job: str, *, step_id: str | None = None, name: str | None = None) -> str:
    steps = workflows()["daily-traffic.yml"]["jobs"][job]["steps"]
    found = [s for s in steps if (step_id and s.get("id") == step_id) or (name and s.get("name") == name)]
    assert len(found) == 1, (step_id, name)
    return str(found[0]["run"])


def git(directory: Path, *arguments: str) -> str:
    environment = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull,
                       GIT_AUTHOR_NAME="writer", GIT_AUTHOR_EMAIL="writer@example.com",
                       GIT_COMMITTER_NAME="writer", GIT_COMMITTER_EMAIL="writer@example.com")
    result = subprocess.run(["git", *arguments], cwd=directory, env=environment, text=True,
                            capture_output=True, check=False)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


@unittest.skipIf(yaml is None and not os.environ.get("GITHUB_ACTIONS"),
                 "PyYAML is not installed: python -m pip install -r .github/requirements.txt")
@unittest.skipUnless(TOOLS, "bash, git and base64 are needed (not on Windows)")
class PushStepTests(unittest.TestCase):
    """Commit and push traffic history, against a bare origin on disk."""

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.origin = self.root / "origin.git"
        subprocess.run(["git", "init", "--quiet", "--bare", "-b", "traffic-history", str(self.origin)],
                       check=True)
        # A first collection, pushed by an earlier run.
        seed = self.root / "seed"
        seed.mkdir()
        (seed / "data").mkdir()
        raw = self.root / "raw-seed"
        raw.mkdir()
        self.write_raw(raw, "2026-10-30", (3, 1, 7, 2))
        traffic.merge(raw, seed / "data", moment("2026-10-31T06:17:00Z"))
        git(seed, "init", "--quiet", "-b", "traffic-history")
        git(seed, "add", "data")
        git(seed, "commit", "--quiet", "-m", "first collection")
        git(seed, "push", "--quiet", str(self.origin), "traffic-history")
        self.history = self.root / "history"
        git(self.root, "clone", "--quiet", "--branch", "traffic-history", str(self.origin), "history")
        # The next collection, merged into the working tree as the previous step does.
        self.runner = self.root / "runner"
        self.raw = self.runner / "raw"
        self.raw.mkdir(parents=True)
        self.write_raw(self.raw, "2026-11-01", (5, 2, 9, 3))
        traffic.merge(self.raw, self.history / "data", moment("2026-11-02T06:17:00Z"))
        # The workflow's merge script, where the step's retry looks for it.
        (self.root / "source/.github/scripts").mkdir(parents=True)
        shutil.copy(SCRIPT, self.root / "source/.github/scripts/traffic_history.py")
        # A sleep that does not wait, so that the retries are instant.
        shim = self.root / "shim"
        shim.mkdir()
        (shim / "sleep").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        (shim / "sleep").chmod(0o755)
        self.shim = shim
        self.output = self.root / "github-output"
        self.output.write_text("", encoding="utf-8")

    @staticmethod
    def write_raw(directory: Path, day: str, counts: tuple[int, int, int, int]) -> None:
        for name, value in responses({day: counts}).items():
            (directory / name).write_text(json.dumps(value), encoding="utf-8")

    def run_step(self) -> subprocess.CompletedProcess[str]:
        environment = dict(os.environ, PATH=f"{self.shim}{os.pathsep}{os.environ['PATH']}",
                           GITHUB_TOKEN="test-token", COLLECTED_AT="2026-11-02T06:17:00Z",
                           GITHUB_OUTPUT=str(self.output), RUNNER_TEMP=str(self.runner),
                           GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)
        return subprocess.run(["bash", "-c", step_script("collect", step_id="push")], cwd=self.history,
                              env=environment, text=True, capture_output=True, check=False)

    def recorded(self) -> str:
        lines = [line for line in self.output.read_text(encoding="utf-8").splitlines() if line]
        self.assertEqual(len(lines), 1, lines)
        self.assertTrue(lines[0].startswith("sha="), lines[0])
        return lines[0][len("sha="):]

    def tip(self) -> str:
        return git(self.origin, "rev-parse", "traffic-history")

    def concurrent_writer(self, name: str = "other.txt") -> str:
        """Another writer advances the branch before this run's first push."""
        other = self.root / "other"
        git(self.root, "clone", "--quiet", "--branch", "traffic-history", str(self.origin), "other")
        (other / "data" / name).write_text("another writer\n", encoding="utf-8")
        git(other, "add", "data")
        git(other, "commit", "--quiet", "-m", "another writer")
        git(other, "push", "--quiet", "origin", "traffic-history")
        return self.tip()

    def test_a_pushed_collection_records_the_commit_it_wrote(self) -> None:
        before = self.tip()
        result = self.run_step()
        self.assertEqual(result.returncode, 0, result.stderr)
        sha = self.recorded()
        self.assertRegex(sha, r"^[0-9a-f]{40}$")
        self.assertNotEqual(sha, before)
        self.assertEqual(sha, self.tip())
        self.assertEqual(git(self.origin, "rev-parse", sha + "^"), before)
        self.assertIn("2026-11-01", git(self.origin, "show", f"{sha}:data/{traffic.DAILY}"))

    def test_an_unchanged_history_records_the_commit_it_stands_at(self) -> None:
        git(self.history, "-c", "user.name=x", "-c", "user.email=x@example.com", "add", "data")
        git(self.history, "-c", "user.name=x", "-c", "user.email=x@example.com", "commit", "--quiet",
            "-m", "already collected")
        git(self.history, "push", "--quiet", "origin", "traffic-history")
        pushed = self.tip()
        result = self.run_step()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No traffic changes to commit", result.stdout)
        self.assertEqual(self.recorded(), pushed)
        self.assertEqual(self.tip(), pushed)

    def test_a_concurrent_writer_moves_the_branch_and_the_retry_rebuilds_on_it(self) -> None:
        writer = self.concurrent_writer()
        result = self.run_step()
        self.assertEqual(result.returncode, 0, result.stderr)
        sha = self.recorded()
        # Not the stale commit built on the old tip, and not the writer's: the rebuilt one.
        self.assertEqual(sha, self.tip())
        self.assertEqual(git(self.origin, "rev-parse", sha + "^"), writer)
        self.assertEqual(git(self.origin, "show", f"{sha}:data/other.txt"), "another writer")
        self.assertIn("2026-11-01", git(self.origin, "show", f"{sha}:data/{traffic.DAILY}"))
        self.assertNotIn("--force", step_script("collect", step_id="push"))

    def test_a_branch_that_never_accepts_the_push_fails_without_a_recorded_commit(self) -> None:
        hook = self.origin / "hooks/pre-receive"
        hook.write_text("#!/bin/sh\necho rejected >&2\nexit 1\n", encoding="utf-8")
        hook.chmod(0o755)
        before = self.tip()
        result = self.run_step()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Could not push the traffic history after 3 attempts", result.stdout)
        self.assertEqual(self.output.read_text(encoding="utf-8"), "")
        self.assertEqual(self.tip(), before)


@unittest.skipIf(yaml is None and not os.environ.get("GITHUB_ACTIONS"),
                 "PyYAML is not installed: python -m pip install -r .github/requirements.txt")
@unittest.skipUnless(TOOLS, "bash is needed (not on Windows)")
class AlertGuardTests(unittest.TestCase):
    """The alert job refuses anything but a full SHA from the collect job."""

    def guard(self, value: str) -> subprocess.CompletedProcess[str]:
        script = step_script("alert", name="Check the collected history commit")
        return subprocess.run(["bash", "-c", script], env=dict(os.environ, HISTORY_SHA=value), text=True,
                              capture_output=True, check=False)

    def test_a_full_lowercase_sha_passes(self) -> None:
        self.assertEqual(self.guard("0123456789abcdef0123456789abcdef01234567").returncode, 0)
        self.assertEqual(self.guard("f" * 40).returncode, 0)

    def test_a_missing_or_malformed_sha_stops_the_job(self) -> None:
        for value in ("", "traffic-history", "main", "abc1234", "A" * 40, "g" * 40, "a" * 39, "a" * 41,
                      " " + "a" * 40, "a" * 40 + "\nb"):
            with self.subTest(value=value):
                result = self.guard(value)
                self.assertEqual(result.returncode, 1)
                self.assertIn("The collect job reported no traffic-history commit", result.stdout)


if __name__ == "__main__":
    unittest.main()
