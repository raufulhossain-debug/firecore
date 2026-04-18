# ADR-0003 — Python backend, TypeScript/Next.js front-end

Date: 2026-04-15
Status: Accepted

## Context

The backend needs rich GIS (Shapely, PostGIS), future CAD interchange
(Rhino Compute, Speckle), and fast iteration on the rules engine. Python
is the clear fit. The front-end needs Mapbox GL, interactive parcel UX,
and a production-grade look. Next.js + TypeScript is the clear fit.

We considered Streamlit for the entire front-end (see
`prototypes/streamlit_demo/`). It's excellent for internal tools but wrong
for a homeowner-facing configurator: no real Mapbox integration, limited
UX control, and it signals "data-science toy" to investors and partners.

## Decision

- **Backend:** Python 3.11+, FastAPI, Pydantic, Shapely, PostGIS (later).
- **Front-end:** Next.js 14+ (App Router), TypeScript, Tailwind, Mapbox GL.
- **Internal tools (Streamlit):** fine for our own feasibility spot-checks;
  never shown to partners or homeowners.

## Consequences

- Two languages; CI runs both matrices.
- Rules YAML is canonical in Python package; front-end consumes via API.
- Static HTML demo (`prototypes/static_html_demo/`) exists as a portable
  pitch artifact that can run without backend — useful for investor meetings
  on planes.
