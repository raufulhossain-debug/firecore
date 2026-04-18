# ADR-0002 — Zoning/code rules as data, not code

Date: 2026-04-15
Status: Accepted

## Context

The rules engine encodes municipal zoning and building code interpretations.
Rule changes happen often (code amendments, policy interpretations, new
jurisdictions). If rules are expressed as Python code, only engineers can
change them; rule review becomes a code review instead of a code-consultant
review, which is wrong for defensibility and for speed.

## Decision

Rules are authored as YAML files under
`packages/rules_engine/firecore_rules/jurisdictions/<jurisdiction>.yaml`.
The Python evaluator is a thin pure-function interpreter over the YAML.
Each rule cites the governing code section (e.g. `LAMC §12.22 A.33.c.6`)
and, where useful, links to the authoritative text.

## Consequences

- Code consultants can author and review rule changes directly.
- `CODEOWNERS` can route YAML diffs to the correct jurisdiction reviewer
  without pulling engineers in.
- Every rule decision is a git-blame-able commit tied to a PR with a
  reviewer — exactly what we need if a plans examiner questions a setback.
- We accept some expressiveness loss vs. writing rules in Python; where the
  YAML doesn't cover a case, we add a new rule `type` rather than drop into
  code.
