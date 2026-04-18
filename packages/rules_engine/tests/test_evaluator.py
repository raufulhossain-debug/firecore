"""Tests for the LA ADU rules evaluator."""
from firecore_rules import evaluate, load_jurisdiction
from firecore_rules.types import ProposedBuild, Site


def _la_standard_site(**overrides) -> Site:
    base = dict(
        lot_sqft=7200, lot_width_ft=60, lot_depth_ft=120,
        zone_code="R1", max_coverage_pct=45, existing_coverage_pct=20,
        height_limit_ft=33,
        setback_front_ft=20, setback_side_ft=5, setback_rear_ft=15,
        transit_half_mi=True, slope_pct=3.0,
        fhsz="Non-HFHSZ", flood_zone="X",
    )
    base.update(overrides)
    return Site(**base)


def _firecore_standard_build() -> ProposedBuild:
    return ProposedBuild(
        footprint_w_ft=30, footprint_d_ft=40, stories=1,
        height_ft=16, foundation="slab", conditioned_sqft=1200,
    )


def _firecore_raised_pier() -> ProposedBuild:
    return _firecore_standard_build().model_copy(
        update={"foundation": "raised_pier", "height_ft": 22}
    )


def _firecore_stepped_pier() -> ProposedBuild:
    return _firecore_standard_build().model_copy(
        update={"foundation": "stepped_pier", "height_ft": 18}
    )


def test_standard_r1_lot_passes():
    j = load_jurisdiction("la_city_adu")
    report = evaluate(j, _la_standard_site(), _firecore_standard_build())
    assert report.passed, [r.message for r in report.blocking_failures]


def test_vhfhsz_still_passes_with_chapter_7a():
    j = load_jurisdiction("la_city_adu")
    site = _la_standard_site(fhsz="VHFHSZ")
    report = evaluate(j, site, _firecore_standard_build())
    assert report.passed


def test_flood_zone_ae_requires_raised_pier():
    j = load_jurisdiction("la_city_adu")
    site = _la_standard_site(flood_zone="AE", bfe_ft=8)
    slab_report = evaluate(j, site, _firecore_standard_build())
    assert not slab_report.passed, "slab should fail in SFHA AE"

    pier_report = evaluate(j, site, _firecore_raised_pier())
    assert pier_report.passed, "raised-pier should pass in SFHA AE"


def test_steep_slope_needs_stepped_pier():
    j = load_jurisdiction("la_city_adu")
    site = _la_standard_site(slope_pct=22)
    slab_report = evaluate(j, site, _firecore_standard_build())
    assert not slab_report.passed, "slab should fail on >15% slope"

    stepped_report = evaluate(j, site, _firecore_stepped_pier())
    assert stepped_report.passed, "stepped-pier should pass on 22% slope"


def test_coverage_cap_enforced():
    j = load_jurisdiction("la_city_adu")
    site = _la_standard_site(existing_coverage_pct=40)  # 40 + ~16.7 = 56.7 > 45
    report = evaluate(j, site, _firecore_standard_build())
    assert not report.passed


def test_2story_requires_transit_or_lower_height():
    j = load_jurisdiction("la_city_adu")
    two_story = ProposedBuild(
        footprint_w_ft=24, footprint_d_ft=25, stories=2,
        height_ft=25, foundation="slab", conditioned_sqft=1200,
    )
    # With transit — passes
    assert evaluate(j, _la_standard_site(), two_story).passed

    # Without transit — 25 ft > 16 ft base → fails height rule
    no_transit = _la_standard_site(transit_half_mi=False)
    assert not evaluate(j, no_transit, two_story).passed


def test_all_rule_types_have_handlers():
    """No rule in any shipped jurisdiction may reference an unhandled type."""
    from firecore_rules.evaluator import RULE_HANDLERS
    from firecore_rules.loader import list_jurisdictions

    for jid in list_jurisdictions():
        j = load_jurisdiction(jid)
        for rule in j.rules:
            assert rule.type in RULE_HANDLERS, f"{jid}:{rule.id} uses unhandled type {rule.type}"
