from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Certification(BaseModel):
    name: str                       # e.g. "CBC Chapter 7A"
    authority: str                  # e.g. "California Building Code"
    reference: str = ""             # report # / listing
    status: Literal["certified", "in_progress", "planned"] = "certified"


class SkuVariant(BaseModel):
    id: str
    name: str
    footprint_w_ft: float
    footprint_d_ft: float
    stories: int
    height_ft: float
    foundation: Literal["slab", "raised_pier", "stepped_pier"]
    conditioned_sqft: int


class Sku(BaseModel):
    id: str
    name: str
    description: str = ""
    climate_archetype: Literal[
        "wildfire", "flood", "hurricane", "desert", "arctic", "seismic", "general"
    ]
    variants: list[SkuVariant]
    roof_pitches: list[str] = Field(default_factory=list)
    rotation_increments_deg: int = 15
    certifications: list[Certification] = Field(default_factory=list)
    # Parametric envelope (bounds within which cert still holds)
    envelope: dict = Field(default_factory=dict)

    def variant(self, variant_id: str) -> Optional[SkuVariant]:
        return next((v for v in self.variants if v.id == variant_id), None)
