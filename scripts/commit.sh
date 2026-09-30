#!/usr/bin/env bash
#
# Commit and push in one step.
#
# Usage:
#   ./scripts/commit.sh <message>
#   ./scripts/commit.sh            (opens an editor for the message)
#
# The pre-commit hook runs the full verification suite, so a broken build
# cannot be pushed. If a commit is rejected, fix the failure rather than
# reaching for --no-verify; if the change really is documentation-only, pass
# --no-verify deliberately and say so in the message.

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

BRANCH="$(git rev-parse --abbrev-ref HEAD)"

# Stage everything first. `git commit -a` silently skips untracked files, which
# made the first run of this script look like it had committed AGENTS.md when it
# had committed nothing at all.
git add -A

if [ -z "$(git diff --cached --name-only)" ]; then
  echo "==> Nothing staged, nothing to commit."
  exit 0
fi

if [ $# -gt 0 ]; then
  git commit -m "$*"
else
  git commit
fi

# Only push on a clean tree. If a hook or a build regenerated something, say so
# loudly rather than pushing a partial state.
if [ -z "$(git status --porcelain)" ]; then
  git push origin "$BRANCH"
  echo "==> Pushed $BRANCH"
else
  echo "==> Committed, but the working tree is not clean, so nothing was pushed:"
  git status --short
  echo "   Re-run once the remaining files are handled."
fi
