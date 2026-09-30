#!/usr/bin/env bash
#
# Install the versioned git hooks.
#
# Why this is a script and not a symlink someone remembers to run: a symlink in
# .git/hooks lives on one machine and dies with it. Anyone who clones this repo
# would silently commit with no verification, which is precisely the failure
# mode the hook exists to prevent.
#
# `core.hooksPath` points git at a directory that IS versioned, so the hook
# travels with the code and cannot drift from it.
#
# Run by `npm install` (via the "prepare" script) and safe to re-run.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  echo "==> Not a git repository, skipping hook installation."
  exit 0
fi

HOOKS_DIR="$ROOT/.githooks"
if [ ! -d "$HOOKS_DIR" ]; then
  echo "==> No $HOOKS_DIR directory, nothing to install."
  exit 0
fi

# Git silently ignores a non-executable hook. The repository lives on a Windows
# mount, where the executable bit does not reliably survive a checkout, so a
# fresh clone got a 100644 pre-commit and committed with no verification at all
# -- silently, and with only a hint nobody reads. Setting it here means the hook
# works even when the recorded mode is wrong.
for hook in "$HOOKS_DIR"/*; do
  [ -f "$hook" ] || continue
  if [ ! -x "$hook" ]; then
    chmod +x "$hook"
    echo "==> Made $(basename "$hook") executable"
  fi
done

git config core.hooksPath "$HOOKS_DIR"
echo "==> core.hooksPath set to .githooks (pre-commit will run npm run verify)"
