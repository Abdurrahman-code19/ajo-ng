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

if [ $# -gt 0 ]; then
  git commit -m "$*"
else
  git commit
fi

if [ -z "$(git status --porcelain)" ]; then
  git push origin "$BRANCH"
  echo "==> Pushed $BRANCH"
else
  echo "==> Committed. Untracked or modified files remain, so nothing was pushed:"
  git status --short
  echo "   Stage and commit them, or push explicitly when ready."
fi
