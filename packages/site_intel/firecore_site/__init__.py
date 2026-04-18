"""FireCore site intelligence — best-effort GIS lookups.

Each client is defensive: transient network / API failures return None rather
than raising, so the caller (API / UI) can gracefully fall back to user input.
"""
from firecore_site.clients.fema import fetch_flood_zone, FemaFlood
from firecore_site.clients.calfire import fetch_fhsz, CalFireFHSZ
from firecore_site.clients.usgs import fetch_seismic, UsgsSeismic
from firecore_site.aggregator import gather, SiteSnapshot

__all__ = [
    "fetch_flood_zone", "FemaFlood",
    "fetch_fhsz", "CalFireFHSZ",
    "fetch_seismic", "UsgsSeismic",
    "gather", "SiteSnapshot",
]
