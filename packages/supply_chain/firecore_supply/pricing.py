"""Landed cost computation — material + tariff + freight + insurance."""

from __future__ import annotations

import math

from firecore_supply.loader import get_tariff
from firecore_supply.types import (
    FreightEstimate,
    LandedCost,
    Location,
    Supplier,
    SupplierQuote,
)


def haversine_miles(a: Location, b: Location) -> float:
    """Great-circle distance between two points in miles."""
    R = 3958.8  # Earth radius in miles
    lat1, lat2 = math.radians(a.lat), math.radians(b.lat)
    dlat = math.radians(b.lat - a.lat)
    dlon = math.radians(b.lon - a.lon)
    h = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(h))


def estimate_freight(
    origin: Location,
    destination: Location,
    total_weight_lbs: float = 10000,
    oversize: bool = False,
) -> FreightEstimate:
    """Estimate freight cost based on distance and weight."""
    dist = haversine_miles(origin, destination)

    # Mode selection
    if origin.country != destination.country and dist > 3000:
        mode = "ocean"
        cost_per_mile = 0.80  # Ocean is cheaper per mile
        transit_days = int(dist / 400)  # ~400 mi/day ocean
    elif dist > 1500:
        mode = "rail"
        cost_per_mile = 1.50
        transit_days = int(dist / 500) + 2  # Rail + drayage
    else:
        mode = "flatbed"
        cost_per_mile = 3.50
        transit_days = max(1, int(dist / 500))

    oversize_surcharge = 1500 if oversize else 0
    base_cost = dist * cost_per_mile
    fuel_surcharge = base_cost * 0.15
    total = base_cost + fuel_surcharge + oversize_surcharge

    return FreightEstimate(
        origin=origin,
        destination=destination,
        distance_mi=round(dist, 1),
        mode=mode,
        cost_total=round(total, 2),
        cost_per_mile=cost_per_mile,
        oversize_surcharge=oversize_surcharge,
        fuel_surcharge_pct=15,
        transit_days=transit_days,
    )


def compute_landed_cost(
    supplier: Supplier,
    quote: SupplierQuote,
    site_location: Location,
    sqft_needed: float,
    material_category: str,
    carbon_per_sqft: float = 0,
) -> LandedCost:
    """
    Compute full landed cost for a material order.

    Includes: material cost, volume discounts, tariffs, freight,
    insurance, and crane/unloading.
    """
    # Material cost with volume discount
    effective_price = quote.unit_cost_per_sqft
    if sqft_needed >= quote.min_order_sqft and quote.volume_discount_pct > 0:
        effective_price *= (1 - quote.volume_discount_pct / 100)
    material_cost = effective_price * sqft_needed

    # Tariff
    tariff = get_tariff(supplier.country, material_category)
    tariff_pct = tariff.effective_tariff() if tariff else 0
    tariff_cost = material_cost * (tariff_pct / 100)

    # Freight
    freight = estimate_freight(supplier.location, site_location)
    freight_cost = freight.cost_total

    # Insurance (0.5% of material value)
    insurance_cost = material_cost * 0.005

    # Crane / unloading (flat estimate based on material weight)
    crane_cost = 1200 if material_category == "clt" else 600

    # Carbon (material + transport)
    material_carbon = carbon_per_sqft * sqft_needed
    # ~0.1 kg CO2 per ton-mile for truck
    transport_carbon = (sqft_needed * 5 / 2000) * freight.distance_mi * 0.1
    total_carbon = material_carbon + transport_carbon

    landed = LandedCost(
        material_cost=round(material_cost, 2),
        tariff_cost=round(tariff_cost, 2),
        freight_cost=round(freight_cost, 2),
        insurance_cost=round(insurance_cost, 2),
        crane_cost=crane_cost,
        total_lead_time_days=supplier.lead_time_days + freight.transit_days,
        carbon_kg=round(total_carbon, 1),
        buy_america_compliant=supplier.buy_america,
    )
    landed.compute_total()
    landed.cost_per_sqft = round(landed.total_cost / sqft_needed, 2) if sqft_needed > 0 else 0
    return landed
