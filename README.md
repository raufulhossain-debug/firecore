# FireCore

**Climate-resilient prefab housing — IP licensing platform.**

FireCore is an early-stage platform that licenses pre-certified, climate-resilient
prefab housing SKUs (starting with wildfire-resilient ADUs) to modular factories
and developers, delivered via a parametric configurator that generates
permit-ready plan sets scoped to a buyer's specific parcel.

> **Status:** pre-seed scaffold. This repo contains the architecture docs, a
> working rules engine, SKU library, site intelligence clients, a parametric
> solver, an API skeleton, and two demo front-ends (static HTML + Streamlit).
> It is NOT a product yet. See `docs/architecture.md` for the full plan.

---

## Repo layout

```
firecore/
├── docs/                           # Architecture, feasibility study, ADRs
├── packages/
│   ├── rules_engine/               # Zoning/code rules as YAML + evaluator (Py)
│   ├── sku_library/                # Certified SKU definitions as YAML (Py)
│   ├── site_intel/                 # FEMA/CalFire/USGS parcel-data clients (Py)
│   ├── solver/                     # Parametric fit engine (Py)
│   ├── api/                        # FastAPI service wiring the above (Py)
│   └── web/                        # Next.js front-end (placeholder)
├── prototypes/
│   ├── static_html_demo/           # Single-file Mapbox HTML demo (pitchable)
│   └── streamlit_demo/             # Internal feasibility tool
└── .github/                        # CI, CODEOWNERS, PR template
```

## Quickstart

Requires Python 3.11+.

```bash
# Create a venv
python3 -m venv .venv
source .venv/bin/activate

# Install all Python packages in editable/dev mode
pip install -e "packages/rules_engine[dev]"
pip install -e "packages/sku_library[dev]"
pip install -e "packages/site_intel[dev]"
pip install -e "packages/solver[dev]"
pip install -e "packages/api[dev]"

# Run tests
pytest

# Run the API
uvicorn firecore_api.main:app --reload
# -> http://localhost:8000/docs

# Try the static HTML demo (no install needed)
open prototypes/static_html_demo/index.html
```

## The rules engine in one paragraph

Zoning and code rules are **data, not code** (`packages/rules_engine/firecore_rules/jurisdictions/*.yaml`).
The evaluator is small (`evaluator.py`) and runs every rule as a pure function
over a `Site` object. This keeps rule authoring in the hands of code consultants
and rule review a YAML diff in a PR, not a software change. See `docs/decisions/0002-rules-as-data.md`.

## License & IP

All rights reserved. Internal use only. See `LICENSE.md`.

## Docs

- [`docs/architecture.md`](docs/architecture.md) — Technical architecture + build plan
- [`docs/feasibility-study.md`](docs/feasibility-study.md) — 20-parcel LA SKU fit study
- [`docs/decisions/`](docs/decisions/) — Architecture Decision Records (ADRs)
