#!/usr/bin/env bash
# Download and verify the exact release asset, then scan all repository refs.
set -euo pipefail
scan_root=$(git rev-parse --show-toplevel)
scan_tmp=$(mktemp -d)
trap 'rm -rf "$scan_tmp"' EXIT
scan_version=8.30.1
scan_archive="gitleaks_${scan_version}_linux_x64.tar.gz"
curl -fLsS "https://github.com/gitleaks/gitleaks/releases/download/v${scan_version}/${scan_archive}" -o "$scan_tmp/$scan_archive"
curl -fLsS "https://github.com/gitleaks/gitleaks/releases/download/v${scan_version}/gitleaks_${scan_version}_checksums.txt" -o "$scan_tmp/checksums.txt"
(
  cd "$scan_tmp"
  grep " ${scan_archive}$" checksums.txt | sha256sum --check
  tar -xzf "$scan_archive" gitleaks
)
cd "$scan_root"
"$scan_tmp/gitleaks" git --config .gitleaks.toml --redact --log-opts='--all'
