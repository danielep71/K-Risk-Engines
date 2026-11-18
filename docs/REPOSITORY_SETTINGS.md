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
repository; [docs/repository-settings.json](repository-settings.json) and the
tool described under [Applying and verifying](#apply) do.
[GOVERNANCE.md](../GOVERNANCE.md) describes how contributors work
within these settings.

[General differences](#general) · [Security features](#security) · [Actions settings](#actions) · [Custom protection](#rulesets) · [Apply and verify](#apply) · [Reuse](#reuse) · [Sources](#sources)

<a id="general"></a>

## 🏷️ General settings — changed values only

| Setting | Documented baseline | Configured value | Effect / qualification |
| --- | --- | --- | --- |
| Allow rebase merging | On (`allow_rebase_merge: true`) | **Off** | Pull requests merge with squash or merge commits only; branch rulesets narrow this further. |
| Automatically delete merged head branches | Off (`delete_branch_on_merge: false`) | **On** | Cleans up task branches and the bot proposal branch after merge; protected retained branches remain subject to their deletion rules. |
| Always suggest updating PR branches | Off (`allow_update_branch: false`) | **On** | Offers updates for the strict up-to-date check below; governance still governs use on shared integration branches. |
| Repository Projects feature | On (`has_projects: true`) | **Off** | Disables the repository feature; this does not describe account-level project boards. |
| Legacy downloads flag | On (`has_downloads: true`) | **Off** | API metadata difference; not a prohibition on release assets or source downloads. |
| GitHub Pages | Not published | **Source: GitHub Actions** (`build_type: workflow`; the recorded source branch stays the default branch, `/`) | The `deploy` job of `document-portal.yml` publishes the static website and the documentation portal from the default branch only; other branches and pull requests are not deployed. With any other source the job deploys nothing and reports a warning. |

Sources: GitHub's [repository REST documentation][repo-api] and
[Pages publishing source documentation][pages-source]. These values are
configuration differences, not blanket recommendations for every project.

<a id="security"></a>

## 🔐 Security features — always enabled

Their initial state depends on the account, the repository's visibility and
any applied security configuration, so they are not classified as differences
from a default. Each is enabled in the repository's **Settings → Advanced
Security** (or **Code security**) page where GitHub offers it, and the
settings tool below verifies them.

| Feature | Configured value | Availability / effect |
| --- | --- | --- |
| Private vulnerability reporting | **On** | Public repositories only. Adds **Security → Report a vulnerability**, the private channel that [SECURITY.md](../SECURITY.md) names. |
| Dependabot alerts | **On** | Every repository. Alerts on vulnerable dependencies. |
| Dependabot security updates | **On** | Every repository; requires Dependabot alerts. Opens pull requests that fix vulnerable dependencies, separately from the scheduled version updates in `.github/dependabot.yml`. |
| Secret scanning | **On** | Public repositories; private repositories need a paid licence. |
| Push protection | **On** | Same availability as secret scanning, which it requires. Blocks pushes that contain a detected secret. |
| Code scanning (CodeQL) | **Advanced setup**; default setup **Off** | Free on public repositories. [`.github/workflows/codeql.yml`](../.github/workflows/codeql.yml) analyzes Actions, JavaScript and Python with the security-extended queries. GitHub rejects advanced-setup uploads while the default setup is on, so it stays off. The settings tool does not read or apply this setting. |

Sources: [private vulnerability reporting][pvr], [Dependabot alerts][dependabot-alerts],
[Dependabot security updates][dependabot-updates] and [secret scanning][secret-scanning].

<a id="actions"></a>

## 🎬 GitHub Actions settings — verified, never written

Like the security features, these are recorded as configured values: their
initial state depends on the account, the repository's creation date and any
organization policy. Set them by hand in **Settings → Actions → General**. The
settings tool reads each one from the REST endpoint below and compares it; it
never writes them, and it does not infer them from the workflow files. A value
that cannot be read (an HTTP error, or a response without the field) is
unknown and counts as drift.

| Setting (manifest key) | Configured value | Read from (`GET repos/OWNER/REPO/…`) | Effect |
| --- | --- | --- | --- |
| Require actions to be pinned to a full-length commit SHA (`sha_pinning_required`) | **On** | `actions/permissions`, `sha_pinning_required` | Workflows fail if they use an action by tag or branch; every action here is already pinned, and the workflow tests require it. |
| Default workflow permissions (`default_workflow_permissions`) | **Read** | `actions/permissions/workflow`, `default_workflow_permissions` | A job without a `permissions` block gets a read-only token; jobs here declare their own permissions anyway. |
| Allow GitHub Actions to create and approve pull requests (`can_approve_pull_request_reviews`) | **Off** | `actions/permissions/workflow`, `can_approve_pull_request_reviews` | The workflow token cannot approve pull requests. The portfolio refresh opens its proposal with a GitHub App token, not with this permission. |
| Approval for workflows from fork pull requests (`fork_pr_approval_policy`) | **Require approval for all external contributors** (`all_external_contributors`) | `actions/permissions/fork-pr-contributor-approval`, `approval_policy` | Public repositories only; not applied, and not drift, on a private one. Workflow runs from fork pull requests wait for approval. |
| Artifact and log retention (`retention_days`) | **90 days** | `actions/permissions/artifact-and-log-retention`, `days` | How long workflow artifacts and logs are kept; a workflow can ask for a shorter retention, as the artifact uploads here do (30 days). |

Sources: GitHub's [Actions permissions REST documentation][actions-permissions-api]
and [Actions settings for a repository][actions-settings], checked on 2026-11-17.

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

<a id="apply"></a>

## 🧰 Applying and verifying

[docs/repository-settings.json](repository-settings.json) holds the general
options above, the five security features, the GitHub Pages source, the five
GitHub Actions settings and the five rulesets with their full parameters. Its rulesets were read from GitHub on
2026-11-01. [.github/scripts/setup_repository.py](../.github/scripts/setup_repository.py)
compares the repository with that file through the GitHub CLI. I run it locally
after each settings change; applying never runs in CI, and a daily read-only
partial check runs in the workflow described below.

```sh
# Read-only: exit 1 on drift; optional dated records in Markdown and JSON.
python3 .github/scripts/setup_repository.py --repo OWNER/REPO --check \
  --report settings-evidence.md --evidence settings-evidence-{date}.json
# Preview: the differences, the plan and its PLAN SHA-256. Writes nothing.
python3 .github/scripts/setup_repository.py --repo OWNER/REPO
# Apply exactly the reviewed plan, journaling each write, then read everything back.
python3 .github/scripts/setup_repository.py --repo OWNER/REPO --apply \
  --approve-plan PLAN_SHA256 --journal settings-journal.json
```

| Mode | Access | Repository permissions of a fine-grained token |
| --- | --- | --- |
| Preview and `--check` | Any access that can read the repository | Metadata: read; with Administration: read, Pages: read and Contents: read every managed value is reported |
| `--apply` | Administrator | Administration: write, Pages: write, Checks: read, Contents: read, Metadata: read |

**Unknown values.** Preview and `--check` report what the token can read and
mark everything else unknown, with its source and HTTP status (for example
`[GET pages (HTTP 403: unreadable)]`, or a general option that GitHub does not
report to this token). An unknown value is drift, never a match: with a
read-only token, `--check` exits 1 and the records say DRIFT. A managed ruleset
must report an explicit `bypass_actors` list; an omitted, null or malformed
value is unknown, not an empty list. `--apply` refuses before any write while
any managed value is unknown, when the token is not an administrator's, or when
merge commits or squash merging are disabled (the release rulesets allow them).

**Workflow token scope.** `--check --token-scope workflow` is the read-only
variant for the limited `GITHUB_TOKEN` of a workflow, which cannot read the
administration settings. A value the token cannot read is `NOT CHECKED`: it is
neither a match nor drift, and the run lists each one with its source. A
managed ruleset whose bypass list is not reported is `NOT CHECKED` too, unless
a difference is already visible in its other parameters. The Pages site counts
as `NOT CHECKED` when GitHub answers HTTP 404, which a token without access
cannot tell from an unpublished site. Without a difference the result is
`PARTIAL` and the exit status is 3; with one it is DRIFT (exit 1), and when
every value is readable it is VERIFIED (exit 0). The mode plans and writes
nothing, refuses `--apply`, `--report` and `--evidence`, and needs `--check`.
The **Detect repository settings drift** workflow
([.github/workflows/settings-drift.yml](../.github/workflows/settings-drift.yml))
runs it every day at 04:41 UTC and on demand, with `contents: read`, a
five-minute timeout and cancellation of superseded runs. It succeeds on exit 0
or 3, fails on a difference or an error, and lists the values it did not check
in its summary. Only `--check` with administrator access verifies everything.

**Plan approval.** The `PLAN SHA-256` covers the repository and its default
branch (the `~DEFAULT_BRANCH` ruleset protects whichever branch it is), the
configuration file's bytes, every observed managed value, the definitions of the rulesets
that cover a managed one, and each planned write with its payload; it leaves
out sources and timestamps, so an unchanged repository and configuration give
the same digest. `--apply` recomputes it and writes nothing unless it equals
`--approve-plan`: if the repository or the file changed since the preview, run
the preview again and review the new plan.

**Journal and recovery.** `--apply` needs a new `--journal` path (like the
records' paths, it may contain `{date}`, the UTC start date). The journal
(JSON, written atomically) lists the planned writes before the first one and
records after each its status (`pending`, `done`, `failed` with the error) and
the ID of a created ruleset, then the read-back result. It holds methods,
endpoints and ruleset names, never payloads or credentials. A failing write
stops the run with no retry and no rollback: read the journal, run the preview
again, and approve the new plan for what remains. The writes go in this order:
missing rulesets, replaced rulesets, security features, the Pages site, the
general options; never the Actions settings. A differing named ruleset is
replaced only with `--update-existing`. Before writing protection, `--apply`
confirms that `HTML and links` succeeded on the default branch. Dependabot
security updates that GitHub reports as paused count as drift. A differing
Actions setting is listed as `DIFF actions …`, and `--apply` fails its
read-back naming each one to set by hand.

**Equivalent protection.** A managed ruleset counts as `covered`, and needs no
write, when active rulesets of the same target with an empty, reported bypass
list and no excluded refs together enforce every configured rule at least as
strictly under any names: on the same refs (`~ALL`, and `~DEFAULT_BRANCH` or the
default branch by name), with as many or more required approvals, checks and
true options, a strict check policy, and no more merge methods. A named
ruleset with stronger parameters is covered, not replaced. Coverage is judged
against the rulesets as the plan leaves them: a ruleset the plan replaces counts
with its configured definition, so what it enforces beyond the file cannot
cover a missing one. The definitions of covering rulesets are part of the plan
digest. For example, the separate `Prevent release branch deletion` ruleset is
covered while `Protect release branches` is in place.

**Records.** `--report` writes a dated Markdown record and `--evidence` a JSON
record (`{date}` in the path becomes the UTC start date) with the timestamp, mode,
repository, default branch, the configuration path and SHA-256, every
configured and observed value with its source, the ruleset statuses and
differences, the planned writes (method, endpoint and ruleset name, never a
payload) and the plan digest. The journal, the Markdown record and the JSON
record must be three different files: the tool refuses before reading anything
when two of them resolve to the same path. Rulesets outside the file, such as disabled ones,
are named in a note and left in place; the tool never deletes a ruleset. Keep
the records and the journal out of the repository unless they are wanted as
dated records; they contain the repository name and ruleset IDs.

<a id="reuse"></a>

## ♻️ Reuse and maintenance

- Keep repository names, usernames, URLs, issue numbers and rule IDs out of this file
  and out of `repository-settings.json`.
- Verify the destination's actual default and inherited policies before copying a value.
- Include a setting only when both its configured value and comparison default are known.
- Remove rows that match the destination's default; retain only its actual differences.
- Recheck this comparison after platform-default changes or an approved configuration change.

> [!NOTE]
> This is intentionally not a complete settings inventory. The security
> features above are recorded as configured values, not as differences from
> a default, because their initial state depends on account, visibility or an
> applied security configuration. Deployment environments and their secrets
> are configured as described in the automation guides and are outside the
> settings tool. Omission does not mean a feature is disabled or unimportant.

<a id="sources"></a>

## 📚 Default and ruleset references

| Reference | Supports |
| --- | --- |
| [Repository REST API][repo-api] | Declared option defaults and parameter meanings |
| [Pages publishing source][pages-source] | Publishing with a custom GitHub Actions workflow |
| [Private vulnerability reporting][pvr] | Availability on public repositories and how the setting is enabled |
| [Dependabot alerts][dependabot-alerts] and [security updates][dependabot-updates] | What the two Dependabot switches do and how they depend on each other |
| [Secret scanning][secret-scanning] | Availability by visibility and the push protection it enables |
| [Creating rulesets][ruleset-create] | Custom targets, bypass configuration and activation; the editor initially uses Disabled enforcement |
| [Available rules][ruleset-rules] | Meaning of selected protection rules, including editor defaults |
| [Actions permissions REST API][actions-permissions-api] and [Actions settings][actions-settings] | The endpoints and fields the tool reads, the values each setting takes and its effect |
| [Security configuration defaults][security-defaults] | Why organization-applied defaults must be distinguished from a standalone baseline |

[repo-api]: https://docs.github.com/en/rest/repos/repos
[pages-source]: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
[pvr]: https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository
[dependabot-alerts]: https://docs.github.com/en/code-security/concepts/supply-chain-security/dependabot-alerts
[dependabot-updates]: https://docs.github.com/en/code-security/concepts/supply-chain-security/dependabot-security-updates
[secret-scanning]: https://docs.github.com/en/code-security/concepts/secret-security/secret-scanning
[ruleset-create]: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository
[ruleset-rules]: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
[actions-permissions-api]: https://docs.github.com/en/rest/actions/permissions
[actions-settings]: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository
[security-defaults]: https://docs.github.com/en/enterprise-cloud@latest/code-security/how-tos/secure-at-scale/configure-enterprise-security/establish-complete-coverage/create-custom-configuration

---

[↑ Back to comparison basis](#scope)
