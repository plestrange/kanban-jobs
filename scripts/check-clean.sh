#!/usr/bin/env bash
# Greps the git index for tracked paths under data/. See ARCHITECTURE.md §9.
set -euo pipefail

bad=$(git ls-files | grep -E '^(data/|config/criteria\.yaml$)' || true)

if [ -n "$bad" ]; then
  echo "ERROR: tracked paths that must stay gitignored:" >&2
  echo "$bad" >&2
  exit 1
fi

echo "check-clean: no data/ paths tracked."
