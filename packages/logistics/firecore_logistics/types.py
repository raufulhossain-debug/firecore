"""Logistics types — factories, routes, shipment legs."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from firecore_supply.types import Location


class Factory(BaseModel):
    """A prefab manufacturing factory."""
    id: str
    name: str
    location: Location
    material_ids: list[str]         # What materials it can process
    assembly_capabilities: list[str] = Field(default_factory=list)  # e.g. ["panel", "volumetric_mod"]
    monthly_capacity_units: int = 20
    current_utilization_pct: float = 65  # Current capacity usage
    crane_available: bool = True
    staging_yard: bool = True       # Has on-site staging area
    accepts_raw_material_delivery: bool = True


class ShipmentLeg(BaseModel):
    """A single leg in a multi-leg shipment."""
    leg_number: int
    origin: Location
    destination: Location
    mode: Literal["flatbed", "container", "rail", "ocean", "local_truck"] = "flatbed"
    distance_mi: float = 0
    cost: float = 0
    transit_days: int = 0
    description: str = ""
    oversize_permit_needed: bool = False
    escort_needed: bool = False


class Route(BaseModel):
    """A complete multi-leg route from raw materials to site."""
    id: str
    description: str
    legs: list[ShipmentLeg] = Field(default_factory=list)
    total_distance_mi: float = 0
    total_cost: float = 0
    total_transit_days: int = 0
    total_carbon_kg: float = 0
    requires_staging: bool = False

    def compute_totals(self) -> None:
        self.total_distance_mi = sum(l.distance_mi for l in self.legs)
        self.total_cost = sum(l.cost for l in self.legs)
        self.total_transit_days = sum(l.transit_days for l in self.legs)
        # Rough carbon: 0.1 kg per ton-mile (truck avg)
        self.total_carbon_kg = round(self.total_distance_mi * 0.5, 1)


class RouteOption(BaseModel):
    """A scored routing option combining supplier, factory, and delivery."""
    rank: int = 0
    supplier_id: str
    factory_id: Optional[str] = None  # None if supplier ships direct
    material_id: str
    variant_id: str
    route: Route
    landed_cost_per_sqft: float = 0
    total_cost: float = 0
    total_days: int = 0             # Manufacturing + all transit
    carbon_kg: float = 0
    buy_america: bool = True
    score: float = 0                # Multi-objective score (0-100)
    score_breakdown: dict[str, float] = Field(default_factory=dict)
