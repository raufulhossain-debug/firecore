from __future__ import annotations
from pathlib import Path

import yaml

from firecore_sku.types import Sku


def _skus_dir() -> Path:
    return Path(__file__).parent / "skus"


def list_skus() -> list[str]:
    return sorted(p.stem for p in _skus_dir().glob("*.yaml"))


def load_sku(sku_id: str) -> Sku:
    path = _skus_dir() / f"{sku_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"No SKU '{sku_id}'. Available: {list_skus()}")
    return Sku(**yaml.safe_load(path.read_text()))
