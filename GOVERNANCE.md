# 🏛️ Portfolio governance

[![Active release branch](https://img.shields.io/badge/Active_branch-release%2F1.0.0-1f3a5f?style=flat-square)](https://github.com/danielep71/K-Risk-Engines/tree/release/1.0.0)
[![Milestone](https://img.shields.io/badge/Milestone-v1.0.0_Hub_governance-483698?style=flat-square)](https://github.com/danielep71/K-Risk-Engines/milestone/2)
[![Priorities](https://img.shields.io/badge/Priorities-P1_·_P2_·_P3-D93F0B?style=flat-square)](https://github.com/danielep71/K-Risk-Engines/labels)
[![License](https://img.shields.io/badge/License-MPL--2.0-0078D6?style=flat-square)](LICENSE)

## 👤 Ownership and scope

**Daniele Penza (@danielep71)** maintains K-Risk-Engines and decides portfolio
scope, inclusion, priorities and publication. Contributors and automation work
within the scope authorized by the maintainer.

This repository owns the portfolio website, navigation, shared presentation,
hub documentation and supporting automation. Each engine repository owns its
methodology, implementation, validation evidence, issues, licences and releases.
A hub change does not authorize a change or release in an engine repository.

This is an independent personal project.

## 🏷️ Portfolio inclusion and status

List a project when its intended risk-management purpose fits the portfolio,
its scope and ownership are clear, and its status can be stated honestly.
Implemented projects must link to their authoritative repository and available
documentation. A planned project may be listed without a repository, provided
the absence of an implementation is explicit.

| Status | Meaning and minimum evidence |
| --- | --- |
| Planned | Intended scope only; no implementation is represented as available. |
| In development | Implementation work is underway; link to the repository and describe what currently exists and what remains incomplete. |
| Prototype | An exploratory implementation exists with a documented scope and limitations. State material gaps in execution or validation evidence explicitly. |
| Released | The project has a published release or distributed artifact identifiable in its own repository. Release availability does not establish independent validation, regulatory compliance or production readiness. |

These labels describe availability and development state, not a certification
scale. A released project can still have significant limitations. Do not infer
status from a roadmap, milestone closure, badge or successful static check.

When changing a listing, verify its claims against the project's documentation,
release and test evidence. Keep the README and website consistent, retain
material caveats, and date status snapshots. The engine repository remains
authoritative if a hub snapshot becomes stale. Record the supporting links in
the change description or relevant issue.

## 🌿 Branches and publication

| Branch | Role |
| --- | --- |
| `main` | Published hub source; GitHub Pages deploys from it. Receives the active release branch through a merge commit, and automated portfolio-status proposals (below). |
| `release/1.0.0` | **Active release branch.** The single base for task branches and pull requests. |
| Other `release/X.Y.Z` | Opened only by maintainer decision, without a `v` prefix. Do not infer a new target from a version number. |
| `fix/<issue>-<slug>`, `docs/<slug>`, `test/<slug>` | Short-lived task branches, created from the active release branch and deleted after merge. |
| `traffic-history` | Generated repository analytics. Not a release branch; never merged into `main` or a release branch. |

1. Create a task branch from the active release branch, never from `main` or
   GitHub's default branch by assumption.
2. Open a pull request against the active release branch. Website checks run
   on pull requests and pushes to `main` and `release/**`.
3. Squash-merge once the checks pass and every review finding is fixed or
   answered.
4. Integrate the release branch into `main` with a merge commit, only after
   maintainer review. Then bring the release branch level with `main`
   again (fast-forward to the integration commit).
5. When `main` receives commits that are not on the release branch, bring
   them in by merging `main` into the release branch. Never rebase or
   force-push a shared branch.

The daily portfolio refresh is the one routine exception: it proposes dated
status snapshots as a pull request from `automation/portfolio-refresh`
directly to `main` (see
[docs/PORTFOLIO_AUTOMATION.md](docs/PORTFOLIO_AUTOMATION.md)), so that status
is not held back by a release. It opens that pull request with a GitHub App
token, so its checks run without a manual approval. The code-review bot
does not review bot-authored pull requests, so the maintainer's review before
merging is the only review of a proposal. Merge `main` into the release
branch after such a pull request lands.

### 📦 Release records

- [VERSION](VERSION) holds the version of the active release branch.
- [CHANGELOG.md](CHANGELOG.md) records each change under the release in
  progress; every task pull request adds its entry. Interim integrations of
  the release branch into `main` leave it unreleased.
- When its milestone is complete and the maintainer approves publication, a
  release commit on the release branch sets the date. That commit is
  integrated into `main`, and the maintainer publishes a GitHub Release
  that creates the `vX.Y.Z` tag on the integration commit, the same day.
  The changelog's version links are added once the tag exists.
- Pull requests follow
  [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md),
  including what was not validated.
- When a new release branch is opened, update this table, the badges at the
  top of this page and of the README, `VERSION`, and `target-branch` in
  [.github/dependabot.yml](.github/dependabot.yml).

### ✅ For every change

- Inspect the diff and run applicable checks before publishing. For website
  changes, run `python3 .github/scripts/check-website.py`; when external links
  change, also run it with `--external`. Review visual changes in a browser.
  Apply the relevant label-script checks when changing label configuration.
- Verify applicable hosted checks and, after integration into `main`, the
  deployment. Investigate failures and fix or revert through a new commit.
  Preserve shared history; do not force-push or delete the long-lived
  branches.
- Report checks actually performed and remaining limitations. Self-review,
  automated checks and independent review are different forms of evidence.

These are working rules, not a claim that every step is enforced by GitHub
settings.

## 🗂️ Issues and decisions

Hub issues cover navigation, presentation, portfolio metadata, documentation
and automation. Route engine-specific methodology, calculation and validation
issues to the corresponding repository.

Assign hub issues to **danielep71**, give each exactly one priority
(`P1`, `P2` or `P3`), appropriate type labels and a relevant milestone.
Release work uses a milestone named `vX.Y.Z - <title>`, matching its release
branch and numbered independently of any engine. Ongoing work outside a
release uses a descriptive milestone; traffic alerts use **Traffic
monitoring**.

The label catalogue is maintained in
[.github/labels.json](.github/labels.json). Record the objective and acceptance
criteria for substantive work. Close completed issues only when those criteria
are met, with a link to the change and relevant verification; explain other
closure reasons explicitly. Record material scope or policy decisions in an
issue, pull request or commit description.

## 🔐 Security and analytics

Report suspected vulnerabilities privately under [SECURITY.md](SECURITY.md).
Never include tokens or confidential client data in issues, examples or commits.
Traffic collection and its operational requirements are documented in
[docs/TRAFFIC.md](docs/TRAFFIC.md); repository traffic does not measure website
visitors or model quality.
