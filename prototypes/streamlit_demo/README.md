# Running the FireCore prototype

## One-time setup

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install streamlit shapely matplotlib requests
```

## Launch

```bash
streamlit run A_firecore_prototype.py
```

Opens in your browser at `http://localhost:8501`.

## What to try

1. Leave defaults and click around the sidebar — you should see an **EXACT FIT** on a standard R1 lot.
2. Set slope to 22% — outcome becomes **MAJOR** (slope out of envelope).
3. Now tick "Include future stepped-pier cert" — outcome becomes **MINOR** (demonstrates the Part B recommendation: closing the slope gap via one new certified variant pushes fit rate from 80% → 95%).
4. Set flood zone to AE, BFE 10 — outcome becomes **MINOR** with the raised-pier variant.
5. Set zone to R3, existing coverage 70%, lot 50×100 — forces 2-story compact variant.

## What it is / isn't

Feasibility-grade demo of the **Site Intelligence + Rules Engine + Parametric Solver** layers from the architecture doc. Not permit-ready. See the "About this prototype" panel in-app.
