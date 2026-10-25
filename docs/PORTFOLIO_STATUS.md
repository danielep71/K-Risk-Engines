# 📊 Portfolio status evidence

[![portfolio refresh](https://img.shields.io/github/actions/workflow/status/danielep71/K-Risk-Engines/portfolio-refresh.yml?branch=main&style=flat-square&label=portfolio%20refresh)](https://github.com/danielep71/K-Risk-Engines/actions/workflows/portfolio-refresh.yml)

Proposed automatically from public project sources; reviewed on merge. Release availability and milestone progress do not establish model validity. This is a snapshot, not a live dashboard; follow the pinned source links for the captured revision and the project repository for newer evidence. Status paragraphs quote the source project: paths, issue numbers and references to “this repository” belong to that engine, not K-Risk-Engines. Presentation changes belong in the portfolio-refresh renderer; do not edit generated quotations or counts by hand.

<a id="saccr"></a>
## 🧩 K-SACCR

Version 1.0.2 is the current release: the 1.0.2 GitHub Release carries the workbook and the user manual. The engine implements EU CRR and Basel CRE52, but only Basel rules are validated in v1.0.2, by the published CRE99 examples. CRR rules are implemented and tested against illustrative values, not validated (methodology).

### 🔗 Sources

- [README.md](https://github.com/danielep71/VBA-SACCR-Toolkit/blob/00bb72d1bf5ec9252b8ca5ba3adc567d948be15d/README.md) — content SHA-256 `5e2778a87cad44a4ab24bde62003011c5ac95c397958b43257c173891a5da21d`
- [docs/methodology/README.md](https://github.com/danielep71/VBA-SACCR-Toolkit/blob/00bb72d1bf5ec9252b8ca5ba3adc567d948be15d/docs/methodology/README.md) — content SHA-256 `66818374518624eed01db9112c15b45f69c967b00115b26f124f6c64d24521ab`
- Published release: [v1.0.2](https://github.com/danielep71/VBA-SACCR-Toolkit/releases/tag/v1.0.2) (2026-10-22T21:46:09Z)

### 🏁 Milestones (tracking only)

- [v0.0.1 - Repo setup](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/1): closed; 26 closed / 0 open issues.
- [v1.0.0 - First Supported Excel Release](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/2): closed; 57 closed / 0 open issues.
- [v1.1.0 - CSV Import, Staging and Workbook Protection](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/3): open; 11 closed / 11 open issues.
- [v1.2.0 - Excel Ribbon Interface](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/4): open; 0 closed / 9 open issues.
- [v1.3.0 - Diagnostics and Independent Validation](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/5): open; 0 closed / 6 open issues.
- [v1.4.0 - Advanced Products and FX Provenance](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/6): open; 0 closed / 3 open issues.
- [v1.5.0 - Simplified SA-CCR](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/7): open; 0 closed / 0 open issues.
- [v1.6.0 - Original Exposure Method](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/8): open; 0 closed / 0 open issues.
- [v1.8.0 - Securities Financing Transactions](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/10): open; 0 closed / 1 open issues.
- [v1.9.0 - Regulatory CVA Risk](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/11): open; 0 closed / 1 open issues.
- [v1.10.0 - Risk-Weighted Assets and Capital](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/12): open; 0 closed / 2 open issues.
- [v1.0.1 - Post release hardening](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/13): closed; 9 closed / 0 open issues.
- [v1.0.2 - Clearing Coverage and CCP Completeness](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/14): closed; 9 closed / 0 open issues.
- [v1.7.0 - Standalone Python Engine and VBA/Python Reconciliation](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/15): open; 0 closed / 10 open issues.

<a id="nmd"></a>
## 🧩 K-IRRBB

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

Version 0.1.0 is a prototype of the v0.1.0 — SA prototype milestone (issue #20). It implements the Basel standardized approach (MAR21-MAR23) in Excel VBA with parameters checked against the BIS text, and every output is reconciled with an independent Python reference. It has not yet been compiled or run in Excel, the engine platform decision is still open (scope), and no result is validated for regulatory use (validation).

### 🔗 Sources

- [README.md](https://github.com/danielep71/MKT-FTRB-SA/blob/4eefd3f69fcd16dd395861e520aeb8feb5adfbd3/README.md) — content SHA-256 `d2d19957af77132a62a616bcf170e0eeb135adc81660aa8811d44694af5e98be`
- [docs/validation.md](https://github.com/danielep71/MKT-FTRB-SA/blob/4eefd3f69fcd16dd395861e520aeb8feb5adfbd3/docs/validation.md) — content SHA-256 `6126bf7dead97f18f2448510397fe421790253fa64535e58e6d2b59fcd622ed6`
- No published stable release (drafts and prereleases excluded).

### 🏁 Milestones (tracking only)

- [v0.0.1 — Repo setup](https://github.com/danielep71/MKT-FTRB-SA/milestone/1): closed; 32 closed / 0 open issues.
- [v0.1.0 — SA prototype](https://github.com/danielep71/MKT-FTRB-SA/milestone/2): open; 49 closed / 9 open issues.
- [v0.2.0 — Regulatory baseline and certification scope](https://github.com/danielep71/MKT-FTRB-SA/milestone/3): open; 0 closed / 1 open issues.

<a id="prepayment"></a>
## 🧩 K-IRRBB Prepayment Models

Current status: specifications only. Repository setup (v0.1.0) closed on 2026-10-21 with accepted data, model and validation contracts; prototype setup (v0.2.0) is the open milestone. No prepayment model, VBA engine, workbook, calibration routine or validated numerical output is delivered. These are development objectives, not implemented features.

### 🔗 Sources

- [README.md](https://github.com/danielep71/K-IRRBB-Prepayment_Models/blob/590250e6f9cb6071a44828179d8fcbab56ad5277/README.md) — content SHA-256 `d9a8ea46b5d2f987697dba000995b62aed3ab26286781acd2f09824f47bce78f`
- [docs/Milestones/v0.1.0.md](https://github.com/danielep71/K-IRRBB-Prepayment_Models/blob/590250e6f9cb6071a44828179d8fcbab56ad5277/docs/Milestones/v0.1.0.md) — content SHA-256 `0b459ecb6ea11faf76f692d2ac3ed01e11219ab892cee1d30b7c714621eae9de`
- No published stable release (drafts and prereleases excluded).

### 🏁 Milestones (tracking only)

- [v0.1.0 - Repo setup](https://github.com/danielep71/K-IRRBB-Prepayment_Models/milestone/1): closed; 22 closed / 0 open issues.
- [v0.2.0 - Prototype setup](https://github.com/danielep71/K-IRRBB-Prepayment_Models/milestone/2): open; 9 closed / 10 open issues.

<a id="sfts"></a>
## 🧩 K-SFTs

Status: repository setup only. There is no calculation engine, public API, production workbook or validated method yet. Nothing here should be used to compute exposure. The regulatory basis is chosen: the EU CRR controls, with the Basel Framework as the methodological reference. The first scope is bilateral SFTs under the Financial Collateral Comprehensive Method; products, collateral and outputs are still open decisions.

### 🔗 Sources

- [README.md](https://github.com/danielep71/K-SFTs/blob/3fc2c977039e1a07f45abf8d0942c02f14b858e2/README.md) — content SHA-256 `c1ddc82b7b897917048ffc214f490c2bee647aec42b34146f5f328afb8e7f34e`
- [docs/methodology/README.md](https://github.com/danielep71/K-SFTs/blob/3fc2c977039e1a07f45abf8d0942c02f14b858e2/docs/methodology/README.md) — content SHA-256 `0aaf917e00377e03d6d079f909b183a972f2c1f872c20f6801bbdb7bfc5ddfb5`
- No published stable release (drafts and prereleases excluded).

### 🏁 Milestones (tracking only)

- [v0.1.0 - Repo setup](https://github.com/danielep71/K-SFTs/milestone/1): open; 31 closed / 1 open issues.
