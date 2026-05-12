#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${WEBSITE_REPO_DIR:-/home/ned/website}"
REMOTE="${WEBSITE_REMOTE:-origin}"
SOURCE_BRANCH="${WEBSITE_SOURCE_BRANCH:-master}"
PROJECT_NAME="${CLOUDFLARE_PAGES_PROJECT:-website}"
DEPLOY_BRANCH="${CLOUDFLARE_PAGES_BRANCH:-generated-data}"
CACHE_DIR="${WEBSITE_IMAGE_CACHE_DIR:-$HOME/.cache/website/static-img}"
CLOUDFLARE_ENV_FILE="${CLOUDFLARE_ENV_FILE:-$HOME/.config/website/cloudflare.env}"

export PATH="$HOME/.local/bin:$HOME/.local/node/bin:$PATH"

if [ -f "$CLOUDFLARE_ENV_FILE" ]; then
  set -a
  # shellcheck source=/dev/null
  . "$CLOUDFLARE_ENV_FILE"
  set +a
fi

cd "$REPO_DIR"

# Check tools.
for command in uv hugo npm npx wrangler rsync curl sha256sum; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "$command is required before refreshing."
    exit 1
  fi
done

# Sync source.
git fetch "$REMOTE" "$SOURCE_BRANCH"
git switch "$SOURCE_BRANCH"
git reset --hard "$REMOTE/$SOURCE_BRANCH"

# Restore generated image cache.
rm -rf public
mkdir -p "$CACHE_DIR" static/img
rsync -a "$CACHE_DIR"/ static/img/

# Scrape and validate data.
uv run python scripts/scraper.py
rsync -a --delete static/img/ "$CACHE_DIR"/

# Build site.
npm ci --no-audit --fund=false --prefer-offline
hugo -b https://edoardo.fyi/ --minify --gc
npx torchlight

# Deploy to Cloudflare Pages.
expected_sha="$(sha256sum static/data.json | awk '{print $1}')"
commit_hash="$(git rev-parse HEAD)"
commit_message="$(git log -1 --pretty=%s)"

wrangler pages deploy public \
  --project-name "$PROJECT_NAME" \
  --branch "$DEPLOY_BRANCH" \
  --commit-hash "$commit_hash" \
  --commit-message "$commit_message" \
  --commit-dirty=true

# Verify live data.
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
