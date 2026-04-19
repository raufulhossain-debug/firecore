"""Multi-objective scoring engine for supply chain routes.

Scores each route option across 4 dimensions:
  - Cost (lower is better)
  - Speed (fewer days is better)
  - Carbon footprint (lower is better)
  - Compliance (Buy America, certifications)

Each dimension is normalized to 0-100, then weighted.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import BaseModel, Field

from firecore_logistics.router import find_optimal_routes
from firecore_logistics.types import RouteOption
from firecore_materials import load_material, select_materials_for_climate


class OptimizationWeights(BaseModel):
    """Weights for multi-objective optimization (must sum to 1.0)."""
    cost: float = 0.40
    speed: float = 0.25
    carbon: float = 0.15
    compliance: float = 0.20

    def normalized(self) -> "OptimizationWeights":
        total = self.cost + self.speed + self.carbon + self.compliance
        if total == 0:
            return OptimizationWeights()
        return OptimizationWeights(
            cost=self.cost / total,
            speed=self.speed / total,
            carbon=self.carbon / total,
            compliance=self.compliance / total,
        )


class ScoredOption(BaseModel):
    """A route option with multi-objective scoring."""
    rank: int = 0
    supplier_id: str
    supplier_name: str = ""
    factory_id: str | None = None
    factory_name: str = ""
    material_id: str
    material_name: str = ""
    variant_id: str
    variant_name: str = ""

    # Raw metrics
    total_cost: float = 0
    cost_per_sqft: float = 0
    total_days: int = 0
    carbon_kg: float = 0
    buy_america: bool = True
    climate_score: float = 0

    # Route details
    route_description: str = ""
    route_legs: int = 0
    total_distance_mi: float = 0

    # Scores (0-100 each)
    score_cost: float = 0
    score_speed: float = 0
    score_carbon: float = 0
    score_compliance: float = 0
    score_total: float = 0

    # What optimization preset would pick this
    best_for: list[str] = Field(default_factory=list)


def _normalize(value: float, min_val: float, max_val: float, invert: bool = True) -> float:
    """Normalize a value to 0-100 scale. If invert=True, lower raw = higher score."""
    if max_val == min_val:
        return 100.0
    ratio = (value - min_val) / (max_val - min_val)
    if invert:
        ratio = 1 - ratio
    return round(max(0, min(100, ratio * 100)), 1)


def _score_options(
    options: list[RouteOption],
    weights: OptimizationWeights,
    fhsz: str = "Non-HFHSZ",
    flood_zone: str = "X",
) -> list[ScoredOption]:
    """Score and rank route options."""
    if not options:
        return []

    w = weights.normalized()

    # Get min/max for normalization
    costs = [o.total_cost for o in options]
    days = [o.total_days for o in options]
    carbons = [o.carbon_kg for o in options]

    min_cost, max_cost = min(costs), max(costs)
    min_days, max_days = min(days), max(days)
    min_carbon, max_carbon = min(carbons), max(carbons)

    # Get climate scores for materials
    climate_recs = select_materials_for_climate(fhsz=fhsz, flood_zone=flood_zone)
    climate_map = {r.material.id: r.climate_score for r in climate_recs}

    # Load supplier/factory names for display
    from firecore_supply.loader import load_suppliers
    from firecore_logistics.factories import load_factories
    suppliers_list, _ = load_suppliers()
    supplier_map = {s.id: s.name for s in suppliers_list}
    factory_map = {f.id: f.name for f in load_factories()}

    scored: list[ScoredOption] = []
    for opt in options:
        # Material info
        mat = load_material(opt.material_id)
        variant = next((v for v in mat.variants if v.id == opt.variant_id), None)

        s_cost = _normalize(opt.total_cost, min_cost, max_cost, invert=True)
        s_speed = _normalize(opt.total_days, min_days, max_days, invert=True)
        s_carbon = _normalize(opt.carbon_kg, min_carbon, max_carbon, invert=True)

        # Compliance score: Buy America + climate suitability
        compliance_base = 80 if opt.buy_america else 20
        climate = climate_map.get(opt.material_id, 0.5)
        s_compliance = min(100, compliance_base + climate * 20)

        total = (
            w.cost * s_cost
            + w.speed * s_speed
            + w.carbon * s_carbon
            + w.compliance * s_compliance
        )

        # Determine what this option is best for
        best_for = []
        if s_cost >= 90:
            best_for.append("lowest_cost")
        if s_speed >= 90:
            best_for.append("fastest_delivery")
        if s_carbon >= 90:
            best_for.append("lowest_carbon")
        if s_compliance >= 90:
            best_for.append("best_compliance")

        scored.append(ScoredOption(
            supplier_id=opt.supplier_id,
            supplier_name=supplier_map.get(opt.supplier_id, opt.supplier_id),
            factory_id=opt.factory_id,
            factory_name=factory_map.get(opt.factory_id, "") if opt.factory_id else "",
            material_id=opt.material_id,
            material_name=mat.name,
            variant_id=opt.variant_id,
            variant_name=variant.name if variant else opt.variant_id,
            total_cost=opt.total_cost,
            cost_per_sqft=opt.landed_cost_per_sqft,
            total_days=opt.total_days,
            carbon_kg=opt.carbon_kg,
            buy_america=opt.buy_america,
            climate_score=climate,
            route_description=opt.route.description,
            route_legs=len(opt.route.legs),
            total_distance_mi=opt.route.total_distance_mi,
            score_cost=s_cost,
            score_speed=s_speed,
            score_carbon=s_carbon,
            score_compliance=s_compliance,
            score_total=round(total, 1),
            best_for=best_for,
        ))

    scored.sort(key=lambda s: -s.score_total)
    for i, s in enumerate(scored):
        s.rank = i + 1

    return scored


def optimize_supply_chain(
    site_lat: float,
    site_lon: float,
    sqft_needed: float = 1200,
    fhsz: str = "Non-HFHSZ",
    flood_zone: str = "X",
    weights: OptimizationWeights | None = None,
    material_ids: list[str] | None = None,
    max_results: int = 10,
) -> list[ScoredOption]:
    """
    Full supply chain optimization for a site.

    1. Selects best materials for the climate zone
    2. Finds all viable routes (direct + factory)
    3. Scores across cost, speed, carbon, compliance
    4. Returns ranked options

    Presets:
      - Default weights: balanced (cost 40%, speed 25%, carbon 15%, compliance 20%)
      - Pure cost:  OptimizationWeights(cost=1, speed=0, carbon=0, compliance=0)
      - Pure speed: OptimizationWeights(cost=0, speed=1, carbon=0, compliance=0)
    """
    if weights is None:
        weights = OptimizationWeights()

    # Determine which materials to evaluate
    if material_ids is None:
        recs = select_materials_for_climate(fhsz=fhsz, flood_zone=flood_zone)
        material_ids = [r.material.id for r in recs if not r.disqualified]

    # Collect route options across all materials
    from firecore_supply.loader import get_quotes_for_variant

    all_options: list[RouteOption] = []
    for mid in material_ids:
        mat = load_material(mid)
        if not mat.variants:
            continue
        # Try each variant, preferring ones that have supplier quotes
        for variant in sorted(mat.variants, key=lambda v: v.cost_per_sqft):
            quotes = get_quotes_for_variant(variant.id)
            if not quotes:
                continue
            routes = find_optimal_routes(
                material_id=mid,
                variant_id=variant.id,
                site_lat=site_lat,
                site_lon=site_lon,
                sqft_needed=sqft_needed,
                max_results=20,
            )
            all_options.extend(routes)
            break  # Use first variant with quotes per material

    # Score everything
    scored = _score_options(all_options, weights, fhsz=fhsz, flood_zone=flood_zone)
    return scored[:max_results]
