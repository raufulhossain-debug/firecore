"""Core types for the material catalog."""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class MaterialCategory(str, Enum):
    SIP = "sip"            # Structural Insulated Panels
    CLT = "clt"            # Cross-Laminated Timber
    STEEL = "light_gauge_steel"  # Light-Gauge Steel Framing


class ClimateZone(str, Enum):
    WILDFIRE = "wildfire"      # WUI / FHSZ zones
    FLOOD = "flood"            # SFHA / coastal
    DESERT = "desert"          # Extreme heat / arid
    ARCTIC = "arctic"          # Extreme cold / snow load
    SEISMIC = "seismic"        # High seismic zones
    STANDARD = "standard"      # No special hazard


class ClimateRating(BaseModel):
    """How well a material performs in a specific climate zone."""
    zone: ClimateZone
    score: float = Field(ge=0, le=1, description="0 = unsuitable, 1 = ideal")
    notes: str = ""
    required_treatments: list[str] = Field(default_factory=list)


class Certification(BaseModel):
    """A code or standard certification the material holds."""
    code: str          # e.g. "CBC_Chapter_7A", "ASTM_E119", "ICC_ESR"
    name: str          # Human-readable name
    status: Literal["certified", "in_progress", "planned"] = "certified"
    expiry_year: Optional[int] = None


class MaterialVariant(BaseModel):
    """A specific product variant within a material system."""
    id: str                           # e.g. "sip_6.5in_osb"
    name: str                         # e.g. "6.5\" OSB-faced SIP"
    thickness_in: float               # Panel / member thickness
    r_value: Optional[float] = None   # Insulation R-value per inch
    weight_psf: float                 # Weight in lbs per sq ft
    cost_per_sqft: float              # Base material cost $/sqft
    lead_time_days: int               # Typical manufacturing lead time
    fire_rating_hr: float = 0         # Fire resistance rating (hours)
    structural_span_ft: float = 0     # Max unsupported span


class Material(BaseModel):
    """A prefab material system (e.g., SIPs, CLT, Steel)."""
    id: str                           # e.g. "sip"
    name: str                         # e.g. "Structural Insulated Panels"
    category: MaterialCategory
    description: str = ""
    climate_ratings: list[ClimateRating] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    variants: list[MaterialVariant] = Field(default_factory=list)
    domestic_availability: float = Field(
        ge=0, le=1, default=0.8,
        description="0 = import only, 1 = fully domestic",
    )
    buy_america_compliant: bool = False
    carbon_kg_per_sqft: float = 0     # Embodied carbon

    def best_variant_for_climate(self, zone: ClimateZone) -> Optional[MaterialVariant]:
        """Return the cheapest variant that has acceptable climate performance."""
        rating = next((r for r in self.climate_ratings if r.zone == zone), None)
        if rating is None or rating.score < 0.3:
            return None
        # Return cheapest variant
        if not self.variants:
            return None
        return min(self.variants, key=lambda v: v.cost_per_sqft)
