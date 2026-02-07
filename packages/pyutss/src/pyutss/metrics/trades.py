"""Trade statistics calculations."""

from __future__ import annotations

from pyutss.results.types import BacktestResult


def calculate_trade_statistics(result: BacktestResult) -> dict[str, float]:
    """Calculate trade statistics."""
    closed_trades = [t for t in result.trades if not t.is_open]

    if not closed_trades:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "largest_win": 0.0,
            "largest_loss": 0.0,
            "avg_trade_pnl": 0.0,
            "avg_trade_duration_days": 0.0,
        }

    total_trades = len(closed_trades)
    winning_trades = [t for t in closed_trades if t.pnl > 0]
    losing_trades = [t for t in closed_trades if t.pnl < 0]

    win_count = len(winning_trades)
    loss_count = len(losing_trades)

    win_rate = (win_count / total_trades) * 100 if total_trades > 0 else 0.0

    gross_profit = sum(t.pnl for t in winning_trades)
    gross_loss = abs(sum(t.pnl for t in losing_trades))

    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    else:
        profit_factor = float("inf") if gross_profit > 0 else 0.0

    avg_win = gross_profit / win_count if win_count > 0 else 0.0
    avg_loss = gross_loss / loss_count if loss_count > 0 else 0.0

    largest_win = max((t.pnl for t in winning_trades), default=0.0)
    largest_loss = abs(min((t.pnl for t in losing_trades), default=0.0))

    avg_trade_pnl = sum(t.pnl for t in closed_trades) / total_trades

    durations = []
    for trade in closed_trades:
        if trade.exit_date is not None:
            duration = (trade.exit_date - trade.entry_date).days
            durations.append(duration)

    avg_duration = sum(durations) / len(durations) if durations else 0.0

    return {
        "total_trades": total_trades,
        "winning_trades": win_count,
        "losing_trades": loss_count,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "largest_win": largest_win,
        "largest_loss": largest_loss,
        "avg_trade_pnl": avg_trade_pnl,
        "avg_trade_duration_days": avg_duration,
    }
