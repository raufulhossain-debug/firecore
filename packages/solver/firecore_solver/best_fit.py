"""Find the best-fit SKU variant for a site against a jurisdiction's rules.

Strategy:
    For each variant of the SKU that can legally be considered (i.e. its
    certification status >= certified, unless allow_future_cert=True), build a
    ProposedBuild, run the rules evaluator, and score the outcome. Return the
    best variant + its evaluation report.

Outcomes:
    EXACT  — std_1story variant passes all blocking rules
    MINOR  — a non-default in-envelope variant passes all blocking rules
    MAJOR  — only a future-cert variant passes (slope envelope expansion)
    NO_FIT — no variant passes
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel

from firecore_rules import evaluate
from firecore_rules.types import EvaluationReport, ProposedBuild, Site, Jurisdiction
from firecore_sku.types import Sku, SkuVariant


class FitOutcome(str, Enum):
    EXACT = "EXACT"
    MINOR = "MINOR"
    MAJOR = "MAJOR"
    NO_FIT = "NO_FIT"


class FitReport(BaseModel):
    outcome: FitOutcome
    variant: Optional[SkuVariant] = None
    rationale: str
    evaluation: Optional[EvaluationReport] = None


def _variant_to_build(v: SkuVariant) -> ProposedBuild:
    return ProposedBuild(
        footprint_w_ft=v.footprint_w_ft,
        footprint_d_ft=v.footprint_d_ft,
        stories=v.stories,
        height_ft=v.height_ft,
        foundation=v.foundation,
        conditioned_sqft=v.conditioned_sqft,
    )


def _is_future_cert(sku: Sku, variant: SkuVariant) -> bool:
    """Heuristic: stepped-pier variants are marked planned in firecore_1200."""
    return variant.foundation == "stepped_pier"


def best_fit(
    sku: Sku,
    jurisdiction: Jurisdiction,
    site: Site,
    *,
    allow_future_cert: bool = False,
) -> FitReport:
    candidates: list[tuple[SkuVariant, EvaluationReport]] = []
    for v in sku.variants:
        if _is_future_cert(sku, v) and not allow_future_cert:
            continue
        rep = evaluate(jurisdiction, site, _variant_to_build(v))
        candidates.append((v, rep))

    # Prefer passing variants; among passing, prefer the default ("std_1story")
    passing = [(v, r) for v, r in candidates if r.passed]
    if passing:
        default = next(
            ((v, r) for v, r in passing if v.id.startswith("std_")),
            None,
        )
        if default:
            v, r = default
            return FitReport(
                outcome=FitOutcome.EXACT,
                variant=v,
                rationale="Standard variant passes all blocking rules.",
                evaluation=r,
            )
        v, r = passing[0]
        return FitReport(
            outcome=FitOutcome.MINOR,
            variant=v,
            rationale=f"In-envelope variant '{v.name}' required.",
            evaluation=r,
        )

    # Nothing passed among currently-certified variants; try future-cert
    if not allow_future_cert:
        future = best_fit(sku, jurisdiction, site, allow_future_cert=True)
        if future.outcome != FitOutcome.NO_FIT:
            return FitReport(
                outcome=FitOutcome.MAJOR,
                variant=future.variant,
                rationale=(
                    f"Fit requires future-cert variant '{future.variant.name}'. "
                    f"File this cert to close the gap."
                ),
                evaluation=future.evaluation,
            )

    best = candidates[0] if candidates else None
    if best is None:
        return FitReport(outcome=FitOutcome.NO_FIT, rationale="No variants available.")
    v, r = best
    failed = "; ".join(x.message for x in r.blocking_failures)
    return FitReport(
        outcome=FitOutcome.NO_FIT,
        variant=v,
        rationale=f"No variant fits. Binding failures: {failed}",
        evaluation=r,
    )
