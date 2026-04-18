from firecore_sku import list_skus, load_sku


def test_firecore_1200_loads():
    sku = load_sku("firecore_1200")
    assert sku.id == "firecore_1200"
    assert sku.climate_archetype == "wildfire"
    assert len(sku.variants) >= 3


def test_variant_lookup():
    sku = load_sku("firecore_1200")
    v = sku.variant("std_1story")
    assert v is not None
    assert v.conditioned_sqft == 1200
    assert v.foundation == "slab"


def test_list_skus_has_firecore():
    assert "firecore_1200" in list_skus()
