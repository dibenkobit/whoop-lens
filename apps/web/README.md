# whoop-lens-web

Next.js 16 frontend for [Whoop Lens](https://whooplens.app). Consumes the
FastAPI backend in `../api`.

## Dev

```bash
bun install
cp .env.local.example .env.local  # edit if your API runs on a non-default port
bun run dev
```

Make sure the backend is running on `http://localhost:8000` first.

## Test

```bash
bun run test
bun run typecheck
bun run lint
bun run build
```

## Deploy (Vercel)

1. Connect this repo to Vercel
2. Root directory = `apps/web`
3. Framework preset = Next.js (auto-detected)
4. Environment variables:
   - `NEXT_PUBLIC_API_URL=https://api.whooplens.app`
5. Deploy. PR previews are automatic.
