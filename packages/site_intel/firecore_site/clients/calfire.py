"""CalFire Fire Hazard Severity Zone (FHSZ) client.

Public ArcGIS REST endpoint. Returns None on failure.
"""
from __future__ import annotations
from typing import Optional

import requests
from pydantic import BaseModel

FHSZ_QUERY = (
    "https://egis.fire.ca.gov/arcgis/rest/services/FHSZ/FHSZ_SRA_LRA_Combined"
    "/MapServer/0/query"
)

# HAZ_CODE mapping per CalFire schema
_LEVELS = {1: "Moderate", 2: "High", 3: "VHFHSZ"}


class CalFireFHSZ(BaseModel):
    level: str     # "Non-HFHSZ" | "Moderate" | "High" | "VHFHSZ"


def fetch_fhsz(lat: float, lon: float, *, timeout: float = 6.0) -> Optional[CalFireFHSZ]:
    params = {
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "HAZ_CODE",
        "f": "json",
    }
    try:
        r = requests.get(FHSZ_QUERY, params=params, timeout=timeout)
        if r.status_code != 200:
            return None
        feats = r.json().get("features", [])
        if not feats:
            return CalFireFHSZ(level="Non-HFHSZ")
        code = feats[0].get("attributes", {}).get("HAZ_CODE")
        return CalFireFHSZ(level=_LEVELS.get(code, "Non-HFHSZ"))
    except Exception:
        return None
