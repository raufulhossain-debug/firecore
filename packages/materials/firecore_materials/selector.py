"""Climate-aware material selection engine."""

from __future__ import annotations

from dataclasses import dataclass, field

from firecore_materials.loader import load_all_materials
from firecore_materials.types import ClimateZone, Material, MaterialVariant


@dataclass
class MaterialRecommendation:
    """A scored material recommendation for a specific climate zone."""
    material: Material
    variant: MaterialVariant
    climate_score: float        # 0-1 climate suitability
    cost_per_sqft: float        # Material cost
    lead_time_days: int
    required_treatments: list[str] = field(default_factory=list)
    disqualified: bool = False
    disqualify_reason: str = ""


def _climate_zone_from_site(fhsz: str, flood_zone: str, slope_pct: float) -> list[ClimateZone]:
    """Infer active climate zones from site data."""
    zones: list[ClimateZone] = []
    if fhsz in ("VHFHSZ", "HFHSZ", "MFHSZ"):
        zones.append(ClimateZone.WILDFIRE)
    if flood_zone in ("AE", "VE", "AO", "AH", "A"):
        zones.append(ClimateZone.FLOOD)
    if not zones:
        zones.append(ClimateZone.STANDARD)
    return zones


def select_materials_for_climate(
    fhsz: str = "Non-HFHSZ",
    flood_zone: str = "X",
    slope_pct: float = 0,
    min_score: float = 0.3,
) -> list[MaterialRecommendation]:
    """
    Given site hazard data, rank all materials by climate suitability.

    Returns a list sorted by climate_score (descending), then cost (ascending).
    Materials below min_score are marked as disqualified but still returned.
    """
    zones = _climate_zone_from_site(fhsz, flood_zone, slope_pct)
    primary_zone = zones[0]

    all_materials = load_all_materials()
    recommendations: list[MaterialRecommendation] = []

    for mat in all_materials:
        rating = next((r for r in mat.climate_ratings if r.zone == primary_zone), None)
        if rating is None:
            continue

        best_variant = mat.best_variant_for_climate(primary_zone)
        if best_variant is None:
            continue

        rec = MaterialRecommendation(
            material=mat,
            variant=best_variant,
            climate_score=rating.score,
            cost_per_sqft=best_variant.cost_per_sqft,
            lead_time_days=best_variant.lead_time_days,
            required_treatments=rating.required_treatments,
        )

        if rating.score < min_score:
            rec.disqualified = True
            rec.disqualify_reason = f"Climate score {rating.score} below threshold {min_score}"

        # Check all active zones — if material fails ANY zone, flag it
        for zone in zones[1:]:
            other_rating = next((r for r in mat.climate_ratings if r.zone == zone), None)
            if other_rating and other_rating.score < min_score:
                rec.disqualified = True
                rec.disqualify_reason = (
                    f"Fails secondary zone {zone.value}: score {other_rating.score}"
                )
            if other_rating:
                rec.required_treatments.extend(other_rating.required_treatments)

        # Deduplicate treatments
        rec.required_treatments = list(dict.fromkeys(rec.required_treatments))
        recommendations.append(rec)

    # Sort: non-disqualified first, then by score desc, then cost asc
    recommendations.sort(key=lambda r: (r.disqualified, -r.climate_score, r.cost_per_sqft))
    return recommendations
