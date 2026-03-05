#!/usr/bin/env bash
# verify_ci_passed.sh — Deployment gate: ensure all CI checks passed for a commit.
#
# Fetches check-runs from the GitHub API and fails if any are missing,
# still in progress, or unsuccessful. Called by the CD workflow before
# any Firebase deployment to prevent deploying from a broken build.
#
# Usage: verify_ci_passed.sh <owner/repo> <commit_sha>
# Requires: gh CLI authenticated with contents:read scope.

set -uo pipefail

REPO="$1"
SHA="$2"

echo "Verifying CI status for commit ${SHA:0:8} in ${REPO}..."

CHECKS_JSON=$(gh api "repos/${REPO}/commits/${SHA}/check-runs" --paginate 2>&1)
if [ $? -ne 0 ]; then
  echo "::error::Failed to fetch CI checks from GitHub API: $CHECKS_JSON" >&2
  exit 1
fi

TOTAL=$(echo "$CHECKS_JSON" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d['total_count'])
")

INCOMPLETE=$(echo "$CHECKS_JSON" | python3 -c "
import json, sys
d = json.load(sys.stdin)
# Exclude CD workflow job to avoid self-blocking when it's currently running
excluded = {'Deploy Release Reports'}
print(len([r for r in d['check_runs']
           if r['name'] not in excluded and r['status'] != 'completed']))
")

FAILURES=$(echo "$CHECKS_JSON" | python3 -c "
import json, sys
d = json.load(sys.stdin)
# Exclude the CD workflow's own job to avoid self-blocking on re-runs
excluded = {'Deploy Release Reports'}
print(len([r for r in d['check_runs']
           if r['name'] not in excluded
           and r['status'] == 'completed'
           and r['conclusion'] not in ('success', 'skipped', 'neutral')]))
")

if [ "$TOTAL" -eq 0 ]; then
  echo "::error::No CI checks found for ${SHA:0:8} — was the tag pushed without triggering CI?" >&2
  exit 1
fi

if [ "$INCOMPLETE" -gt 0 ]; then
  echo "::error::${INCOMPLETE} CI check(s) still in progress for ${SHA:0:8} — deploy cannot proceed" >&2
  exit 1
fi

if [ "$FAILURES" -gt 0 ]; then
  echo "::error::${FAILURES} CI check(s) failed for ${SHA:0:8} — refusing to deploy" >&2
  exit 1
fi

echo "CI gate passed: ${TOTAL} check(s) completed successfully for ${SHA:0:8}"
exit 0
