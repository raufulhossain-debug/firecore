"""FireCore parametric solver — finds the best-fit SKU variant for a site."""
from firecore_solver.best_fit import (
    best_fit,
    FitOutcome,
    FitReport,
)

__all__ = ["best_fit", "FitOutcome", "FitReport"]
