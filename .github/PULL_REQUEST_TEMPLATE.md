<!-- Task PRs target the active release branch named in GOVERNANCE.md.
Release-to-main integrations and automation/portfolio-refresh proposals target main.
State which route applies below. -->

## 🔗 Linked issues

Resolves #

## 🧾 Changes

-

## 💡 Why

## ✅ Validated

<!-- Commands and checks actually run, with results. Hosted checks run on this pull request. -->

- [ ] `python3 .github/scripts/check-website.py`
- [ ] `python3 .github/scripts/check-website.py --external` (when external links change)
- [ ] `python3 -m unittest discover -s .github/scripts -p 'test_*.py'` (when site checks or portfolio automation change)
- [ ] Visual review in a browser (when the website changes)

## 🔎 Final-head review

<!-- After fix pushes, wait for any earlier review to finish, then post
@codex review as a top-level conversation comment. Check the completed review
SHA against the current PR head. See GOVERNANCE.md, Review after fix pushes.
For bot-authored PRs skipped by Codex, record the maintainer's final-head
manual review and explicitly state that Codex was skipped. -->

- Final PR head SHA:
- Review type (Codex / maintainer manual review for a skipped bot PR):
- Reviewed commit SHA and review permalink:
- Required CI result and run link:

- [ ] Review covers the current PR head; all findings are fixed or answered and applicable threads resolved.
- [ ] Required CI passes for the current revision and GitHub merge requirements are satisfied.
- [ ] Any push after this record is followed by renewed review and CI verification.

## ⚠️ Not validated

<!-- State plainly what was not checked and why. Write "Nothing" only if that is true. -->

## ☑️ Checklist

- [ ] The base follows GOVERNANCE.md: active release branch for tasks; main for release integration or portfolio-refresh proposals.
- [ ] Each linked issue has a milestone and exactly one priority label.
- [ ] Portfolio claims match each engine repository's own evidence (GOVERNANCE.md, Portfolio inclusion and status).
- [ ] No tokens, credentials or confidential data.
