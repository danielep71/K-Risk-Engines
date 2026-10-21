# Repository traffic history

The daily export runs at **06:00 UTC daily**
and can be started manually from **Actions → Daily traffic export** on `main`.
It measures GitHub repository traffic, not visits to the GitHub Pages website.

## One-time credential setup

1. Open **Settings → Environments**, create `analytics`, and restrict its
   deployment branches to `main` only.
2. Create or update a fine-grained personal access token that includes
   `danielep71/K-Risk-Engines` with **Administration: read**.
3. Store that token as the environment secret **TRAFFIC_TOKEN** in `analytics`.
   Do not put the token in files, issues or chat. Rotate it every 90 days.
4. Run **Daily traffic export** manually on `main` and verify the new snapshot
   on `traffic-history`. Until that succeeds, badge values remain `pending`.

The repository files do not include the credential. Setup is complete only
when step 4 succeeds: a manual run on `main` that writes a new snapshot.
Secrets in another repository are not automatically shared with this one.

## Stored data

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

## Alerts and permissions

The exporter opens an alert for a substantial increase in
rolling views/clones, additional stars/forks, or a newly observed referrer with
at least five views. Alerts are deduplicated by date, assigned to `danielep71`,
labelled `P3` and `repository`, and placed in `Traffic monitoring`. The
milestone is created when first needed and reopened if it has been closed, so
closing it after a review never blocks the next alert. First-run data
establishes the baseline without creating an alert.

`TRAFFIC_TOKEN` is available only to the API-fetch step. The job uses its
separate `GITHUB_TOKEN` to push history and create alerts. It does not execute
repository scripts or run website checks. Environment branch restrictions are
required protection; the environment name alone is not a security boundary.
