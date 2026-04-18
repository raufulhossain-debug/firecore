# ADR-0001 — Monorepo with multi-language packages

Date: 2026-04-15
Status: Accepted

## Context

The platform needs a Python backend (rules engine, solver, GIS clients, API)
and a TypeScript front-end (Next.js + Mapbox). We also need to share types
and rule definitions between server and client, and eventually emit factory
artifacts (cut files, BOMs) that may live in their own packages.

## Decision

Single monorepo. Python packages under `packages/` each with their own
`pyproject.toml`. Front-end under `packages/web/` (Next.js). Shared rule
definitions (YAML) are canonical in `packages/rules_engine/` and consumed by
the API; the front-end fetches them from the API rather than duplicating.

## Consequences

- One repo for all diligence, issue tracking, CI.
- Per-package `pyproject.toml` allows independent versioning if we ever
  extract the rules engine as an open-source SDK.
- We accept monorepo tooling complexity (CI matrices) in exchange for
  unified review across Python + TS.
