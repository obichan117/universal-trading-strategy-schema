"""Temporal signal evaluators: calendar, event."""

from typing import Any

import pandas as pd

from pyutss.engine.evaluator.context import EvaluationContext, EvaluationError


def eval_calendar_signal(
    signal: dict[str, Any], context: EvaluationContext
) -> pd.Series:
    """Evaluate calendar signal (returns boolean-like 0/1)."""
    data = context.get_data()
    field = signal.get("field", "day_of_week")
    index = data.index

    if field == "day_of_week":
        return pd.Series(index.dayofweek, index=index)
    elif field == "day_of_month":
        return pd.Series(index.day, index=index)
    elif field == "month":
        return pd.Series(index.month, index=index)
    elif field == "week_of_year":
        return pd.Series(index.isocalendar().week.values, index=index)
    elif field == "is_month_start":
        return _is_first_trading_day(index).astype(int)
    elif field == "is_month_end":
        return _is_last_trading_day(index).astype(int)
    elif field == "is_quarter_end":
        return pd.Series((index.month % 3 == 0) & (_is_last_trading_day(index)), index=index).astype(int)
    else:
        raise EvaluationError(f"Unknown calendar field: {field}")


def eval_event_signal(
    signal: dict[str, Any], context: EvaluationContext
) -> pd.Series:
    """Evaluate event signal.

    Returns 1 for dates within the event window, 0 otherwise.
    The window is defined by days_before and days_after the event date.
    """
    event_type = signal.get("event", "EARNINGS_RELEASE")
    days_before = signal.get("days_before", 0)
    days_after = signal.get("days_after", 0)
    data = context.get_data()

    if context.event_data is None:
        return pd.Series(0, index=data.index, dtype=int)

    event_dates = context.event_data.get(event_type, [])
    if not event_dates:
        return pd.Series(0, index=data.index, dtype=int)

    result = pd.Series(0, index=data.index, dtype=int)
    for event_date in event_dates:
        for i, idx in enumerate(data.index):
            current = idx.date() if hasattr(idx, "date") else idx
            diff = (event_date - current).days
            if -days_after <= diff <= days_before:
                result.iloc[i] = 1
    return result


def _is_first_trading_day(index: pd.DatetimeIndex) -> pd.Series:
    """Check if each date is first trading day of month."""
    year_month = index.to_period("M")
    first_days = index.to_series().groupby(year_month).transform("min")
    return pd.Series(index == first_days.values, index=index)


def _is_last_trading_day(index: pd.DatetimeIndex) -> pd.Series:
    """Check if each date is last trading day of month."""
    year_month = index.to_period("M")
    last_days = index.to_series().groupby(year_month).transform("max")
    return pd.Series(index == last_days.values, index=index)
