#!/usr/bin/env bash
# Sync local docs/ to a checkout of bajpai-labs/documentation (docs/vortex-pqc).
#
# Usage:
#   ./scripts/sync-docs.sh /path/to/documentation
#
# Example:
#   git clone https://github.com/bajpai-labs/documentation.git ../documentation
#   ./scripts/sync-docs.sh ../documentation

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_REPO="${1:-}"

if [[ -z "${TARGET_REPO}" ]]; then
  echo "Usage: $0 /path/to/documentation-repo" >&2
  exit 1
fi

if [[ ! -d "${TARGET_REPO}/.git" ]]; then
  echo "Error: ${TARGET_REPO} is not a git repository" >&2
  exit 1
fi

DEST="${TARGET_REPO}/docs/vortex-pqc"
mkdir -p "${DEST}"

rsync -av --delete \
  --exclude '.DS_Store' \
  "${ROOT}/docs/" "${DEST}/"

echo "Synced ${ROOT}/docs/ → ${DEST}/"
echo "Review and commit in the documentation repo:"
echo "  cd ${TARGET_REPO}"
echo "  git add docs/vortex-pqc/"
echo "  git commit -m 'docs(vortex-pqc): manual sync'"
echo "  git push origin main"
