# packages/web — Next.js front-end (placeholder)

The production front-end is intentionally **not scaffolded in this commit**.
Once a front-end engineer is onboarded, initialize with:

```bash
cd packages/web
pnpm create next-app@latest . --ts --tailwind --app --eslint --src-dir --import-alias "@/*"
pnpm add mapbox-gl @turf/turf
```

Until then, see `prototypes/static_html_demo/` for a portable pitch-ready demo
that talks to the same API contract (POST `/evaluate`).
