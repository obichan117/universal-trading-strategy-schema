"""MCP tool definitions for UTSS."""

from datetime import date
from typing import Any

import yaml
from utss.capabilities import SUPPORTED_CONDITION_TYPES, SUPPORTED_INDICATORS
from utss_llm.conversation import (
    ConversationSession,
)

# Session storage
_sessions: dict[str, ConversationSession] = {}


async def build_strategy(
    prompt: str,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Build a trading strategy interactively.

    Start a new strategy building session or continue an existing one.
    The conversation will guide you through defining entry/exit conditions,
    position sizing, and risk management.

    Args:
        prompt: Your strategy description or answer to the current question.
                Examples:
                - "I want a mean reversion strategy for tech stocks"
                - "RSI" (answering indicator question)
                - "30" (answering threshold question)
                - "1" (selecting first option)
        session_id: Optional session ID to continue a previous conversation.
                   Omit to start a new session.

    Returns:
        dict with:
        - session_id: Use this to continue the conversation
        - type: "question" | "confirmation" | "complete" | "error"
        - message: Human-readable message
        - options: List of options if type is "question"
        - strategy_yaml: Final UTSS YAML if type is "complete"
        - preview_yaml: Preview of strategy being built
    """
    # Get or create session
    if session_id and session_id in _sessions:
        session = _sessions[session_id]
        response = await session.answer(prompt)
    else:
        session = ConversationSession()
        _sessions[session.session_id] = session
        response = await session.start(prompt if prompt else None)

    # Build response dict
    result: dict[str, Any] = {
        "session_id": session.session_id,
        "type": response.type.value,
        "message": response.message,
    }

    if response.question:
        result["options"] = [
            {
                "id": opt.id,
                "label": opt.label,
                "description": opt.description,
            }
            for opt in response.question.options
        ]
        result["question"] = response.question.text
        result["allow_custom"] = response.question.allow_custom

    if response.strategy_yaml:
        result["strategy_yaml"] = response.strategy_yaml

    if response.preview_yaml:
        result["preview_yaml"] = response.preview_yaml

    # Clean up completed sessions
    if response.is_complete:
        del _sessions[session.session_id]

    return result


async def validate_strategy(strategy_yaml: str) -> dict[str, Any]:
    """Validate a UTSS strategy YAML.

    Checks if the strategy conforms to the UTSS schema and reports any errors.

    Args:
        strategy_yaml: The UTSS strategy in YAML format

    Returns:
        dict with:
        - valid: True if strategy is valid
        - errors: List of validation errors (if any)
        - warnings: List of warnings (if any)
    """
    try:
        from utss import validate_yaml

        result = validate_yaml(strategy_yaml)

        return {
            "valid": result.is_valid,
            "errors": result.errors if hasattr(result, "errors") else [],
            "warnings": result.warnings if hasattr(result, "warnings") else [],
        }
    except Exception as e:
        return {
            "valid": False,
            "errors": [str(e)],
            "warnings": [],
        }


async def backtest_strategy(
    strategy_yaml: str,
    symbol: str,
    start_date: str,
    end_date: str,
    initial_capital: float = 100000,
) -> dict[str, Any]:
    """Run a backtest on a UTSS strategy.

    Simulates the strategy against historical data and returns performance metrics.
    Uses real market data from Yahoo Finance (US/JP) or J-Quants (JP only).

    Args:
        strategy_yaml: The UTSS strategy in YAML format
        symbol: Stock symbol to test (e.g., "AAPL", "7203.T")
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        initial_capital: Starting capital (default: 100000)

    Returns:
        dict with:
        - success: True if backtest completed
        - error: Error message if failed
        - data_source: Which data provider was used
        - metrics: Performance metrics including:
            - total_return_pct
            - sharpe_ratio
            - max_drawdown_pct
            - win_rate
            - total_trades
        - trades: List of trades executed
    """
    try:
        from pyutss import Engine, MetricsCalculator
        from pyutss.data import fetch

        # Parse strategy
        strategy = yaml.safe_load(strategy_yaml)

        # Parse dates
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)

        # Fetch real market data (auto-detects source based on symbol)
        data = fetch(symbol, start, end)

        if data.empty:
            return {
                "success": False,
                "error": f"No data available for {symbol} in the specified date range",
            }

        if len(data) < 10:
            return {
                "success": False,
                "error": f"Insufficient data for backtest: only {len(data)} data points",
            }

        # Run backtest using unified Engine
        engine = Engine(initial_capital=initial_capital)
        result = engine.backtest(strategy=strategy, data=data, symbol=symbol)

        # Calculate metrics
        calculator = MetricsCalculator()
        metrics = calculator.calculate(result)

        return {
            "success": True,
            "data_source": "yahoo_finance",  # Registry uses Yahoo by default
            "data_points": len(data),
            "metrics": {
                "total_return_pct": round(metrics.total_return_pct, 2),
                "annualized_return_pct": round(metrics.annualized_return_pct, 2),
                "sharpe_ratio": round(metrics.sharpe_ratio, 2),
                "sortino_ratio": round(metrics.sortino_ratio, 2),
                "max_drawdown_pct": round(metrics.max_drawdown_pct, 2),
                "win_rate": round(metrics.win_rate, 2),
                "profit_factor": round(metrics.profit_factor, 2),
                "total_trades": metrics.total_trades,
            },
            "summary": {
                "initial_capital": initial_capital,
                "final_equity": round(result.final_equity, 2),
                "total_return": round(result.total_return, 2),
            },
            "trades": [
                {
                    "entry_date": str(t.entry_date),
                    "exit_date": str(t.exit_date) if t.exit_date else None,
                    "direction": t.direction,
                    "entry_price": round(t.entry_price, 2),
                    "exit_price": round(t.exit_price, 2) if t.exit_price else None,
                    "pnl": round(t.pnl, 2),
                    "pnl_pct": round(t.pnl_pct, 2),
                }
                for t in result.trades[:10]  # Limit to first 10 trades
            ],
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def list_indicators() -> dict[str, Any]:
    """List all supported technical indicators.

    Returns the indicators available for use in UTSS strategies,
    organized by category.

    Returns:
        dict with indicator categories and their indicators
    """
    # Organize indicators by category
    categories = {
        "Moving Averages": ["SMA", "EMA", "WMA", "DEMA", "TEMA", "KAMA", "HULL", "VWMA"],
        "Momentum": [
            "RSI",
            "MACD",
            "MACD_SIGNAL",
            "MACD_HIST",
            "STOCH_K",
            "STOCH_D",
            "STOCH_RSI",
            "ROC",
            "MOMENTUM",
            "WILLIAMS_R",
            "CCI",
            "MFI",
            "CMO",
            "TSI",
        ],
        "Trend": [
            "ADX",
            "PLUS_DI",
            "MINUS_DI",
            "AROON_UP",
            "AROON_DOWN",
            "AROON_OSC",
            "SUPERTREND",
            "PSAR",
        ],
        "Volatility": [
            "ATR",
            "STDDEV",
            "VARIANCE",
            "BB_UPPER",
            "BB_LOWER",
            "BB_MIDDLE",
            "BB_WIDTH",
            "BB_PERCENT_B",
            "NATR",
            "KELTNER_UPPER",
            "KELTNER_LOWER",
        ],
        "Volume": ["OBV", "CMF", "AD", "ADL", "VOLUME_OSC", "VOLUME_ROC", "VWAP"],
    }

    return {
        "total_indicators": len(SUPPORTED_INDICATORS),
        "categories": categories,
        "condition_types": SUPPORTED_CONDITION_TYPES,
    }


async def revise_strategy(
    session_id: str,
    instruction: str,
) -> dict[str, Any]:
    """Revise an in-progress strategy.

    Make changes to a strategy that's being built in an active session.

    Args:
        session_id: The session ID from build_strategy
        instruction: What to change (e.g., "change RSI threshold to 25")

    Returns:
        dict with updated preview and confirmation
    """
    if session_id not in _sessions:
        return {
            "success": False,
            "error": f"Session not found: {session_id}",
        }

    session = _sessions[session_id]
    response = await session.revise(instruction)

    return {
        "success": True,
        "message": response.message,
        "preview_yaml": response.preview_yaml,
    }
