"""Engine capability reporting.

Reports what the pyutss engine actually implements vs what the UTSS
schema defines. Used for honest capability validation and gap analysis.
"""

from __future__ import annotations

from pyutss.engine.indicators.dispatcher import (
    INDICATOR_REGISTRY,
    _COMPONENT_SHORTCUTS,
)

# Indicators implemented in IndicatorService — derived from the registry
# so this can never drift out of sync with the actual dispatch code.
IMPLEMENTED_INDICATORS: set[str] = (
    set(INDICATOR_REGISTRY.keys()) | set(_COMPONENT_SHORTCUTS.keys())
)

# Signal types implemented in SignalEvaluator
IMPLEMENTED_SIGNAL_TYPES: set[str] = {
    "price", "indicator", "constant", "calendar",
    "portfolio", "$ref", "$param", "expr",
}

# Signal types defined in the schema but intentionally not yet implemented.
# These are tracked here so the sync test can distinguish "not yet" from "forgot".
DEFERRED_SIGNAL_TYPES: set[str] = {
    "fundamental", "event", "relative", "external",
}

# Condition types implemented in ConditionEvaluator
IMPLEMENTED_CONDITION_TYPES: set[str] = {
    "comparison", "and", "or", "not", "expr", "always",
}

# Action types implemented in Engine
IMPLEMENTED_ACTION_TYPES: set[str] = {
    "trade", "alert", "hold",
}

# Sizing types implemented in sizing.py
IMPLEMENTED_SIZING_TYPES: set[str] = {
    "fixed_amount", "fixed_quantity", "percent_of_equity",
    "percent_of_cash", "percent_of_position",
    "risk_based", "kelly", "volatility_adjusted",
}

# Universe types implemented in UniverseResolver
IMPLEMENTED_UNIVERSE_TYPES: set[str] = {
    "static", "index", "screener",
}


def validate_engine_capabilities() -> dict[str, dict]:
    """Compare engine capabilities against schema definitions.

    Returns a dict with keys for each capability area, containing:
    - schema: set of all schema-defined values
    - implemented: set of implemented values
    - missing: set of values in schema but not implemented
    - coverage: float percentage of schema values implemented
    """
    try:
        from utss.capabilities import (
            SUPPORTED_ACTION_TYPES,
            SUPPORTED_CONDITION_TYPES,
            SUPPORTED_INDICATORS,
            SUPPORTED_SIGNAL_TYPES,
            SUPPORTED_SIZING_TYPES,
            SUPPORTED_UNIVERSE_TYPES,
        )
    except ImportError:
        return {"error": "utss package not installed"}

    def _compare(schema_list: list[str], implemented: set[str]) -> dict:
        schema_set = set(schema_list)
        missing = schema_set - implemented
        coverage = len(schema_set & implemented) / len(schema_set) * 100 if schema_set else 100
        return {
            "schema": schema_set,
            "implemented": implemented,
            "missing": missing,
            "coverage": round(coverage, 1),
        }

    return {
        "indicators": _compare(SUPPORTED_INDICATORS, IMPLEMENTED_INDICATORS),
        "signal_types": _compare(SUPPORTED_SIGNAL_TYPES, IMPLEMENTED_SIGNAL_TYPES),
        "condition_types": _compare(SUPPORTED_CONDITION_TYPES, IMPLEMENTED_CONDITION_TYPES),
        "action_types": _compare(SUPPORTED_ACTION_TYPES, IMPLEMENTED_ACTION_TYPES),
        "sizing_types": _compare(SUPPORTED_SIZING_TYPES, IMPLEMENTED_SIZING_TYPES),
        "universe_types": _compare(SUPPORTED_UNIVERSE_TYPES, IMPLEMENTED_UNIVERSE_TYPES),
    }


def print_capability_report() -> None:
    """Print a human-readable capability report."""
    report = validate_engine_capabilities()
    if "error" in report:
        print(f"Error: {report['error']}")
        return

    print("=" * 60)
    print("UTSS Engine Capability Report")
    print("=" * 60)

    for area, data in report.items():
        total = len(data["schema"])
        implemented = len(data["schema"] & data["implemented"])
        print(f"\n{area}: {implemented}/{total} ({data['coverage']}%)")
        if data["missing"]:
            for m in sorted(data["missing"]):
                print(f"  - {m}")
