"""Pure-function rule evaluator.

Each rule `type` maps to a small pure function. The evaluator loads a
jurisdiction's rules, runs them against (site, build), and returns an
EvaluationReport.

To add a new rule *type*:
    1. Add the Literal to Rule.type in types.py
    2. Add a handler below
    3. Register in the RULE_HANDLERS dict

To add a new *rule* in an existing type:
    Just add the YAML entry — no code change required.
"""
from __future__ import annotations

from typing import Callable

from firecore_rules.types import (
    EvaluationReport,
    ProposedBuild,
    Rule,
    RuleResult,
    Site,
    Jurisdiction,
)


RuleHandler = Callable[[Rule, Site, ProposedBuild], RuleResult]


def _ok(rule: Rule, msg: str) -> RuleResult:
    return RuleResult(rule_id=rule.id, passed=True,  severity=rule.severity, message=msg)


def _fail(rule: Rule, msg: str) -> RuleResult:
    return RuleResult(rule_id=rule.id, passed=False, severity=rule.severity, message=msg)


# --- Handlers -----------------------------------------------------------------

def _h_max_adu_size(rule: Rule, site: Site, build: ProposedBuild) -> RuleResult:
    max_sqft = rule.params["max_sqft"]
    if build.conditioned_sqft <= max_sqft:
        return _ok(rule, f"{build.conditioned_sqft} ≤ {max_sqft} sqft cap")
    return _fail(rule, f"{build.conditioned_sqft} > {max_sqft} sqft cap")


def _h_setback(rule: Rule, site: Site, build: ProposedBuild) -> RuleResult:
    """Ensures site's setbacks are at least the rule's minimums."""
    req = rule.params
    issues = []
    for side in ("front", "side", "rear"):
        key = f"setback_{side}_ft"
        if getattr(site, key) < req.get(side, 0):
            issues.append(f"{side} {getattr(site, key)} < required {req[side]}")
    if issues:
        return _fail(rule, "; ".join(issues))
    return _ok(rule, "setbacks meet minimums")


def _h_max_height(rule: Rule, site: Site, build: ProposedBuild) -> RuleResult:
    base = rule.params.get("base_ft", 16)
    transit_bonus = rule.params.get("transit_bonus_ft", 0)
    limit = base + (transit_bonus if site.transit_half_mi else 0)
    if build.height_ft <= limit:
        return _ok(rule, f"{build.height_ft} ft ≤ {limit} ft (transit={site.transit_half_mi})")
    return _fail(rule, f"{build.height_ft} ft > {limit} ft")


def _h_max_coverage(rule: Rule, site: Site, build: ProposedBuild) -> RuleResult:
    added = (build.footprint_w_ft * build.footprint_d_ft) / site.lot_sqft * 100
    total = site.existing_coverage_pct + added
    cap = min(site.max_coverage_pct, rule.params.get("cap_pct", 100))
    if total <= cap:
        return _ok(rule, f"existing {site.existing_coverage_pct:.0f}% + added {added:.1f}% = {total:.1f}% ≤ {cap}%")
    return _fail(rule, f"{total:.1f}% > {cap}% cap")


def _h_fire_wui(rule: Rule, site: Site, build: ProposedBuild) -> RuleResult:
    required_fhsz_levels = rule.params.get("requires_chapter_7a_in", ["High", "VHFHSZ"])
    if site.fhsz in required_fhsz_levels:
        return _ok(rule, f"FHSZ {site.fhsz}: Chapter 7A package required (SKU provides)")
    return _ok(rule, f"FHSZ {site.fhsz}: no WUI hardening required")


def _h_flood(rule: Rule, site: Site, build: ProposedBuild) -> RuleResult:
    sfha = site.flood_zone in {"A", "AE", "VE"}
    if not sfha:
        return _ok(rule, "outside SFHA")
    required_foundations = rule.params.get("allowed_foundations_in_sfha", ["raised_pier"])
    freeboard_ft = rule.params.get("freeboard_ft", 1.0)
    if build.foundation in required_foundations:
        return _ok(
            rule,
            f"SFHA {site.flood_zone} (BFE {site.bfe_ft}); "
            f"{build.foundation} with {freeboard_ft} ft freeboard satisfies",
        )
    return _fail(
        rule,
        f"SFHA {site.flood_zone} requires one of {required_foundations}; "
        f"build uses {build.foundation}",
    )


def _h_slope(rule: Rule, site: Site, build: ProposedBuild) -> RuleResult:
    tol_slab = rule.params.get("slab_max_pct", 15)
    tol_stepped = rule.params.get("stepped_pier_max_pct", 40)
    if build.foundation == "stepped_pier":
        limit = tol_stepped
    else:
        limit = tol_slab
    if site.slope_pct <= limit:
        return _ok(rule, f"slope {site.slope_pct:.1f}% ≤ {limit}% ({build.foundation})")
    return _fail(rule, f"slope {site.slope_pct:.1f}% > {limit}% ({build.foundation})")


def _h_min_lot_size(rule: Rule, site: Site, build: ProposedBuild) -> RuleResult:
    min_sqft = rule.params.get("min_sqft", 0)
    if site.lot_sqft >= min_sqft:
        return _ok(rule, f"lot {site.lot_sqft} ≥ {min_sqft}")
    return _fail(rule, f"lot {site.lot_sqft} < {min_sqft}")


def _h_transit_proximity_bonus(rule: Rule, site: Site, build: ProposedBuild) -> RuleResult:
    # Informational only; other rules read site.transit_half_mi
    msg = "within ½-mi major transit" if site.transit_half_mi else "not within ½-mi major transit"
    return _ok(rule, msg)


RULE_HANDLERS: dict[str, RuleHandler] = {
    "min_lot_size": _h_min_lot_size,
    "max_adu_size": _h_max_adu_size,
    "setback": _h_setback,
    "max_height": _h_max_height,
    "max_coverage": _h_max_coverage,
    "fire_wui_compliance": _h_fire_wui,
    "flood_compliance": _h_flood,
    "slope_tolerance": _h_slope,
    "transit_proximity_bonus": _h_transit_proximity_bonus,
}


def evaluate(jurisdiction: Jurisdiction, site: Site, build: ProposedBuild) -> EvaluationReport:
    results: list[RuleResult] = []
    for rule in jurisdiction.rules:
        handler = RULE_HANDLERS.get(rule.type)
        if handler is None:
            results.append(
                RuleResult(
                    rule_id=rule.id,
                    passed=False,
                    severity="blocking",
                    message=f"No handler for rule type '{rule.type}' — check evaluator registration",
                )
            )
            continue
        results.append(handler(rule, site, build))
    return EvaluationReport(
        jurisdiction_id=jurisdiction.id, site=site, build=build, results=results
    )
