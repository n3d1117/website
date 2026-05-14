#!/usr/bin/env bash
set -euo pipefail

start_time="$SECONDS"
REPO_DIR="${WEBSITE_REPO_DIR:-/home/ned/website}"
REMOTE="${WEBSITE_REMOTE:-origin}"
SOURCE_BRANCH="${WEBSITE_SOURCE_BRANCH:-master}"
PROJECT_NAME="${CLOUDFLARE_PAGES_PROJECT:-website}"
DEPLOY_BRANCH="${CLOUDFLARE_PAGES_BRANCH:-generated-data}"
CACHE_DIR="${WEBSITE_IMAGE_CACHE_DIR:-$HOME/.cache/website/static-img}"
SCRAPER_ENV_FILE="${WEBSITE_SCRAPER_ENV_FILE:-$REPO_DIR/.env}"
CLOUDFLARE_ENV_FILE="${CLOUDFLARE_ENV_FILE:-$HOME/.config/website/cloudflare.env}"
NOTIFY_LOG_FILE="${WEBSITE_NOTIFY_LOG_FILE:-/var/log/update-service.log}"
NOTIFY_LOG_LINES="${WEBSITE_NOTIFY_LOG_LINES:-80}"
DEPLOY_ATTEMPTS="${WEBSITE_DEPLOY_ATTEMPTS:-2}"
DEPLOY_RETRY_DELAY_SECONDS="${WEBSITE_DEPLOY_RETRY_DELAY_SECONDS:-5}"
RUN_LOG_FILE="$(mktemp "${TMPDIR:-/tmp}/website-refresh.XXXXXX.log")"
live_data_file=""

export PATH="$HOME/.local/bin:$HOME/.local/node/bin:$PATH"
exec > >(tee "$RUN_LOG_FILE") 2>&1

source_env_file() {
  local env_file="$1"

  if [ ! -f "$env_file" ]; then
    return 0
  fi

  set -a
  # shellcheck source=/dev/null
  . "$env_file"
  set +a
}

source_env_file "$SCRAPER_ENV_FILE"
source_env_file "$CLOUDFLARE_ENV_FILE"
export PLEX_METADATA_CACHE_FILE="${PLEX_METADATA_CACHE_FILE:-$HOME/.cache/website/plex-metadata.json}"

notify_failure() {
  local exit_code="$1"

  if [ "${WEBSITE_NOTIFY_ON_FAILURE:-1}" = "0" ]; then
    return 0
  fi

  if [ -z "${TELEGRAM_BOT_TOKEN:-}" ] || [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
    return 0
  fi

  local host branch commit log_file tail_log message
  host="$(hostname 2>/dev/null || echo unknown)"
  branch="$(git -C "$REPO_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "$SOURCE_BRANCH")"
  commit="$(git -C "$REPO_DIR" rev-parse --short HEAD 2>/dev/null || echo unknown)"
  log_file="${RUN_LOG_FILE:-$NOTIFY_LOG_FILE}"

  if [ -f "$log_file" ]; then
    tail_log="$(tail -n "$NOTIFY_LOG_LINES" "$log_file" 2>/dev/null | tail -c 3000 || true)"
  else
    tail_log="No log file found at $log_file."
  fi

  message="$(cat <<EOF
Website refresh failed on $host
Repo: website
Branch: $branch
Commit: $commit
Exit: $exit_code

$tail_log
EOF
)"

  curl --fail --silent --show-error --max-time 10 \
    -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d chat_id="$TELEGRAM_CHAT_ID" \
    --data-urlencode text="$message" >/dev/null || true
}

on_exit() {
  local exit_code="$?"
  local elapsed="$((SECONDS - start_time))"

  if [ -n "$live_data_file" ]; then
    rm -f "$live_data_file"
  fi

  echo "Total refresh time: ${elapsed}s"

  if [ "$exit_code" -ne 0 ]; then
    notify_failure "$exit_code"
  fi

  rm -f "$RUN_LOG_FILE"
}

trap on_exit EXIT

mkdir -p "$HOME/.cache/website"
exec 9>"$HOME/.cache/website/refresh.lock"
flock 9

run_quiet() {
  local label="$1"
  shift
  local log_file
  log_file="$(mktemp)"
  printf '%s... ' "$label"
  if "$@" >"$log_file" 2>&1; then
    echo "ok"
    rm -f "$log_file"
  else
    echo "failed"
    cat "$log_file"
    rm -f "$log_file"
    return 1
  fi
}

run_quiet_retry() {
  local label="$1"
  local attempts="$2"
  local delay_seconds="$3"
  shift 3

  local attempt log_file
  for ((attempt = 1; attempt <= attempts; attempt++)); do
    log_file="$(mktemp)"
    printf '%s (attempt %s/%s)... ' "$label" "$attempt" "$attempts"
    if "$@" >"$log_file" 2>&1; then
      echo "ok"
      rm -f "$log_file"
      return 0
    fi

    echo "failed"
    cat "$log_file"
    rm -f "$log_file"

    if [ "$attempt" -lt "$attempts" ]; then
      echo "Retrying $label in ${delay_seconds}s..."
      sleep "$delay_seconds"
    fi
  done

  return 1
}

cd "$REPO_DIR"

# Check tools.
for command in uv hugo wrangler rsync curl sha256sum; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "$command is required before refreshing."
    exit 1
  fi
done

# Sync source.
run_quiet "Syncing source" bash -c '
  git fetch "$1" "$2"
  git switch "$2"
  git reset --hard "$1/$2"
' _ "$REMOTE" "$SOURCE_BRANCH"

# Restore generated image cache.
rm -rf public
mkdir -p "$CACHE_DIR" static/img
run_quiet "Restoring image cache" rsync -a "$CACHE_DIR"/ static/img/

# Scrape and validate data.
uv run python scripts/scraper.py
run_quiet "Saving image cache" rsync -a --delete static/img/ "$CACHE_DIR"/

# Build site.
run_quiet "Building Hugo site" hugo -b https://edoardo.fyi/ --minify --gc

# Deploy to Cloudflare Pages.
expected_sha="$(sha256sum static/data.json | awk '{print $1}')"
commit_hash="$(git rev-parse HEAD)"
commit_message="$(git log -1 --pretty=%s)"

run_quiet_retry "Deploying to Cloudflare Pages" "$DEPLOY_ATTEMPTS" "$DEPLOY_RETRY_DELAY_SECONDS" wrangler pages deploy public \
  --project-name "$PROJECT_NAME" \
  --branch "$DEPLOY_BRANCH" \
  --commit-hash "$commit_hash" \
  --commit-message "$commit_message" \
  --commit-dirty=true

# Verify live data.
deadline=$((SECONDS + 600))
live_data_file="$(mktemp)"

while [ "$SECONDS" -lt "$deadline" ]; do
  if curl --fail --silent --show-error "https://edoardo.fyi/data.json?deploy=$commit_hash&t=$(date +%s)" -o "$live_data_file"; then
    actual_sha="$(sha256sum "$live_data_file" | awk '{print $1}')"
    if [ "$actual_sha" = "$expected_sha" ]; then
      echo "Live data matches deployed data."
      rm -rf public data/scraper.json static/data.json static/scraper.json static/img .hugo_build.lock
      exit 0
    fi
  fi

  sleep 20
done

echo "Live data did not match deployed data within 10 minutes."
exit 1
