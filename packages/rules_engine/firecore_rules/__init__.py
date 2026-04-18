"""FireCore rules engine — zoning & code rules as data.

Rules live in YAML under `jurisdictions/`. The evaluator is a thin pure-function
interpreter that applies a jurisdiction's rule set to a Site and returns per-rule
pass/fail results.
"""
from firecore_rules.types import Site, Rule, RuleResult, Jurisdiction
from firecore_rules.loader import load_jurisdiction, list_jurisdictions
from firecore_rules.evaluator import evaluate

__all__ = [
    "Site",
    "Rule",
    "RuleResult",
    "Jurisdiction",
    "load_jurisdiction",
    "list_jurisdictions",
    "evaluate",
]
