"""Weight calculation schemes for portfolio allocation.

Provides various methods to calculate target weights for multi-asset portfolios.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    pass


class WeightScheme(ABC):
    """Abstract base class for weight calculation schemes."""

    @abstractmethod
    def calculate(
        self,
        symbols: list[str],
        data: dict[str, pd.DataFrame],
        current_date: pd.Timestamp,
        lookback: int = 60,
    ) -> dict[str, float]:
        """Calculate target weights for each symbol.

        Args:
            symbols: List of symbols in portfolio
            data: Dict mapping symbol to OHLCV DataFrame
            current_date: Current date for weight calculation
            lookback: Number of days to look back for calculations

        Returns:
            Dict mapping symbol to target weight (sum to 1.0)
        """
        pass


class EqualWeight(WeightScheme):
    """Equal weight allocation: 1/n for each asset."""

    def calculate(
        self,
        symbols: list[str],
        data: dict[str, pd.DataFrame],
        current_date: pd.Timestamp,
        lookback: int = 60,
    ) -> dict[str, float]:
        """Calculate equal weights."""
        if not symbols:
            return {}
        weight = 1.0 / len(symbols)
        return {symbol: weight for symbol in symbols}


class InverseVolatility(WeightScheme):
    """Inverse volatility weighting: weight by 1/volatility."""

    def __init__(self, min_weight: float = 0.0, max_weight: float = 1.0) -> None:
        """Initialize inverse volatility scheme.

        Args:
            min_weight: Minimum weight per asset
            max_weight: Maximum weight per asset
        """
        self.min_weight = min_weight
        self.max_weight = max_weight

    def calculate(
        self,
        symbols: list[str],
        data: dict[str, pd.DataFrame],
        current_date: pd.Timestamp,
        lookback: int = 60,
    ) -> dict[str, float]:
        """Calculate inverse volatility weights."""
        if not symbols:
            return {}

        volatilities = {}
        for symbol in symbols:
            df = data.get(symbol)
            if df is None or df.empty:
                volatilities[symbol] = np.inf
                continue

            # Get data up to current date
            df = df[df.index <= current_date]
            if len(df) < 2:
                volatilities[symbol] = np.inf
                continue

            # Use last `lookback` days
            returns = df["close"].pct_change().dropna().tail(lookback)
            if len(returns) < 2:
                volatilities[symbol] = np.inf
                continue

            volatilities[symbol] = returns.std()

        # Calculate inverse volatility weights
        inv_vols = {}
        for symbol, vol in volatilities.items():
            if vol > 0 and vol != np.inf:
                inv_vols[symbol] = 1.0 / vol
            else:
                inv_vols[symbol] = 0.0

        total_inv_vol = sum(inv_vols.values())
        if total_inv_vol == 0:
            # Fall back to equal weight
            weight = 1.0 / len(symbols) if symbols else 0
            return {s: weight for s in symbols}

        weights = {s: inv_vols[s] / total_inv_vol for s in symbols}

        # Apply min/max constraints
        weights = self._apply_constraints(weights)
        return weights

    def _apply_constraints(self, weights: dict[str, float]) -> dict[str, float]:
        """Apply min/max weight constraints."""
        # Clip weights
        for symbol in weights:
            weights[symbol] = max(self.min_weight, min(self.max_weight, weights[symbol]))

        # Renormalize
        total = sum(weights.values())
        if total > 0:
            weights = {s: w / total for s, w in weights.items()}

        return weights


class RiskParity(WeightScheme):
    """Risk parity: equal risk contribution from each asset.

    Uses iterative algorithm to find weights where each asset
    contributes equally to total portfolio risk.
    """

    def __init__(
        self,
        max_iterations: int = 100,
        tolerance: float = 1e-6,
    ) -> None:
        """Initialize risk parity scheme.

        Args:
            max_iterations: Maximum iterations for optimization
            tolerance: Convergence tolerance
        """
        self.max_iterations = max_iterations
        self.tolerance = tolerance

    def calculate(
        self,
        symbols: list[str],
        data: dict[str, pd.DataFrame],
        current_date: pd.Timestamp,
        lookback: int = 60,
    ) -> dict[str, float]:
        """Calculate risk parity weights."""
        if not symbols or len(symbols) == 1:
            if len(symbols) == 1:
                return {symbols[0]: 1.0}
            return {}

        # Build returns matrix
        returns_dict = {}
        for symbol in symbols:
            df = data.get(symbol)
            if df is None or df.empty:
                continue

            df = df[df.index <= current_date]
            returns = df["close"].pct_change().dropna().tail(lookback)
            if len(returns) >= 2:
                returns_dict[symbol] = returns

        valid_symbols = list(returns_dict.keys())
        if len(valid_symbols) < 2:
            # Fall back to equal weight
            weight = 1.0 / len(symbols) if symbols else 0
            return {s: weight for s in symbols}

        # Align returns by date
        returns_df = pd.DataFrame(returns_dict)
        returns_df = returns_df.dropna()

        if len(returns_df) < 5:
            weight = 1.0 / len(symbols)
            return {s: weight for s in symbols}

        # Calculate covariance matrix
        cov_matrix = returns_df.cov().values
        n = len(valid_symbols)

        # Initialize with equal weights
        weights = np.ones(n) / n

        # Iterative risk parity optimization
        for _ in range(self.max_iterations):
            # Portfolio volatility
            port_var = weights @ cov_matrix @ weights
            port_vol = np.sqrt(port_var) if port_var > 0 else 1e-8

            # Marginal risk contribution
            marginal_contrib = cov_matrix @ weights
            risk_contrib = weights * marginal_contrib / port_vol

            # Target: equal risk contribution
            target_risk = port_vol / n

            # Update weights
            new_weights = weights * (target_risk / (np.abs(risk_contrib) + 1e-10))
            new_weights = np.abs(new_weights)  # Ensure non-negative
            new_weights = new_weights / new_weights.sum()

            # Check convergence
            if np.max(np.abs(new_weights - weights)) < self.tolerance:
                weights = new_weights
                break

            weights = new_weights

        # Final cleanup - ensure non-negative
        weights = np.maximum(weights, 0)

        # Build result dict
        result = {symbol: 0.0 for symbol in symbols}
        for i, symbol in enumerate(valid_symbols):
            result[symbol] = float(weights[i])

        # Redistribute weights for symbols without data
        missing = [s for s in symbols if s not in valid_symbols]
        if missing:
            valid_weight = sum(result[s] for s in valid_symbols)
            if valid_weight > 0:
                for s in valid_symbols:
                    result[s] = result[s] / valid_weight

        return result


class TargetWeights(WeightScheme):
    """Fixed target weights specified by user."""

    def __init__(self, weights: dict[str, float]) -> None:
        """Initialize with target weights.

        Args:
            weights: Dict mapping symbol to target weight
        """
        self._weights = weights

    def calculate(
        self,
        symbols: list[str],
        data: dict[str, pd.DataFrame],
        current_date: pd.Timestamp,
        lookback: int = 60,
    ) -> dict[str, float]:
        """Return fixed target weights."""
        result = {s: self._weights.get(s, 0.0) for s in symbols}

        # Normalize
        total = sum(result.values())
        if total > 0:
            result = {s: w / total for s, w in result.items()}
        else:
            # Fall back to equal weight
            weight = 1.0 / len(symbols) if symbols else 0
            result = {s: weight for s in symbols}

        return result


# Convenience functions

def equal_weight() -> EqualWeight:
    """Create equal weight scheme."""
    return EqualWeight()


def inverse_volatility(
    min_weight: float = 0.0,
    max_weight: float = 1.0,
) -> InverseVolatility:
    """Create inverse volatility weight scheme.

    Args:
        min_weight: Minimum weight per asset
        max_weight: Maximum weight per asset
    """
    return InverseVolatility(min_weight=min_weight, max_weight=max_weight)


def risk_parity(
    max_iterations: int = 100,
    tolerance: float = 1e-6,
) -> RiskParity:
    """Create risk parity weight scheme.

    Args:
        max_iterations: Maximum iterations for optimization
        tolerance: Convergence tolerance
    """
    return RiskParity(max_iterations=max_iterations, tolerance=tolerance)


def target_weights(weights: dict[str, float]) -> TargetWeights:
    """Create fixed target weight scheme.

    Args:
        weights: Dict mapping symbol to target weight
    """
    return TargetWeights(weights=weights)
