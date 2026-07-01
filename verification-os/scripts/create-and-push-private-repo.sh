#!/usr/bin/env bash
# Create a private GitHub repo and push VerificationOS.
# Requires: gh CLI authenticated with repo creation scope (gh auth login).
set -euo pipefail

OWNER="${1:-fxdv}"
REPO="${2:-verification-os}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cd "$ROOT"

if ! command -v gh >/dev/null 2>&1; then
  echo "Install GitHub CLI: https://cli.github.com/"
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Authenticate first: gh auth login"
  exit 1
fi

if git remote get-url origin >/dev/null 2>&1; then
  echo "Remote 'origin' already exists: $(git remote get-url origin)"
  echo "Pushing to existing remote..."
  git push -u origin main
  exit 0
fi

gh repo create "${OWNER}/${REPO}" \
  --private \
  --source=. \
  --remote=origin \
  --push \
  --description "Hypothesis-verification engine for solo deeptech AI studios (harness, pipeline, HI dashboard)"

echo ""
echo "Private repo ready: https://github.com/${OWNER}/${REPO}"
