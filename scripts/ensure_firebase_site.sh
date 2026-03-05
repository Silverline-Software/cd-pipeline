#!/usr/bin/env bash
# ensure_firebase_site.sh — Idempotently create a Firebase Hosting site.
#
# Exits 0 whether the site is newly created or already exists.
# Exits 1 on real errors (auth failure, quota, etc.) so the pipeline fails loudly.
#
# Usage: ensure_firebase_site.sh <firebase_project_id> <site_id>

set -uo pipefail

PROJECT="$1"
SITE_ID="$2"

OUTPUT=$(firebase hosting:sites:create "$SITE_ID" --project "$PROJECT" 2>&1)
EXIT_CODE=$?

if [ "$EXIT_CODE" -eq 0 ]; then
  echo "Created Firebase Hosting site: $SITE_ID"
  exit 0
fi

if echo "$OUTPUT" | grep -qi "already exist"; then
  echo "Firebase Hosting site already exists: $SITE_ID"
  exit 0
fi

echo "Error ensuring Firebase Hosting site exists:" >&2
echo "$OUTPUT" >&2
exit 1
