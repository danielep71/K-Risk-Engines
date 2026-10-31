# ⚙️ Repository settings · Non-default configuration

[![Scope](https://img.shields.io/badge/Scope-Non--default_settings-00338D?style=flat-square)](#scope)
[![Format](https://img.shields.io/badge/Format-Portable-005EB8?style=flat-square)](#reuse)
[![Comparison](https://img.shields.io/badge/Comparison-Documented_defaults-483698?style=flat-square)](#sources)

**Only deliberate differences · No repository identifiers · Reusable configuration**

<a id="scope"></a>

## 🧭 Comparison basis

This document records only settings that differ from the comparison baseline:
a new standalone GitHub.com repository, without inherited organization rules,
an applied security configuration or copied template customizations. General
options use GitHub's documented REST parameter defaults; those defaults are
not a guarantee of every account's repository-creation UI behavior.

Custom active rulesets are compared with an otherwise unprotected repository,
not with individual checkboxes preselected inside the ruleset editor. In
particular, deletion protection may be preselected when creating a ruleset;
creating and activating that targeted ruleset is still a customization.

Reference documentation checked: **2026-10-29**. GitHub's live settings remain
authoritative. Copying this file does not apply settings or verify another
repository. [GOVERNANCE.md](../GOVERNANCE.md) describes how contributors work
within these settings.

[General differences](#general) · [Security features](#security) · [Custom protection](#rulesets) · [Reuse](#reuse) · [Sources](#sources)

<a id="general"></a>

## 🏷️ General settings — changed values only

| Setting | Documented baseline | Configured value | Effect / qualification |
| --- | --- | --- | --- |
| Allow rebase merging | On (`allow_rebase_merge: true`) | **Off** | Pull requests merge with squash or merge commits only; branch rulesets narrow this further. |
| Automatically delete merged head branches | Off (`delete_branch_on_merge: false`) | **On** | Cleans up task branches and the bot proposal branch after merge; protected retained branches remain subject to their deletion rules. |
| Always suggest updating PR branches | Off (`allow_update_branch: false`) | **On** | Offers updates for the strict up-to-date check below; governance still governs use on shared integration branches. |
| Repository Projects feature | On (`has_projects: true`) | **Off** | Disables the repository feature; this does not describe account-level project boards. |
| Legacy downloads flag | On (`has_downloads: true`) | **Off** | API metadata difference; not a prohibition on release assets or source downloads. |
| GitHub Pages | Not published | **Deploy from a branch: default branch, `/` (root)** | Publishes the static website from the default branch only; other branches are not deployed. |

Sources: GitHub's [repository REST documentation][repo-api] and
[Pages publishing source documentation][pages-source]. These values are
configuration differences, not blanket recommendations for every project.

<a id="security"></a>

## 🔐 Security features — always enabled

Their initial state depends on the account, the repository's visibility and
any applied security configuration, so they are not classified as differences
from a default. Each is enabled in the repository's **Settings → Advanced
Security** (or **Code security**) page where GitHub offers it; no script
applies or verifies them, so check them there after any settings change.

| Feature | Configured value | Availability / effect |
| --- | --- | --- |
| Private vulnerability reporting | **On** | Public repositories only. Adds **Security → Report a vulnerability**, the private channel that [SECURITY.md](../SECURITY.md) names. |
| Dependabot alerts | **On** | Every repository. Alerts on vulnerable dependencies. |
| Dependabot security updates | **On** | Every repository; requires Dependabot alerts. Opens pull requests that fix vulnerable dependencies, separately from the scheduled version updates in `.github/dependabot.yml`. |
| Secret scanning | **On** | Public repositories; private repositories need a paid licence. |
| Push protection | **On** | Same availability as secret scanning, which it requires. Blocks pushes that contain a detected secret. |

Sources: [private vulnerability reporting][pvr], [Dependabot alerts][dependabot-alerts],
[Dependabot security updates][dependabot-updates] and [secret scanning][secret-scanning].

<a id="rulesets"></a>

## 🛡️ Custom active protection

The baseline has no corresponding custom active rulesets. The following five
rulesets are explicit additions. All are **Active**, have **no excluded refs**
and **no bypass actors**. Default-valued supporting parameters below are
included only to describe each custom rule completely; they are not counted
as separate deviations from GitHub defaults. Disabled rulesets are not listed:
they enforce nothing.

| Custom ruleset | Target | Added restrictions |
| --- | --- | --- |
| Protect main | `~DEFAULT_BRANCH` | Require PR, resolved conversations and strict up-to-date `HTML and links` from GitHub Actions; allow merge commits only; block deletion and force pushes. |
| Protect release branches | `refs/heads/release/**` | Require PR, resolved conversations and the same strict required check; allow squash or merge commits; block deletion and force pushes. |
| Prevent release branch deletion | `refs/heads/release/**` | Independent deletion restriction. |
| Protect release tags | `refs/tags/v*` | Block updates, deletion and force pushes. |
| Protect traffic history | `refs/heads/traffic-history` | Block deletion and force pushes. Direct pushes stay allowed for the Daily traffic export workflow ([docs/TRAFFIC.md](TRAFFIC.md)). |

### 🔬 Supporting parameters for the two PR rulesets

| Parameter | Default-branch rule | Release-branch rule |
| --- | --- | --- |
| Required status context | `HTML and links` | `HTML and links` |
| Expected check integration | GitHub Actions (`15368`) | GitHub Actions (`15368`) |
| Up-to-date requirement | Strict | Strict |
| Required check enforced on creation | Yes | No — branch bootstrap exception |
| Required approving reviews | 0 | 0 |
| Required review-thread resolution | Yes | Yes |
| Permitted PR merge methods | Merge | Squash, merge |
| Administrator/app bypass | None | None |

**Operational implications:** zero approvals does not establish independent
review. The release bootstrap exception does not exempt subsequent changes.
Every change to the default and release branches, including bringing a release
branch level with the default branch, goes through a pull request; a direct
push, even a fast-forward, is refused. Do not rely on an administrator bypass.
Tag protection does not itself restrict tag creation or authorize publishing a
release.

The check name and branch patterns are reusable conventions, not built-in
GitHub jobs or automatically existing branches. Confirm that the required job
reports on every relevant PR before adopting these rules.

<a id="reuse"></a>

## ♻️ Reuse and maintenance

- Keep repository names, usernames, URLs, issue numbers and rule IDs out of this file.
- Verify the destination's actual default and inherited policies before copying a value.
- Include a setting only when both its configured value and comparison default are known.
- Remove rows that match the destination's default; retain only its actual differences.
- Recheck this comparison after platform-default changes or an approved configuration change.

> [!NOTE]
> This is intentionally not a complete settings inventory. The security
> features above are recorded as configured values, not as differences from
> a default, because their initial state depends on account, visibility or an
> applied security configuration. Deployment environments and their secrets are configured as described in the
> automation guides. Omission does not mean a feature is disabled or unimportant.

<a id="sources"></a>

## 📚 Default and ruleset references

| Reference | Supports |
| --- | --- |
| [Repository REST API][repo-api] | Declared option defaults and parameter meanings |
| [Pages publishing source][pages-source] | Publishing from a branch and folder |
| [Private vulnerability reporting][pvr] | Availability on public repositories and how the setting is enabled |
| [Dependabot alerts][dependabot-alerts] and [security updates][dependabot-updates] | What the two Dependabot switches do and how they depend on each other |
| [Secret scanning][secret-scanning] | Availability by visibility and the push protection it enables |
| [Creating rulesets][ruleset-create] | Custom targets, bypass configuration and activation; the editor initially uses Disabled enforcement |
| [Available rules][ruleset-rules] | Meaning of selected protection rules, including editor defaults |
| [Security configuration defaults][security-defaults] | Why organization-applied defaults must be distinguished from a standalone baseline |

[repo-api]: https://docs.github.com/en/rest/repos/repos
[pages-source]: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
[pvr]: https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository
[dependabot-alerts]: https://docs.github.com/en/code-security/concepts/supply-chain-security/dependabot-alerts
[dependabot-updates]: https://docs.github.com/en/code-security/concepts/supply-chain-security/dependabot-security-updates
[secret-scanning]: https://docs.github.com/en/code-security/concepts/secret-security/secret-scanning
[ruleset-create]: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository
[ruleset-rules]: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
[security-defaults]: https://docs.github.com/en/enterprise-cloud@latest/code-security/how-tos/secure-at-scale/configure-enterprise-security/establish-complete-coverage/create-custom-configuration

---

[↑ Back to comparison basis](#scope)
