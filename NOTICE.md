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
