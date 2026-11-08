# Document portal pilot

Analysis opened in [#223](https://github.com/danielep71/K-Risk-Engines/issues/223)
before implementation on 2026-11-08; tracked in **v1.1.0 - Document Portal**.
This is a technical pilot, not approval to replace the production website.

## Recommendation

Use an additive documentation portal at `/K-Risk-Engines/documentation/`.
Keep the current landing page, every existing asset and its fragments intact.
Compare Material for MkDocs 9.8.1 and Zensical 0.1.0 on the same input and
configuration. The pilot is technically buildable; production adoption is gated
on browser evidence, hosted checks and maintainer review.

Alternatives considered: keep the static site alone (lowest change, no internal
document search); use Material only (supported fallback); replace the landing
page (deferred design and URL migration); federate complete repositories through
plugins (deferred compatibility, licensing and content-maintenance complexity).

## Audited baseline and ownership

The hub is a hand-authored `index.html`, `assets/site.css`, SVG/PNG/JPEG artwork,
and Markdown in `docs/`; there is no pre-existing MkDocs configuration.
The recorded Pages configuration is legacy deployment from `main` at `/` in
[repository-settings.json](repository-settings.json). The existing
`website-checks.yml` checks HTML, links, Markdown, scripts and workflow controls;
it does not build or deploy a documentation generator. GitHub's branch-based
Pages build is separate. No Pages setting is changed by this pilot.

[GOVERNANCE.md](../GOVERNANCE.md) assigns the hub presentation/navigation and
each engine its methodology, implementation, evidence and releases. Task PRs
currently target `release/1.0.1`. Creating the v1.1.0 planning milestone does not
silently change the active branch, VERSION or publication policy. A release
branch transition needs a coherent follow-up governance change.

The existing [portfolio automation](PORTFOLIO_AUTOMATION.md) already reads
source documents and release/milestone metadata, retains provenance and proposes
updates through reviewed PRs. Its snapshot is the only source of hub status
paragraphs, published-release metadata and milestone counts in this pilot.
Source-document locations were separately audited at immutable commits recorded
in [sources.json](../tools/portal/sources.json). Different observation revisions
are explicitly distinguished; a newly built page is not a newly verified status.
The release branch snapshot can lag `main`, and the pilot does not relabel it as
current. Existing branch synchronization rules apply before integration.

All eight default-branch trees and governance documents were inspected. None
had a MkDocs/Zensical configuration in the audited tree. Existing engine
websites are not migrated and engine workflows are not modified.

| Domain | Repository | Methodology entry | Validation entry | Excel evidence entry |
| --- | --- | --- | --- | --- |
| CCR | K-SACCR | docs/methodology/README.md | docs/methodology/TEST_CASES.md | docs/EXCEL_EVIDENCE.md |
| CCR | K-SFTs | docs/methodology/README.md | docs/methodology/TEST_CASES.md | No dedicated document selected |
| Market Risk | K-FRTB-SA | docs/methodology.md | docs/validation.md | docs/EXCEL_EVIDENCE.md |
| Market Risk | K-CVA | docs/methodology/README.md | docs/methodology/TEST_CASES.md | docs/evidence/excel-run-194e9cd.md |
| IRRBB | K-IRRBB-NMDs | docs/methodology/README.md | docs/methodology/VALIDATION_PLAN.md | docs/EXCEL_EVIDENCE.md |
| IRRBB | K-IRRBB-Prepayment_Models | docs/methodology/README.md | docs/methodology/VALIDATION_PLAN.md | docs/EXCEL_EVIDENCE.md |
| Liquidity | K-LCR | docs/methodology/README.md | docs/methodology/VALIDATION_PLAN.md | No dedicated document selected |
| Liquidity | K-NSFR | prototype/docs/methodology/PROTOTYPE.md | docs/validation/VALIDATION.md | docs/validation/HOST_EVIDENCE.md |

The entries are document locations, not certifications. In particular, a test
case format, validation plan or host-record specification is not proof of an
executed run. The K-CVA record concerns a scaffold run; it does not validate
calculations. Full READMEs remain the limitation entry points. Missing selected
Excel documents are disclosed without claiming the repositories have no evidence.

## Content architecture

One root [mkdocs.yml](../mkdocs.yml), one portfolio manifest, one reviewed status
snapshot, one small map of source-document paths and SHA-256 digests. Build-time
pages are disposable under ignored `build/`. No generated engine documentation
is committed. Existing `PORTFOLIO_STATUS.md` is reused **byte for byte**, and
existing artwork is copied only into build output. Engine pages link to pinned
original documents; engine licences and notices remain at source.

Each of eight engine gateways has separate status, release, milestones,
methodology, validation, Excel evidence and limitations pages. Four domain
pages preserve the current pairing (CVA in Market Risk). Search indexes gateway
pages and the hub snapshot. **Full text of linked engine documents is not yet
federated into search**; this boundary is visible in the portal. Full-text
federation would require a separately tested import/rewrite pipeline, asset and
licence handling and commit-bound verification; no unsupported include plugin is
silently relied on.

## Compatibility findings

Official sources checked on 2026-11-08:
[configuration/migration](https://zensical.org/docs/compatibility/mkdocs/migration/),
[plugins](https://zensical.org/docs/compatibility/mkdocs/plugins/),
[Mermaid](https://zensical.org/docs/authoring/diagrams/).
These online claims are distinguished from local build evidence.

| Capability | Pilot choice | Verification / limitation |
| --- | --- | --- |
| Configuration | Shared YAML; explicit directory URLs and paths | Both strict builds succeed |
| Plugins | Only `search` | Native support documented; browser search still a release gate |
| Markdown | admonition, attr_list, md_in_html, tables, toc, details, superfences | Same config builds with both; specimen retained |
| Mermaid | SuperFences `mermaid` fence | Compatible markup generated; browser SVG rendering not yet verified |
| Images | Existing local SVG, PNG, JPEG | File references pass; responsive visual review pending |
| CSS | Minimal image sizing and link wrapping | No template overrides or Python callbacks |
| Hooks | Not used | Unsupported by Zensical |
| Other plugins | Explicitly rejected by pilot config check | Unsupported plugins may otherwise be silently ignored; gen-files is unsupported |
| Templates | Stock themes | Zensical MiniJinja cannot call arbitrary Python as Jinja can |
| Publishing | Actions artifact, later upload/deploy Pages | Zensical has no gh-deploy; do not use it |
| Proprietary features | None | No zensical.toml, custom theme variant or Zensical-specific content |

The two builders may use different search engines and presentation. Equal file
counts do not prove search, accessibility or visual equivalence. A successful
build is necessary but insufficient for migration.

## Reproduce and compare

Use Python 3.13.18 as in CI, a clean virtual environment and repository root:

```sh
python -m pip install --require-hashes --only-binary=:all: -r tools/requirements-portal.txt
python tools/portal/build.py
python tools/portal/test_portal.py
python tools/portal/check.py
python tools/portal/check.py --external
python -m http.server 8000 --directory build/pages-zensical
```

Visit `/documentation/` on the local server. Serve `build/pages-mkdocs` separately
for comparison. The CI workflow builds both with read-only permissions and
uploads candidates and `comparison.json`; there is **no deployment job**.
Both candidates retain existing tracked public paths and place documentation
under a new prefix. `comparison.json` inventories every generated HTML URL;
checks reject missing files/anchors, output path differences, unsupported plugin
configuration and selected obsolete repository references. Historical portfolio
quotations are not rewritten just to hide older release identifiers.

External checking verifies every selected immutable document against its recorded
SHA-256. Network or HTTP failures fail that check; they are not called a pass.
The existing `check-website.py --external` remains the general hub link checker.

## Browser acceptance record (pending)

Review both builders at desktop 1440×900 and mobile 390×844:

- Home, each domain, one engine overview and each topic, long portfolio snapshot.
- Navigation drawer/tabs, keyboard focus, wrapping and horizontal overflow.
- Search each of the eight engine names and `validation`; open a result.
- Mermaid must render an SVG, with readable labels; inspect PNG and SVG artwork.
- Compare current landing page and all its anchors in each packaged candidate.
- Record screenshots, browser/version, console/network failures, commit and build
  provenance; have the maintainer accept material design differences.

Local browser installation failed because the downloaded Chromium archive was
invalid. No desktop/mobile, interactive search or rendered Mermaid pass is
claimed. Keep this as an explicit acceptance blocker, not an unchecked assumption.

## Publication gate and rollback

GitHub Pages has one published site per repository. Deploying only the new
portal artifact would remove the current root and assets. Do not create a second
competing deploy workflow or switch Pages settings during the pilot.

After the comparison is accepted, propose a separate deployment PR that:

1. Builds and checks both candidates from reviewed `main`; keeps a known-good
   previous artifact and the baseline URL inventory.
2. Uses GitHub Pages Actions deployment (`actions/configure-pages`,
   `actions/upload-pages-artifact`, `actions/deploy-pages`, each SHA-pinned) to
   publish the **complete** chosen `build/pages-zensical` or `build/pages-mkdocs`
   artifact, not the documentation subdirectory alone.
3. Uses read-only build permissions; gives only the deploy job `pages: write`
   and `id-token: write`, with `github-pages` environment and serialized deploys.
4. Coordinates the Pages source-setting change from legacy to workflow mode,
   updates workflow-control tests, and verifies live root, assets, old fragments,
   documentation URLs and search after deployment. Publish only from `main`.
5. Retains Material selection for a reversible engine switch and prevents
   accidental selection from an unreviewed PR or branch.

Before deployment, rollback is simply closing/reverting the pilot change;
production never moved. After adoption, deploy the previous complete verified
artifact or the equivalent Material candidate, preserving the documentation
prefix and all old paths. Never roll back by deleting the new URL namespace.

Automatic source updates continue through existing portfolio-refresh PRs; the
next build consumes the merged snapshot without a second status store. Changes
to the source-document map require review and revalidation of digests. No AI
status inference, version guessed from branch names, auto-merge, source-engine
write access or model validation claim is introduced.
