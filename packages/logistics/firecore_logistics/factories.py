"""Load factory definitions."""

from __future__ import annotations

from pathlib import Path

import yaml

from firecore_logistics.types import Factory

_DATA_DIR = Path(__file__).parent / "data"


def load_factories() -> list[Factory]:
    """Load all registered factories."""
    path = _DATA_DIR / "factories.yaml"
    with open(path) as f:
        data = yaml.safe_load(f)
    return [Factory(**f) for f in data.get("factories", [])]


def get_factories_for_material(material_id: str) -> list[Factory]:
    """Get factories that can process a specific material."""
    return [f for f in load_factories() if material_id in f.material_ids]


def get_nearest_factory(
    material_id: str, site_lat: float, site_lon: float
) -> Factory | None:
    """Find the nearest factory for a material to a given site."""
    from firecore_supply.pricing import haversine_miles
    from firecore_supply.types import Location

    site = Location(lat=site_lat, lon=site_lon)
    factories = get_factories_for_material(material_id)
    if not factories:
        return None
    return min(factories, key=lambda f: haversine_miles(f.location, site))
