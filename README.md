# KDP Deutschland Data Mining

German-language Amazon KDP niche intelligence pipeline for demand, saturation, competitor, BSR, review, and Sachbuch opportunity analysis.

## Services

- `backend`: FastAPI API and persistence layer
- `worker`: Celery worker for asynchronous collection and analysis jobs
- `scheduler`: Celery Beat schedule for recurring search-run and BSR refreshes
- `frontend`: Next.js dashboard shell
- `postgres`: PostgreSQL database
- `redis`: Redis cache and queue broker
- `nginx` (`prod` profile): reverse proxy, TLS termination, and rate limiting
- `certbot` (`prod` profile): Let's Encrypt renewal worker
- `uptime-kuma` (`monitoring` profile): external uptime monitor

## Desktop runtime

Authenticated Amazon.de collection is intended to run on your desktop, not as a cloud-only worker. The backend and frontend stay in Docker, while collection uses your logged-in local Chrome session through the host bridge.

## Quick start

1. Copy `.env.example` to `.env`.
2. Start Chrome with remote debugging enabled on port `9222` using the profile that is already logged in to Amazon.
3. Run the desktop launcher:

```powershell
.\scripts\start_desktop_stack.ps1 -Build
```

4. Open `http://localhost:3000` for the dashboard.
5. Open `http://localhost:8000/docs` for the API.

If Docker is already running and you only need the host bridge:

```powershell
.\scripts\start_chrome_bridge.ps1
```

The dashboard now exposes `GET /api/v1/health/runtime` so you can confirm whether the local Chrome bridge is actually reachable.

## Production stack

Production services can still be deployed for storage, reporting, and monitoring, but authenticated Amazon browsing should remain desktop-local.

Run the production edge services with:

```bash
APP_ENV=production
docker compose --profile prod up -d --build
```

Issue the first certificate on the VPS with:

```bash
./ops/certbot/init-letsencrypt.sh your-domain.example admin@example.com
```

Optional monitoring stack:

```bash
docker compose --profile monitoring up -d uptime-kuma
```

## Operations

- Docker log rotation is enabled in `docker-compose.yml` with `json-file` limits.
- Daily backup script: `./ops/backup/backup.sh`
- UFW bootstrap: `./ops/ufw/setup.sh`
- Fail2ban jail template: `./ops/fail2ban/jail.local`
- Host logrotate policy: `./ops/logrotate/kdp-deutschland`
- Sentry is enabled automatically when `SENTRY_DSN` or `NEXT_PUBLIC_SENTRY_DSN` is set.

## Current scope

The repository currently includes:

- seed keyword intake, expansion, enrichment, and clustering
- recurring search-run and BSR time-series collection
- competitor intelligence and Sachbuch blueprint analysis
- GO/MAYBE/NO-GO opportunity scoring
- Markdown, PDF, CSV, and JSON report generation and download
- local and production Docker orchestration with monitoring and backup scaffolding
