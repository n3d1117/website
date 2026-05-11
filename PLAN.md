# Scraping and Deploy Plan

## Goal

Make deploys fast and reliable while keeping:

- `master` clean
- daily updates at the same time
- updates on push
- `https://edoardo.fyi/data.json` unchanged

## Approach

Use two branches:

- `master`: source/content only
- `generated-data`: deploy branch with source plus generated scraper files

Cloudflare should deploy `generated-data`.

Generated files live only on `generated-data`:

- `data/scraper.json`
- `static/data.json`
- `static/img/*`

Do not commit `public/`.

## Pi Setup

The Pi is reachable locally as SSH alias `pihole`.

It already has this cron:

```cron
0 4 */1 * * /home/ned/update.sh >>/var/log/update-service.log 2>&1
```

`/home/ned/update.sh` currently updates Pi-hole and Tailscale. Extend this script to also refresh the website data.

Current Pi gaps to handle before enabling:

- clone repo to `/home/ned/website`
- install `uv`
- add GitHub push credentials for `generated-data`
- add GitHub host key to `known_hosts`
- copy/symlink `scripts/pi/website-refresh.sh` to `/home/ned/website-refresh.sh`

## Daily Flow

`pihole` runs once per day at 04:00 local time:

1. `/home/ned/update.sh` updates Pi-hole.
2. `/home/ned/update.sh` updates Tailscale.
3. `/home/ned/update.sh` runs the website refresh script.
4. Website script fetches latest `master`.
5. It checks out `generated-data`.
6. It resets `generated-data` to `master`.
7. It restores existing `static/img` cache.
8. It runs the scraper.
9. It validates JSON and referenced images.
10. It commits generated files.
11. It force-pushes `generated-data`.
12. A lightweight GitHub Action run on `generated-data` calls the Cloudflare deploy hook.
13. Cloudflare builds `generated-data`.

Keep website logic in its own script, for example:

```bash
/home/ned/website-refresh.sh
```

Then call that from `/home/ned/update.sh`. This keeps the cron simple while keeping website logic separate.

Add clear comments to both scripts. Future me should be able to understand:

- why `generated-data` exists
- why `master` is reset into it
- why `static/img` is preserved as a cache
- why the branch is force-pushed
- why validation happens before commit/push

## Push Flow

Avoid polling.

Use a small GitHub Action plus Tailscale:

1. Push to `master`.
2. GitHub Action starts.
3. The action joins the tailnet as an ephemeral tagged node.
4. The action uses normal SSH over the tailnet to the Pi (`pi-cph`).
5. `pihole` runs the same generated-data refresh script.
6. `pihole` force-pushes `generated-data`.
7. A lightweight GitHub Action run on `generated-data` calls the Cloudflare deploy hook.
8. Cloudflare builds `generated-data`.

This gives push deploys without polling, without a self-hosted runner, and without exposing the Pi to the internet.

Use Tailscale ACLs so the GitHub Action can only reach `pihole` on TCP 22.
The Pi authorized key is command-restricted to `/home/ned/website-refresh.sh`.

GitHub repo secrets needed:

- `TS_OAUTH_CLIENT_ID`
- `TS_OAUTH_SECRET`
- `PI_SSH_PRIVATE_KEY`
- `DEPLOY_HOOK`

Tailnet setup needed:

- OAuth client can create nodes tagged `tag:github-actions`
- Network ACL allows `tag:github-actions` to reach `100.120.84.116:22`

## Supabase

Remove Supabase from the scraper.

It is only being used as an image cache. The Pi disk plus Git branch is simpler:

- local cache is faster
- fewer network calls
- fewer moving parts
- no broken Supabase downloads

## Scraper Improvements

- Reuse local images when valid.
- Download only missing images.
- Write files atomically with `.part` then rename.
- Add timeouts and `raise_for_status()`.
- Validate every referenced image exists and is non-zero.
- Keep previous good data on source failure.
- Use a GitHub token so GitHub projects do not disappear.
- Fail before commit if output is invalid.

## Build Changes

Cloudflare build should only build the site:

```bash
hugo -b https://edoardo.fyi/ --minify --gc
npx torchlight
```

No scraping. No image downloading. No WebP binary download.

## Phase 1 Repo Changes

- `scraper.py` uses local `static/img` cache.
- Supabase is removed from the scraper path.
- Python dependencies use `uv` with `pyproject.toml` and `uv.lock`.
- `scripts/scrape.sh` runs scraper plus validation.
- `scripts/validate-scraper-output.py` blocks missing or zero-byte images.
- `scripts/refresh-generated-data.sh` rebuilds and pushes `generated-data`.
- `.github/workflows/deploy.yml` triggers Pi refresh on pushes to `master`.
- `scripts/pi/website-refresh.sh` is the Pi-side entrypoint.
- GitHub Action uses Tailscale plus command-restricted SSH to reach the Pi.
- `build.sh` only runs Hugo and Torchlight.
- `requirements.txt` was removed so Cloudflare does not install Python dependencies.

## Current Follow-Up

- Source changes are committed on `master`.
- The Pi refresh path reaches the Pi and completes scraping/validation.
- `scripts/refresh-generated-data.sh` configures its own Git author so cron/SSH runs can commit without machine-global Git setup.
- Cloudflare did not auto-build from the branch push, so the workflow calls the existing `DEPLOY_HOOK` whenever `generated-data` is pushed.
- The hook is accepted by Cloudflare, but live `data.json` is still old.
- The workflow now fails if `https://edoardo.fyi/data.json` does not match `generated-data` within 10 minutes.
- Current evidence: `generated-data` has 6 GitHub projects, live `edoardo.fyi` has 0, and `edoardo.pages.dev` only serves `a`.
- Check that the domain, Pages project, production branch, and deploy hook all point to the same `generated-data` project.

## Expected Result

- Daily updates still happen.
- Push updates still happen.
- `master` stays clean.
- `data.json` URL stays the same.
- Movie covers are cached heavily.
- Deploys are much faster.
- Broken images fail before deploy.
