"""Signal and condition evaluator for UTSS strategies."""

import logging
from dataclasses import dataclass
from typing import Any

import pandas as pd

from pyutss.engine.indicators import IndicatorService

logger = logging.getLogger(__name__)


class EvaluationError(Exception):
    """Error during signal/condition evaluation."""

    pass


@dataclass
class PortfolioState:
    """Current portfolio state for signal evaluation.

    Updated by the backtest engine on each bar.
    """

    cash: float = 0.0
    equity: float = 0.0
    positions: dict[str, Any] = None  # symbol -> Position
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0

    def __post_init__(self):
        if self.positions is None:
            self.positions = {}


@dataclass
class EvaluationContext:
    """Context for evaluating signals and conditions.

    Contains all data needed to evaluate signals, including
    primary and optional secondary timeframe data, and portfolio state.
    """

    primary_data: pd.DataFrame
    secondary_data: pd.DataFrame | None = None
    signal_library: dict[str, Any] | None = None
    condition_library: dict[str, Any] | None = None
    parameters: dict[str, float] | None = None
    portfolio_state: PortfolioState | None = None
    current_bar_idx: int = 0  # Current bar index for portfolio lookups

    def get_data(self, timeframe: str | None = None) -> pd.DataFrame:
        """Get data for specified timeframe."""
        if timeframe is None or self.secondary_data is None:
            return self.primary_data
        return self.secondary_data


