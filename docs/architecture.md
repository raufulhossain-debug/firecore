# Prefab IP Licensing Platform — Technical Spec & Architecture
**Working title: "FireCore / ClimateCore"**
**Version 0.1 — April 2026**

---

## 1. Product thesis

A platform that licenses **pre-certified, climate-resilient prefab housing SKUs** to modular factories and developers, delivered via a parametric configurator that generates permit-ready plan sets scoped to the buyer's specific parcel.

Revenue mechanics:
- **Per-unit royalty** (primary): 4–8% of built cost, or fixed $4K–$10K per unit
- **Regional exclusivity fee** (optional): upfront, per factory per region
- **Configurator SaaS** (developer/homeowner side): $500–$2,000 per generated plan set
- **Preferred-supplier rebate** (BOM): 3–8% on specified components

---

## 2. System architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    FRONT-END LAYER                           │
│  Homeowner/developer web app  │  Licensee factory portal     │
└──────────────────────┬───────────────────┬──────────────────┘
                       │                   │
┌──────────────────────▼───────────────────▼──────────────────┐
│                   APPLICATION LAYER                          │
│  Configurator engine  │  Licensing/royalty  │  Admin/CMS     │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                     CORE SERVICES                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │Site Intel   │ │Rules Engine │ │Parametric   │            │
│  │(GIS/parcel) │ │(zoning/code)│ │SKU solver   │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │Drawing Gen  │ │BOM Gen      │ │Cert Registry│            │
│  │(CAD/BIM)    │ │(suppliers)  │ │(HUD/ICC/7A) │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                     DATA LAYER                               │
│  Parcel DB │ Zoning DB │ Hazard DB │ SKU DB │ Royalty ledger│
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Core services — detail

### 3.1 Site Intelligence service

**Purpose:** Given a US address or APN, return a structured "site constraints object."

**Data sources:**
| Data | Source | API/Access | Cost |
|---|---|---|---|
| Parcel geometry + APN | Regrid (paid) or county GIS | REST/WFS | $0.01–$0.10/lookup |
| Zoning | Zoneomics / county GIS / Symbium | REST | $0.05–$0.50/lookup |
| FEMA flood | NFHL (free) | ArcGIS REST | Free |
| Wildfire (CA) | CalFire FHSZ | ArcGIS REST | Free |
| Seismic | USGS Design Maps | REST | Free |
| Wind/snow | ASCE Hazard Tool API | REST | Free (registered) |
| Topography/slope | USGS 3DEP | DEM tiles | Free |
| Soils | NRCS SSURGO | REST | Free |
| Transit proximity | GTFS feeds / Google Distance Matrix | REST | $0.005/call |

**Output schema (JSON):**
```json
{
  "apn": "4420-015-012",
  "address": "...",
  "lot_sqft": 7200,
  "lot_geometry_wkt": "POLYGON((...))",
  "zone_code": "R1",
  "overlays": ["HPOZ-Angelino-Heights"],
  "setbacks": {"front": 20, "side": 5, "rear": 15},
  "height_limit_ft": 33,
  "max_coverage_pct": 45,
  "flood": {"zone": "X", "bfe_ft": null},
  "fire": {"fhsz": "VHFHSZ", "wui": true},
  "seismic": {"site_class": "D", "sds": 1.8},
  "wind_mph": 95,
  "snow_psf": 0,
  "slope_pct": 3.2,
  "transit_half_mi": true,
  "existing_coverage_pct": 38
}
```

### 3.2 Rules Engine

**Purpose:** Translate site constraints × target jurisdiction × target SKU into a pass/fail + buildable-envelope spec.

**Implementation options:**
- **Option 1 — DSL-based** (recommended): Write zoning rules in a constrained DSL (Python/YAML hybrid) that's human-auditable by code consultants. Prevents drift between "what the code says" and "what the software does."
- **Option 2 — LLM-assisted**: Use an LLM over code text to answer compliance questions. Faster to prototype; not auditable enough for production.
- **Option 3 — Hybrid**: LLM drafts DSL; human code consultant reviews and signs off per jurisdiction.

**Jurisdiction coverage priority (year 1):**
1. LA City (LAMC §12.22 A.33 + Standard Plan Program)
2. San Jose (Pre-Approved ADU Program)
3. San Diego (Companion Unit Program)
4. Oakland (ADU rules)
5. Sacramento
6. Seattle (DADU rules)
7. Portland (ADU rules)
8. Denver (ADU rules)
9. Austin (ADU rules)
10. Miami-Dade (for flood SKU later)

~10 jurisdictions covers ~40% of the high-value ADU/prefab market.

### 3.3 Parametric SKU solver

**Purpose:** Given a buildable envelope and a SKU's variation parameters, find a valid configuration (or return "no fit").

