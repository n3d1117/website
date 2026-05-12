#!/usr/bin/env bash
set -euo pipefail

# Build and deploy the site directly from the Pi to Cloudflare Pages.
# This keeps generated data out of git while preserving the image cache.

PROJECT_NAME="${CLOUDFLARE_PAGES_PROJECT:-website}"
DEPLOY_BRANCH="${CLOUDFLARE_PAGES_BRANCH:-generated-data}"
CACHE_DIR="${WEBSITE_IMAGE_CACHE_DIR:-$HOME/.cache/website/static-img}"
REPO_DIR="$(git rev-parse --show-toplevel)"

cd "$REPO_DIR"

export PATH="$HOME/.local/bin:$HOME/.local/node/bin:$PATH"

for command in uv hugo npm npx wrangler; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "$command is required before deploying."
    exit 1
  fi
done

rm -rf public

mkdir -p "$CACHE_DIR" static/img
if [ -d "$CACHE_DIR" ]; then
  rsync -a "$CACHE_DIR"/ static/img/
fi

scripts/scrape.sh
rsync -a --delete static/img/ "$CACHE_DIR"/

npm ci
sh build.sh

expected_sha="$(sha256sum static/data.json | awk '{print $1}')"
commit_hash="$(git rev-parse HEAD)"
commit_message="$(git log -1 --pretty=%s)"

wrangler pages deploy public \
  --project-name "$PROJECT_NAME" \
  --branch "$DEPLOY_BRANCH" \
  --commit-hash "$commit_hash" \
  --commit-message "$commit_message" \
  --commit-dirty=true

deadline=$((SECONDS + 600))

while [ "$SECONDS" -lt "$deadline" ]; do
  if curl --fail --silent --show-error "https://edoardo.fyi/data.json?deploy=$commit_hash&t=$(date +%s)" -o /tmp/website-live-data.json; then
    actual_sha="$(sha256sum /tmp/website-live-data.json | awk '{print $1}')"
    if [ "$actual_sha" = "$expected_sha" ]; then
      echo "Live data matches deployed data."
      rm -f /tmp/website-live-data.json
      rm -rf public data/scraper.json static/data.json static/scraper.json static/img .hugo_build.lock
      exit 0
    fi
  fi

  sleep 20
done

echo "Live data did not match deployed data within 10 minutes."
exit 1