class SignalEvaluator:
    """Evaluates UTSS signals against OHLCV data.

    Supports all UTSS signal types:
    - price: OHLCV price fields
    - indicator: Technical indicators (SMA, EMA, RSI, MACD, etc.)
    - fundamental: Fundamental metrics (not yet implemented)
    - calendar: Date patterns (day_of_week, is_month_end, etc.)
    - portfolio: Portfolio state (not yet implemented)
    - constant: Fixed values
    - arithmetic: Math operations on signals
    - expr: Custom expressions (limited support)

    Example:
        evaluator = SignalEvaluator()
        context = EvaluationContext(primary_data=ohlcv_df)

        # Evaluate a signal
        signal = {"type": "indicator", "indicator": "RSI", "params": {"period": 14}}
        values = evaluator.evaluate_signal(signal, context)
    """

    def __init__(self) -> None:
        """Initialize signal evaluator."""
        self._cache: dict[str, pd.Series] = {}

    def clear_cache(self) -> None:
        """Clear calculation cache."""
        self._cache.clear()

    def evaluate_signal(
        self,
        signal: dict[str, Any],
        context: EvaluationContext,
    ) -> pd.Series:
        """Evaluate a signal definition to get a numeric series.

        Args:
            signal: Signal definition from UTSS strategy
            context: Evaluation context with data

        Returns:
            Series of signal values
        """
        # Check for $ref first (can appear without explicit type)
        if "$ref" in signal:
            return self._eval_ref_signal(signal, context)

        signal_type = signal.get("type", "price")

        if signal_type == "price":
            return self._eval_price_signal(signal, context)
        elif signal_type == "indicator":
            return self._eval_indicator_signal(signal, context)
        elif signal_type == "constant":
            return self._eval_constant_signal(signal, context)
        elif signal_type == "calendar":
            return self._eval_calendar_signal(signal, context)
        elif signal_type == "arithmetic":
            return self._eval_arithmetic_signal(signal, context)
        elif signal_type == "portfolio":
            return self._eval_portfolio_signal(signal, context)
        elif signal_type == "$ref":
            return self._eval_ref_signal(signal, context)
        else:
            raise EvaluationError(f"Unsupported signal type: {signal_type}")

    def _eval_price_signal(
        self, signal: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate price signal."""
        data = context.get_data()
        field = signal.get("field", "close")

        field_map = {
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
            "hl2": None,
            "hlc3": None,
            "ohlc4": None,
        }

        if field in ["hl2", "hlc3", "ohlc4"]:
            if field == "hl2":
                return (data["high"] + data["low"]) / 2
            elif field == "hlc3":
                return (data["high"] + data["low"] + data["close"]) / 3
            else:
                return (data["open"] + data["high"] + data["low"] + data["close"]) / 4

        col = field_map.get(field, "close")
        if col and col in data.columns:
            return data[col]

        raise EvaluationError(f"Unknown price field: {field}")

    def _eval_indicator_signal(
        self, signal: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate indicator signal."""
        data = context.get_data()
        indicator = signal.get("indicator", "").upper()
        params = signal.get("params", {})

        # Resolve parameter references
        resolved_params = self._resolve_params(params, context)

        # Get source series
        source = self._get_source(data, resolved_params)

        if indicator == "SMA":
            period = int(resolved_params.get("period", 20))
            return IndicatorService.sma(source, period)

        elif indicator == "EMA":
            period = int(resolved_params.get("period", 20))
            return IndicatorService.ema(source, period)

        elif indicator == "WMA":
            period = int(resolved_params.get("period", 20))
            return IndicatorService.wma(source, period)

        elif indicator == "RSI":
            period = int(resolved_params.get("period", 14))
            return IndicatorService.rsi(source, period)

        elif indicator == "MACD":
            fast = int(resolved_params.get("fast_period", 12))
            slow = int(resolved_params.get("slow_period", 26))
            signal_period = int(resolved_params.get("signal_period", 9))
            result = IndicatorService.macd(source, fast, slow, signal_period)
            # Return specified line or MACD line by default
            line = resolved_params.get("line", "macd")
            if line == "signal":
                return result.signal_line
            elif line == "histogram":
                return result.histogram
            return result.macd_line

        elif indicator == "STOCH" or indicator == "STOCHASTIC":
            k_period = int(resolved_params.get("k_period", 14))
            d_period = int(resolved_params.get("d_period", 3))
            result = IndicatorService.stochastic(
                data["high"], data["low"], data["close"], k_period, d_period
            )
            line = resolved_params.get("line", "k")
            return result.d if line == "d" else result.k

        elif indicator == "BB" or indicator == "BOLLINGER":
            period = int(resolved_params.get("period", 20))
            std_dev = float(resolved_params.get("std_dev", 2.0))
            result = IndicatorService.bollinger_bands(source, period, std_dev)
            band = resolved_params.get("band", "percent_b")
            if band == "upper":
                return result.upper
            elif band == "lower":
                return result.lower
            elif band == "middle":
                return result.middle
            elif band == "bandwidth":
                return result.bandwidth
            return result.percent_b

        elif indicator == "ATR":
            period = int(resolved_params.get("period", 14))
            return IndicatorService.atr(data["high"], data["low"], data["close"], period)

        elif indicator == "OBV":
            return IndicatorService.obv(data["close"], data["volume"])

        elif indicator == "ADX":
            period = int(resolved_params.get("period", 14))
            return IndicatorService.adx(data["high"], data["low"], data["close"], period)

        elif indicator == "CCI":
            period = int(resolved_params.get("period", 20))
            return IndicatorService.cci(data["high"], data["low"], data["close"], period)

        elif indicator == "WILLIAMS_R" or indicator == "WILLR":
            period = int(resolved_params.get("period", 14))
            return IndicatorService.williams_r(
                data["high"], data["low"], data["close"], period
            )

        elif indicator == "MFI":
            period = int(resolved_params.get("period", 14))
            return IndicatorService.mfi(
                data["high"], data["low"], data["close"], data["volume"], period
            )

        elif indicator == "VWAP":
            return IndicatorService.vwap(
                data["high"], data["low"], data["close"], data["volume"]
            )

        else:
            raise EvaluationError(f"Unsupported indicator: {indicator}")

    def _eval_constant_signal(
        self, signal: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate constant signal."""
        value = signal.get("value", 0)
        if isinstance(value, str) and value.startswith("$param."):
            param_name = value[7:]
            if context.parameters and param_name in context.parameters:
                value = context.parameters[param_name]
            else:
                raise EvaluationError(f"Parameter not found: {param_name}")

        data = context.get_data()
        return pd.Series(float(value), index=data.index)

    def _eval_calendar_signal(
        self, signal: dict[str, Any], context: EvaluationContext
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
            return self._is_first_trading_day(index).astype(int)
        elif field == "is_month_end":
            return self._is_last_trading_day(index).astype(int)
        elif field == "is_quarter_end":
            return pd.Series((index.month % 3 == 0) & (self._is_last_trading_day(index)), index=index).astype(int)
        else:
            raise EvaluationError(f"Unknown calendar field: {field}")

    def _eval_arithmetic_signal(
        self, signal: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate arithmetic signal."""
        operator = signal.get("operator", "+")
        operands = signal.get("operands", [])

        if len(operands) < 2:
            raise EvaluationError("Arithmetic signal requires at least 2 operands")

        values = [self.evaluate_signal(op, context) for op in operands]
        result = values[0]

        for val in values[1:]:
            if operator == "+":
                result = result + val
            elif operator == "-":
                result = result - val
            elif operator == "*":
                result = result * val
            elif operator == "/":
                result = result / val
            else:
                raise EvaluationError(f"Unknown arithmetic operator: {operator}")

        return result

    def _eval_portfolio_signal(
        self, signal: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate portfolio signal.

        Portfolio signals provide access to current portfolio state:
        - unrealized_pnl: Unrealized profit/loss of current positions
        - realized_pnl: Total realized profit/loss
        - position_size: Current position size (shares)
        - position_value: Current position value (dollars)
        - days_in_position: Days since position entry
        - cash: Available cash
        - equity: Total portfolio equity
        - exposure: Position value as % of equity
        - win_rate: Win rate of closed trades

        Note: During backtesting, these return the state at each bar.
        For static analysis without backtest context, returns zeros.
        """
        data = context.get_data()
        field = signal.get("field", "unrealized_pnl")
        symbol = signal.get("symbol")  # Optional: specific symbol

        # If no portfolio state, return zeros (for static analysis)
        if context.portfolio_state is None:
            return pd.Series(0.0, index=data.index)

        ps = context.portfolio_state

        # Build series - for now, return current state as constant
        # During actual backtest, the engine updates this per bar
        if field == "unrealized_pnl":
            value = ps.unrealized_pnl
        elif field == "realized_pnl":
            value = ps.realized_pnl
        elif field == "cash":
            value = ps.cash
        elif field == "equity":
            value = ps.equity
        elif field == "position_size":
            if symbol and symbol in ps.positions:
                value = ps.positions[symbol].quantity
            elif ps.positions:
                # Sum all positions
                value = sum(p.quantity for p in ps.positions.values())
            else:
                value = 0.0
        elif field == "position_value":
            if symbol and symbol in ps.positions:
                pos = ps.positions[symbol]
                value = pos.quantity * pos.avg_price
            elif ps.positions:
                value = sum(p.quantity * p.avg_price for p in ps.positions.values())
            else:
                value = 0.0
        elif field == "days_in_position":
            if symbol and symbol in ps.positions:
                pos = ps.positions[symbol]
                value = pos.days_held if hasattr(pos, 'days_held') else 0
            elif ps.positions:
                # Max days held across all positions
                value = max(
                    (p.days_held if hasattr(p, 'days_held') else 0)
                    for p in ps.positions.values()
                )
            else:
                value = 0
        elif field == "exposure":
            if ps.equity > 0:
                position_value = sum(
                    p.quantity * p.avg_price for p in ps.positions.values()
                )
                value = (position_value / ps.equity) * 100
            else:
                value = 0.0
        elif field == "win_rate":
            if ps.total_trades > 0:
                value = (ps.winning_trades / ps.total_trades) * 100
            else:
                value = 0.0
        elif field == "total_trades":
            value = ps.total_trades
        elif field == "has_position":
            if symbol:
                value = 1.0 if symbol in ps.positions else 0.0
            else:
                value = 1.0 if ps.positions else 0.0
        else:
            raise EvaluationError(f"Unknown portfolio field: {field}")

        return pd.Series(float(value), index=data.index)

    def _eval_ref_signal(
        self, signal: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate reference signal."""
        ref = signal.get("$ref", "")
        if ref.startswith("#/signals/"):
            ref_name = ref[10:]
            if context.signal_library and ref_name in context.signal_library:
                return self.evaluate_signal(context.signal_library[ref_name], context)
        raise EvaluationError(f"Signal reference not found: {ref}")

    def _resolve_params(
        self, params: dict[str, Any], context: EvaluationContext
    ) -> dict[str, Any]:
        """Resolve parameter references in params dict."""
        resolved = {}
        for key, val in params.items():
            if isinstance(val, str) and val.startswith("$param."):
                param_name = val[7:]
                if context.parameters and param_name in context.parameters:
                    resolved[key] = context.parameters[param_name]
                else:
                    raise EvaluationError(f"Parameter not found: {param_name}")
            else:
                resolved[key] = val
        return resolved

    def _get_source(self, data: pd.DataFrame, params: dict[str, Any]) -> pd.Series:
        """Get source price series."""
        source = params.get("source", "close")
        if source == "close":
            return data["close"]
        elif source == "open":
            return data["open"]
        elif source == "high":
            return data["high"]
        elif source == "low":
            return data["low"]
        elif source == "hl2":
            return (data["high"] + data["low"]) / 2
        elif source == "hlc3":
            return (data["high"] + data["low"] + data["close"]) / 3
        elif source == "ohlc4":
            return (data["open"] + data["high"] + data["low"] + data["close"]) / 4
        return data["close"]

    def _is_first_trading_day(self, index: pd.DatetimeIndex) -> pd.Series:
        """Check if each date is first trading day of month."""
        year_month = index.to_period("M")
        first_days = index.to_series().groupby(year_month).transform("min")
        return pd.Series(index == first_days.values, index=index)

    def _is_last_trading_day(self, index: pd.DatetimeIndex) -> pd.Series:
        """Check if each date is last trading day of month."""
        year_month = index.to_period("M")
        last_days = index.to_series().groupby(year_month).transform("max")
        return pd.Series(index == last_days.values, index=index)


class ConditionEvaluator:
    """Evaluates UTSS conditions against signals.

    UTSS v1.0 Condition Types:
    - comparison: Compare signal to value (>, <, =, etc.)
    - and/or/not: Logical combinations
    - expr: Formula expressions for complex patterns
    - always: Always true

    Example:
        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)
        context = EvaluationContext(primary_data=ohlcv_df)

        # Simple comparison
        condition = {
            "type": "comparison",
            "left": {"type": "indicator", "indicator": "RSI", "params": {"period": 14}},
            "operator": "<",
            "right": {"type": "constant", "value": 30}
        }
        result = cond_eval.evaluate_condition(condition, context)

        # Expression (cross above)
        condition = {
            "type": "expr",
            "formula": "SMA(50)[-1] <= SMA(200)[-1] and SMA(50) > SMA(200)"
        }
    """

    def __init__(self, signal_evaluator: SignalEvaluator) -> None:
        """Initialize condition evaluator."""
        self.signal_eval = signal_evaluator

    def evaluate_condition(
        self,
        condition: dict[str, Any],
        context: EvaluationContext,
    ) -> pd.Series:
        """Evaluate a condition to get boolean series.

        Args:
            condition: Condition definition from UTSS strategy
            context: Evaluation context

        Returns:
            Boolean series where True indicates condition met
        """
        # Check for $ref first (can appear without explicit type field)
        if "$ref" in condition:
            return self._eval_ref(condition, context)

        cond_type = condition.get("type", "comparison")

        if cond_type == "comparison":
            return self._eval_comparison(condition, context)
        elif cond_type == "and":
            return self._eval_and(condition, context)
        elif cond_type == "or":
            return self._eval_or(condition, context)
        elif cond_type == "not":
            return self._eval_not(condition, context)
        elif cond_type == "expr":
            return self._eval_expr(condition, context)
        elif cond_type == "always":
            return pd.Series(True, index=context.get_data().index)
        elif cond_type == "$ref":
            return self._eval_ref(condition, context)
        else:
            raise EvaluationError(f"Unsupported condition type: {cond_type}")

    def _eval_comparison(
        self, condition: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate comparison condition."""
        left = self.signal_eval.evaluate_signal(condition["left"], context)
        right = self.signal_eval.evaluate_signal(condition["right"], context)
        operator = condition.get("operator", "=")

        if operator == "<" or operator == "lt":
            return left < right
        elif operator == "<=" or operator == "lte":
            return left <= right
        elif operator == "=" or operator == "==" or operator == "eq":
            return left == right
        elif operator == ">=" or operator == "gte":
            return left >= right
        elif operator == ">" or operator == "gt":
            return left > right
        elif operator == "!=" or operator == "ne":
            return left != right
        else:
            raise EvaluationError(f"Unknown comparison operator: {operator}")

    def _eval_and(
        self, condition: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate AND condition."""
        conditions = condition.get("conditions", [])
        if not conditions:
            return pd.Series(True, index=context.get_data().index)

        result = self.evaluate_condition(conditions[0], context)
        for cond in conditions[1:]:
            result = result & self.evaluate_condition(cond, context)
        return result

    def _eval_or(
        self, condition: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate OR condition."""
        conditions = condition.get("conditions", [])
        if not conditions:
            return pd.Series(False, index=context.get_data().index)

        result = self.evaluate_condition(conditions[0], context)
        for cond in conditions[1:]:
            result = result | self.evaluate_condition(cond, context)
        return result

    def _eval_not(
        self, condition: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate NOT condition."""
        inner = condition.get("condition", {})
        return ~self.evaluate_condition(inner, context)

    def _eval_expr(
        self, condition: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate expression condition.

        Supports formula expressions for common patterns:
        - Simple comparisons: "RSI(14) < 30", "close > SMA(20)"
        - Logical operators: "and", "or", "not"
        - Offset access: "close[-1]", "SMA(20)[-1]"
        - Crossover detection: "SMA(50)[-1] <= SMA(200)[-1] and SMA(50) > SMA(200)"

        Example formulas:
        - "RSI(14) < 30"                                    # RSI oversold
        - "close > SMA(200)"                                # Price above 200 SMA
        - "SMA(50) > SMA(200)"                              # Golden cross state
        - "SMA(50)[-1] <= SMA(200)[-1] and SMA(50) > SMA(200)"  # Golden cross event
        - "not (RSI(14) > 70)"                              # Not overbought
        """
        formula = condition.get("formula", "")
        if not formula:
            raise EvaluationError("Expression condition requires 'formula' field")

        from pyutss.engine.expr_parser import ExpressionError, ExpressionParser

        parser = ExpressionParser()
        try:
            return parser.evaluate(formula, context.get_data(), self.signal_eval)
        except ExpressionError as e:
            raise EvaluationError(f"Expression evaluation error: {e}") from e

    def _eval_ref(
        self, condition: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate reference condition."""
        ref = condition.get("$ref", "")
        if ref.startswith("#/conditions/"):
            ref_name = ref[13:]
            if context.condition_library and ref_name in context.condition_library:
                return self.evaluate_condition(
                    context.condition_library[ref_name], context
                )
        raise EvaluationError(f"Condition reference not found: {ref}")
