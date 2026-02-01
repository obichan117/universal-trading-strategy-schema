"""Rebalancing logic for portfolio management.

Handles periodic rebalancing triggers based on calendar or threshold rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    pass


class RebalanceFrequency(Enum):
    """Rebalancing frequency options."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    NEVER = "never"


@dataclass
class RebalanceConfig:
    """Configuration for rebalancing behavior."""

    frequency: RebalanceFrequency = RebalanceFrequency.MONTHLY
    threshold_pct: float | None = None  # Rebalance if any weight drifts by this %
    day_of_week: int = 0  # Monday = 0 (for weekly)
    day_of_month: int = 1  # First day (for monthly)


class Rebalancer:
    """Handles rebalancing trigger logic for portfolios.

    Supports both calendar-based (monthly, weekly, etc.) and
    threshold-based rebalancing triggers.

    Example:
        rebalancer = Rebalancer(RebalanceConfig(
            frequency=RebalanceFrequency.MONTHLY,
            threshold_pct=5.0,  # Also rebalance if weights drift 5%
        ))

        for current_date in trading_dates:
            if rebalancer.should_rebalance(current_date, current_weights, target_weights):
                # Perform rebalancing
                pass
    """

    def __init__(self, config: RebalanceConfig | None = None) -> None:
        """Initialize rebalancer.

        Args:
            config: Rebalancing configuration
        """
        self.config = config or RebalanceConfig()
        self._last_rebalance_date: date | None = None

    def reset(self) -> None:
        """Reset rebalancer state."""
        self._last_rebalance_date = None

    def should_rebalance(
        self,
        current_date: date | pd.Timestamp,
        current_weights: dict[str, float] | None = None,
        target_weights: dict[str, float] | None = None,
    ) -> bool:
        """Check if rebalancing should occur.

        Args:
            current_date: Current date to check
            current_weights: Current portfolio weights (optional, for threshold)
            target_weights: Target portfolio weights (optional, for threshold)

        Returns:
            True if rebalancing should occur
        """
        if isinstance(current_date, pd.Timestamp):
            current_date = current_date.date()

        # Check threshold-based rebalancing first
        if self._should_rebalance_threshold(current_weights, target_weights):
            self._last_rebalance_date = current_date
            return True

        # Check calendar-based rebalancing
        if self._should_rebalance_calendar(current_date):
            self._last_rebalance_date = current_date
            return True

        return False

    def _should_rebalance_calendar(self, current_date: date) -> bool:
        """Check if calendar-based rebalancing should occur."""
        freq = self.config.frequency

        if freq == RebalanceFrequency.NEVER:
            return False

        if freq == RebalanceFrequency.DAILY:
            return True

        if freq == RebalanceFrequency.WEEKLY:
            # Rebalance on specified day of week
            return current_date.weekday() == self.config.day_of_week

        if freq == RebalanceFrequency.MONTHLY:
            # Rebalance on first trading day of month
            if self._last_rebalance_date is None:
                return self._is_first_trading_day_of_month(current_date)

            # Check if we've moved to a new month
            return (
                current_date.month != self._last_rebalance_date.month
                or current_date.year != self._last_rebalance_date.year
            )

        if freq == RebalanceFrequency.QUARTERLY:
            if self._last_rebalance_date is None:
                return self._is_first_trading_day_of_quarter(current_date)

            # Check if we've moved to a new quarter
            current_quarter = (current_date.month - 1) // 3
            last_quarter = (self._last_rebalance_date.month - 1) // 3
            return (
                current_quarter != last_quarter
                or current_date.year != self._last_rebalance_date.year
            )

        if freq == RebalanceFrequency.YEARLY:
            if self._last_rebalance_date is None:
                return self._is_first_trading_day_of_year(current_date)

            return current_date.year != self._last_rebalance_date.year

        return False

    def _should_rebalance_threshold(
        self,
        current_weights: dict[str, float] | None,
        target_weights: dict[str, float] | None,
    ) -> bool:
        """Check if threshold-based rebalancing should occur."""
        if self.config.threshold_pct is None:
            return False

        if current_weights is None or target_weights is None:
            return False

        # Check if any weight has drifted beyond threshold
        for symbol in target_weights:
            current = current_weights.get(symbol, 0.0)
            target = target_weights.get(symbol, 0.0)

            if target > 0:
                drift_pct = abs((current - target) / target) * 100
                if drift_pct >= self.config.threshold_pct:
                    return True

        return False

    def _is_first_trading_day_of_month(self, current_date: date) -> bool:
        """Check if date is first trading day of month."""
        # Simple check: is it day 1-5 and weekday?
        return current_date.day <= 5 and current_date.weekday() < 5

    def _is_first_trading_day_of_quarter(self, current_date: date) -> bool:
        """Check if date is first trading day of quarter."""
        quarter_start_months = [1, 4, 7, 10]
        return (
            current_date.month in quarter_start_months
            and current_date.day <= 5
            and current_date.weekday() < 5
        )

    def _is_first_trading_day_of_year(self, current_date: date) -> bool:
        """Check if date is first trading day of year."""
        return (
            current_date.month == 1
            and current_date.day <= 5
            and current_date.weekday() < 5
        )

    @property
    def last_rebalance_date(self) -> date | None:
        """Get the last rebalance date."""
        return self._last_rebalance_date
