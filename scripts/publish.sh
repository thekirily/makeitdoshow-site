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
# Ordinary fast-forward only. A concurrent main change causes Git to reject the push.
git push origin HEAD:main
