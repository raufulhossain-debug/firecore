"""Tests for the multi-objective optimizer."""

from firecore_optimizer import optimize_supply_chain, OptimizationWeights


LA_LAT, LA_LON = 34.05, -118.24


def test_optimize_returns_results():
    results = optimize_supply_chain(
        site_lat=LA_LAT, site_lon=LA_LON, sqft_needed=1200,
    )
    assert len(results) >= 1
    assert results[0].rank == 1
    assert results[0].score_total > 0


def test_results_are_ranked_by_score():
    results = optimize_supply_chain(
        site_lat=LA_LAT, site_lon=LA_LON,
    )
    for i in range(len(results) - 1):
        assert results[i].score_total >= results[i + 1].score_total


def test_pure_cost_weights_favor_cheapest():
    cost_weights = OptimizationWeights(cost=1, speed=0, carbon=0, compliance=0)
    results = optimize_supply_chain(
        site_lat=LA_LAT, site_lon=LA_LON,
        weights=cost_weights,
    )
    if len(results) >= 2:
        assert results[0].total_cost <= results[1].total_cost


def test_pure_speed_weights_favor_fastest():
    speed_weights = OptimizationWeights(cost=0, speed=1, carbon=0, compliance=0)
    results = optimize_supply_chain(
        site_lat=LA_LAT, site_lon=LA_LON,
        weights=speed_weights,
    )
    if len(results) >= 2:
        assert results[0].total_days <= results[1].total_days


def test_wildfire_zone_prefers_steel():
    results = optimize_supply_chain(
        site_lat=LA_LAT, site_lon=LA_LON,
        fhsz="VHFHSZ",
    )
    top_3_materials = [r.material_id for r in results[:3]]
    assert "steel" in top_3_materials, f"Steel should be in top 3 for wildfire, got {top_3_materials}"


def test_all_results_have_scores():
    results = optimize_supply_chain(
        site_lat=LA_LAT, site_lon=LA_LON,
    )
    for r in results:
        assert 0 <= r.score_cost <= 100
        assert 0 <= r.score_speed <= 100
        assert 0 <= r.score_carbon <= 100
        assert 0 <= r.score_compliance <= 100
        assert r.score_total > 0
        assert r.material_name != ""
        assert r.supplier_name != ""


def test_buy_america_flagged_correctly():
    results = optimize_supply_chain(
        site_lat=LA_LAT, site_lon=LA_LON,
        max_results=20,
    )
    for r in results:
        if "cn" in r.supplier_id:
            assert r.buy_america is False
