# 📜 Changelog

[![Keep a Changelog](https://img.shields.io/badge/Keep_a_Changelog-1.1.0-E05735?style=flat-square)](https://keepachangelog.com/en/1.1.0/)
[![SemVer](https://img.shields.io/badge/SemVer-2.0.0-3F4551?style=flat-square)](https://semver.org/spec/v2.0.0.html)
[![Development](https://img.shields.io/badge/Development-1.0.1-483698?style=flat-square)](VERSION)

All notable changes to the K-Risk Engines hub are recorded here. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Engine
repositories keep their own changelogs; this file covers the hub only.

## [Unreleased]

### 🔧 Changed

- Describe portfolio refresh inputs by configuration rather than a stale
  fixed repository count (#83).
- Show the counterparty credit risk framework the calculators belong to, in
  the README and on the website: a diagram from the K-SACCR and K-SFTs
  exposures to the ordinary and CCP capital branches and their aggregation,
  with CVA risk as a separate market-risk memo item, shared with those
  repositories (`assets/CCR_framework.svg`, `.png`; #89).
- Name the non-maturity deposit project K-IRRBB NMDs consistently in the
  website, portfolio configuration and generated documentation (#81).
- Include K-SFTs in the website, portfolio evidence and automatic refresh;
  list K-CVA as private without exposing private source content (#79).
- Audit non-Markdown files: correct generated proposal CI guidance, workflow
  credential/rotation comments, website source attribution and the prepayment
  roadmap link (#76).
- Audit hub Markdown: clarify maintenance scope, valid PR targets, security-fix
  routing, shared-runner credential boundaries, traffic alert deduplication and
  attribution of generated engine status quotations (#73).
- Require review evidence for the final PR head after fix pushes, with an
  explicit Codex rerun procedure and manual review for skipped bot PRs (#58).
- Permit bot-authored commits from authorized repository workflows, preserving
  their attribution and existing review and CI requirements (#66).
- Open `release/1.0.1`, update the development version and badges, and retarget
  Dependabot version updates to the active release branch (#52).
- Require the GitHub Actions `HTML and links` check on `main` and `release/**`,
  preserving fast-forward synchronization after the integration commit passes.
  Traffic history retains deletion and force-push protection without website CI (#52).
- Enable private vulnerability reporting and make its GitHub form the primary
  reporting route; enable Dependabot security updates and prerequisites (#52).
- Update the portfolio refresh GitHub App token action from v3.2.0 to the
  pinned v3.3.0 release, reapplying the update proposed in #55 under maintainer
  authorship (#56). Scheduled refresh runs on `main` verified it live
  (#60).
- The changelog links each version to its release and comparison, and
  `GOVERNANCE.md` states that the tag is created by publishing the GitHub
  Release (#50).
- The issue chooser links all four engine repositories, including K-IRRBB
  Prepayment Models; the authorship rule in `GOVERNANCE.md` states the policy
  without referring to an instruction outside the repository (#67).
- Governance records the finished `release/1.0.0` branch, squash merges for
  portfolio-refresh proposals and the changelog badge in the release-branch
  checklist. The README adds a latest-release badge and labels the clones badge
  as including CI; the traffic documentation states that schedules can run late
  and that clone counts include the repository's own checkouts (#68).
- `GOVERNANCE.md` and `SECURITY.md` call `release/1.0.1` the active release
  branch throughout, used as the maintenance queue; squash commit titles carry
  only the PR number; the portfolio-refresh paragraph refers to step 5 for
  synchronization; the `[Unreleased]` list is one list again.

## [1.0.0] - 2026-10-22

First hub release, prepared on `release/1.0.0` and tracked in the
[v1.0.0 - Hub governance](https://github.com/danielep71/K-Risk-Engines/milestone/2)
milestone.

### ✨ Added

- Portfolio landing page and styles (`index.html`, `assets/site.css`) with
  social preview artwork, published through GitHub Pages from `main`.
- README with the portfolio table, badges, and website and traffic sections.
- Issue label catalogue with synchronization and drift workflows.
- Website checks: a dependency-free script for HTML structure, assets,
  anchors and external links, run in GitHub Actions.
- Daily repository traffic export to `traffic-history`, with badges and
  alert issues (`docs/TRAFFIC.md`).
- Daily portfolio status refresh that proposes status updates as a pull
  request (`docs/PORTFOLIO_AUTOMATION.md`, `docs/PORTFOLIO_STATUS.md`).
- Governance, security policy and hub issue forms that route engine-specific
  reports to the engine repositories.
- MPL-2.0 licence with an exclusion for the portfolio artwork (`LICENSE`,
  `NOTICE.md`).
- Editor and Git configuration (`.editorconfig`, `.gitattributes`,
  `.gitignore`).
- Pull request template, Dependabot updates for GitHub Actions, this
  changelog and `VERSION` (#14).
- Website checks also validate links in tracked Markdown files: relative
  targets, heading and `<a id>` anchors, and external URLs in the external
  pass, with tests for the checker (#13).

### 🔧 Changed

- Website checks also run on pull requests and pushes to `release/**`
  branches (#6).
- `GOVERNANCE.md` documents the release-branch workflow, with
  `release/1.0.0` as the active release branch (#7).
- Traffic documentation and `NOTICE.md` no longer cite another repository
  as the origin of the hub's setup (#9).
- The traffic credential setup states what completes it (a manual run that
  writes a snapshot) instead of describing how the files were installed (#11).
- The traffic documentation and workflow header describe `traffic-history` as
  it is: initialized from `main`, with shared history, a README and the
  analytics data (#10).
- Workflow and configuration headers describe each file's purpose instead
  of naming another repository as its source (#12).
- The daily portfolio refresh opens its pull request with a GitHub App token,
  so its checks run without a manual approval; the refresh itself keeps a
  read-only token. The maintainer's review is the only review of a proposal,
  because the code-review bot skips bot-authored pull requests (#23).
- Configuration, scripts and workflows no longer carry wording from the
  repositories they were adapted from: orphan `.gitattributes` comments,
  template User-Agent names and engine-specific comments are gone, the
  label scripts default to `.github/label-policy.json`, the label policy
  selects a new `website` profile instead of `application`, and the P1
  label no longer mentions application state (#33).
- The README carries section glyphs consistent with the engine repositories;
  the portfolio anchor stays stable (#37).
- All Markdown documentation carries heading glyphs and status badges, and
  stale statements about reviews of refresh proposals, traffic alert rules
  and the prepayment artwork are corrected (#40).
- The README, website footer, governance and notice describe the hub as an
  independent personal project without naming any firm (#43).
- `GOVERNANCE.md` describes how a release is dated, integrated into `main`,
  tagged and published (#48).

### 🐛 Fixed

- The README **Stars** badge links to the repository page: the stargazers
  page returns HTTP 404 to visitors who are not signed in (#13).
- Traffic alerts are filed even when the **Traffic monitoring** milestone
  has been closed: the workflow reopens it instead of failing on a duplicate
  title (#8).

[Unreleased]: https://github.com/danielep71/K-Risk-Engines/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/danielep71/K-Risk-Engines/releases/tag/v1.0.0
