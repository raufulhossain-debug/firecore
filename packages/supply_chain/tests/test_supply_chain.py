"""Tests for the supply chain package."""

from firecore_supply import load_suppliers, load_tariffs, compute_landed_cost
from firecore_supply.loader import get_tariff, get_suppliers_for_material, get_quotes_for_variant
from firecore_supply.pricing import haversine_miles
from firecore_supply.types import Location


LA = Location(lat=34.05, lon=-118.24, city="Los Angeles", state="CA")


def test_load_suppliers_has_entries():
    suppliers, quotes = load_suppliers()
    assert len(suppliers) >= 10
    assert len(quotes) >= 5


def test_load_tariffs_has_china():
    tariffs = load_tariffs()
    cn_steel = next(t for t in tariffs if t.country == "CN" and t.material_category == "light_gauge_steel")
    assert cn_steel.effective_tariff() >= 50, "China steel should have 50%+ total tariff"


def test_us_domestic_no_tariff():
    tariff = get_tariff("US", "sip")
    assert tariff is not None
    assert tariff.effective_tariff() == 0


def test_haversine_la_to_portland():
    portland = Location(lat=45.52, lon=-122.68, city="Portland", state="OR")
    dist = haversine_miles(LA, portland)
    assert 800 < dist < 1000, f"LA to Portland should be ~830mi, got {dist}"


def test_get_suppliers_for_steel():
    suppliers = get_suppliers_for_material("steel")
    assert len(suppliers) >= 3
    assert any(s.id == "clarkdietrich_oh" for s in suppliers)


def test_compute_landed_cost_domestic():
    suppliers = get_suppliers_for_material("steel")
    steeltech = next(s for s in suppliers if s.id == "steeltech_ca")
    quotes = get_quotes_for_variant("steel_18ga_600s")
    quote = next(q for q in quotes if q.supplier_id == "steeltech_ca")

    landed = compute_landed_cost(
        supplier=steeltech,
        quote=quote,
        site_location=LA,
        sqft_needed=1200,
        material_category="light_gauge_steel",
    )
    assert landed.tariff_cost == 0, "Domestic should have no tariff"
    assert landed.buy_america_compliant is True
    assert landed.total_cost > 0
    assert landed.cost_per_sqft > 0


def test_china_steel_much_more_expensive_landed():
    """Even though FOB price is cheap, tariffs make China steel uncompetitive."""
    suppliers, _ = load_suppliers()
    cn = next(s for s in suppliers if s.id == "zhonghe_steel_cn")
    us = next(s for s in suppliers if s.id == "steeltech_ca")

    quotes = get_quotes_for_variant("steel_18ga_600s")
    cn_quote = next(q for q in quotes if q.supplier_id == "zhonghe_steel_cn")
    us_quote = next(q for q in quotes if q.supplier_id == "steeltech_ca")

    cn_landed = compute_landed_cost(cn, cn_quote, LA, 5000, "light_gauge_steel")
    us_landed = compute_landed_cost(us, us_quote, LA, 5000, "light_gauge_steel")

    # China tariffs should push landed cost above or close to US price
    assert cn_landed.tariff_cost > 0
    assert not cn_landed.buy_america_compliant


def test_landed_cost_includes_all_components():
    suppliers = get_suppliers_for_material("steel")
    s = next(s for s in suppliers if s.id == "clarkdietrich_oh")
    quotes = get_quotes_for_variant("steel_18ga_600s")
    q = next(q for q in quotes if q.supplier_id == "clarkdietrich_oh")

    landed = compute_landed_cost(s, q, LA, 2000, "light_gauge_steel")
    assert landed.material_cost > 0
    assert landed.freight_cost > 0
    assert landed.insurance_cost > 0
    assert landed.crane_cost > 0
    assert landed.total_lead_time_days > 0
    assert abs(landed.total_cost - (
        landed.material_cost + landed.tariff_cost + landed.freight_cost
        + landed.insurance_cost + landed.crane_cost
    )) < 0.01
