# ⚖️ Licensing and attribution

[![License](https://img.shields.io/badge/License-MPL--2.0-1f3a5f?style=flat-square)](LICENSE)
[![Artwork excluded](https://img.shields.io/badge/Artwork-excluded_from_MPL-B60205?style=flat-square)](#portfolio-artwork-exclusion)
[![Independent project](https://img.shields.io/badge/Independent-personal_project-6E7781?style=flat-square)](#linked-projects-and-third-party-rights)

Copyright 2026 Daniele Penza and contributors.

## 📝 Code and documentation

The hub's code and documentation, including HTML, CSS, scripts, workflows,
configuration and Markdown files, are covered by the Mozilla Public License
2.0 in [LICENSE](LICENSE), unless a file carries a separate notice.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

<a id="portfolio-artwork-exclusion"></a>

## 🖼️ Portfolio artwork exclusion

`assets/K-Risk-Engines-social-preview-v2.jpg` is an AI-generated decorative portfolio
image and is excluded from the MPL-2.0 grant. No separate reuse licence is
granted for this image by this repository. Contact the maintainer before
reusing it. This exclusion does not apply to `assets/site.css` or asset
documentation.

<a id="linked-projects-and-third-party-rights"></a>

## 🔗 Linked projects and third-party rights

Linked engine repositories retain their own licences. This hub's licence
does not relicense their code, documentation or assets, or grant rights to
third-party names, trademarks or logos. This is an independent personal
project.

<a id="quality-gates"></a>

## 🧪 Quality gates

`pyproject.toml`, `tools/requirements-quality-ci.txt`,
`.github/requirements.txt` and `.github/scripts/test_workflow_controls.py`
were adapted from danielep71/MyTemplate (a private template repository)
under the Mozilla Public License 2.0; MyTemplate adapted the first three from
[danielep71/K-SFTs](https://github.com/danielep71/K-SFTs) under the same
licence. Modifications: the checks cover `.github/scripts`, PyYAML is treated
as untyped by mypy, and the workflow rules name this repository's jobs, its
required check `HTML and links` and the traffic push as the one checkout that
keeps credentials.

<a id="adapted-files"></a>

## 🧩 Adapted files

The following files were adapted from
danielep71/MyTemplate, a private template repository, under the
Mozilla Public License 2.0. MyTemplate in turn adapted them from
[danielep71/K-SFTs](https://github.com/danielep71/K-SFTs), with the target end
date rule from danielep71/K-NSFR, both
under the Mozilla Public License 2.0:

- `.github/scripts/check_issues.py`
- `.github/scripts/test_check_issues.py`
- `.github/workflows/issue-triage.yml`
- the target end date and dependency fields of `.github/ISSUE_TEMPLATE/hub-bug.yml`
  and `.github/ISSUE_TEMPLATE/hub-improvement.yml`

Modifications: file locations; hub form names; no rule reserving `P1` for
calculation bugs, since the hub has no calculations; the hub's JSON-formatted
issue forms are read as JSON; references to this repository's
[GOVERNANCE.md](GOVERNANCE.md).

<a id="mit-licensed-files"></a>

## 🧾 MIT-licensed file

`.github/workflows/pr-milestones.yml` was adapted from
[danielep71/K-FRTB-SA](https://github.com/danielep71/K-FRTB-SA), through
danielep71/MyTemplate (a private template repository), under the
MIT License below. Its tests in `.github/scripts/test_pr_milestones.py` were
adapted from MyTemplate. Modifications: pushes and manual runs use only the
default branch's copy, the job has `issues: read` so the script can read pull
requests on a private repository, and the comments refer to this repository's
[GOVERNANCE.md](GOVERNANCE.md). This notice applies to that file, not to
unrelated project files.

```text
MIT License

Copyright (c) 2026 Daniele Penza

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

<a id="traffic-history-merge"></a>

## 📈 Traffic history merge

The merge rules of `.github/scripts/traffic_history.py` (newest observation
of each date, idempotent merge, validation before writing), its alert's
dependencies and planning sections, and the split of
`.github/workflows/daily-traffic.yml` into collection and alert jobs were
adapted from danielep71/MyTemplate (a private template repository)
under the Mozilla Public License 2.0. Modifications: this repository's CSV
layout and badge files, its alert thresholds and labels, and the GitHub App
credential of the collection job.

<a id="settings-tool"></a>

## 🧰 Settings tool

`.github/scripts/setup_repository.py` and
`.github/scripts/test_setup_repository.py` were adapted from
danielep71/MyTemplate (a private template repository) under the Mozilla Public
License 2.0. Modifications: file locations, the hub's settings file and
required check, rebase merging as a fifth general option, and the GitHub Pages
source.
