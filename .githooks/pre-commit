#!/usr/bin/env bash
#
# Run the full verification suite before every commit.
#
# Rationale: this repo contains the money rules for a real financial product.
# A commit that breaks the ledger, the fee arithmetic, or the document build
# should never reach main, because "it compiled yesterday" is not evidence
# that it still holds. A hook that blocks is cheaper than a member disputing a
# kobo that a refactor silently moved.

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

echo "==> Type-checking and running domain tests"
if ! npm run verify; then
  echo ""
  echo "COMMIT BLOCKED: verification failed."
  echo "Fix the failure, or stage nothing and commit with --no-verify if the"
  echo "change is documentation-only."
  exit 1
fi

echo ""
echo "==> Verification passed"
