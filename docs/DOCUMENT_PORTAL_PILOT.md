# Document portal pilot

Analysis opened in [#223](https://github.com/danielep71/K-Risk-Engines/issues/223)
before implementation on 2026-11-08; tracked in **v1.1.0 - Document Portal**.
The pilot was accepted on 2026-11-09 (#240) and the portal is published
additively at `/K-Risk-Engines/documentation/`, built with Zensical; the
landing page and every existing path are unchanged (see
[Publication and rollback](#publication-and-rollback)).

## Recommendation

Use an additive documentation portal at `/K-Risk-Engines/documentation/`.
Keep the current landing page, every existing asset and its fragments intact.
Compare Material for MkDocs 9.8.1 and Zensical 0.1.0 on the same input and
configuration. Adoption followed the browser evidence, the hosted checks and
review recorded below.

Alternatives considered: keep the static site alone (lowest change, no internal
document search); use Material only (supported fallback); replace the landing
page (deferred design and URL migration); federate complete repositories through
plugins (deferred compatibility, licensing and content-maintenance complexity).

## Audited baseline and ownership

The hub is a hand-authored `index.html`, `assets/site.css`, SVG/PNG/JPEG artwork,
and Markdown in `docs/`; there is no pre-existing MkDocs configuration.
At the audit, the recorded Pages configuration was legacy deployment from
`main` at `/`. The existing `website-checks.yml` checks HTML, links, Markdown,
scripts and workflow controls; it does not build or deploy a documentation
generator. The pilot changed no Pages setting; publication moved the Pages
source to GitHub Actions, as now recorded in
[repository-settings.json](repository-settings.json) (below).

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
in [sources.json](../tools/portal/sources.json), each with its audit date
(K-FRTB-SA re-audited on 2026-11-13 at `231991c`). Different observation revisions
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
| Market Risk | K-FRTB-SA | docs/methodology.md | docs/validation.md | docs/evidence/2026-11-12-excel-check-1badef1.md |
| Market Risk | K-CVA | docs/methodology/README.md | docs/methodology/TEST_CASES.md | docs/evidence/excel-run-194e9cd.md |
| IRRBB | K-IRRBB-NMDs | docs/methodology/README.md | docs/methodology/VALIDATION_PLAN.md | docs/EXCEL_EVIDENCE.md |
| IRRBB | K-IRRBB-Prepayment_Models | docs/methodology/README.md | docs/methodology/VALIDATION_PLAN.md | docs/EXCEL_EVIDENCE.md |
| Liquidity | K-LCR | docs/methodology/README.md | docs/methodology/VALIDATION_PLAN.md | No dedicated document selected |
| Liquidity | K-NSFR | prototype/docs/methodology/PROTOTYPE.md | docs/validation/VALIDATION.md | docs/validation/HOST_EVIDENCE.md |

The entries are document locations, not certifications. In particular, a test
case format, validation plan or host-record specification is not proof of an
executed run. The K-CVA record concerns a scaffold run; it does not validate
calculations. The K-FRTB-SA records are two desktop Excel sessions on one
host, a run on `323260b` and the unattended check on `1badef1`; the selected
record is the check, which links the run. Neither validates results for
regulatory use. Full READMEs remain
the limitation entry points. Missing selected Excel documents are disclosed
without claiming the repositories have no evidence.

## Content architecture

One root [mkdocs.yml](../mkdocs.yml), one portfolio manifest, one reviewed status
snapshot, one small map of source-document paths and SHA-256 digests. Build-time
pages are disposable under ignored `build/`. No generated engine documentation
is committed. Existing `PORTFOLIO_STATUS.md` is reused **byte for byte**, and
existing artwork is copied only into build output. Hub reference documents
listed in `REFERENCES` of `tools/portal/build.py` (currently
[CCR_AT_A_GLANCE.md](CCR_AT_A_GLANCE.md)) are reused byte for byte under
`reference/` in the same way. Engine pages link to pinned
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
| Plugins | Only `search` | Native support documented; browser search verified in both builds on 2026-11-09 |
| Markdown | admonition, attr_list, md_in_html, tables, toc, details, superfences | Same config builds with both; specimen retained |
| Mermaid | SuperFences `mermaid` fence | Rendered as a diagram in both builds on 2026-11-09 (script loaded at view time) |
| Images | Existing local SVG, PNG, JPEG, PDF | File references pass; reviewed at 1280 and 390 px on 2026-11-09 |
| CSS | Minimal image sizing and link wrapping | No template overrides or Python callbacks |
| Hooks | Not used | Unsupported by Zensical |
| Other plugins | Explicitly rejected by pilot config check | Unsupported plugins may otherwise be silently ignored; gen-files is unsupported |
| Templates | Stock themes | Zensical MiniJinja cannot call arbitrary Python as Jinja can |
| Publishing | Pages artifact and deployment from GitHub Actions | Zensical has no gh-deploy; do not use it |
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
uploads candidates and `comparison.json`; only its `deploy` job publishes, from
the default branch (see [Publication and rollback](#publication-and-rollback)).
Both candidates retain existing tracked public paths and place documentation
under a new prefix. `comparison.json` inventories every generated HTML URL;
checks reject missing files/anchors, output path differences, unsupported plugin
configuration and selected obsolete repository references. Historical portfolio
quotations are not rewritten just to hide older release identifiers.

External checking verifies every selected immutable document against its recorded
SHA-256. Network or HTTP failures fail that check; they are not called a pass.
The existing `check-website.py --external` remains the general hub link checker.

## Browser acceptance record

Planned review of both builders at desktop 1440×900 and mobile 390×844:

- Home, each domain, one engine overview and each topic, long portfolio snapshot.
- Navigation drawer/tabs, keyboard focus, wrapping and horizontal overflow.
- Search each of the eight engine names and `validation`; open a result.
- Mermaid must render an SVG, with readable labels; inspect PNG and SVG artwork.
- Compare current landing page and all its anchors in each packaged candidate.
- Record screenshots, browser/version, console/network failures, commit and build
  provenance; have material design differences accepted.

Record of 2026-11-09, hub commit `52f647c` (the #240 head), Chromium through
Playwright, both candidates served locally at 1280×900 and 390×844: the home,
compatibility and K-SACCR status pages load with no horizontal overflow; the
Mermaid specimen renders as a diagram with readable labels in both; searching
`validation` returns results in both (20 in Material, 35 in Zensical). Not
reviewed: every domain and topic page, each engine-name search, keyboard focus
and screen-reader output, and the landing-page anchors inside the candidates
(the static files are copied byte for byte and `check.py` verifies them).
Material for MkDocs announces its end of life on 2027-05-05 and names Zensical
its successor; Zensical is therefore the published builder, and Material stays
the tested fallback.

## Publication and rollback

GitHub Pages has one published site per repository, so deploying the portal
directory alone would remove the current root and assets. The `deploy` job of
[document-portal.yml](../.github/workflows/document-portal.yml) therefore
publishes the **complete** `build/pages-zensical` candidate: every tracked file
unchanged, plus the portal under `/documentation/`.

1. It publishes only on pushes to the default branch and manual runs on it;
   pull requests and other branches build and check the candidates but never
   package or deploy them.
2. The build job is read-only and packages the candidate with
   `actions/upload-pages-artifact`; only the deploy job has `pages: write` and
   `id-token: write`, uses the `github-pages` environment and queues behind
   any deployment in progress (`actions/deploy-pages`). Both actions are
   SHA-pinned; `actions/configure-pages` is not needed and not used.
3. It deploys only while the Pages source is **GitHub Actions**
   (`build_type: workflow`, [repository settings](REPOSITORY_SETTINGS.md)).
   With the earlier branch source it deploys nothing and reports a warning, so
   the workflow can reach `main` before the setting changes.
4. After each deployment it fetches the root, `assets/site.css`, a Markdown
   document, the portal home, an engine gateway and the search index, and
   fails if any is missing.
5. The workflow-control tests pin this shape: the default-branch condition,
   the complete-candidate path, the builder choice and the deploy permissions.

Rollback: run the workflow manually on the default branch with the `mkdocs`
builder to publish the equivalent Material candidate, or revert the change and
run it again to republish an earlier commit. Every old path and the
`/documentation/` prefix stay in place either way; never roll back by deleting
the new URL namespace. To return to branch publishing, set the Pages source
back to the default branch and revert this workflow change.

Automatic source updates continue through existing portfolio-refresh PRs; the
next build consumes the merged snapshot without a second status store. Changes
to the source-document map require review and revalidation of digests. No AI
status inference, version guessed from branch names, auto-merge, source-engine
write access or model validation claim is introduced.
