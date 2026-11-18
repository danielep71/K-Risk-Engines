# 🧩 Changelog fragments

A pull request records its changelog entry as its own file here, so that two open pull
requests never edit the same lines of [CHANGELOG.md](../CHANGELOG.md).

- **Name:** `<issue>.<category>.md`, for example `374.changed.md`. The category is one
  of `added`, `changed`, `deprecated`, `removed`, `fixed` or `security`.
- **Content:** one Markdown list item (`- ...`) that cites its issue as `(#<issue>)`;
  continuation lines are indented by two spaces. Write it impersonally, as the entries of
  the changelog are.
- **Check:** `python3 .github/scripts/changelog_fragments.py check`. The unit tests run it
  on this directory.
- **Release:** the release commit assembles the fragments into the `[Unreleased]` section
  (`python3 .github/scripts/changelog_fragments.py assemble`, then `--write`), which puts
  each entry at the top of its category, newest first, and deletes the fragments. See
  [GOVERNANCE.md](../GOVERNANCE.md), Release records.

Entries written before this directory existed stay in `CHANGELOG.md`.
