# Contributing

## Branching

Trunk-based. Short-lived feature branches off `main`. No git-flow.

Branch names: `type/short-desc` — e.g. `feat/la-adu-setback-rule`, `fix/flood-bfe-unit`, `rules/san-jose-adu-v1`.

## Commits

Conventional Commits preferred but not enforced:

```
feat(rules): add LA ADU maximum height rule for transit-proximate lots
fix(solver): coverage gate off-by-one when existing_coverage_pct == 0
docs(adr): add ADR-0004 on certification registry schema
```

## Code review

- Every PR needs one reviewer approval.
- PRs touching `packages/rules_engine/firecore_rules/jurisdictions/*.yaml` require
  the jurisdiction's designated code consultant (see `.github/CODEOWNERS`).
- PRs touching `packages/sku_library/firecore_sku/skus/*.yaml` require the
  architect-of-record and structural engineer-of-record.

## Testing

```bash
pytest
```

All rule-engine PRs must include a test that exercises the rule with at least
one passing and one failing site. SKU PRs must include a fit test against the
20-parcel feasibility fixture.

## The rules DSL

Rules live in YAML. See `packages/rules_engine/firecore_rules/jurisdictions/la_city_adu.yaml`
for the reference. Rule authors should cite the exact municipal code section
and, where possible, link to the authoritative text. If the code is ambiguous,
add a comment and route the PR to the code consultant.
