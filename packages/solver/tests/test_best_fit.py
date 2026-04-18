"""End-to-end solver tests mirroring the Part B feasibility study."""
from firecore_rules import load_jurisdiction
from firecore_rules.types import Site
from firecore_sku import load_sku
from firecore_solver import FitOutcome, best_fit


def _site(**overrides) -> Site:
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


def _setup():
    return load_sku("firecore_1200"), load_jurisdiction("la_city_adu")


def test_standard_r1_is_exact_fit():
    sku, j = _setup()
    r = best_fit(sku, j, _site())
    assert r.outcome == FitOutcome.EXACT
    assert r.variant.id == "std_1story"


def test_flood_ae_is_minor_fit_with_raised_pier():
    sku, j = _setup()
    r = best_fit(sku, j, _site(flood_zone="AE", bfe_ft=8))
    assert r.outcome == FitOutcome.MINOR
    assert r.variant.foundation == "raised_pier"


def test_steep_slope_is_major_without_allow_future_cert():
    sku, j = _setup()
    r = best_fit(sku, j, _site(slope_pct=22))
    assert r.outcome == FitOutcome.MAJOR
    assert r.variant.foundation == "stepped_pier"


def test_steep_slope_with_allow_future_cert_is_minor():
    sku, j = _setup()
    r = best_fit(sku, j, _site(slope_pct=22), allow_future_cert=True)
    assert r.outcome == FitOutcome.MINOR
    assert r.variant.foundation == "stepped_pier"


def test_dense_urban_forces_2story_compact():
    sku, j = _setup()
    # 50x100 lot, 60% existing coverage, transit present — forces compact 2-story
    r = best_fit(sku, j, _site(
        lot_sqft=5000, lot_width_ft=50, lot_depth_ft=100,
        existing_coverage_pct=35, max_coverage_pct=50,
        transit_half_mi=True,
    ))
    # std is 30x40=1200sqft; dense lot should still fit std by footprint only if coverage allows.
    # Here 35% + 24% = 59% > 50% cap → std fails, compact (24*25=600sqft ≈ 12%) fits.
    assert r.outcome == FitOutcome.MINOR
    assert r.variant.id == "compact_2story"
