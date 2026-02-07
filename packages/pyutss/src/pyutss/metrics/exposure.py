"""Market exposure calculations."""

from __future__ import annotations

from pyutss.results.types import BacktestResult


def calculate_exposure(result: BacktestResult) -> dict[str, float]:
    """Calculate market exposure metrics."""
    if not result.portfolio_history:
        return {
            "total_exposure_days": 0,
            "exposure_pct": 0.0,
        }

    days_with_positions = sum(
        1 for snapshot in result.portfolio_history if snapshot.positions_value > 0
    )

    total_days = len(result.portfolio_history)
    exposure_pct = (days_with_positions / total_days) * 100 if total_days > 0 else 0.0

    return {
        "total_exposure_days": days_with_positions,
        "exposure_pct": exposure_pct,
    }
