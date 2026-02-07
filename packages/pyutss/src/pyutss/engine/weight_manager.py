"""Portfolio weight management for multi-symbol backtesting."""

from __future__ import annotations

from datetime import date

from pyutss.engine.executor import BacktestExecutor, OrderRequest
from pyutss.engine.portfolio import PortfolioManager
from pyutss.portfolio.weights import EqualWeight, WeightScheme


def get_weight_scheme(
    weights: str | WeightScheme | dict[str, float],
) -> WeightScheme:
    """Get weight scheme from specification."""
    if isinstance(weights, WeightScheme):
        return weights
    if isinstance(weights, dict):
        from pyutss.portfolio.weights import TargetWeights
        return TargetWeights(weights)
    if weights == "equal":
        return EqualWeight()
    if weights == "inverse_vol":
        from pyutss.portfolio.weights import InverseVolatility
        return InverseVolatility()
    if weights == "risk_parity":
        from pyutss.portfolio.weights import RiskParity
        return RiskParity()
    return EqualWeight()


def get_weight_scheme_name(
    weights: str | WeightScheme | dict[str, float],
) -> str:
    """Get name of weight scheme."""
    if isinstance(weights, str):
        return weights
    if isinstance(weights, dict):
        return "custom"
    return weights.__class__.__name__


def get_current_weights(
    pm: PortfolioManager,
    prices: dict[str, float],
) -> dict[str, float]:
    """Get current portfolio weights."""
    equity = pm.get_equity(prices)
    if equity <= 0:
        return {}
    weights = {}
    for symbol, pos in pm.positions.items():
        p = prices.get(symbol, pos.avg_price)
        weights[symbol] = (pos.quantity * p) / equity
    return weights


def rebalance(
    executor: BacktestExecutor,
    pm: PortfolioManager,
    symbols: list[str],
    prices: dict[str, float],
    target_weights: dict[str, float],
) -> float:
    """Rebalance portfolio to target weights. Returns turnover %."""
    equity = pm.get_equity(prices)
    turnover = 0.0

    for symbol in symbols:
        target_weight = target_weights.get(symbol, 0)
        target_value = equity * target_weight
        price = prices.get(symbol, 0)
        if price <= 0:
            continue

        target_qty = target_value / price
        current_qty = pm.positions[symbol].quantity if symbol in pm.positions else 0
        delta_qty = target_qty - current_qty

        if abs(delta_qty) < 0.01:
            continue

        if delta_qty > 0:
            # Buy more via executor
            order = OrderRequest(symbol=symbol, direction="buy", quantity=delta_qty, price=price)
            fill = executor.execute(order)
            if fill is None:
                continue

            cost = fill.quantity * price + fill.commission + fill.slippage
            if cost <= pm.cash:
                if symbol in pm.positions:
                    pos = pm.positions[symbol]
                    new_qty = pos.quantity + fill.quantity
                    pos.avg_price = (pos.avg_price * pos.quantity + price * fill.quantity) / new_qty
                    pos.quantity = new_qty
                    pm.cash -= cost
                else:
                    pm.open_position(
                        symbol, fill.quantity, price, "long",
                        pm.portfolio_history[-1].date if pm.portfolio_history else date.today(),
                        commission=fill.commission, slippage=fill.slippage,
                        reason="rebalance",
                    )
            trade_value = fill.quantity * price
        else:
            # Sell some via executor
            abs_delta = abs(delta_qty)
            order = OrderRequest(symbol=symbol, direction="sell", quantity=abs_delta, price=price)
            fill = executor.execute(order)
            if fill is None:
                continue

            if symbol in pm.positions:
                pos = pm.positions[symbol]
                if fill.quantity >= pos.quantity - 0.01:
                    d = pm.portfolio_history[-1].date if pm.portfolio_history else date.today()
                    pm.close_position(symbol, price, d, "rebalance", fill.commission, fill.slippage)
                else:
                    proceeds = fill.quantity * price - fill.commission - fill.slippage
                    pm.cash += proceeds
                    pos.quantity -= fill.quantity
            trade_value = fill.quantity * price

        turnover += trade_value / equity if equity > 0 else 0

    return turnover * 100
