"""Engine capability reporting.

Reports what the pyutss engine actually implements vs what the UTSS
schema defines. Used for honest capability validation and gap analysis.
"""

from __future__ import annotations

# Indicators implemented in IndicatorService
IMPLEMENTED_INDICATORS: set[str] = {
    # Moving Averages
    "SMA", "EMA", "WMA", "DEMA", "TEMA", "KAMA", "HULL", "VWMA",
    # Momentum
    "RSI", "MACD", "MACD_SIGNAL", "MACD_HIST",
    "STOCH_K", "STOCH_D", "STOCH_RSI", "ROC", "MOMENTUM",
    "WILLIAMS_R", "CCI", "MFI", "CMO", "TSI",
    # Trend
    "ADX", "PLUS_DI", "MINUS_DI", "SUPERTREND", "PSAR",
    "AROON_UP", "AROON_DOWN", "AROON_OSC",
    # Volatility
    "ATR", "STDDEV", "VARIANCE",
    "BB_UPPER", "BB_MIDDLE", "BB_LOWER", "BB_WIDTH", "BB_PERCENT",
    "DC_UPPER", "DC_MIDDLE", "DC_LOWER",
    "KC_UPPER", "KC_MIDDLE", "KC_LOWER",
    # Volume
    "OBV", "VWAP", "AD", "CMF", "KLINGER",
    # Statistical
    "HIGHEST", "LOWEST", "PERCENTILE", "RANK", "ZSCORE",
    "BETA", "CORRELATION", "RETURN", "DRAWDOWN",
    # Ichimoku
    "ICHIMOKU_TENKAN", "ICHIMOKU_KIJUN",
    "ICHIMOKU_SENKOU_A", "ICHIMOKU_SENKOU_B", "ICHIMOKU_CHIKOU",
}

# Signal types implemented in SignalEvaluator
IMPLEMENTED_SIGNAL_TYPES: set[str] = {
    "price", "indicator", "constant", "calendar",
    "portfolio", "$ref", "$param", "expr",
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
            SUPPORTED_INDICATORS,
            SUPPORTED_SIGNAL_TYPES,
            SUPPORTED_CONDITION_TYPES,
            SUPPORTED_ACTION_TYPES,
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
