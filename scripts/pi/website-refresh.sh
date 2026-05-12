#!/usr/bin/env bash
set -euo pipefail

# Pi entrypoint for website refreshes.
#
# GitHub Actions calls this over Tailscale SSH after pushes to master.
# /home/ned/update.sh also calls this during the daily 04:00 cron.
#
# This first updates master so the repo-owned deploy script is always current.

REPO_DIR="${WEBSITE_REPO_DIR:-/home/ned/website}"
REMOTE="${WEBSITE_REMOTE:-origin}"
SOURCE_BRANCH="${WEBSITE_SOURCE_BRANCH:-master}"

# Cron shells are minimal and may not include uv's install directory.
export PATH="$HOME/.local/bin:$PATH"

cd "$REPO_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required on the Pi before running website refresh."
  echo "Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi

git fetch "$REMOTE" "$SOURCE_BRANCH"
git switch "$SOURCE_BRANCH"
git reset --hard "$REMOTE/$SOURCE_BRANCH"

scripts/deploy-direct.sh
