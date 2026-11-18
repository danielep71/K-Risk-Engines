#!/usr/bin/env python3
"""Validate and assemble the changelog fragments in changelog.d/.

A task pull request records its changelog entry as its own file,
changelog.d/<issue>.<category>.md, so that two open pull requests never edit the
same lines of CHANGELOG.md. A fragment is one Markdown list item that cites its
issue as (#<issue>). `check` validates every fragment; `assemble` previews the
[Unreleased] section with the fragments in it and, with --write, puts them there
and deletes them. The release commit assembles them (GOVERNANCE.md).
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Keep a Changelog order, with the headings CHANGELOG.md already uses.
CATEGORIES = {
    "added": "✨ Added",
    "changed": "🔧 Changed",
    "deprecated": "⚠️ Deprecated",
    "removed": "🗑️ Removed",
    "fixed": "🐛 Fixed",
    "security": "🔐 Security",
}
NAME = re.compile(r"(\d+)\.([a-z]+)\.md")
UNRELEASED = "## [Unreleased]"


@dataclass(frozen=True)
class Fragment:
    path: Path
    issue: int
    category: str
    text: str


def read_fragments(directory: Path) -> tuple[list[Fragment], list[str]]:
    """Every fragment of the directory, and the problems found; README.md is not a fragment."""
    fragments: list[Fragment] = []
    problems: list[str] = []
    if not directory.is_dir():
        return fragments, problems
    for path in sorted(directory.iterdir()):
        if path.name == "README.md" or path.name.startswith("."):
            continue
        match = NAME.fullmatch(path.name)
        if not match:
            problems.append(f"{path.name}: the name must be <issue>.<category>.md")
            continue
        issue, category = int(match.group(1)), match.group(2)
        if category not in CATEGORIES:
            problems.append(f"{path.name}: unknown category {category!r}; use {', '.join(CATEGORIES)}")
            continue
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n").strip("\n")
        lines = text.split("\n")
        if not text.startswith("- "):
            problems.append(f"{path.name}: must be one list item starting with '- '")
        elif any(line.startswith("- ") for line in lines[1:]):
            problems.append(f"{path.name}: must hold a single list item")
        elif any(line and not line.startswith("  ") for line in lines[1:]):
            problems.append(f"{path.name}: continuation lines must be indented by two spaces")
        elif f"#{issue}" not in text:
            problems.append(f"{path.name}: the entry must cite its issue as (#{issue})")
        fragments.append(Fragment(path, issue, category, text))
    return fragments, problems


def unreleased_bounds(lines: list[str]) -> tuple[int, int]:
    start = next((i for i, line in enumerate(lines) if line.strip() == UNRELEASED), None)
    if start is None:
        raise ValueError(f"CHANGELOG.md has no {UNRELEASED} section")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## [")), len(lines))
    return start, end


def assemble(changelog: str, fragments: Sequence[Fragment]) -> str:
    """The changelog with each fragment at the top of its category in [Unreleased], newest first."""
    lines = changelog.split("\n")
    start, end = unreleased_bounds(lines)
    section = lines[start + 1:end]
    # Split the section into its leading text and its ### blocks, keeping each block's lines.
    blocks: dict[str, list[str]] = {}
    order: list[str] = []
    preamble: list[str] = []
    current: str | None = None
    for line in section:
        if line.startswith("### "):
            current = line[4:].strip()
            blocks[current] = []
            order.append(current)
        elif current is None:
            preamble.append(line)
        else:
            blocks[current].append(line)
    for category in CATEGORIES:
        mine = sorted((f for f in fragments if f.category == category), key=lambda f: -f.issue)
        if not mine:
            continue
        heading = CATEGORIES[category]
        entries = [f.text for f in mine]
        if heading in blocks:
            body = list(blocks[heading])
            while body and body[0] == "":
                body.pop(0)
            blocks[heading] = [""] + entries + body
        else:
            blocks[heading] = [""] + entries + [""]
            order.append(heading)
    canonical = [heading for heading in CATEGORIES.values()]
    known = [heading for heading in canonical if heading in order]
    extra = [heading for heading in order if heading not in canonical]
    rebuilt = list(preamble)
    for heading in known + extra:
        body = list(blocks[heading])
        while body and body[-1] == "":
            body.pop()
        rebuilt += [f"### {heading}"] + body + [""]
    while rebuilt and rebuilt[-1] == "":
        rebuilt.pop()
    return "\n".join(lines[:start + 1] + rebuilt + [""] + lines[end:])


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="validate every fragment; exit 1 on a problem")
    assembling = commands.add_parser("assemble", help="preview the [Unreleased] section with the fragments")
    assembling.add_argument("--write", action="store_true",
                            help="write CHANGELOG.md and delete the fragments that were assembled")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    directory = args.root / "changelog.d"
    fragments, problems = read_fragments(directory)
    for problem in problems:
        print(f"FAIL: {problem}")
    if args.command == "check":
        print(f"changelog-fragments: {'FAIL' if problems else 'PASS'} ({len(fragments)} fragment(s))")
        return 1 if problems else 0
    if problems:
        print("Nothing assembled: fix the fragments first.", file=sys.stderr)
        return 1
    changelog_path = args.root / "CHANGELOG.md"
    result = assemble(changelog_path.read_text(encoding="utf-8"), fragments)
    if not args.write:
        lines = result.split("\n")
        start, end = unreleased_bounds(lines)
        print("\n".join(lines[start:end]))
        print(f"PREVIEW ONLY: {len(fragments)} fragment(s); nothing was changed. Rerun with --write.")
        return 0
    changelog_path.write_text(result, encoding="utf-8", newline="\n")
    for fragment in fragments:
        fragment.path.unlink()
    print(f"Assembled {len(fragments)} fragment(s) into CHANGELOG.md and deleted them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
