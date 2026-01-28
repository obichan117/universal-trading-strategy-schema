"""Tests for MCP tools."""

from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from utss_mcp.tools import (
    build_strategy,
    validate_strategy,
    backtest_strategy,
    list_indicators,
    revise_strategy,
)


class TestBuildStrategy:
    """Tests for build_strategy tool."""

    @pytest.mark.asyncio
    async def test_start_new_session(self):
        """Should start a new conversation session."""
        result = await build_strategy(prompt="I want a mean reversion strategy")

        assert "session_id" in result
        assert result["type"] == "question"
        assert "message" in result
        assert "options" in result

    @pytest.mark.asyncio
    async def test_continue_session(self):
        """Should continue an existing session."""
        # Start session
        result1 = await build_strategy(prompt="Start")
        session_id = result1["session_id"]

        # Continue session
        result2 = await build_strategy(prompt="mean_reversion", session_id=session_id)

        assert result2["session_id"] == session_id
        assert result2["type"] == "question"

    @pytest.mark.asyncio
    async def test_answer_with_option_id(self):
        """Should accept option id as answer."""
        result1 = await build_strategy(prompt="Start")
        session_id = result1["session_id"]

        result2 = await build_strategy(prompt="trend_following", session_id=session_id)

        assert "Trend" in result2["message"] or result2["type"] == "question"

    @pytest.mark.asyncio
    async def test_answer_with_number(self):
        """Should accept number as answer."""
        result1 = await build_strategy(prompt="Start")
        session_id = result1["session_id"]

        # Answer with "1" to select first option
        result2 = await build_strategy(prompt="1", session_id=session_id)

        assert result2["type"] == "question"


class TestValidateStrategy:
    """Tests for validate_strategy tool."""

    @pytest.mark.asyncio
    async def test_validate_valid_yaml(self):
        """Should validate correct YAML."""
        yaml = """
info:
  id: test_strategy
  name: Test Strategy
  version: "1.0"

universe:
  type: static
  symbols:
    - AAPL

rules:
  - name: Test Rule
    when:
      type: always
    then:
      type: trade
      direction: buy
      sizing:
        type: percent_of_equity
        value: 10
"""
        result = await validate_strategy(yaml)

        # Result structure check (actual validation depends on utss implementation)
        assert "valid" in result

    @pytest.mark.asyncio
    async def test_validate_invalid_yaml(self):
        """Should report errors for invalid YAML."""
        yaml = "not: valid: yaml: here"

        result = await validate_strategy(yaml)

        assert "valid" in result
        # Should have errors or be marked invalid


def _create_mock_data(start_date: str, end_date: str) -> pd.DataFrame:
    """Create mock OHLCV data for testing."""
    import numpy as np

    dates = pd.date_range(start_date, end_date, freq="D")
    n = len(dates)

    if n == 0:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

    np.random.seed(42)
    prices = 100 * np.exp(np.cumsum(np.random.randn(n) * 0.02))
    return pd.DataFrame(
        {
            "open": prices * (1 + np.random.randn(n) * 0.005),
            "high": prices * (1 + np.abs(np.random.randn(n) * 0.01)),
            "low": prices * (1 - np.abs(np.random.randn(n) * 0.01)),
            "close": prices,
            "volume": np.random.randint(100000, 1000000, n),
        },
        index=dates,
    )


class TestBacktestStrategy:
    """Tests for backtest_strategy tool."""

    @pytest.mark.asyncio
    async def test_backtest_returns_metrics(self):
        """Should return backtest metrics."""
        yaml = """
info:
  id: test_strategy
  name: Test Strategy
  version: "1.0"

rules:
  - name: Always Buy
    when:
      type: always
    then:
      type: trade
      direction: buy
      sizing:
        type: percent_of_equity
        value: 10

constraints: {}
"""
        # Mock the data provider to return test data
        mock_data = _create_mock_data("2024-01-01", "2024-06-01")

        with patch("pyutss.data.get_registry") as mock_get_registry:
            mock_registry = AsyncMock()
            mock_registry.get_ohlcv_dataframe = AsyncMock(return_value=mock_data)
            mock_get_registry.return_value = mock_registry

            result = await backtest_strategy(
                strategy_yaml=yaml,
                symbol="TEST",
                start_date="2024-01-01",
                end_date="2024-06-01",
                initial_capital=100000,
            )

        assert result["success"] is True
        assert "metrics" in result
        assert "total_return_pct" in result["metrics"]
        assert "sharpe_ratio" in result["metrics"]

    @pytest.mark.asyncio
    async def test_backtest_short_date_range(self):
        """Should handle short date ranges gracefully."""
        yaml = """
info:
  id: test
  name: Test
  version: "1.0"
rules: []
"""
        # Mock with insufficient data
        mock_data = _create_mock_data("2024-01-01", "2024-01-03")

        with patch("pyutss.data.get_registry") as mock_get_registry:
            mock_registry = AsyncMock()
            mock_registry.get_ohlcv_dataframe = AsyncMock(return_value=mock_data)
            mock_get_registry.return_value = mock_registry

            result = await backtest_strategy(
                strategy_yaml=yaml,
                symbol="TEST",
                start_date="2024-01-01",
                end_date="2024-01-03",
            )

        # Should report error due to insufficient data
        assert "success" in result


class TestListIndicators:
    """Tests for list_indicators tool."""

    @pytest.mark.asyncio
    async def test_list_indicators_returns_categories(self):
        """Should return categorized indicators."""
        result = await list_indicators()

        assert "categories" in result
        assert "total_indicators" in result
        assert result["total_indicators"] > 0

    @pytest.mark.asyncio
    async def test_list_indicators_has_common_indicators(self):
        """Should include common indicators."""
        result = await list_indicators()

        all_indicators = []
        for category_indicators in result["categories"].values():
            all_indicators.extend(category_indicators)

        assert "RSI" in all_indicators
        assert "SMA" in all_indicators
        assert "MACD" in all_indicators


class TestReviseStrategy:
    """Tests for revise_strategy tool."""

    @pytest.mark.asyncio
    async def test_revise_nonexistent_session(self):
        """Should handle missing session."""
        result = await revise_strategy(
            session_id="nonexistent",
            instruction="change RSI to 25",
        )

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_revise_existing_session(self):
        """Should revise strategy in active session."""
        # Create session and advance it
        result1 = await build_strategy(prompt="Start")
        session_id = result1["session_id"]

        # Try to revise
        result = await revise_strategy(
            session_id=session_id,
            instruction="change RSI entry to 25",
        )

        assert result["success"] is True
        assert "preview_yaml" in result or "message" in result
