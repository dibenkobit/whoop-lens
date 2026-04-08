# whoop-lens-api

FastAPI backend for [Whoop Lens](https://whooplens.app). Accepts a Whoop data
export ZIP and returns a computed report. See `../docs/superpowers/specs/`.

## Dev

```bash
uv sync
uv run uvicorn app.main:app --reload
uv run pytest
```

## Deploy (Railway)

1. Connect this repo to Railway
2. Set Root Directory = `apps/api`
3. Add a Postgres add-on (sets `DATABASE_URL` automatically)
4. Set env vars:
   - `CORS_ORIGIN=https://whooplens.app`
   - `SHARE_TTL_DAYS=30`
   - `MAX_UPLOAD_MB=50`
   - `LOG_LEVEL=INFO`
5. Deploy. Health is at `/healthz`.

Builder is [Railpack](https://railpack.com) (set in `railway.toml`). It auto-detects
`uv.lock` and `.python-version` (3.13), so no extra build config is needed. The
start command in `railway.toml` runs `alembic upgrade head` before launching
`uvicorn`.

## Env vars

| Key | Default | Notes |
|---|---|---|
| `DATABASE_URL` | — | Required. Set by Railway Postgres add-on. |
| `CORS_ORIGIN` | `http://localhost:3000` | Comma-separated origins |
| `MAX_UPLOAD_MB` | 50 | |
| `SHARE_TTL_DAYS` | 30 | |
| `LOG_LEVEL` | INFO | |
