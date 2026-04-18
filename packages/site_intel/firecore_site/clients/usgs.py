"""USGS Seismic Design Maps client (stub).

Real API: https://earthquake.usgs.gov/ws/designmaps/
Returns None on failure so consumers can fall back to site_class="D" default.
"""
from __future__ import annotations
from typing import Optional

import requests
from pydantic import BaseModel


class UsgsSeismic(BaseModel):
    site_class: str = "D"
    sds: float = 0.0
    sd1: float = 0.0


def fetch_seismic(lat: float, lon: float, *, timeout: float = 6.0) -> Optional[UsgsSeismic]:
    # ASCE 7-22 endpoint; parameters vary by reference document
    url = "https://earthquake.usgs.gov/ws/designmaps/asce7-22.json"
    params = {
        "latitude": lat, "longitude": lon,
        "riskCategory": "II", "siteClass": "D", "title": "firecore",
    }
    try:
        r = requests.get(url, params=params, timeout=timeout)
        if r.status_code != 200:
            return None
        d = r.json().get("response", {}).get("data", {})
        return UsgsSeismic(
            site_class="D",
            sds=float(d.get("sds", 0) or 0),
            sd1=float(d.get("sd1", 0) or 0),
        )
    except Exception:
        return None
