"""Offline tests — clients return None on failure and gracefully handle empty features."""
from unittest.mock import patch

from firecore_site.clients.fema import fetch_flood_zone
from firecore_site.clients.calfire import fetch_fhsz


class _Resp:
    def __init__(self, status, payload):
        self.status_code = status
        self._payload = payload
    def json(self):
        return self._payload


def test_fema_returns_none_on_http_error():
    with patch("firecore_site.clients.fema.requests.get", return_value=_Resp(500, {})):
        assert fetch_flood_zone(34.05, -118.25) is None


def test_fema_returns_x_on_empty_features():
    with patch("firecore_site.clients.fema.requests.get",
               return_value=_Resp(200, {"features": []})):
        r = fetch_flood_zone(34.05, -118.25)
        assert r is not None and r.zone == "X"


def test_fema_parses_ae_feature():
    payload = {"features": [{"attributes": {"FLD_ZONE": "AE", "STATIC_BFE": 8.0}}]}
    with patch("firecore_site.clients.fema.requests.get",
               return_value=_Resp(200, payload)):
        r = fetch_flood_zone(34.0, -118.4)
        assert r is not None
        assert r.zone == "AE"
        assert r.bfe_ft == 8.0


def test_calfire_parses_haz_code():
    payload = {"features": [{"attributes": {"HAZ_CODE": 3}}]}
    with patch("firecore_site.clients.calfire.requests.get",
               return_value=_Resp(200, payload)):
        r = fetch_fhsz(34.0, -118.5)
        assert r is not None and r.level == "VHFHSZ"


def test_calfire_handles_exception():
    with patch("firecore_site.clients.calfire.requests.get", side_effect=Exception("boom")):
        assert fetch_fhsz(34.0, -118.5) is None
