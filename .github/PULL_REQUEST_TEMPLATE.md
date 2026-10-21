<!-- Target the active release branch named in GOVERNANCE.md, not main. -->

## Linked issues

Resolves #

## Changes

-

## Why

## Validated

<!-- Commands and checks actually run, with results. Hosted checks run on this pull request. -->

- [ ] `python3 .github/scripts/check-website.py`
- [ ] `python3 .github/scripts/check-website.py --external` (when external links change)
- [ ] `python3 -m unittest discover -s .github/scripts -p 'test_portfolio_refresh.py'` (when portfolio automation changes)
- [ ] Visual review in a browser (when the website changes)

## Not validated

<!-- State plainly what was not checked and why. Write "Nothing" only if that is true. -->

## Checklist

- [ ] The base branch is the active release branch.
- [ ] Each linked issue has a milestone and exactly one priority label.
- [ ] Portfolio claims match each engine repository's own evidence (GOVERNANCE.md, Portfolio inclusion and status).
- [ ] No tokens, credentials or confidential data.
