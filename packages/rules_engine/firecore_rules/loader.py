"""Load jurisdiction rule sets from YAML."""
from __future__ import annotations

from importlib import resources
from pathlib import Path

import yaml

from firecore_rules.types import Jurisdiction


def _rules_dir() -> Path:
    return Path(__file__).parent / "jurisdictions"


def list_jurisdictions() -> list[str]:
    """Return the IDs (filenames w/o .yaml) of available jurisdictions."""
    return sorted(p.stem for p in _rules_dir().glob("*.yaml"))


def load_jurisdiction(jurisdiction_id: str) -> Jurisdiction:
    """Load a jurisdiction by its ID (e.g. 'la_city_adu')."""
    path = _rules_dir() / f"{jurisdiction_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(
            f"No rule file for '{jurisdiction_id}'. Available: {list_jurisdictions()}"
        )
    data = yaml.safe_load(path.read_text())
    return Jurisdiction(**data)
