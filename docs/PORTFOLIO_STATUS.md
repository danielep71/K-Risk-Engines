# Portfolio status evidence

Proposed automatically from public project sources; reviewed on merge. Release availability and milestone progress do not establish model validity.

<a id="saccr"></a>
## K-SACCR

Version 1.0.1 is the current release: the 1.0.1 GitHub Release carries the workbook and the user manual. The engine implements EU CRR and Basel CRE52, but only Basel rules are validated in v1.0.1, by the published CRE99 examples. CRR rules are implemented and tested against illustrative values, not validated (methodology).

### Sources

- [README.md](https://github.com/danielep71/VBA-SACCR-Toolkit/blob/7ad778c54cc917396b7e690eaf7ddfefb6a56009/README.md) — content SHA-256 `e130302a53359d97ccc9e9ce0376e4887da16507b0326b68c30f59a72680aee9`
- [docs/methodology/README.md](https://github.com/danielep71/VBA-SACCR-Toolkit/blob/7ad778c54cc917396b7e690eaf7ddfefb6a56009/docs/methodology/README.md) — content SHA-256 `2805f4187aa4562250f73f231c81e64bb7ca9bf649e8f2568032fa3e91a8e39f`
- Published release: [v1.0.1](https://github.com/danielep71/VBA-SACCR-Toolkit/releases/tag/v1.0.1) (2026-10-18T16:51:06Z)

### Milestones (tracking only)

- [v0.0.1 - Repo setup](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/1): closed; 26 closed / 0 open issues.
- [v1.0.0 - First Supported Excel Release](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/2): closed; 57 closed / 0 open issues.
- [v1.1.0 - CSV Import and Staging](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/3): open; 0 closed / 9 open issues.
- [v1.2.0 - Excel Ribbon Interface](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/4): open; 0 closed / 9 open issues.
- [v1.3.0 - Diagnostics and Independent Validation](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/5): open; 0 closed / 6 open issues.
- [v1.4.0 - Advanced Products and FX Provenance](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/6): open; 0 closed / 3 open issues.
- [v1.5.0 - Simplified SA-CCR](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/7): open; 0 closed / 0 open issues.
- [v1.6.0 - Original Exposure Method](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/8): open; 0 closed / 0 open issues.
- [v1.8.0 - Securities Financing Transactions](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/10): open; 0 closed / 1 open issues.
- [v1.9.0 - Regulatory CVA Risk](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/11): open; 0 closed / 1 open issues.
- [v1.10.0 - Risk-Weighted Assets and Capital](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/12): open; 0 closed / 1 open issues.
- [v1.0.1 - Post release hardening](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/13): closed; 9 closed / 0 open issues.
- [v1.0.2 - Clearing Coverage and CCP Completeness](https://github.com/danielep71/VBA-SACCR-Toolkit/milestone/14): open; 2 closed / 6 open issues.

<a id="nmd"></a>
## K-IRRBB

v0.2.0 – Workbook, data and Excel tests (in progress). The v0.1.0 foundation, closed on 2026-10-09, established source layout, documentation, issue governance, CI and static source checks; v0.2.0 builds the first workbook, data import and Excel test harness. Neither delivers pricing, econometric fitting, a production workbook or certified IRRBB outputs. - Decay model (draft, not validated, milestone v0.3.0): core, public facade IRRBB_Decay, harness cases and example, reviewed on release/v0.3.0 and present here since this branch was levelled with main; built to MODEL_CONTRACTS.md and under review in #36; no Excel evidence is recorded yet. Rate and stable-amount models are not built. - Application profile: an Excel workbook will be the end-user deliverable, assembled from reviewed exported VBA source. - Production calculations live in src/core/ without direct Excel object dependencies; at present the data import&#x27;s parsing, validation, summaries and fingerprint, and the draft decay calculations. - src/modules/ exposes the documented public facade (the data import and the draft decay model, listed in docs/PUBLIC_API.txt); src/workbook/ contains host glue only. - tests/ holds synthetic fixtures, expected results and the VBA regression harness; evidence from a real Excel run must be separately recorded. - No client data, confidential third-party material, vendor source code or customer-specific models are allowed in Git; the repository and its history are public.

### Sources

- [README.md](https://github.com/danielep71/K-IRRBB-NMDs/blob/973501c82f2f9011acfdc9d741ab2af0132cb96c/README.md) — content SHA-256 `f9d21461d714a5238736637e6e312d37e17c4e04889e7453525afde51f97a832`
- [docs/EXCEL_EVIDENCE.md](https://github.com/danielep71/K-IRRBB-NMDs/blob/973501c82f2f9011acfdc9d741ab2af0132cb96c/docs/EXCEL_EVIDENCE.md) — content SHA-256 `c4e538abb905a34ee27a98cf0ebcee9d6c4e3cb1d359191656499dcc8ff96620`
- No published stable release (drafts and prereleases excluded).

### Milestones (tracking only)

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
## K-FRTB-SA

Version 0.1.0 is a prototype of the v0.1.0 — SA prototype milestone (issue #20). It implements the Basel standardized approach (MAR21-MAR23) in Excel VBA with parameters checked against the BIS text, and every output is reconciled with an independent Python reference. It has not yet been compiled or run in Excel, the engine platform decision is still open (scope), and no result is validated for regulatory use (validation).

### Sources

- [README.md](https://github.com/danielep71/MKT-FTRB-SA/blob/00cbe7a9206e38bd7d8a8f5c02190ce3a94f56e9/README.md) — content SHA-256 `d2d19957af77132a62a616bcf170e0eeb135adc81660aa8811d44694af5e98be`
- [docs/validation.md](https://github.com/danielep71/MKT-FTRB-SA/blob/00cbe7a9206e38bd7d8a8f5c02190ce3a94f56e9/docs/validation.md) — content SHA-256 `6126bf7dead97f18f2448510397fe421790253fa64535e58e6d2b59fcd622ed6`
- No published stable release (drafts and prereleases excluded).

### Milestones (tracking only)

- [v0.0.1 — Repo setup](https://github.com/danielep71/MKT-FTRB-SA/milestone/1): closed; 32 closed / 0 open issues.
- [v0.1.0 — SA prototype](https://github.com/danielep71/MKT-FTRB-SA/milestone/2): open; 45 closed / 8 open issues.
- [v0.2.0 — Regulatory baseline and certification scope](https://github.com/danielep71/MKT-FTRB-SA/milestone/3): open; 0 closed / 1 open issues.

<a id="prepayment"></a>
## K-IRRBB Prepayment Models

Current status: repository setup only. No prepayment model, VBA engine, workbook, calibration routine or validated numerical output is delivered. These are development objectives, not implemented features.

### Sources

- [README.md](https://github.com/danielep71/K-IRRBB-Prepayment_Models/blob/3461d891a4e076932c4c21ef30f569d62eafab3e/README.md) — content SHA-256 `996529f3e17f7b02faa4260331b1daf4c78c080d0e7fe828ff35cdd63145ef34`
- [docs/Milestones/v0.1.0.md](https://github.com/danielep71/K-IRRBB-Prepayment_Models/blob/3461d891a4e076932c4c21ef30f569d62eafab3e/docs/Milestones/v0.1.0.md) — content SHA-256 `827dec514b038db611335288c16afbe968654ac18f5061f5a887a51808bd737e`
- No published stable release (drafts and prereleases excluded).

### Milestones (tracking only)

- [v0.1.0 - Repo setup](https://github.com/danielep71/K-IRRBB-Prepayment_Models/milestone/1): open; 16 closed / 4 open issues.
