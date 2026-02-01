"""Time series cross-validation splits for backtesting.

Provides rolling window and purged k-fold splits to prevent look-ahead bias.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import pandas as pd


@dataclass
class Split:
    """A single train/test split."""

    train_start: int
    train_end: int
    test_start: int
    test_end: int

    @property
    def train_indices(self) -> tuple[int, int]:
        """Get train indices as (start, end)."""
        return (self.train_start, self.train_end)

    @property
    def test_indices(self) -> tuple[int, int]:
        """Get test indices as (start, end)."""
        return (self.test_start, self.test_end)


class TimeSeriesSplit:
    """Rolling window time series cross-validation.

    Creates expanding or sliding window splits for walk-forward analysis.

    Example:
        splitter = TimeSeriesSplit(
            n_splits=5,
            train_pct=0.7,
            test_pct=0.3,
            gap=5,  # 5-day gap between train and test
        )

        for train_idx, test_idx in splitter.split(data):
            train_data = data.iloc[train_idx[0]:train_idx[1]]
            test_data = data.iloc[test_idx[0]:test_idx[1]]
            # ... run backtest
    """

    def __init__(
        self,
        n_splits: int = 5,
        train_pct: float = 0.7,
        test_pct: float = 0.3,
        gap: int = 0,
        expanding: bool = False,
        min_train_size: int = 20,
    ) -> None:
        """Initialize time series splitter.

        Args:
            n_splits: Number of splits
            train_pct: Percentage of each window for training
            test_pct: Percentage of each window for testing
            gap: Number of periods between train and test (to prevent leakage)
            expanding: If True, use expanding window; if False, sliding window
            min_train_size: Minimum training set size
        """
        self.n_splits = n_splits
        self.train_pct = train_pct
        self.test_pct = test_pct
        self.gap = gap
        self.expanding = expanding
        self.min_train_size = min_train_size

    def split(
        self,
        data: pd.DataFrame | int,
    ) -> Iterator[tuple[tuple[int, int], tuple[int, int]]]:
        """Generate train/test splits.

        Args:
            data: DataFrame or total number of samples

        Yields:
            Tuples of ((train_start, train_end), (test_start, test_end))
        """
        n_samples = len(data) if isinstance(data, pd.DataFrame) else data

        if n_samples < self.min_train_size + 10:
            raise ValueError(f"Insufficient data: need at least {self.min_train_size + 10} samples")

        # Calculate test size - ensure enough data for each split
        test_size = int(n_samples * self.test_pct / (1 + self.test_pct * (self.n_splits - 1)))
        test_size = max(test_size, 5)  # Minimum test size

        # Calculate step between windows
        step_size = test_size if not self.expanding else (n_samples - self.min_train_size) // self.n_splits

        for i in range(self.n_splits):
            if self.expanding:
                # Expanding window: training grows, test slides
                train_start = 0
                # Each split has progressively more training data
                train_end = self.min_train_size + i * step_size
                test_start = train_end + self.gap
                test_end = min(test_start + test_size, n_samples)
            else:
                # Sliding window - forward walk
                # First window starts at beginning, each subsequent slides forward
                train_size = int(n_samples * self.train_pct / (1 + (self.n_splits - 1) * self.test_pct))
                train_size = max(train_size, self.min_train_size)

                train_start = i * test_size
                train_end = train_start + train_size
                test_start = train_end + self.gap
                test_end = min(test_start + test_size, n_samples)

            # Ensure valid split
            if train_end - train_start < self.min_train_size:
                continue
            if test_end - test_start < 1:
                continue
            if test_start >= n_samples:
                continue
            if train_end > n_samples:
                continue

            yield (
                (train_start, min(train_end, n_samples)),
                (max(test_start, 0), min(test_end, n_samples)),
            )

    def get_splits(
        self,
        data: pd.DataFrame | int,
    ) -> list[Split]:
        """Get all splits as Split objects.

        Args:
            data: DataFrame or total number of samples

        Returns:
            List of Split objects
        """
        splits = []
        for train_idx, test_idx in self.split(data):
            splits.append(Split(
                train_start=train_idx[0],
                train_end=train_idx[1],
                test_start=test_idx[0],
                test_end=test_idx[1],
            ))
        return splits


class PurgedKFold:
    """Purged K-Fold cross-validation for time series.

    Similar to standard K-Fold but with a gap (purge) between
    train and test sets to prevent data leakage.

    Example:
        splitter = PurgedKFold(
            n_splits=5,
            purge_gap=10,  # 10-day gap
        )

        for train_idx, test_idx in splitter.split(data):
            # ... run backtest
    """

    def __init__(
        self,
        n_splits: int = 5,
        purge_gap: int = 5,
    ) -> None:
        """Initialize purged K-Fold splitter.

        Args:
            n_splits: Number of folds
            purge_gap: Gap between train and test sets
        """
        self.n_splits = n_splits
        self.purge_gap = purge_gap

    def split(
        self,
        data: pd.DataFrame | int,
    ) -> Iterator[tuple[tuple[int, int], tuple[int, int]]]:
        """Generate train/test splits.

        Note: For time series, we only use data before test set for training
        (no future data).

        Args:
            data: DataFrame or total number of samples

        Yields:
            Tuples of ((train_start, train_end), (test_start, test_end))
        """
        n_samples = len(data) if isinstance(data, pd.DataFrame) else data

        fold_size = n_samples // self.n_splits

        for i in range(self.n_splits):
            test_start = i * fold_size
            test_end = (i + 1) * fold_size if i < self.n_splits - 1 else n_samples

            # Training uses all data before test set (minus purge gap)
            train_end = max(test_start - self.purge_gap, 0)
            train_start = 0

            if train_end <= train_start:
                continue

            yield (
                (train_start, train_end),
                (test_start, test_end),
            )

    def get_splits(
        self,
        data: pd.DataFrame | int,
    ) -> list[Split]:
        """Get all splits as Split objects.

        Args:
            data: DataFrame or total number of samples

        Returns:
            List of Split objects
        """
        splits = []
        for train_idx, test_idx in self.split(data):
            splits.append(Split(
                train_start=train_idx[0],
                train_end=train_idx[1],
                test_start=test_idx[0],
                test_end=test_idx[1],
            ))
        return splits
