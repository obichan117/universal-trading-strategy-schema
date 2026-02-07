"""Period breakdown calculations."""

from __future__ import annotations

from pyutss.metrics.types import PeriodBreakdown
from pyutss.results.types import BacktestResult


def period_breakdown(
    result: BacktestResult,
    period_type: str,
) -> list[PeriodBreakdown]:
    """Generate period breakdown.

    Args:
        result: BacktestResult with equity curve and portfolio history.
        period_type: "month" or "year".
    """
    if len(result.equity_curve) < 1 or not result.portfolio_history:
        return []

    breakdowns: list[PeriodBreakdown] = []
    period_format = "%Y-%m" if period_type == "month" else "%Y"

    periods: dict[str, list] = {}
    for snapshot in result.portfolio_history:
        period_key = snapshot.date.strftime(period_format)
        if period_key not in periods:
            periods[period_key] = []
        periods[period_key].append(snapshot)

    for period_key in sorted(periods.keys()):
        snapshots = periods[period_key]

        start_snapshot = snapshots[0]
        end_snapshot = snapshots[-1]

        start_equity = start_snapshot.equity
        end_equity = end_snapshot.equity

        return_pct = (
            ((end_equity - start_equity) / start_equity) * 100
            if start_equity > 0
            else 0.0
        )

        period_trades = [
            t
            for t in result.trades
            if t.entry_date.strftime(period_format) == period_key
        ]
        winning = sum(1 for t in period_trades if t.pnl > 0)

        period_equity = [s.equity for s in snapshots]
        if period_equity:
            running_max = 0.0
            max_dd_pct = 0.0
            for eq in period_equity:
                running_max = max(running_max, eq)
                if running_max > 0:
                    dd_pct = ((running_max - eq) / running_max) * 100
                    max_dd_pct = max(max_dd_pct, dd_pct)
        else:
            max_dd_pct = 0.0

        breakdowns.append(
            PeriodBreakdown(
                period=period_key,
                start_date=start_snapshot.date,
                end_date=end_snapshot.date,
                start_equity=start_equity,
                end_equity=end_equity,
                return_pct=return_pct,
                trades=len(period_trades),
                winning_trades=winning,
                max_drawdown_pct=max_dd_pct,
            )
        )

    return breakdowns
