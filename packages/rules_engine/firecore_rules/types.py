"""Pydantic models shared across the rules engine."""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


FHSZ = Literal["Non-HFHSZ", "Moderate", "High", "VHFHSZ"]
FloodZone = Literal["X", "A", "AE", "VE"]


class Site(BaseModel):
    """A parcel + its contextual hazards. Canonical input to the rules engine."""

    address: str = ""
    apn: str = ""
    # Geometry (simplified MVP — real impl uses a polygon)
    lot_sqft: int
    lot_width_ft: float
    lot_depth_ft: float
    # Zoning
    zone_code: str
    overlays: list[str] = Field(default_factory=list)
    max_coverage_pct: float = 45.0
    existing_coverage_pct: float = 0.0
    height_limit_ft: float = 33.0
    setback_front_ft: float = 20.0
    setback_side_ft: float = 4.0
    setback_rear_ft: float = 4.0
    # Context
    transit_half_mi: bool = False
    slope_pct: float = 0.0
    # Hazards
    fhsz: FHSZ = "Non-HFHSZ"
    flood_zone: FloodZone = "X"
    bfe_ft: float = 0.0
    seismic_site_class: str = "D"
    wind_mph: float = 110.0


class ProposedBuild(BaseModel):
    """What we intend to put on the site. Consumed alongside Site by rules."""

    footprint_w_ft: float
    footprint_d_ft: float
    stories: int = 1
    height_ft: float
    foundation: Literal["slab", "raised_pier", "stepped_pier"] = "slab"
    conditioned_sqft: int


class Rule(BaseModel):
    """A single rule loaded from YAML."""

    id: str
    title: str
    citation: str                        # e.g. "LAMC §12.22 A.33.c.6"
    type: Literal[
        "min_lot_size",
        "max_adu_size",
        "setback",
        "max_height",
        "max_coverage",
        "fire_wui_compliance",
        "flood_compliance",
        "slope_tolerance",
        "transit_proximity_bonus",
    ]
    params: dict[str, Any] = Field(default_factory=dict)
    severity: Literal["blocking", "warning", "info"] = "blocking"
    notes: str = ""


class Jurisdiction(BaseModel):
    id: str
    name: str
    state: str
    code_version: str = ""
    reviewed_by: str = ""
    reviewed_on: str = ""
    rules: list[Rule]


class RuleResult(BaseModel):
    rule_id: str
    passed: bool
    severity: str
    message: str


class EvaluationReport(BaseModel):
    jurisdiction_id: str
    site: Site
    build: ProposedBuild
    results: list[RuleResult]

    @property
    def blocking_failures(self) -> list[RuleResult]:
        return [r for r in self.results if not r.passed and r.severity == "blocking"]

    @property
    def passed(self) -> bool:
        return len(self.blocking_failures) == 0
