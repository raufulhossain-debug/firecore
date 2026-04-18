# Static HTML demo

A single-file `index.html` — open it in any browser. No backend, no install.

This is the **pitch-ready** artifact:
- Leaflet + OpenStreetMap tiles (no API key)
- Client-side mirror of the rules engine & solver (for portability only;
  production uses the Python packages via `/evaluate` API)
- 9 LA preset parcels drawn from the Part B feasibility study — click a pin
  and "Load preset" to see a realistic hazard profile

## To show it

```bash
open prototypes/static_html_demo/index.html
# or drag the file into a browser window
```

## What to demo

1. Default view loads a Standard 1-story **EXACT FIT**.
2. Click the Mandeville Canyon pin → **MAJOR FIT** (slope >20%).
3. Check "Include future stepped-pier cert" → becomes **MINOR FIT**.
4. Click Venice → **MINOR FIT** with raised-pier (flood AE).
5. Click Mid-City → **MINOR FIT** with compact 2-story (coverage-tight).

## Keeping in sync with Python

The JS rules mirror `packages/rules_engine/evaluator.py`. If you change Python
rules, update the JS stanza too (or delete the static demo once the real
Next.js front-end consumes `/evaluate` directly).
