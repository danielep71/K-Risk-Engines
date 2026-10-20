# K-Risk Engines

**Transparent methods. Traceable results.**

A single entry point to independent financial risk models and calculation engines for benchmarking, model challenge, audit, advisory and education.

![K-Risk Engines portfolio](assets/K-Risk-Engines-social-preview.png)

## Explore the portfolio

| Project | Purpose | Status at 20 October 2026 |
| --- | --- | --- |
| [K-SACCR](https://github.com/danielep71/VBA-SACCR-Toolkit) | SA-CCR calculation and reconciliation | Released workbook; see project-specific validation limits |
| [K-IRRBB](https://github.com/danielep71/K-IRRBB_Behavioral_Models) | Non-maturity deposit behavioural modelling | In development; draft decay model |
| [K-FRTB-SA](https://github.com/danielep71/MKT-FTRB-SA) | Standardized market-risk aggregation | Prototype; Excel execution evidence pending |
| Prepayment models | Behavioural loan prepayment modelling | Planned; no implementation available |

Each repository owns its implementation, methodology, tests, issues and releases. Consult it for current scope, evidence and licensing. This hub contains presentation and portfolio documentation, not calculation code.

## Website

The static landing page is `index.html`; images and styles live in [`assets/`](assets/). No build or external dependencies are required.

For GitHub Pages, select **Settings → Pages → Deploy from a branch → main → / (root)**. The intended URL is `https://danielep71.github.io/K-Risk-Engines/`.

## Website checks

Run `python3 .github/scripts/check-website.py` from the repository root.
Add `--external` to check external URLs with curl.

The dependency-free check covers explicit HTML tag nesting, document title,
language and doctype, duplicate IDs, image alt attributes, local assets,
CSS `url()` references and internal anchors. It is a focused structural
check, not a full HTML standards or accessibility validator.

GitHub Actions runs local checks on every pull request to `main` and push
to `main`. External links are checked on pushes, weekly and on manual runs;
redirects are accepted. Broken links fail the check. Network errors, HTTP
403/429 and server errors are reported as warnings because availability
could not be verified. External page fragments are not validated.

## Review approach

1. Align data, scope, conventions and assumptions.
2. Compare intermediate calculations and investigate differences.
3. Record versions, reference results, explanations and unresolved limitations.

Agreement with a benchmark supports a review; it does not by itself establish model validity or regulatory compliance.

## Portfolio direction

Develop the existing projects on their own validation evidence, define a separate prepayment project, and maintain consistent presentation and documentation across the collection. Detailed milestones remain in each model repository.

An independent project by [Daniele Penza](https://github.com/danielep71). Not an official product of, or endorsed by, KPMG. Individual project licences apply to their respective contents.
