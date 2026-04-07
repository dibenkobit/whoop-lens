# whoop-lens-api

FastAPI backend for [Whoop Lens](https://whooplens.app). Accepts a Whoop data
export ZIP and returns a computed report. See `../docs/superpowers/specs/`.

## Dev

```bash
uv sync
uv run uvicorn app.main:app --reload
uv run pytest
```
