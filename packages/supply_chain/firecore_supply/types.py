"""Supply chain types — suppliers, quotes, tariffs, landed costs."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Location(BaseModel):
    """Geographic coordinates + address."""
    lat: float
    lon: float
    city: str = ""
    state: str = ""
    country: str = "US"


class Supplier(BaseModel):
    """A material supplier or factory."""
    id: str                         # e.g. "premier_sips_or"
    name: str                       # e.g. "Premier SIPs"
    location: Location
    material_ids: list[str]         # Which materials they supply
    variant_ids: list[str] = Field(default_factory=list)  # Specific variants (empty = all)
    country: str = "US"
    lead_time_days: int = 21        # Default lead time
    min_order_sqft: int = 500       # Minimum order size
    max_capacity_sqft_month: int = 50000  # Monthly production capacity
    certifications: list[str] = Field(default_factory=list)  # e.g. ["ISO_9001", "FSC"]
    buy_america: bool = True
    reliability_score: float = Field(ge=0, le=1, default=0.85)


class SupplierQuote(BaseModel):
    """A price quote from a supplier for a specific material variant."""
    supplier_id: str
    material_id: str
    variant_id: str
    unit_cost_per_sqft: float       # FOB factory price
    volume_discount_pct: float = 0  # Discount for bulk orders
    min_order_sqft: int = 500
    valid_until: Optional[str] = None  # ISO date
    notes: str = ""


class TariffSchedule(BaseModel):
    """Import tariff rates by country and material category."""
    country: str                    # Origin country code
    material_category: str          # e.g. "sip", "clt", "light_gauge_steel"
    hts_code: str = ""              # Harmonized Tariff Schedule code
    base_rate_pct: float = 0        # Base tariff rate
    section_301_pct: float = 0      # Section 301 (China) tariff
    anti_dumping_pct: float = 0     # Anti-dumping duty
    countervailing_pct: float = 0   # Countervailing duty
    total_tariff_pct: float = 0     # Computed total
    uflpa_restricted: bool = False  # Uyghur Forced Labor Prevention Act flag
    notes: str = ""

    def effective_tariff(self) -> float:
        return self.base_rate_pct + self.section_301_pct + self.anti_dumping_pct + self.countervailing_pct


class FreightEstimate(BaseModel):
    """Estimated freight cost for a shipment leg."""
    origin: Location
    destination: Location
    distance_mi: float
    mode: Literal["flatbed", "container", "rail", "ocean"] = "flatbed"
    cost_total: float = 0
    cost_per_mile: float = 3.50     # Default flatbed rate
    oversize_surcharge: float = 0
    fuel_surcharge_pct: float = 15
    transit_days: int = 0


class LandedCost(BaseModel):
    """Full landed cost breakdown for a material shipment."""
    material_cost: float            # Unit cost × quantity
    tariff_cost: float = 0          # Import duties
    freight_cost: float = 0         # All shipping legs
    insurance_cost: float = 0       # Cargo insurance (typically 0.5% of material)
    crane_cost: float = 0           # On-site crane / unloading
    total_cost: float = 0           # Sum of all
    cost_per_sqft: float = 0        # Total / sqft ordered
    total_lead_time_days: int = 0   # Manufacturing + transit
    carbon_kg: float = 0            # Total embodied + transport carbon
    buy_america_compliant: bool = True

    def compute_total(self) -> None:
        self.total_cost = (
            self.material_cost + self.tariff_cost + self.freight_cost
            + self.insurance_cost + self.crane_cost
        )
