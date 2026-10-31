# 📊 Portfolio status evidence

[![portfolio refresh](https://img.shields.io/github/actions/workflow/status/danielep71/K-Risk-Engines/portfolio-refresh.yml?branch=main&style=flat-square&label=portfolio%20refresh)](https://github.com/danielep71/K-Risk-Engines/actions/workflows/portfolio-refresh.yml)

Proposed automatically from public project sources; reviewed on merge. Release availability and milestone progress do not establish model validity. This is a snapshot, not a live dashboard; follow the pinned source links for the captured revision and the project repository for newer evidence. Status paragraphs quote the source project: paths, issue numbers and references to “this repository” belong to that engine, not K-Risk-Engines. Presentation changes belong in the portfolio-refresh renderer; do not edit generated quotations or counts by hand.

<a id="saccr"></a>
## 🧩 K-SACCR

Version 1.0.2 is the current release: the 1.0.2 GitHub Release carries the workbook and the user manual. The engine implements EU CRR and Basel CRE52, but only Basel rules are validated in v1.0.2, by the published CRE99 examples. CRR rules are implemented and tested against illustrative values, not validated (methodology).

### 🔗 Sources

- [README.md](https://github.com/danielep71/K-SACCR/blob/599e40b283dd3783ca69c9305e170633819ea5c1/README.md) — content SHA-256 `db85e8a1714643c867f6a80acfc22ebbc090218d8c0b3b449056b77be35e7468`
- [docs/methodology/README.md](https://github.com/danielep71/K-SACCR/blob/599e40b283dd3783ca69c9305e170633819ea5c1/docs/methodology/README.md) — content SHA-256 `18d345f0d3f1e28a066a63b0aa0b59c1b84bd612903f4d0d24e01438a98e905a`
- Published release: [v1.0.2](https://github.com/danielep71/K-SACCR/releases/tag/v1.0.2) (2026-10-22T21:46:09Z)

### 🏁 Milestones (tracking only)

- [v0.0.1 - Repo setup](https://github.com/danielep71/K-SACCR/milestone/1): closed; 26 closed / 0 open issues.
- [v1.0.0 - First Supported Excel Release](https://github.com/danielep71/K-SACCR/milestone/2): closed; 57 closed / 0 open issues.
- [v1.1.0 - CSV Import, Staging and Workbook Protection](https://github.com/danielep71/K-SACCR/milestone/3): open; 15 closed / 14 open issues.
- [v1.2.0 - Excel Ribbon Interface](https://github.com/danielep71/K-SACCR/milestone/4): open; 0 closed / 9 open issues.
- [v1.3.0 - Diagnostics and Independent Validation](https://github.com/danielep71/K-SACCR/milestone/5): open; 0 closed / 6 open issues.
- [v1.4.0 - Advanced Products and FX Provenance](https://github.com/danielep71/K-SACCR/milestone/6): open; 0 closed / 3 open issues.
- [v1.5.0 - Simplified SA-CCR](https://github.com/danielep71/K-SACCR/milestone/7): open; 0 closed / 0 open issues.
- [v1.6.0 - Original Exposure Method](https://github.com/danielep71/K-SACCR/milestone/8): open; 0 closed / 0 open issues.
- v1.8.0 - Securities Financing Transactions: historical snapshot recorded open; 0 closed / 1 open issues. Milestone URL no longer available as of 2026-10-27.
- v1.9.0 - Regulatory CVA Risk: historical snapshot recorded open; 0 closed / 1 open issues. Milestone URL no longer available as of 2026-10-27.
- v1.10.0 - Risk-Weighted Assets and Capital: historical snapshot recorded open; 0 closed / 2 open issues. Milestone URL no longer available as of 2026-10-27.
- [v1.0.1 - Post release hardening](https://github.com/danielep71/K-SACCR/milestone/13): closed; 9 closed / 0 open issues.
- [v1.0.2 - Clearing Coverage and CCP Completeness](https://github.com/danielep71/K-SACCR/milestone/14): closed; 10 closed / 0 open issues.
- [v1.7.0 - Standalone Python Engine and VBA/Python Reconciliation](https://github.com/danielep71/K-SACCR/milestone/15): open; 0 closed / 10 open issues.

<a id="nmd"></a>
## 🧩 K-IRRBB NMDs

v0.2.0 – Workbook, data and Excel tests (in progress). The v0.1.0 foundation, closed on 2026-10-09, established source layout, documentation, issue governance, CI and static source checks; v0.2.0 builds the first workbook, data import and Excel test harness. Neither delivers pricing, econometric fitting, a production workbook or certified IRRBB outputs. - Decay model (draft, not validated, milestone v0.3.0): core, public facade IRRBB_Decay, harness cases and example, reviewed on release/v0.3.0 and present here since this branch was levelled with main; built to MODEL_CONTRACTS.md and under review in #36; no Excel evidence is recorded yet. Rate and stable-amount models are not built. - Application profile: an Excel workbook will be the end-user deliverable, assembled from reviewed exported VBA source. - Production calculations live in src/core/ without direct Excel object dependencies; at present the data import&#x27;s parsing, validation, summaries and fingerprint, and the draft decay calculations. - src/modules/ exposes the documented public facade (the data import and the draft decay model, listed in docs/PUBLIC_API.txt); src/workbook/ contains host glue only. - tests/ holds synthetic fixtures, expected results and the VBA regression harness; evidence from a real Excel run must be separately recorded. - No client data, confidential third-party material, vendor source code or customer-specific models are allowed in Git; the repository and its history are public.

### 🔗 Sources

- [README.md](https://github.com/danielep71/K-IRRBB-NMDs/blob/973501c82f2f9011acfdc9d741ab2af0132cb96c/README.md) — content SHA-256 `f9d21461d714a5238736637e6e312d37e17c4e04889e7453525afde51f97a832`
- [docs/EXCEL_EVIDENCE.md](https://github.com/danielep71/K-IRRBB-NMDs/blob/973501c82f2f9011acfdc9d741ab2af0132cb96c/docs/EXCEL_EVIDENCE.md) — content SHA-256 `c4e538abb905a34ee27a98cf0ebcee9d6c4e3cb1d359191656499dcc8ff96620`
- No published stable release (drafts and prereleases excluded).

### 🏁 Milestones (tracking only)

- [v0.1.0 - Repository foundation](https://github.com/danielep71/K-IRRBB-NMDs/milestone/1): closed; 20 closed / 0 open issues.
- [v0.2.0 - Workbook, data and Excel tests](https://github.com/danielep71/K-IRRBB-NMDs/milestone/2): open; 10 closed / 4 open issues.
- [v0.3.0 - Decay model](https://github.com/danielep71/K-IRRBB-NMDs/milestone/3): open; 0 closed / 1 open issues.
- [v0.4.0 - Interest-rate model](https://github.com/danielep71/K-IRRBB-NMDs/milestone/4): open; 0 closed / 1 open issues.
- [v0.5.0 - Stable-amount model](https://github.com/danielep71/K-IRRBB-NMDs/milestone/5): open; 0 closed / 1 open issues.
- [v0.6.0 - Integrated calibration and backtesting](https://github.com/danielep71/K-IRRBB-NMDs/milestone/6): open; 0 closed / 1 open issues.
- [v0.7.0 - Scenarios and regulatory overlays](https://github.com/danielep71/K-IRRBB-NMDs/milestone/7): open; 0 closed / 2 open issues.
- [v0.8.0 - User workflow and ALM export](https://github.com/danielep71/K-IRRBB-NMDs/milestone/8): open; 0 closed / 0 open issues.
- [v0.9.0 - Release candidate](https://github.com/danielep71/K-IRRBB-NMDs/milestone/9): open; 0 closed / 0 open issues.
- [v1.0.0 - First validated NMD application](https://github.com/danielep71/K-IRRBB-NMDs/milestone/10): open; 0 closed / 0 open issues.

<a id="frtb"></a>
## 🧩 K-FRTB-SA

Version 0.2.0 is a prototype of the v0.2.0 — SA prototype milestone (issue #20). It implements the Basel standardized approach (MAR21-MAR23) in Excel VBA with parameters checked against the BIS text, and every output is reconciled with an independent Python reference. It has not yet been compiled or run in Excel, the engine platform decision is still open (scope), and no result is validated for regulatory use (validation).

### 🔗 Sources

- [README.md](https://github.com/danielep71/K-FRTB-SA/blob/0540f892614ac0479591c78b648e7f808ea4a8c0/README.md) — content SHA-256 `3acaa98e5c248cff49111ca8d7afeea2ddee8a4a006551eac58ce2884892a668`
- [docs/validation.md](https://github.com/danielep71/K-FRTB-SA/blob/0540f892614ac0479591c78b648e7f808ea4a8c0/docs/validation.md) — content SHA-256 `6126bf7dead97f18f2448510397fe421790253fa64535e58e6d2b59fcd622ed6`
- No published stable release (drafts and prereleases excluded).

### 🏁 Milestones (tracking only)

- [v0.1.0 — Repo setup](https://github.com/danielep71/K-FRTB-SA/milestone/1): closed; 10 closed / 0 open issues.
- [v0.2.0 — SA prototype](https://github.com/danielep71/K-FRTB-SA/milestone/2): open; 29 closed / 8 open issues.
- [v0.3.0 — Regulatory baseline and certification scope](https://github.com/danielep71/K-FRTB-SA/milestone/3): open; 6 closed / 1 open issues.

<a id="prepayment"></a>
## 🧩 K-IRRBB Prepayment Models

Current status: specifications only. Repository setup (v0.1.0) closed on 2026-10-21 with accepted data, model and validation contracts; prototype setup (v0.2.0) is the open milestone. No prepayment model, VBA engine, workbook, calibration routine or validated numerical output is delivered. These are development objectives, not implemented features.

### 🔗 Sources

- [README.md](https://github.com/danielep71/K-IRRBB-Prepayment_Models/blob/5cc8b146863f202ee38a7a3efb25d2d29d450b56/README.md) — content SHA-256 `cbf5e6e4599343f4d4b27ebab56d29b58e3c32b252226f2207219c2985b87a12`
- [docs/Milestones/v0.1.0.md](https://github.com/danielep71/K-IRRBB-Prepayment_Models/blob/5cc8b146863f202ee38a7a3efb25d2d29d450b56/docs/Milestones/v0.1.0.md) — content SHA-256 `0b459ecb6ea11faf76f692d2ac3ed01e11219ab892cee1d30b7c714621eae9de`
- No published stable release (drafts and prereleases excluded).

### 🏁 Milestones (tracking only)

- [v0.1.0 - Repo setup](https://github.com/danielep71/K-IRRBB-Prepayment_Models/milestone/1): closed; 22 closed / 0 open issues.
- [v0.2.0 - Prototype setup](https://github.com/danielep71/K-IRRBB-Prepayment_Models/milestone/2): open; 13 closed / 8 open issues.

<a id="sfts"></a>
## 🧩 K-SFTs

Status: working prototype, not a validated method. The repository holds a prototype that calculates E\*, RWA and own funds of SFT netting sets (PROTOTYPE.md). It runs in Excel and reproduces an independent reference, but it is not the methodology of record and departs from recorded decisions. Nothing here should be used to compute regulatory exposure. The regulatory basis is chosen: the EU CRR controls, with the Basel Framework as the methodological reference; products, collateral and outputs are still open decisions.

### 🔗 Sources

- [README.md](https://github.com/danielep71/K-SFTs/blob/ff18bc9ea6736fb7de6a8f16ffd32266b1975baa/README.md) — content SHA-256 `2a5803ac272002cd1b0ea9b896b373889b2778f9c103fdcabec289def3babfb0`
- [docs/methodology/README.md](https://github.com/danielep71/K-SFTs/blob/ff18bc9ea6736fb7de6a8f16ffd32266b1975baa/docs/methodology/README.md) — content SHA-256 `af72da1ace6034887fc8f3699dc18477dbdcd4fc845e92f72c6b8bde4332a77d`
- Published release: [v0.2.0](https://github.com/danielep71/K-SFTs/releases/tag/v0.2.0) (2026-10-30T15:40:16Z)

### 🏁 Milestones (tracking only)

- [v0.1.0 - Repo setup](https://github.com/danielep71/K-SFTs/milestone/1): closed; 32 closed / 0 open issues.
- [v0.2.0 - Prototype setup](https://github.com/danielep71/K-SFTs/milestone/2): closed; 29 closed / 0 open issues.
- v0.2.1: historical snapshot recorded open; 0 closed / 1 open issues. Milestone URL no longer available as of 2026-10-29.
- [v0.3.0 - Methodology and numerical assurance](https://github.com/danielep71/K-SFTs/milestone/4): open; 5 closed / 7 open issues.
- [v1.0.0 - First supported release](https://github.com/danielep71/K-SFTs/milestone/5): open; 0 closed / 6 open issues.

<a id="cva"></a>
## 🧩 K-CVA

Repository setup only. There is no calculation engine, public API, workbook or validated method yet. Nothing here should be used to compute capital. Repository CI checks infrastructure; it does not establish numerical correctness or regulatory compliance.

### 🔗 Sources

- [README.md](https://github.com/danielep71/K-CVA/blob/260fac21f23b3916d050fa7de5707f030f7c1cc8/README.md) — content SHA-256 `f35e2cc035a59ec769099383dd0e9a738b73d5a41bde5bde6bfb5b0a1f8a94fa`
- [docs/methodology/README.md](https://github.com/danielep71/K-CVA/blob/260fac21f23b3916d050fa7de5707f030f7c1cc8/docs/methodology/README.md) — content SHA-256 `318fd173082af0b4351d349e61d9d0e515cbd5f7ed576638989307cb0deec32f`
- No published stable release (drafts and prereleases excluded).

### 🏁 Milestones (tracking only)

- [v0.1.0 - Repo setup](https://github.com/danielep71/K-CVA/milestone/1): open; 27 closed / 4 open issues.
- [v0.2.0 - BA-CVA](https://github.com/danielep71/K-CVA/milestone/2): open; 0 closed / 1 open issues.

<a id="lcr"></a>
## 🧩 K-LCR

Repository setup. There is no LCR calculation engine, validated workbook, Excel import/compile run or supported host claim yet. Windows desktop Excel 64-bit is an engineering target, not a tested configuration. This project is intended for reference and independent validation, not operational reporting or production use.

### 🔗 Sources

- [README.md](https://github.com/danielep71/K-LCR/blob/05477725ecd6c8efe4adda77c3e13114a9c2e03d/README.md) — content SHA-256 `439a86a3426144bcde07fcc493ffe9d644df08db59f0eb883ea89a60a5791c65`
- [docs/DECISIONS.md](https://github.com/danielep71/K-LCR/blob/05477725ecd6c8efe4adda77c3e13114a9c2e03d/docs/DECISIONS.md) — content SHA-256 `98b2a89c3f387fcdf0758a67cfb507cc4ce29e24aea15f5de917780a7ac2dc05`
- No published stable release (drafts and prereleases excluded).

### 🏁 Milestones (tracking only)

- [v0.1.0 - Repo setup](https://github.com/danielep71/K-LCR/milestone/1): open; 49 closed / 18 open issues.
