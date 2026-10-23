# 🔐 K-Risk-Engines security policy

[![Reporting](https://img.shields.io/badge/Reporting-private_GitHub_form-B60205?style=flat-square)](#report-a-vulnerability-privately)
[![Supported](https://img.shields.io/badge/Supported-main-2ea44f?style=flat-square)](https://github.com/danielep71/K-Risk-Engines/tree/main)
[![Response](https://img.shields.io/badge/Response-best_effort-6E7781?style=flat-square)](#handling-reports)

<a id="scope-and-supported-version"></a>

## 🎯 Scope and supported version

This repository is a portfolio and documentation hub. This policy covers its
website source and assets, repository tooling, and GitHub Actions workflows.
The supported version is the current `main` branch and the website deployed
from it; older snapshots and modified copies are not maintained separately.
Implement fixes through the active maintenance branch and integrate them into
`main` under [GOVERNANCE.md](GOVERNANCE.md). Coordinate disclosure privately
before opening a public remediation PR.

Each linked risk engine is maintained in its own repository. Report vulnerabilities
in an engine through that repository's security policy. Ordinary calculation
defects without security impact belong in the engine's issue tracker; broken
links and other non-security hub defects belong in this repository's issues.

<a id="report-a-vulnerability-privately"></a>

## 📨 Report a vulnerability privately

Do not disclose suspected vulnerabilities in public issues, pull requests,
commit messages, or screenshots.

Use GitHub's [private vulnerability reporting form](https://github.com/danielep71/K-Risk-Engines/security/advisories/new)
(**Security → Report a vulnerability**) as the primary route.
If you cannot use the form, email **danielep71@gmail.com** with the subject
**Private security report — K-Risk-Engines**.

Include:

- the affected URL, file or workflow and, where possible, the full commit SHA;
- the potential security impact and minimal reproduction steps;
- any tested workaround.

Use synthetic examples. Do not send credentials, tokens, personal information,
or confidential client or portfolio data. Revoke or rotate any exposed secret
immediately before reporting the incident.

<a id="handling-reports"></a>

## 🧭 Handling reports

Reports are handled on a best-effort basis by the maintainer. Remediation and
public disclosure timing will be coordinated with the reporter according to
severity; no guaranteed response time or bug bounty is offered.

This policy does not authorize testing GitHub infrastructure, linked websites,
or other third-party systems. Report vulnerabilities in those services through
their own security channels.
