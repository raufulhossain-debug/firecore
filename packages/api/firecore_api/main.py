"""FireCore HTTP API.

Exposes:
    GET  /health
    GET  /jurisdictions
    GET  /skus
    POST /evaluate       — run rules + solver against a Site
    POST /site-intel     — attempt public-API hazard lookup for a lat/lon

Run locally:
    uvicorn firecore_api.main:app --reload
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from firecore_rules import list_jurisdictions, load_jurisdiction
from firecore_rules.types import Site
from firecore_sku import list_skus, load_sku
from firecore_site import gather as gather_site_intel
from firecore_solver import best_fit, FitReport

app = FastAPI(
    title="FireCore API",
    version="0.1.0",
    description="Climate-resilient prefab SKU licensing — feasibility service.",
)

# CORS open for local dev; tighten in production via env var
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class EvaluateRequest(BaseModel):
    sku_id: str = "firecore_1200"
    jurisdiction_id: str = "la_city_adu"
    site: Site
    allow_future_cert: bool = False


class SiteIntelRequest(BaseModel):
    lat: float
    lon: float


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/jurisdictions")
def jurisdictions() -> list[str]:
    return list_jurisdictions()


@app.get("/skus")
def skus() -> list[str]:
    return list_skus()


@app.post("/evaluate", response_model=FitReport)
def evaluate_endpoint(req: EvaluateRequest) -> FitReport:
    try:
        sku = load_sku(req.sku_id)
        j = load_jurisdiction(req.jurisdiction_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return best_fit(sku, j, req.site, allow_future_cert=req.allow_future_cert)


@app.post("/site-intel")
def site_intel_endpoint(req: SiteIntelRequest) -> dict:
    snap = gather_site_intel(req.lat, req.lon)
    return snap.model_dump()
