"""FEMA National Flood Hazard Layer (NFHL) client.

Public ArcGIS REST endpoint; no auth required. Returns None on failure.
"""
from __future__ import annotations
from typing import Optional

import requests
from pydantic import BaseModel

NFHL_QUERY = (
    "https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer/28/query"
)


class FemaFlood(BaseModel):
    zone: str             # "X", "A", "AE", "VE", etc.
    bfe_ft: float = 0.0


def fetch_flood_zone(lat: float, lon: float, *, timeout: float = 6.0) -> Optional[FemaFlood]:
    params = {
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "FLD_ZONE,STATIC_BFE",
        "f": "json",
    }
    try:
        r = requests.get(NFHL_QUERY, params=params, timeout=timeout)
        if r.status_code != 200:
            return None
        feats = r.json().get("features", [])
        if not feats:
            return FemaFlood(zone="X", bfe_ft=0.0)   # outside SFHA
        a = feats[0].get("attributes", {}) or {}
        return FemaFlood(zone=a.get("FLD_ZONE") or "X", bfe_ft=float(a.get("STATIC_BFE") or 0))
    except Exception:
        return None
