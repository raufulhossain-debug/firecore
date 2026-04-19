"""Multi-leg supply chain route optimizer."""

from __future__ import annotations

from firecore_logistics.factories import get_factories_for_material
from firecore_logistics.types import Factory, Route, RouteOption, ShipmentLeg
from firecore_supply.loader import get_suppliers_for_material, get_quotes_for_variant
from firecore_supply.pricing import compute_landed_cost, estimate_freight, haversine_miles
from firecore_supply.types import Location, Supplier


def _build_direct_route(
    supplier: Supplier, site: Location
) -> Route:
    """Supplier ships directly to job site (no factory stop)."""
    freight = estimate_freight(supplier.location, site)
    leg = ShipmentLeg(
        leg_number=1,
        origin=supplier.location,
        destination=site,
        mode=freight.mode,
        distance_mi=freight.distance_mi,
        cost=freight.cost_total,
        transit_days=freight.transit_days,
        description=f"Direct: {supplier.name} → Site",
    )
    route = Route(
        id=f"direct_{supplier.id}",
        description=f"Direct ship from {supplier.name}",
        legs=[leg],
    )
    route.compute_totals()
    return route


def _build_factory_route(
    supplier: Supplier, factory: Factory, site: Location
) -> Route:
    """Supplier → Factory (assembly) → Job site."""
    # Leg 1: Supplier → Factory
    leg1_freight = estimate_freight(supplier.location, factory.location)
    leg1 = ShipmentLeg(
        leg_number=1,
        origin=supplier.location,
        destination=factory.location,
        mode=leg1_freight.mode,
        distance_mi=leg1_freight.distance_mi,
        cost=leg1_freight.cost_total,
        transit_days=leg1_freight.transit_days,
        description=f"Raw materials: {supplier.name} → {factory.name}",
    )

    # Leg 2: Factory → Site (assembled panels, may be oversize)
    leg2_freight = estimate_freight(factory.location, site, oversize=True)
    oversize = haversine_miles(factory.location, site) < 500  # Oversize only practical < 500mi
    leg2 = ShipmentLeg(
        leg_number=2,
        origin=factory.location,
        destination=site,
        mode="flatbed",
        distance_mi=leg2_freight.distance_mi,
        cost=leg2_freight.cost_total,
        transit_days=leg2_freight.transit_days,
        description=f"Assembled panels: {factory.name} → Site",
        oversize_permit_needed=oversize,
    )

    # Factory processing time (3-5 days depending on utilization)
    factory_days = 3 if factory.current_utilization_pct < 60 else 5

    route = Route(
        id=f"via_{factory.id}_{supplier.id}",
        description=f"{supplier.name} → {factory.name} → Site",
        legs=[leg1, leg2],
        requires_staging=factory.staging_yard,
    )
    route.compute_totals()
    route.total_transit_days += factory_days  # Add assembly time
    return route


def find_optimal_routes(
    material_id: str,
    variant_id: str,
    site_lat: float,
    site_lon: float,
    sqft_needed: float = 1200,
    max_results: int = 5,
) -> list[RouteOption]:
    """
    Find and rank all viable supply chain routes for a material to a site.

    Evaluates:
    1. Direct ship from each supplier
    2. Supplier → nearest factory → site (multi-leg)

    Returns ranked RouteOptions sorted by total landed cost.
    """
    site = Location(lat=site_lat, lon=site_lon, city="Job Site")
    suppliers = get_suppliers_for_material(material_id)
    quotes = get_quotes_for_variant(variant_id)
    factories = get_factories_for_material(material_id)

    options: list[RouteOption] = []

    for supplier in suppliers:
        # Find matching quote
        quote = next((q for q in quotes if q.supplier_id == supplier.id), None)
        if quote is None:
            continue

        # Get material category for tariff lookup
        from firecore_materials import load_material
        mat = load_material(material_id)
        mat_category = mat.category.value

        # Option A: Direct ship
        direct_route = _build_direct_route(supplier, site)
        landed = compute_landed_cost(
            supplier, quote, site, sqft_needed, mat_category, mat.carbon_kg_per_sqft
        )
        options.append(RouteOption(
            supplier_id=supplier.id,
            factory_id=None,
            material_id=material_id,
            variant_id=variant_id,
            route=direct_route,
            landed_cost_per_sqft=landed.cost_per_sqft,
            total_cost=landed.total_cost,
            total_days=landed.total_lead_time_days,
            carbon_kg=landed.carbon_kg,
            buy_america=landed.buy_america_compliant,
        ))

        # Option B: Via each compatible factory
        for factory in factories:
            factory_route = _build_factory_route(supplier, factory, site)
            # Add factory route cost to landed cost
            factory_freight_adder = factory_route.total_cost - direct_route.total_cost
            factory_total = landed.total_cost + max(0, factory_freight_adder)
            factory_days = landed.total_lead_time_days + factory_route.total_transit_days - direct_route.total_transit_days

            options.append(RouteOption(
                supplier_id=supplier.id,
                factory_id=factory.id,
                material_id=material_id,
                variant_id=variant_id,
                route=factory_route,
                landed_cost_per_sqft=round(factory_total / sqft_needed, 2) if sqft_needed > 0 else 0,
                total_cost=round(factory_total, 2),
                total_days=max(factory_days, landed.total_lead_time_days),
                carbon_kg=round(landed.carbon_kg + factory_route.total_carbon_kg, 1),
                buy_america=landed.buy_america_compliant,
            ))

    # Sort by total cost and assign ranks
    options.sort(key=lambda o: o.total_cost)
    for i, opt in enumerate(options):
        opt.rank = i + 1

    return options[:max_results]
