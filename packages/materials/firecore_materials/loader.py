"""Load material definitions from YAML catalog."""

from __future__ import annotations

from pathlib import Path

import yaml

from firecore_materials.types import Material

_CATALOG_DIR = Path(__file__).parent / "catalog"


def list_materials() -> list[str]:
    """Return IDs of all available materials."""
    return sorted(p.stem for p in _CATALOG_DIR.glob("*.yaml"))


def load_material(material_id: str) -> Material:
    """Load a single material by ID."""
    path = _CATALOG_DIR / f"{material_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Material '{material_id}' not found in {_CATALOG_DIR}")
    with open(path) as f:
        data = yaml.safe_load(f)
    return Material(**data)


def load_all_materials() -> list[Material]:
    """Load every material in the catalog."""
    return [load_material(mid) for mid in list_materials()]
