"""Tests for the changelog fragments (.github/scripts/changelog_fragments.py)."""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".github" / "scripts"))

import changelog_fragments as fragments  # noqa: E402

CHANGELOG = """# Changelog

## [Unreleased]

### 🔧 Changed

- An older change (#10).

## [1.0.0] - 2026-10-22

### ✨ Added

- First (#1).
"""


class Workspace:
    def __init__(self, test: unittest.TestCase) -> None:
        directory = tempfile.TemporaryDirectory()
        test.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / "changelog.d").mkdir()
        (self.root / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")

    def add(self, name: str, text: str) -> Path:
        path = self.root / "changelog.d" / name
        path.write_text(text, encoding="utf-8")
        return path

    def run(self, *argv: str) -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            status = fragments.main(["--root", str(self.root), *argv])
        return status, output.getvalue()

    @property
    def changelog(self) -> str:
        return (self.root / "CHANGELOG.md").read_text(encoding="utf-8")


class FragmentTests(unittest.TestCase):
    def test_the_repository_fragments_are_valid(self) -> None:
        _, problems = fragments.read_fragments(ROOT / "changelog.d")
        self.assertEqual(problems, [])

    def test_a_valid_fragment_passes_and_readme_is_ignored(self) -> None:
        work = Workspace(self)
        work.add("README.md", "# Fragments\n")
        work.add("12.changed.md", "- A change (#12).\n")
        status, output = work.run("check")
        self.assertEqual(status, 0, output)
        self.assertIn("changelog-fragments: PASS (1 fragment(s))", output)

    def test_invalid_fragments_are_reported(self) -> None:
        cases = {
            "notes.md": "must be <issue>.<category>.md",
            "12.other.md": "unknown category 'other'",
            "13.fixed.md": "must be one list item starting with '- '",
            "14.fixed.md": "must hold a single list item",
            "15.fixed.md": "continuation lines must be indented",
            "16.fixed.md": "must cite its issue as (#16)",
        }
        bodies = {
            "notes.md": "- x (#1)\n", "12.other.md": "- x (#12)\n", "13.fixed.md": "A line (#13).\n",
            "14.fixed.md": "- one (#14)\n- two (#14)\n", "15.fixed.md": "- one (#15)\nnot indented\n",
            "16.fixed.md": "- cites another (#99)\n",
        }
        for name, message in cases.items():
            with self.subTest(name=name):
                work = Workspace(self)
                work.add(name, bodies[name])
                status, output = work.run("check")
                self.assertEqual(status, 1)
                self.assertIn(message, output)

    def test_assembly_puts_entries_at_the_top_of_their_category_newest_first(self) -> None:
        work = Workspace(self)
        work.add("12.changed.md", "- A change\n  over two lines (#12).\n")
        work.add("20.changed.md", "- A newer change (#20).\n")
        work.add("13.fixed.md", "- A fix (#13).\n")
        work.add("14.added.md", "- Something new (#14).\n")
        status, output = work.run("assemble")
        self.assertEqual(status, 0, output)
        self.assertEqual(work.changelog, CHANGELOG, "the preview never writes")
        self.assertIn("PREVIEW ONLY: 4 fragment(s)", output)
        status, output = work.run("assemble", "--write")
        self.assertEqual(status, 0, output)
        self.assertEqual(work.changelog, """# Changelog

## [Unreleased]

### ✨ Added

- Something new (#14).

### 🔧 Changed

- A newer change (#20).
- A change
  over two lines (#12).
- An older change (#10).

### 🐛 Fixed

- A fix (#13).

## [1.0.0] - 2026-10-22

### ✨ Added

- First (#1).
""")
        self.assertEqual(sorted(p.name for p in (work.root / "changelog.d").iterdir()), [])

    def test_released_sections_are_left_alone(self) -> None:
        work = Workspace(self)
        work.add("3.added.md", "- Late (#3).\n")
        work.run("assemble", "--write")
        released = work.changelog.split("## [1.0.0]", 1)[1]
        self.assertEqual(released, CHANGELOG.split("## [1.0.0]", 1)[1])

    def test_assembling_nothing_changes_nothing(self) -> None:
        work = Workspace(self)
        status, output = work.run("assemble", "--write")
        self.assertEqual(status, 0, output)
        self.assertEqual(work.changelog, CHANGELOG)

    def test_a_problem_blocks_assembly(self) -> None:
        work = Workspace(self)
        work.add("12.changed.md", "- A change (#12).\n")
        work.add("oops.md", "x")
        status, _ = work.run("assemble", "--write")
        self.assertEqual(status, 1)
        self.assertEqual(work.changelog, CHANGELOG)
        self.assertTrue((work.root / "changelog.d" / "12.changed.md").exists())

    def test_a_missing_unreleased_section_is_an_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "no ## \\[Unreleased\\] section"):
            fragments.assemble("# Changelog\n", [])

    def test_assembly_is_idempotent_for_the_real_changelog_shape(self) -> None:
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertEqual(fragments.assemble(text, []).rstrip("\n"), text.rstrip("\n"))


if __name__ == "__main__":
    unittest.main()
