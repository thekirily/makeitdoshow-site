#!/usr/bin/env bash
# The owner runs this command at film upload. The agent must never run it.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "$(git branch --show-current)" != launch ]]; then
  echo 'Publish from the launch branch.' >&2
  exit 1
fi
if [[ -n "$(git status --porcelain)" ]]; then
  echo 'Commit or preserve outstanding changes before publishing.' >&2
  exit 1
fi
if [[ "$(git remote get-url origin)" != 'https://github.com/thekirily/makeitdoshow-site.git' && "$(git remote get-url origin)" != 'git@github.com:thekirily/makeitdoshow-site.git' ]]; then
  echo 'Unexpected remote; publication stopped.' >&2
  exit 1
fi
python3 scripts/preflight.py
python3 scripts/verify.py
python3 -m unittest discover -s tests -v
git fetch origin main
if ! git merge-base --is-ancestor origin/main HEAD; then
  echo 'Public main has new changes. Integrate and verify them on launch before publishing.' >&2
  exit 1
fi
# Merge the reviewed PR through GitHub, rather than introducing workflow files
# through a Git push made with the narrower shell OAuth credential.
publish_sha=$(git rev-parse HEAD)
pr_number=$(gh pr list --repo thekirily/makeitdoshow-site --state open --head launch --base main --json number --jq 'if length == 1 then .[0].number else error("Expected one open launch pull request") end')
pr_sha=$(gh pr view "$pr_number" --repo thekirily/makeitdoshow-site --json headRefOid --jq .headRefOid)
if [[ "$pr_sha" != "$publish_sha" ]]; then
  echo 'The remote PR differs from this checkout. Fetch and review before publishing.' >&2
  exit 1
fi
pr_draft=$(gh pr view "$pr_number" --repo thekirily/makeitdoshow-site --json isDraft --jq .isDraft)
if [[ "$pr_draft" == true ]]; then
  gh pr ready "$pr_number" --repo thekirily/makeitdoshow-site
fi
# No admin bypass, force push, branch deletion, or automatic product publication.
gh pr merge "$pr_number" --repo thekirily/makeitdoshow-site --merge --match-head-commit "$publish_sha"
