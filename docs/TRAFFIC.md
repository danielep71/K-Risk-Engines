# 📈 Repository traffic history

[![daily traffic export](https://img.shields.io/github/actions/workflow/status/danielep71/K-Risk-Engines/daily-traffic.yml?branch=main&style=flat-square&label=daily%20traffic%20export)](https://github.com/danielep71/K-Risk-Engines/actions/workflows/daily-traffic.yml)
[![Schedule](https://img.shields.io/badge/Schedule-06:17_UTC_nominal-1f3a5f?style=flat-square)](https://github.com/danielep71/K-Risk-Engines/actions/workflows/daily-traffic.yml)
[![Data](https://img.shields.io/badge/Data-traffic--history-483698?style=flat-square)](https://github.com/danielep71/K-Risk-Engines/tree/traffic-history)

The daily export is scheduled for **06:17 UTC**, off the hour, and can be started manually
from **Actions → Daily traffic export** on `main`. GitHub may start scheduled
runs hours late; each snapshot records the time it was actually taken.
It measures GitHub repository traffic, not visits to the GitHub Pages website.

## 🔑 One-time credential setup

The traffic API requires **Administration: read** on this repository. The
export obtains it from a dedicated GitHub App, as an installation token that
expires after an hour and is revoked when the job ends, so no long-lived token
needs rotating.

1. Open **Settings → Environments**, create `analytics`, and restrict its
   deployment branches to `main` only.
2. Under **Settings → Developer settings → GitHub Apps**, create an App for
   this export only. Disable its webhook, grant only the repository permission
   **Administration: read** (Metadata: read is added automatically) and allow
   installation only on this account.
3. Install the App on `danielep71/K-Risk-Engines` only.
4. In `analytics`, store the App's **Client ID** as the environment variable
   **TRAFFIC_APP_CLIENT_ID**, then generate a private key and store the whole
   `.pem` content as the environment secret **TRAFFIC_APP_PRIVATE_KEY**.
   Delete the downloaded `.pem` afterwards. Do not put the key in files, issues
   or chat.
5. Run **Daily traffic export** manually on `main` and verify the new snapshot
   on `traffic-history`. Until that succeeds, badge values remain `pending`.

The repository files do not include the credential. Setup is complete only
when step 5 succeeds: a manual run on `main` that writes a new snapshot.
Secrets in another repository are not automatically shared with this one.

### 🗓️ Credential history

Until 31 October 2026 the export used **TRAFFIC_TOKEN**, a fine-grained
personal access token with the same permission and a 90-day expiry, rotated by
hand ([#57](https://github.com/danielep71/K-Risk-Engines/issues/57)).
[#94](https://github.com/danielep71/K-Risk-Engines/issues/94) records the
migration to the App: after a run with the App succeeded, the token was revoked
and the secret deleted.

### 🔁 Rotating the private key

The installation tokens need no rotation. Rotate the App's private key if it
may have been exposed, or if this workflow is modified by someone other than
the maintainer:

1. Generate a new private key in the App's settings.
2. Replace `TRAFFIC_APP_PRIVATE_KEY` in **Settings → Environments →
   `analytics`**. The environment secret takes precedence over a repository
   secret of the same name, so a repository secret does not take effect.
3. Run **Daily traffic export** manually on `main` and confirm that **Fetch
   GitHub traffic API data** succeeds and a new snapshot is written.
4. Only then delete the old key in the App's settings, checking its
   fingerprint first, and run the export once more.

## 🗄️ Stored data

The `traffic-history` branch holds the analytics data and a short README:

| File | Contents |
| --- | --- |
| `README.md` | Branch description and a link to this page |
| `data/traffic.csv` | Daily snapshots of rolling 14-day traffic and repository counts |
| `data/traffic_daily.csv` | Daily views and clones, and `observed_at`: the collection that last reported them |
| `data/referrers.csv` | Top referrers per snapshot |
| `data/popular_paths.csv` | Popular repository paths per snapshot |
| `data/badges/*.json` | Shields endpoint data for clones, visits and 14-day visitors |

**`traffic-history` exception.** A data-only branch created by this workflow
would be an orphan. This repository's branch is the exception: it was
initialized from `main` at `85159f7` (commit `1b6d86d`), so its history shares
`main`'s early commits, while its current tree contains only the files above.
It is kept as it is: never recreated, rewritten, or merged into `main` or a
release branch. The workflow would create an orphan branch only if it were
missing.

[.github/scripts/traffic_history.py](../.github/scripts/traffic_history.py)
merges each collection, with tests in
[test_traffic_history.py](../.github/scripts/test_traffic_history.py):

- The newest observation of a date wins: a date the API reports again takes
  the new values, unless a newer collection already reported it. Dates a
  collection does not report keep their stored values; nothing is summed
  across collections.
- Merging the same collection twice changes nothing, and a later run on the
  same day replaces that day's snapshot, referrers and paths rather than
  adding them twice.
- Every response and every existing file is validated before anything is
  written, so an invalid collection leaves the history unchanged.
- Files written before `observed_at` existed are read as they are and
  rewritten with the column on the next merge; their rows count as older than
  any collection.

The history is public. It contains aggregate counts, referrers and paths, not
individual visitor identities. GitHub retains only a short traffic window;
missed collection beyond that window cannot be recovered by this workflow.
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

Each alert carries what **Issue triage** requires: a dependencies section
(`None.`) and a target end date 14 days after the snapshot, or the day before
the `Traffic monitoring` milestone's due date if that comes first. Give that
milestone a due date, or triage reports every alert in it.

The closed-milestone path was verified against live GitHub, before the alert
moved into its own job and script, in
[#59](https://github.com/danielep71/K-Risk-Engines/issues/59): a synthetic local
fixture reopened the existing milestone and created one alert; a second run
created no duplicate. Cleanup restored the original milestone state and a
subsequent normal export succeeded. The test did not write synthetic traffic
history.

The workflow has two jobs, each with one write permission:

- **Export GitHub traffic** (`collect`): the `analytics` environment and
  `contents: write`. The App token is passed only to the API-fetch step; the
  job's `GITHUB_TOKEN` pushes the history. Apart from the default branch's
  merge script it runs no repository code or tests.
- **Traffic alert** (`alert`): no environment, so it never receives the App's
  credentials, with `issues: write` to open the alert and manage its
  milestone.

The API requests use `X-GitHub-Api-Version: 2022-11-28`, like the hub's other
scripts. Environment branch restrictions are required protection; the
environment name alone is not a security boundary.
