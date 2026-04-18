## Summary

<!-- What does this PR change and why? -->

## Type

- [ ] Feature
- [ ] Bug fix
- [ ] Rules change (jurisdiction YAML)
- [ ] SKU change (certification-affecting)
- [ ] Docs / ADR
- [ ] Refactor / chore

## Rule or SKU changes

If this PR touches `packages/rules_engine/firecore_rules/jurisdictions/*.yaml`
or `packages/sku_library/firecore_sku/skus/*.yaml`, confirm:

- [ ] Cites the governing code section / certification document
- [ ] Reviewed by the correct CODEOWNER (code consultant / AOR / SEOR)
- [ ] Test added that exercises the rule with at least one pass and one fail
- [ ] `code_version` / SKU `certifications` field updated if applicable

## Testing

<!-- How was this validated? -->

## Risk

- [ ] Affects permit-ready output
- [ ] Affects royalty calculation
- [ ] Affects existing licensee deliverables
