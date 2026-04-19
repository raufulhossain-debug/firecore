"""Tests for the logistics package."""

from firecore_logistics import load_factories, find_optimal_routes
from firecore_logistics.factories import get_factories_for_material, get_nearest_factory


# LA site coordinates
LA_LAT, LA_LON = 34.05, -118.24


def test_load_factories():
    factories = load_factories()
    assert len(factories) >= 5
    assert any(f.id == "factory_socal" for f in factories)


def test_factories_for_steel():
    factories = get_factories_for_material("steel")
    assert len(factories) >= 2
    ids = [f.id for f in factories]
    assert "factory_socal" in ids


def test_nearest_factory_to_la_for_steel():
    f = get_nearest_factory("steel", LA_LAT, LA_LON)
    assert f is not None
    assert f.id == "factory_socal", f"Expected SoCal factory, got {f.id}"


def test_find_routes_for_steel():
    routes = find_optimal_routes(
        material_id="steel",
        variant_id="steel_18ga_600s",
        site_lat=LA_LAT,
        site_lon=LA_LON,
        sqft_needed=1200,
    )
    assert len(routes) >= 1
    # Should be ranked by cost
    for i in range(len(routes) - 1):
        assert routes[i].total_cost <= routes[i + 1].total_cost
    # Top option should have rank 1
    assert routes[0].rank == 1


def test_route_has_legs():
    routes = find_optimal_routes(
        material_id="steel",
        variant_id="steel_18ga_600s",
        site_lat=LA_LAT,
        site_lon=LA_LON,
    )
    for route in routes:
        assert len(route.route.legs) >= 1
        for leg in route.route.legs:
            assert leg.distance_mi > 0
            assert leg.transit_days >= 0


def test_factory_route_has_two_legs():
    routes = find_optimal_routes(
        material_id="steel",
        variant_id="steel_18ga_600s",
        site_lat=LA_LAT,
        site_lon=LA_LON,
        max_results=20,
    )
    factory_routes = [r for r in routes if r.factory_id is not None]
    assert len(factory_routes) >= 1, "Should have at least one factory route"
    for fr in factory_routes:
        assert len(fr.route.legs) == 2, "Factory routes should have 2 legs"


def test_domestic_routes_are_buy_america():
    routes = find_optimal_routes(
        material_id="steel",
        variant_id="steel_18ga_600s",
        site_lat=LA_LAT,
        site_lon=LA_LON,
    )
    domestic = [r for r in routes if "cn" not in r.supplier_id]
    for r in domestic:
        assert r.buy_america is True
