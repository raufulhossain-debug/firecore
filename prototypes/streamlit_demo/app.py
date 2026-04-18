"""
FireCore-1200 ADU Feasibility Prototype
----------------------------------------
A Streamlit web app that takes a Los Angeles parcel (address or manual
characteristics), evaluates it against the FireCore-1200 wildfire-resilient
ADU SKU, and returns a feasibility report + indicative site plan.

Run locally:
    pip install streamlit shapely matplotlib requests
    streamlit run A_firecore_prototype.py

Notes on honesty:
    - Live parcel/zoning/FHSZ API calls work when the network allows; when
      they fail, the app falls back to user-entered characteristics so the
      rules engine and solver are still fully demoable.
    - This is a feasibility-grade tool. Outputs are NOT permit-ready
      drawings. Real permit sets require an architect-of-record stamp.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import requests
import streamlit as st
from shapely.geometry import Polygon, box

# ---------------------------------------------------------------------------
# SKU definition — FireCore-1200
# ---------------------------------------------------------------------------

@dataclass
class SkuVariant:
    name: str
    footprint: tuple[int, int]  # width x depth, feet
    stories: int
    height_ft: int
    foundation: str  # "slab" | "raised_pier" | "stepped_pier"
    conditioned_sqft: int

FIRECORE_VARIANTS = [
    SkuVariant("Standard 1-story",  (30, 40), 1, 16, "slab",         1200),
    SkuVariant("Compact 2-story",   (24, 25), 2, 25, "slab",         1200),
    SkuVariant("Flood raised-pier", (30, 40), 1, 22, "raised_pier",  1200),
    SkuVariant("Hillside stepped",  (30, 40), 1, 18, "stepped_pier", 1200),  # future cert
]

FIRECORE_ROOF_PITCHES = ["3:12", "4:12", "5:12"]  # all Class-A certified

# ---------------------------------------------------------------------------
# Site constraints object (populated from APIs or user input)
# ---------------------------------------------------------------------------

@dataclass
class Site:
    address: str = ""
    apn: str = ""
    lot_sqft: int = 7200
    lot_width_ft: int = 60
    lot_depth_ft: int = 120
    zone_code: str = "R1"
    setback_front_ft: int = 20
    setback_side_ft: int = 5
    setback_rear_ft: int = 15
    max_coverage_pct: int = 45
    existing_coverage_pct: int = 35
    height_limit_ft: int = 33
    fhsz: str = "Non-HFHSZ"     # "Non-HFHSZ" | "Moderate" | "High" | "VHFHSZ"
    flood_zone: str = "X"        # "X" | "AE" | "VE"
    bfe_ft: float = 0.0          # base flood elevation (if flood)
    slope_pct: float = 3.0
    transit_half_mi: bool = True
    overlays: list[str] = field(default_factory=list)

# ---------------------------------------------------------------------------
# Evaluation logic
# ---------------------------------------------------------------------------

@dataclass
class GateResult:
    name: str
    passed: bool
    notes: str

@dataclass
class FitResult:
    variant: SkuVariant
    gates: list[GateResult]
    outcome: str   # EXACT | MINOR | MAJOR | NO_FIT
    buildable_box: Optional[tuple[float, float]] = None
    reasoning: str = ""

    @property
    def passed_all(self) -> bool:
        return all(g.passed for g in self.gates)

def buildable_envelope(site: Site) -> tuple[float, float]:
    """Usable rectangle after setbacks (width, depth)."""
    w = max(0.0, site.lot_width_ft - 2 * site.setback_side_ft)
    d = max(0.0, site.lot_depth_ft - site.setback_front_ft - site.setback_rear_ft)
    return w, d

def evaluate_variant(site: Site, variant: SkuVariant) -> FitResult:
    gates: list[GateResult] = []
    w_env, d_env = buildable_envelope(site)
    gates.append(GateResult(
        "Lot size / buildable envelope",
        w_env >= variant.footprint[0] and d_env >= variant.footprint[1],
        f"Envelope {w_env:.0f}×{d_env:.0f} ft vs. SKU {variant.footprint[0]}×{variant.footprint[1]} ft",
    ))

    added_coverage_pct = (variant.footprint[0] * variant.footprint[1]) / site.lot_sqft * 100
    total_coverage = site.existing_coverage_pct + added_coverage_pct
    gates.append(GateResult(
        "Lot coverage",
        total_coverage <= site.max_coverage_pct,
        f"Existing {site.existing_coverage_pct}% + SKU {added_coverage_pct:.1f}% = {total_coverage:.1f}% (max {site.max_coverage_pct}%)",
    ))

    if variant.stories == 2:
        height_ok = variant.height_ft <= 25 and (site.transit_half_mi or variant.height_ft <= 16)
        gates.append(GateResult(
            "Height (2-story)",
            height_ok,
            "Requires ½-mi transit or ≤16 ft; transit=" + ("yes" if site.transit_half_mi else "no"),
        ))
    else:
        gates.append(GateResult(
            "Height (1-story)",
            variant.height_ft <= 16,
            f"{variant.height_ft} ft ≤ 16 ft by-right",
        ))

    fire_ok = True
    fire_notes = "SKU native Chapter 7A package sufficient"
    if site.fhsz in ("High", "VHFHSZ"):
        fire_notes = "VHFHSZ — SKU 7A package required (covered); confirm 100-ft defensible space"
    gates.append(GateResult("Fire / WUI compliance", fire_ok, fire_notes))

    if site.flood_zone in ("AE", "VE"):
        flood_ok = variant.foundation == "raised_pier"
        gates.append(GateResult(
            "Flood compliance",
            flood_ok,
            f"SFHA {site.flood_zone} (BFE {site.bfe_ft} ft) — requires raised-pier variant",
        ))
    else:
        gates.append(GateResult("Flood compliance", True, "Outside SFHA"))

    slope_ok = site.slope_pct <= 15 or variant.foundation == "stepped_pier"
    slope_note = f"Slope {site.slope_pct:.1f}% vs. tolerance "
    slope_note += "≤40% (stepped-pier)" if variant.foundation == "stepped_pier" else "≤15% (slab)"
    gates.append(GateResult("Slope feasibility", slope_ok, slope_note))

    passed = all(g.passed for g in gates)

    needs_minor = variant.name != "Standard 1-story"
    if passed:
        outcome = "EXACT" if not needs_minor else "MINOR"
    else:
        failed_on_slope = not any(g.passed for g in gates if g.name == "Slope feasibility")
        outcome = "MAJOR" if failed_on_slope else "NO_FIT"

    reasoning = _explain(gates, outcome, variant)

    return FitResult(
        variant=variant,
        gates=gates,
        outcome=outcome,
        buildable_box=(w_env, d_env),
        reasoning=reasoning,
    )

def _explain(gates, outcome, variant):
    failed = [g for g in gates if not g.passed]
    if outcome == "EXACT":
        return f"Standard 1-story FireCore-1200 fits exactly — all gates pass."
    if outcome == "MINOR":
        return f"Fits with in-envelope variation ({variant.name}). Stays within certification."
    if outcome == "MAJOR":
        return "Slope exceeds certified envelope. Requires stepped-pier variant (future cert) or custom foundation."
    return "No in-envelope configuration fits. Binding constraints: " + ", ".join(g.name for g in failed)

def best_fit(site: Site, allow_future_cert: bool = False) -> FitResult:
    results = []
    for v in FIRECORE_VARIANTS:
        if v.foundation == "stepped_pier" and not allow_future_cert:
            continue
        results.append(evaluate_variant(site, v))

    order = {"EXACT": 0, "MINOR": 1, "MAJOR": 2, "NO_FIT": 3}
    results.sort(key=lambda r: order[r.outcome])
    return results[0]

# ---------------------------------------------------------------------------
# Best-effort public-data lookups (graceful fallback)
# ---------------------------------------------------------------------------

def try_fema_flood_zone(lon: float, lat: float) -> Optional[dict]:
    """FEMA NFHL is a public ArcGIS service. May be blocked by sandbox."""
    url = (
        "https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer/28/query"
        f"?geometry={lon},{lat}&geometryType=esriGeometryPoint"
        "&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=FLD_ZONE,STATIC_BFE&f=json"
    )
    try:
        r = requests.get(url, timeout=6)
        if r.status_code == 200:
            js = r.json()
            feats = js.get("features", [])
            if feats:
                attrs = feats[0].get("attributes", {})
                return {"zone": attrs.get("FLD_ZONE", "X"),
                        "bfe": attrs.get("STATIC_BFE") or 0.0}
            return {"zone": "X", "bfe": 0.0}
    except Exception:
        pass
    return None

def try_calfire_fhsz(lon: float, lat: float) -> Optional[str]:
    """CalFire FHSZ ArcGIS — may be blocked by sandbox."""
    url = (
        "https://egis.fire.ca.gov/arcgis/rest/services/FHSZ/FHSZ_SRA_LRA_Combined/MapServer/0/query"
        f"?geometry={lon},{lat}&geometryType=esriGeometryPoint"
        "&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=HAZ_CODE&f=json"
    )
    try:
        r = requests.get(url, timeout=6)
        if r.status_code == 200:
            feats = r.json().get("features", [])
            if feats:
                code = feats[0]["attributes"].get("HAZ_CODE")
                return {1: "Moderate", 2: "High", 3: "VHFHSZ"}.get(code, "Non-HFHSZ")
    except Exception:
        pass
    return None

# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------

def draw_site_plan(site: Site, fit: FitResult):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_aspect("equal")
    ax.add_patch(patches.Rectangle(
        (0, 0), site.lot_width_ft, site.lot_depth_ft,
        fill=True, facecolor="#f6f6f2", edgecolor="#444", linewidth=1.5))

    w_env, d_env = buildable_envelope(site)
    ax.add_patch(patches.Rectangle(
        (site.setback_side_ft, site.setback_front_ft), w_env, d_env,
        fill=False, edgecolor="#888", linestyle="--"))

    if fit.outcome in ("EXACT", "MINOR"):
        fw, fd = fit.variant.footprint
        x = site.setback_side_ft + (w_env - fw) / 2
        y = site.setback_front_ft + (d_env - fd) / 2
        color = "#2f8f4e" if fit.outcome == "EXACT" else "#c68a00"
        ax.add_patch(patches.Rectangle((x, y), fw, fd, fill=True,
                                       facecolor=color, alpha=0.55, edgecolor=color))
        ax.text(x + fw / 2, y + fd / 2, fit.variant.name,
                ha="center", va="center", fontsize=9, color="white", fontweight="bold")

    ax.set_xlim(-10, site.lot_width_ft + 10)
    ax.set_ylim(-10, site.lot_depth_ft + 10)
    ax.set_title(f"Feasibility: {fit.outcome}  |  Zone {site.zone_code}  |  {site.lot_sqft} sqft")
    ax.set_xlabel("ft")
    ax.set_ylabel("ft")
    return fig

# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(page_title="FireCore-1200 Feasibility", layout="wide")
    st.title("FireCore-1200 — ADU Feasibility Prototype")
    st.caption("Los Angeles | Wildfire-resilient prefab ADU licensing platform — feasibility demo")

    with st.sidebar:
        st.header("Site inputs")
        st.markdown("Live APIs attempted; fall back to manual if blocked.")

        mode = st.radio("Input mode", ["Manual entry", "Address lookup (best-effort)"])

        site = Site()

        if mode == "Address lookup (best-effort)":
            st.text_input("Address", key="addr", placeholder="1234 Example St, Los Angeles, CA")
            lat = st.number_input("Latitude",  value=34.05, format="%.5f")
            lon = st.number_input("Longitude", value=-118.25, format="%.5f")
            if st.button("Attempt live lookup"):
                with st.spinner("Querying FEMA + CalFire…"):
                    flood = try_fema_flood_zone(lon, lat)
                    fhsz  = try_calfire_fhsz(lon, lat)
                if flood:
                    site.flood_zone = flood["zone"]
                    site.bfe_ft = float(flood["bfe"] or 0)
                    st.success(f"FEMA: {flood['zone']} (BFE {site.bfe_ft})")
                else:
                    st.warning("FEMA lookup unavailable; use manual below.")
                if fhsz:
                    site.fhsz = fhsz
                    st.success(f"CalFire FHSZ: {fhsz}")
                else:
                    st.warning("CalFire lookup unavailable; use manual below.")

        st.divider()
        st.subheader("Lot")
        site.zone_code = st.selectbox("Zone", ["R1", "R2", "R3", "RD1.5", "RE11", "RE15", "RE20"], index=0)
        site.lot_width_ft = st.number_input("Lot width (ft)", 20, 500, 60)
        site.lot_depth_ft = st.number_input("Lot depth (ft)", 40, 500, 120)
        site.lot_sqft = site.lot_width_ft * site.lot_depth_ft
        st.metric("Lot area", f"{site.lot_sqft:,} sqft")

        st.subheader("Setbacks (state ADU mins)")
        site.setback_front_ft = st.slider("Front", 0, 30, 20)
        site.setback_side_ft  = st.slider("Side",  0, 15, 4)
        site.setback_rear_ft  = st.slider("Rear",  0, 25, 4)

        st.subheader("Context")
        site.max_coverage_pct      = st.slider("Zone max coverage %", 20, 80, 45)
        site.existing_coverage_pct = st.slider("Existing coverage %", 0, 80, 35)
        site.slope_pct             = st.slider("Average slope %",     0.0, 60.0, 3.0)
        site.transit_half_mi       = st.checkbox("Within ½-mi major transit", value=True)

        st.subheader("Hazards")
        site.fhsz = st.selectbox("FHSZ", ["Non-HFHSZ", "Moderate", "High", "VHFHSZ"],
                                 index=["Non-HFHSZ","Moderate","High","VHFHSZ"].index(site.fhsz))
        site.flood_zone = st.selectbox("FEMA flood zone", ["X", "AE", "VE"],
                                       index=["X","AE","VE"].index(site.flood_zone))
        if site.flood_zone in ("AE", "VE"):
            site.bfe_ft = st.number_input("Base flood elevation (ft)", 0.0, 30.0, site.bfe_ft or 8.0)

        allow_future_cert = st.checkbox("Include future stepped-pier cert", value=False,
                                        help="Models the slope-gap closure proposed in Part B.")

    fit = best_fit(site, allow_future_cert=allow_future_cert)

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Feasibility result")
        badge = {"EXACT":"✅ EXACT FIT","MINOR":"🟡 MINOR VARIATION (in envelope)",
                 "MAJOR":"🟠 MAJOR VARIATION (out of envelope)","NO_FIT":"🔴 NO FIT"}[fit.outcome]
        st.markdown(f"### {badge}")
        st.markdown(f"**Recommended variant:** {fit.variant.name}")
        st.markdown(f"**Reasoning:** {fit.reasoning}")

        st.subheader("Gate checks")
        for g in fit.gates:
            st.markdown(("✅ " if g.passed else "❌ ") + f"**{g.name}** — {g.notes}")

        st.subheader("Indicative BOM class")
        st.markdown(
            "- Class-A fiber-cement cladding\n"
            "- Ember-resistant vents (8×)\n"
            "- Tempered dual-pane low-E windows\n"
            "- 1-hr rated soffits / eaves\n"
            "- Foundation: **" + fit.variant.foundation + "**\n"
            "- Title 24 compliance package (CZ8/CZ9)"
        )

    with col_right:
        st.subheader("Site plan (indicative)")
        st.pyplot(draw_site_plan(site, fit))

        st.caption(
            "**Not a permit set.** Drawings submitted to LA DBS for ADU "
            "permit must be stamped by a CA-licensed architect. This app "
            "outputs feasibility only."
        )

    st.divider()
    with st.expander("About this prototype"):
        st.markdown("""
This is a **feasibility-grade** prototype of the front end of the prefab IP
licensing platform. It demonstrates three of the six core services described
in the technical spec:

1. **Site Intelligence** (best-effort public API lookup + manual override)
2. **Rules Engine** (LA ADU rules + Chapter 7A + flood + slope gates)
3. **Parametric SKU solver** (selects best-fit FireCore-1200 variant)

What it deliberately does **not** do:
- Generate permit-ready stamped drawings (requires architect-of-record)
- Run structural/Title 24 calcs (references certified SKU package by ID)
- Cover jurisdictions beyond LA
- Track royalties, licensees, or factory QC
- Produce factory cut files

The gap between this demo and a real product is roughly 18–30 months of
focused work + ~$4–5M, per the phased plan in the architecture doc.
""")

if __name__ == "__main__":
    main()
