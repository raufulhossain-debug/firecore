from fastapi.testclient import TestClient

from firecore_api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_jurisdictions_includes_la():
    r = client.get("/jurisdictions")
    assert r.status_code == 200
    assert "la_city_adu" in r.json()


def test_skus_includes_firecore():
    r = client.get("/skus")
    assert r.status_code == 200
    assert "firecore_1200" in r.json()


def test_evaluate_exact_fit():
    body = {
        "site": {
            "lot_sqft": 7200, "lot_width_ft": 60, "lot_depth_ft": 120,
            "zone_code": "R1", "max_coverage_pct": 45, "existing_coverage_pct": 20,
            "setback_front_ft": 20, "setback_side_ft": 5, "setback_rear_ft": 15,
            "transit_half_mi": True, "slope_pct": 3.0,
            "fhsz": "Non-HFHSZ", "flood_zone": "X",
        }
    }
    r = client.post("/evaluate", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["outcome"] == "EXACT"
