#!/usr/bin/env bash
set -euo pipefail

# This script rebuilds the deploy branch.
#
# master stays clean and contains only source/content.
# generated-data is reset to master, then generated scraper files are added.
# Cloudflare deploys generated-data, so data.json and images are available live.

BRANCH="${WEBSITE_GENERATED_BRANCH:-generated-data}"
SOURCE_BRANCH="${WEBSITE_SOURCE_BRANCH:-master}"
REMOTE="${WEBSITE_REMOTE:-origin}"
CACHE_DIR="${WEBSITE_IMAGE_CACHE_DIR:-$HOME/.cache/website/static-img}"
REPO_DIR="$(git rev-parse --show-toplevel)"

cd "$REPO_DIR"

echo "Refreshing $BRANCH from $SOURCE_BRANCH..."

git fetch "$REMOTE" "$SOURCE_BRANCH" "$BRANCH" || git fetch "$REMOTE" "$SOURCE_BRANCH"

if git show-ref --verify --quiet "refs/remotes/$REMOTE/$BRANCH"; then
  git switch "$BRANCH" || git switch -c "$BRANCH" "$REMOTE/$BRANCH"
else
  git switch -C "$BRANCH" "$REMOTE/$SOURCE_BRANCH"
fi

# Preserve the generated image cache before resetting to master.
# The cache makes movie/poster runs fast because existing covers are reused.
mkdir -p "$CACHE_DIR"
if [ -d static/img ]; then
  rsync -a --delete static/img/ "$CACHE_DIR/"
fi

# Rebase generated-data onto the latest source branch.
# This intentionally removes generated files from the worktree before restoring
# them from the local cache and the scraper.
git reset --hard "$REMOTE/$SOURCE_BRANCH"

mkdir -p static/img
rsync -a "$CACHE_DIR/" static/img/

scripts/scrape.sh

# Generated files are ignored on master, so force-add them only here.
git add -f data/scraper.json static/data.json static/img

if git diff --cached --quiet; then
  echo "No generated changes to commit."
else
  git commit -m "Update generated data"
fi

# generated-data is rebuilt from master every run, so force-with-lease is expected.
git push --force-with-lease "$REMOTE" "$BRANCH"
