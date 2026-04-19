"""Load supplier and tariff data from YAML."""

from __future__ import annotations

from pathlib import Path

import yaml

from firecore_supply.types import Supplier, SupplierQuote, TariffSchedule

_DATA_DIR = Path(__file__).parent / "data"


def load_suppliers() -> tuple[list[Supplier], list[SupplierQuote]]:
    """Load all suppliers and their quotes."""
    path = _DATA_DIR / "suppliers.yaml"
    with open(path) as f:
        data = yaml.safe_load(f)
    suppliers = [Supplier(**s) for s in data.get("suppliers", [])]
    quotes = [SupplierQuote(**q) for q in data.get("quotes", [])]
    return suppliers, quotes


def load_tariffs() -> list[TariffSchedule]:
    """Load tariff schedules."""
    path = _DATA_DIR / "tariffs.yaml"
    with open(path) as f:
        data = yaml.safe_load(f)
    tariffs = []
    for t in data.get("tariffs", []):
        ts = TariffSchedule(**t)
        ts.total_tariff_pct = ts.effective_tariff()
        tariffs.append(ts)
    return tariffs


def get_tariff(country: str, material_category: str) -> TariffSchedule | None:
    """Look up tariff for a specific country + material combo."""
    for t in load_tariffs():
        if t.country == country and t.material_category == material_category:
            return t
    return None


def get_suppliers_for_material(material_id: str) -> list[Supplier]:
    """Get all suppliers that carry a given material."""
    suppliers, _ = load_suppliers()
    return [s for s in suppliers if material_id in s.material_ids]


def get_quotes_for_variant(variant_id: str) -> list[SupplierQuote]:
    """Get all quotes for a specific material variant."""
    _, quotes = load_suppliers()
    return [q for q in quotes if q.variant_id == variant_id]
