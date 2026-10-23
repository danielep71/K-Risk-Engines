# 📈 Repository traffic history

[![daily traffic export](https://img.shields.io/github/actions/workflow/status/danielep71/K-Risk-Engines/daily-traffic.yml?branch=main&style=flat-square&label=daily%20traffic%20export)](https://github.com/danielep71/K-Risk-Engines/actions/workflows/daily-traffic.yml)
[![Schedule](https://img.shields.io/badge/Schedule-06:00_UTC_nominal-1f3a5f?style=flat-square)](https://github.com/danielep71/K-Risk-Engines/actions/workflows/daily-traffic.yml)
[![Data](https://img.shields.io/badge/Data-traffic--history-483698?style=flat-square)](https://github.com/danielep71/K-Risk-Engines/tree/traffic-history)

The daily export is scheduled for **06:00 UTC** and can be started manually
from **Actions → Daily traffic export** on `main`. GitHub may start scheduled
runs hours late; each snapshot records the time it was actually taken.
It measures GitHub repository traffic, not visits to the GitHub Pages website.

## 🔑 One-time credential setup

1. Open **Settings → Environments**, create `analytics`, and restrict its
   deployment branches to `main` only.
2. Create or update a fine-grained personal access token that includes
   `danielep71/K-Risk-Engines` with **Administration: read**.
3. Store that token as the environment secret **TRAFFIC_TOKEN** in `analytics`.
   Do not put the token in files, issues or chat. Rotate it before expiry and
   at least every 90 days; verify the actual date in GitHub token settings.
   Track the current rotation and reminder in [#57](https://github.com/danielep71/K-Risk-Engines/issues/57).
4. Run **Daily traffic export** manually on `main` and verify the new snapshot
   on `traffic-history`. Until that succeeds, badge values remain `pending`.

The repository files do not include the credential. Setup is complete only
when step 4 succeeds: a manual run on `main` that writes a new snapshot.
Secrets in another repository are not automatically shared with this one.

## 🗄️ Stored data

The `traffic-history` branch holds the analytics data and a short README:

| File | Contents |
| --- | --- |
| `README.md` | Branch description and a link to this page |
| `data/traffic.csv` | Daily snapshots of rolling 14-day traffic and repository counts |
| `data/traffic_daily.csv` | Daily views and clones, refreshed within the API window |
| `data/referrers.csv` | Top referrers per snapshot |
| `data/popular_paths.csv` | Popular repository paths per snapshot |
| `data/badges/*.json` | Shields endpoint data for clones, visits and 14-day visitors |

The branch was initialized from `main` at `85159f7` (commit `1b6d86d`), so
its history shares `main`'s early commits, while its current tree contains
only the files above. The workflow would create it as an orphan branch only
if it were missing. It is never merged into `main` or a release branch, and
its history is not rewritten.

The history is public. It contains aggregate counts, referrers and paths, not
individual visitor identities. GitHub retains only a short traffic window;
missed collection beyond that window cannot be recovered by this workflow.
Repeated same-day runs replace that day's snapshot rather than adding it twice.
Visits sum daily unique visitors; they are **not** distinct people across days.
The clones badge totals all recorded clones, including this repository's own CI
checkouts and maintainer clones, so it does not measure outside interest.

## 🚨 Alerts and permissions

The exporter compares the latest snapshot with the previous one and opens an
alert when 14-day views reach at least twice the previous value and at least
100 more, when 14-day clones reach at least twice the previous value and at
least 10 more, when stars or forks increase, or when a referrer not seen before
has at least five views. Alerts are deduplicated by date, assigned to `danielep71`,
labelled `P3` and `repository`, and placed in `Traffic monitoring`. The
milestone is created when first needed and reopened if it has been closed, so
closing it does not cause a duplicate-milestone-title failure when a new alert
is needed. If an alert for that date already exists (open or closed), the run
exits without updating it or reopening its milestone. First-run data
establishes the baseline without creating an alert. A zero baseline is easy to
exceed: the repository's own CI checkouts and maintainer clones can trigger a
clone alert, as on 2026-10-21 (#30).

The closed-milestone path was verified against live GitHub in
[#59](https://github.com/danielep71/K-Risk-Engines/issues/59): a synthetic local
fixture reopened the existing milestone and created one alert; a second run
created no duplicate. Cleanup restored the original milestone state and a
subsequent normal export succeeded. The test did not write synthetic traffic
history.

`TRAFFIC_TOKEN` is passed only to the API-fetch step. The job uses its
separate `GITHUB_TOKEN` to push history and create alerts. It does not execute
repository scripts or run website checks. Environment branch restrictions are
required protection; the environment name alone is not a security boundary.
