# 📊 Portfolio status evidence

[![portfolio refresh](https://img.shields.io/github/actions/workflow/status/danielep71/K-Risk-Engines/portfolio-refresh.yml?branch=main&style=flat-square&label=portfolio%20refresh)](https://github.com/danielep71/K-Risk-Engines/actions/workflows/portfolio-refresh.yml)

Proposed automatically from public project sources; reviewed on merge. Release availability and milestone progress do not establish model validity. This is a snapshot, not a live dashboard; follow the pinned source links for the captured revision and the project repository for newer evidence. Status paragraphs quote the source project: paths, issue numbers and references to “this repository” belong to that engine, not K-Risk-Engines. Presentation changes belong in the portfolio-refresh renderer; do not edit generated quotations or counts by hand.

<a id="saccr"></a>
## 🧩 K-SACCR

Version 1.2.0 is the current release: the 1.2.0 GitHub Release carries the workbook and the user manual. The engine implements EU CRR and Basel CRE52, but only Basel rules are validated in v1.2.0, by the published CRE99 examples. CRR rules are implemented and tested against illustrative values, not validated (methodology). Since then, on the active release branch, the CRR calculation has been validated against a bank&#x27;s production SA-CCR engine on a real portfolio (#667): see Validation.

### 🔗 Sources

- [README.md](https://github.com/danielep71/K-SACCR/blob/d706d175a84abadab99eebd027012c0b5676472b/README.md) — content SHA-256 `03017b9f9f7fc78cbb1ce866259c46cf4e5cbbeffd3e08fae5d79fdbb646db9a`
- [docs/methodology/README.md](https://github.com/danielep71/K-SACCR/blob/d706d175a84abadab99eebd027012c0b5676472b/docs/methodology/README.md) — content SHA-256 `69d39f0da6d243fc3aa516ca762c6fc5eac97ffb2918d9f2f7ff76e45e83b95f`
- Published release: [v1.2.0](https://github.com/danielep71/K-SACCR/releases/tag/v1.2.0) (2026-11-07T09:46:22Z)

### 🏁 Milestones (tracking only)

- [v0.0.1 - Repo setup](https://github.com/danielep71/K-SACCR/milestone/1): closed; 12 closed / 0 open issues.
- [v1.0.0 - First Supported Excel Release](https://github.com/danielep71/K-SACCR/milestone/2): closed; 51 closed / 0 open issues.
- [v1.1.0 - CSV Import, Staging and Workbook Protection](https://github.com/danielep71/K-SACCR/milestone/3): closed; 32 closed / 0 open issues.
- [v1.2.0 - Excel Ribbon Interface](https://github.com/danielep71/K-SACCR/milestone/4): closed; 14 closed / 0 open issues.
- [v1.3.0 - Diagnostics and Independent Validation](https://github.com/danielep71/K-SACCR/milestone/5): open; 17 closed / 10 open issues.
- [v1.4.0 - Advanced Products and FX Provenance](https://github.com/danielep71/K-SACCR/milestone/6): open; 0 closed / 3 open issues.
- [v1.5.0 - Simplified SA-CCR](https://github.com/danielep71/K-SACCR/milestone/7): open; 0 closed / 0 open issues.
- [v1.6.0 - Original Exposure Method](https://github.com/danielep71/K-SACCR/milestone/8): open; 0 closed / 0 open issues.
- v1.8.0 - Securities Financing Transactions: historical snapshot recorded open; 0 closed / 1 open issues. Milestone URL no longer available as of 2026-10-27.
- v1.9.0 - Regulatory CVA Risk: historical snapshot recorded open; 0 closed / 1 open issues. Milestone URL no longer available as of 2026-10-27.
- v1.10.0 - Risk-Weighted Assets and Capital: historical snapshot recorded open; 0 closed / 2 open issues. Milestone URL no longer available as of 2026-10-27.
- [v1.0.1 - Post release hardening](https://github.com/danielep71/K-SACCR/milestone/13): closed; 9 closed / 0 open issues.
- [v1.0.2 - Clearing Coverage and CCP Completeness](https://github.com/danielep71/K-SACCR/milestone/14): closed; 10 closed / 0 open issues.
- [v1.7.0 - Standalone Python Engine and VBA/Python Reconciliation](https://github.com/danielep71/K-SACCR/milestone/15): open; 0 closed / 10 open issues.
- [v1.3.5 - COREP Templates](https://github.com/danielep71/K-SACCR/milestone/16): open; 0 closed / 1 open issues.
- [v1.3.1 - Dashboard and reporting](https://github.com/danielep71/K-SACCR/milestone/17): open; 0 closed / 0 open issues.

<a id="nmd"></a>
## 🧩 K-IRRBB NMDs

v0.2.0 - Workbook, data and Excel tests (in progress). The v0.1.0 foundation, closed on 2026-10-09, established source layout, documentation, issue governance, CI and static source checks; v0.2.0 builds the first workbook, data import and Excel test harness. Neither delivers pricing, econometric fitting, a production workbook or certified IRRBB outputs. - Decay model (draft, not validated, milestone v0.3.0): core, public facade IRRBB_Decay, harness cases and example, reviewed on release/v0.3.0 and present here since this branch was levelled with main; built to MODEL_CONTRACTS.md and under review in #36; no Excel evidence is recorded yet. Rate and stable-amount models are not built. - Application profile: an Excel workbook will be the end-user deliverable, assembled from reviewed exported VBA source. - Production calculations live in src/core/ without direct Excel object dependencies; at present the data import&#x27;s parsing, validation, summaries and fingerprint, and the draft decay calculations. - src/modules/ exposes the documented public facade (the data import and the draft decay model, listed in docs/PUBLIC_API.txt); src/workbook/ contains host glue only. - tests/ holds synthetic fixtures, expected results and the VBA regression harness; evidence from a real Excel run must be separately recorded. - No client data, confidential third-party material, vendor source code or customer-specific models are allowed in Git; the repository and its history are public.

### 🔗 Sources

- [README.md](https://github.com/danielep71/K-IRRBB-NMDs/blob/626836d947234b2e7cdd25bd941c2aaa843a6fcc/README.md) — content SHA-256 `5a819702e4a71e7dbab522621ee5776fef5d86bd4bde26aaa1b050979d3ccd69`
- [docs/EXCEL_EVIDENCE.md](https://github.com/danielep71/K-IRRBB-NMDs/blob/626836d947234b2e7cdd25bd941c2aaa843a6fcc/docs/EXCEL_EVIDENCE.md) — content SHA-256 `c4e538abb905a34ee27a98cf0ebcee9d6c4e3cb1d359191656499dcc8ff96620`
- No published stable release (drafts and prereleases excluded).

### 🏁 Milestones (tracking only)

- [v0.1.0 - Repository foundation](https://github.com/danielep71/K-IRRBB-NMDs/milestone/1): closed; 13 closed / 0 open issues.
- [v0.2.0 - Workbook, data and Excel tests](https://github.com/danielep71/K-IRRBB-NMDs/milestone/2): open; 54 closed / 6 open issues.
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

- [README.md](https://github.com/danielep71/K-FRTB-SA/blob/3999cbe0b52b506749834e72a10f3f466035143c/README.md) — content SHA-256 `6621862733399cb176c584f2cb1370034fdbea27daa27c0edde4bc67ab104765`
- [docs/validation.md](https://github.com/danielep71/K-FRTB-SA/blob/3999cbe0b52b506749834e72a10f3f466035143c/docs/validation.md) — content SHA-256 `593f2af7d6f028f1769c0952daf26830b71a8792899fc24d65f07769190c3907`
- No published stable release (drafts and prereleases excluded).

### 🏁 Milestones (tracking only)

- [v0.1.0 — Repo setup](https://github.com/danielep71/K-FRTB-SA/milestone/1): closed; 10 closed / 0 open issues.
- [v0.2.0 — SA prototype](https://github.com/danielep71/K-FRTB-SA/milestone/2): open; 59 closed / 5 open issues.
- [v0.3.0 — Regulatory baseline and certification scope](https://github.com/danielep71/K-FRTB-SA/milestone/3): open; 10 closed / 0 open issues.

<a id="prepayment"></a>
## 🧩 K-IRRBB Prepayment Models

Current status: prototype development. Repository setup (v0.1.0) closed on 2026-10-21; prototype setup (v0.2.0) is open. Committed source includes workbook build/export tooling, SMM/CPR conversions, a VBA importer with its facade and workbook adapter, and a 16-case VBA harness. All twelve DATA cases have independent Python references that run offline. No Windows Excel build, compilation or execution is established; calibration, projections, EVE and gap calculations remain unimplemented. No workbook or validated model output has been released.

### 🔗 Sources

- [README.md](https://github.com/danielep71/K-IRRBB-Prepayment_Models/blob/efffd119102c4a282b690052022f1365d291f5a8/README.md) — content SHA-256 `61e66f846a4fd34634752ce3fa031379387d2b57b9fda957c4f78a0dbc5cc5c7`
- [docs/Milestones/v0.1.0.md](https://github.com/danielep71/K-IRRBB-Prepayment_Models/blob/efffd119102c4a282b690052022f1365d291f5a8/docs/Milestones/v0.1.0.md) — content SHA-256 `0b459ecb6ea11faf76f692d2ac3ed01e11219ab892cee1d30b7c714621eae9de`
- No published stable release (drafts and prereleases excluded).

### 🏁 Milestones (tracking only)

- [v0.1.0 - Repo setup](https://github.com/danielep71/K-IRRBB-Prepayment_Models/milestone/1): closed; 17 closed / 0 open issues.
- [v0.2.0 - Prototype setup](https://github.com/danielep71/K-IRRBB-Prepayment_Models/milestone/2): open; 29 closed / 7 open issues.

<a id="sfts"></a>
## 🧩 K-SFTs

Status: working prototype, not a validated method. The repository holds a prototype that calculates E\*, RWA and own funds of SFT netting sets (PROTOTYPE.md). It runs in Excel and reproduces an independent reference, but it is not the methodology of record and departs from recorded decisions. Nothing here should be used to compute regulatory exposure. The regulatory basis is chosen: the EU CRR controls, with the Basel Framework as the methodological reference; products, collateral and outputs are still open decisions.

### 🔗 Sources

- [README.md](https://github.com/danielep71/K-SFTs/blob/4427adaccdc4ec7df2e67b4394965998488a947e/README.md) — content SHA-256 `81f41bf5398b8442977cbed485017f0a22008626959ea0f332c00a5bc4ebc0ea`
- [docs/methodology/README.md](https://github.com/danielep71/K-SFTs/blob/4427adaccdc4ec7df2e67b4394965998488a947e/docs/methodology/README.md) — content SHA-256 `da10ea0b2ba72d4943ad94a6a680dc606c12ff85835380ba0a2a100ec6e8e1df`
- Published release: [v0.2.0](https://github.com/danielep71/K-SFTs/releases/tag/v0.2.0) (2026-10-30T15:40:16Z)

### 🏁 Milestones (tracking only)

- [v0.1.0 - Repo setup](https://github.com/danielep71/K-SFTs/milestone/1): closed; 32 closed / 0 open issues.
- [v0.2.0 - Prototype setup](https://github.com/danielep71/K-SFTs/milestone/2): closed; 29 closed / 0 open issues.
- v0.2.1: historical snapshot recorded open; 0 closed / 1 open issues. Milestone URL no longer available as of 2026-10-29.
- [v0.3.0 - Methodology and numerical assurance](https://github.com/danielep71/K-SFTs/milestone/4): open; 7 closed / 6 open issues.
- [v1.0.0 - First supported release](https://github.com/danielep71/K-SFTs/milestone/5): open; 0 closed / 6 open issues.

<a id="cva"></a>
## 🧩 K-CVA

Repository setup only. There is no calculation engine, public API, workbook or validated method yet. Nothing here should be used to compute capital. Repository CI checks infrastructure; it does not establish numerical correctness or regulatory compliance.

### 🔗 Sources

- [README.md](https://github.com/danielep71/K-CVA/blob/92d0e983357fe7a5696050ed7fec4dbe4ff91072/README.md) — content SHA-256 `d9c227b8c7ef1f04cf5cf62ab0a7e2c8095ca46a48529ba60664d4d11876dd21`
- [docs/methodology/README.md](https://github.com/danielep71/K-CVA/blob/92d0e983357fe7a5696050ed7fec4dbe4ff91072/docs/methodology/README.md) — content SHA-256 `edb95552337b7ac614297b25ac4cf2a3597fb6e30dce700adf8afb7a69830cb7`
- No published stable release (drafts and prereleases excluded).

### 🏁 Milestones (tracking only)

- [v0.1.0 - Repo setup](https://github.com/danielep71/K-CVA/milestone/1): closed; 43 closed / 0 open issues.
- [v0.2.0 - Prototype setup](https://github.com/danielep71/K-CVA/milestone/2): open; 0 closed / 6 open issues.

<a id="lcr"></a>
## 🧩 K-LCR

Repository setup. There is no LCR calculation engine, validated workbook, Excel import/compile run or supported host claim yet. Windows desktop Excel 64-bit is an engineering target, not a tested configuration. This project is intended for reference and independent validation, not operational reporting or production use.

### 🔗 Sources

- [README.md](https://github.com/danielep71/K-LCR/blob/7b343cc5c6f91423802c0cc56bfe4d9b50d102a5/README.md) — content SHA-256 `0faee6378d3ad8502af50d5e4f69bbb38ab35afda51971c0022e50cc4076d216`
- [docs/DECISIONS.md](https://github.com/danielep71/K-LCR/blob/7b343cc5c6f91423802c0cc56bfe4d9b50d102a5/docs/DECISIONS.md) — content SHA-256 `a56d3bc8ba7d51b331aa6d9056a170d387ebad1a3c87d431972c383755813ea0`
- No published stable release (drafts and prereleases excluded).

### 🏁 Milestones (tracking only)

- [v0.1.0 - Repo setup](https://github.com/danielep71/K-LCR/milestone/1): open; 59 closed / 0 open issues.
- [v0.2.0 - Host execution](https://github.com/danielep71/K-LCR/milestone/2): open; 0 closed / 5 open issues.

<a id="nsfr"></a>
## 🧩 K-NSFR

Repository setup (v0.1.0). No admitted NSFR calculation engine, workbook or validated regulatory profile exists yet; the benchmark prototype is stored but not admitted. Do not use this baseline for regulatory reporting, production decisions or a claim of compliance.

### 🔗 Sources

- [README.md](https://github.com/danielep71/K-NSFR/blob/3dca8965cce5ee3e03baf74fbf53d6ba0bd3fd26/README.md) — content SHA-256 `f57100299c5a21fac61eb00388d13376e5f6d0b9db667780452998ba91e83d59`
- [docs/DECISIONS.md](https://github.com/danielep71/K-NSFR/blob/3dca8965cce5ee3e03baf74fbf53d6ba0bd3fd26/docs/DECISIONS.md) — content SHA-256 `2d95280283349169157a7440eb80e2ec5f5147018b20d98acb6e834f5ab02c38`
- No published stable release (drafts and prereleases excluded).

### 🏁 Milestones (tracking only)

- [v0.1.0 - Repo setup](https://github.com/danielep71/K-NSFR/milestone/1): closed; 63 closed / 0 open issues.
- [v0.2.0 - Prototype Setup](https://github.com/danielep71/K-NSFR/milestone/2): open; 4 closed / 8 open issues.
