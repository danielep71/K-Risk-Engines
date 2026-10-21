# Changelog

All notable changes to the K-Risk Engines hub are recorded here. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Engine
repositories keep their own changelogs; this file covers the hub only.

## [Unreleased]

No changes yet outside release 1.0.0.

## [1.0.0] - not yet released

First hub release, prepared on `release/1.0.0` and tracked in the
[v1.0.0 - Hub governance](https://github.com/danielep71/K-Risk-Engines/milestone/2)
milestone. The date is set when the release is published, after its milestone
is complete; interim integrations into `main` leave it unreleased.

### Added

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

### Changed

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
  so checks and review run without a manual approval; the refresh itself
  keeps a read-only token (#23).
- Configuration, scripts and workflows no longer carry wording from the
  repositories they were adapted from: orphan `.gitattributes` comments,
  template User-Agent names and engine-specific comments are gone, the
  label scripts default to `.github/label-policy.json`, the label policy
  selects a new `website` profile instead of `application`, and the P1
  label no longer mentions application state (#33).
- The README carries section glyphs consistent with the engine repositories;
  the portfolio anchor stays stable (#37).

### Fixed

- The README **Stars** badge links to the repository page: the stargazers
  page returns HTTP 404 to visitors who are not signed in (#13).
- Traffic alerts are filed even when the **Traffic monitoring** milestone
  has been closed: the workflow reopens it instead of failing on a duplicate
  title (#8).