**Tech stack:**
- **Core geometry:** Rhino Compute (headless Rhino/Grasshopper) OR Shapely+NumPy for 2D-only MVP
- **Long-term:** Speckle for multi-format interchange; IFC.js for browser preview
- **Each SKU** is defined as:
  - Fixed structural spine (unchangeable — this is what's certified)
  - Parametric variables with discrete allowed values (rotation, pitch, glazing slots, etc.)
  - Hard constraints (max footprint, min setback, slope tolerance)
  - Soft preferences (orientation for solar, etc.)

**Solver approach:** Constraint satisfaction (CSP) over discrete parameters. For MVP, brute-force enumeration is fine (<1,000 combinations per SKU).

### 3.4 Drawing/BIM generator

**Purpose:** Emit a permit-ready package scoped to the chosen configuration.

**MVP output:**
- Site plan PDF (scaled, dimensioned, showing setbacks)
- Floor plan PDF (from SKU template, rotated/mirrored as chosen)
- Elevations (4-side, generated from parametric choices)
- Structural cover sheet (referencing certified calcs — not re-running them)
- Title 24 energy compliance sheet (pre-calculated per SKU variant)
- BOM with supplier SKUs

**Production output (v2+):**
- Full CD set, sealed by licensed architect/engineer of record
- IFC + Revit files for factory
- Factory cut files (Weinmann BTL, Hundegger cambium-X)

**Critical legal reality:** Drawings submitted for permit must be stamped by a California-licensed architect (Business & Professions Code §5536). The platform doesn't replace the stamp — it feeds the architect a 95%-complete package they review and seal. Model: your company employs or contracts 1–2 staff architects who review configurator outputs and stamp. Throughput: a staff architect can review/stamp 3–5 pre-approved configurations per day.

### 3.5 Certification Registry

**Purpose:** Source of truth for what's certified where. Every generated plan set references a specific certification ID + version.

**Tracked items per SKU:**
- HUD modular approval (if applicable)
- State DSA/HCD modular approval
- ICC-ES reports for novel assemblies
- Chapter 7A compliance package
- FORTIFIED/IBHS rating (for later SKUs)
- Title 24 compliance (per climate zone)
- Manufacturer QC plan

**Version control:** Same git-style versioning as software. A factory producing under license must reference a specific SKU-version hash. Changes require re-cert (expensive — avoid).

### 3.6 Licensing & royalty ledger

**Purpose:** Track every generated plan → built unit → royalty owed.

- Serialized plan ID per generation
- Licensee reports unit completion + address
- Automated royalty invoice
- Audit log (immutable, potentially on-chain if you want to pitch that; realistically Postgres + append-only table is fine)
- Factory QC data upload (photos, inspection reports, testing results)

---

## 4. Tech stack recommendation

| Layer | Tech | Rationale |
|---|---|---|
| Front-end | Next.js + TypeScript + Tailwind | Standard, fast, good map integration |
| Maps/GIS | Mapbox GL + Turf.js | Best-in-class for parcel/polygon UX |
| Backend API | Python FastAPI | Rich GIS + CAD ecosystem |
| Database | PostgreSQL + PostGIS | Spatial queries, parcel geometry |
| Object storage | S3 or R2 | Plan sets, CAD files |
| Geometry | Shapely (MVP) → Rhino Compute (v2) | Progressive complexity |
| PDF gen | ReportLab + WeasyPrint | Flexible document generation |
| Rules DSL | Custom Python DSL | Auditable by non-engineers |
| Auth | Clerk or Auth0 | Separate homeowner vs. licensee flows |
| Payments | Stripe | Royalty invoicing + SaaS |
| CAD interchange | Speckle | Revit/Rhino/IFC bridge |

---

## 5. Build phases & milestones

### Phase 0 — Foundation (months 0–6)
**Goal:** Prove technical fit for one SKU in one city.
- Design FireCore-1200 SKU with a licensed architect + structural engineer (~$80–150K)
- Begin LA Standard Plan Program certification (~$20–40K + 4–8 months review)
- Build Site Intelligence service for LA (APIs + parsers)
- Build Rules Engine for LA ADU code (DSL + 50–100 rules)
- Build 2D parametric solver in Shapely
- Manual-assist feasibility reports (no customer-facing app yet)
- **Deliverable:** Internal demo like Part A prototype. 1–2 modular factories under LOI.
- **Team:** 1 founder, 1 senior full-stack eng, 1 licensed architect (contract), 1 SE (contract)
- **Burn:** ~$600K

### Phase 1 — MVP launch (months 6–15)
**Goal:** First licensed unit built and revenue flowing.
- Complete LA Standard Plan approval
- Sign 2 modular factory licensees (LOIs → agreements)
- Launch homeowner-facing configurator (LA only, FireCore-1200 only)
- Deliverables engine generating permit-ready PDFs (architect-reviewed + stamped)
- Licensing portal for factories
- First 5–20 licensed units built
- **Deliverable:** $200K–$1M ARR, 2 factory partners, proven unit economics
- **Team:** +1 eng, +1 architect-of-record (FTE), +1 BD
- **Burn:** ~$1.2M incremental

### Phase 2 — Multi-jurisdiction + 2nd SKU (months 15–30)
**Goal:** Expand rules engine to 4 cities; add hillside-pier SKU variant.
- Add San Jose, San Diego, Oakland rules
- Certify the stepped-pier foundation variant (closes 15% gap from Part B study)
- Open configurator to 4 cities
- Sign 5+ factory licensees total
- Begin design on flood SKU (Florida/Gulf focus)
- **Deliverable:** $2M–$5M ARR, geographic + SKU diversification, Series A readable
- **Team:** +2 eng, +1 code consultant, +2 BD, +1 PM
- **Burn:** ~$3M incremental

### Phase 3 — Climate catalog + insurance partnership (months 30+)
- Flood SKU certified + licensed (Miami-Dade pilot)
- FORTIFIED partnership for insurance premium discount pass-through
- Desert/extreme-heat SKU
- International exploration (Canada cold-climate, Gulf heat)

---

## 6. Costs & capital plan (rough)

| Phase | Dur. | Burn | Key outputs |
|---|---|---|---|
| 0 — Foundation | 6 mo | $600K | SKU designed, LA cert filed, internal demo |
| 1 — MVP | 9 mo | $1.2M | LA cert done, 2 licensees, first units built |
| 2 — Expand | 15 mo | $3M | 4 cities, 2 SKUs, 5+ licensees, $2–5M ARR |
| **Total to Series A** | **30 mo** | **~$4.8M** | Defensible IP + GTM proof |

**Pre-seed/seed target:** $2–3M to fund Phase 0 + early Phase 1.
**Series A target:** $10–15M at end of Phase 1 / start of Phase 2, premised on licensed-unit velocity.

---

## 7. Key risks & mitigations

| Risk | Mitigation |
|---|---|
| Disintermediation — factories copy SKU | Cert portfolio + brand + insurance partnership; trade-secret BIM + utility patents on novel assemblies |
| Code drift between jurisdictions | DSL + code consultant per jurisdiction; re-audit quarterly |
| Architect-of-record bottleneck | Staff 1 senior + 1 junior from day 1; build reviewer tooling that bundles 80% of the check |
| Certification delay | Start CA Standard Plan filing before software is built (it's the long pole) |
| Liability from licensed-built defects | Strong licensing agreement + mandatory licensee E&O + QA audits; never take design-of-record liability |
| Modular factory partner fails | Non-exclusive at first; regional exclusivity only after 12 mo proven performance |
| Low per-unit royalty dollars | Couple royalty with preferred-supplier rebate (3–8% BOM margin) |
| Scope creep to "any house, anywhere" | Say no. One climate, one lot archetype, two cities before expanding. |

---

## 8. Defensibility stack

Ranked strongest → weakest:

1. **Certification portfolio** (HUD, ICC-ES, Chapter 7A, Standard Plan approvals). Takes years + real money. This is the moat.
2. **Insurance partnerships** (FORTIFIED-equivalent → premium discount). Network effect — the more units built, the more actuarial data, the better the discount.
3. **Factory relationships + exclusive regions.** Hard to dislodge an incumbent licensee.
4. **Brand trust** (homeowner + lender + inspector recognition of the SKU name).
5. **Jurisdictional rules engine.** Hard to replicate but eventually commoditizes.
6. **Parametric SKU solver.** Commodity tech, no real moat.
7. **Architectural design itself.** Weakly protected by copyright; narrowly by design patent.

The correct strategy: invest aggressively in 1–3, use 4–6 as product leverage, don't pretend 7 is defensible.

---

## 9. Open questions for the founder

- Do you have a founding architect/structural engineer co-founder? If not, this is your #1 hiring priority. No amount of software compensates.
- Which California modular factory can you get to LOI first? Factory Built Homes (Hanford), Pacific Modern Homes (Sacramento), Connect Homes (Anza) are reasonable first calls.
- Are you willing to run this as a services-heavy business for 18 months before it looks like a software company? Because that's the shape of year 1.
- Do you have relationships with LA Building & Safety or HCD? Warm-intro into the Standard Plan Program office saves months.

---

## 10. Recommended reading / precedents

- **ARM Holdings model** — licensing economics
- **FORTIFIED Home (IBHS)** — certification-as-product
- **Higharc** — configurator UX for production homes (conventional, not prefab)
- **Symbium** — ADU zoning rules engine (complementary, possibly partnership)
- **Plant Prefab / Connect Homes / Dvele** — vertically integrated prefab (study what they got wrong on margins)
- **Katerra post-mortem** — cautionary tale on vertical integration
- **LA City Standard Plan Program** (ladbs.org) — actual cert pathway to target
