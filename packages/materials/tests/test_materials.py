"""Tests for the material catalog and climate selector."""

from firecore_materials import (
    load_material,
    list_materials,
    select_materials_for_climate,
)
from firecore_materials.types import ClimateZone


def test_list_materials_includes_big_3():
    mats = list_materials()
    assert "sip" in mats
    assert "clt" in mats
    assert "steel" in mats


def test_load_sip_has_variants():
    sip = load_material("sip")
    assert sip.name == "Structural Insulated Panels"
    assert len(sip.variants) >= 3
    assert sip.buy_america_compliant is True


def test_load_steel_is_noncombustible():
    steel = load_material("steel")
    wildfire = next(r for r in steel.climate_ratings if r.zone == ClimateZone.WILDFIRE)
    assert wildfire.score >= 0.9, "Steel should be top-rated for wildfire"


def test_clt_carbon_negative():
    clt = load_material("clt")
    assert clt.carbon_kg_per_sqft < 0, "CLT should be carbon-negative"


def test_best_variant_for_wildfire_is_steel():
    recs = select_materials_for_climate(fhsz="VHFHSZ")
    top = recs[0]
    assert top.material.id == "steel", f"Expected steel for wildfire, got {top.material.id}"
    assert not top.disqualified


def test_best_variant_for_standard_is_sip():
    recs = select_materials_for_climate(fhsz="Non-HFHSZ", flood_zone="X")
    top = recs[0]
    # SIP should score highest for standard (0.9) and be cheapest
    assert top.material.id == "sip", f"Expected SIP for standard, got {top.material.id}"


def test_flood_zone_disqualifies_low_scorers():
    recs = select_materials_for_climate(flood_zone="AE")
    for rec in recs:
        if rec.material.id == "clt":
            assert rec.disqualified, "CLT should be disqualified for flood zone AE"


def test_all_recommendations_have_variants():
    recs = select_materials_for_climate()
    for rec in recs:
        assert rec.variant is not None
        assert rec.cost_per_sqft > 0
        assert rec.lead_time_days > 0
