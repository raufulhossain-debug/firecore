"""FireCore Materials — prefab material catalog with climate ratings."""

from firecore_materials.types import (
    ClimateRating,
    Certification,
    Material,
    MaterialCategory,
    MaterialVariant,
)
from firecore_materials.loader import load_material, list_materials
from firecore_materials.selector import select_materials_for_climate

__all__ = [
    "ClimateRating",
    "Certification",
    "Material",
    "MaterialCategory",
    "MaterialVariant",
    "load_material",
    "list_materials",
    "select_materials_for_climate",
]
