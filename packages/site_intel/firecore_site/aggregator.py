"""Aggregate site intel from multiple public sources into a single snapshot."""
from __future__ import annotations
from typing import Optional

from pydantic import BaseModel

from firecore_site.clients.fema import FemaFlood, fetch_flood_zone
from firecore_site.clients.calfire import CalFireFHSZ, fetch_fhsz
from firecore_site.clients.usgs import UsgsSeismic, fetch_seismic


class SiteSnapshot(BaseModel):
    lat: float
    lon: float
    flood: Optional[FemaFlood] = None
    fhsz: Optional[CalFireFHSZ] = None
    seismic: Optional[UsgsSeismic] = None

    @property
    def missing_sources(self) -> list[str]:
        m = []
        if self.flood is None:   m.append("fema_flood")
        if self.fhsz  is None:   m.append("calfire_fhsz")
        if self.seismic is None: m.append("usgs_seismic")
        return m


def gather(lat: float, lon: float) -> SiteSnapshot:
    """Best-effort parallel gather. For MVP we serialize; later use asyncio."""
    return SiteSnapshot(
        lat=lat, lon=lon,
        flood=fetch_flood_zone(lat, lon),
        fhsz=fetch_fhsz(lat, lon),
        seismic=fetch_seismic(lat, lon),
    )
