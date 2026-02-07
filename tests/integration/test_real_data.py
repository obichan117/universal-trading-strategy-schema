"""Integration tests for data fetching and MCP tools with REAL market data.

These tests focus on:
1. Data provider connectivity (Yahoo Finance)
2. MCP tool integration
3. End-to-end pipeline: MCP tools → pyutss → Yahoo Finance

For strategy backtest tests, see test_examples.py
"""

from datetime import date, timedelta

import pytest

from pyutss.data import available_sources, fetch


def has_yahoo():
    """Check if Yahoo Finance is available."""
    return "yahoo" in available_sources()


def normalize_columns(df):
    """Normalize column names to lowercase."""
    df.columns = [c.lower() for c in df.columns]
    return df


# Skip all tests if Yahoo Finance is not available
pytestmark = pytest.mark.skipif(not has_yahoo(), reason="Yahoo Finance not available")


class TestDataFetching:
    """Tests for real data fetching from Yahoo Finance."""

    def test_fetch_single_symbol(self):
        """Should fetch AAPL data from Yahoo Finance."""
        end_date = date.today()
        start_date = end_date - timedelta(days=365)

        data = fetch("AAPL", start_date, end_date)

        assert data is not None
        assert len(data) > 200  # ~252 trading days
        # Check columns exist (case-insensitive)
        cols_lower = [c.lower() for c in data.columns]
        assert "open" in cols_lower
        assert "close" in cols_lower
        assert "volume" in cols_lower

        print(f"\n=== AAPL Data Fetch ===")
        print(f"Rows: {len(data)}")
        print(f"Date range: {data.index[0]} to {data.index[-1]}")

    def test_fetch_multiple_symbols(self):
        """Should fetch data for multiple symbols."""
        end_date = date.today()
        start_date = end_date - timedelta(days=90)

        symbols = ["AAPL", "MSFT", "GOOGL", "SPY"]
        for symbol in symbols:
            data = fetch(symbol, start_date, end_date)
            assert data is not None
            assert len(data) > 50
            data = normalize_columns(data)
            assert data["close"].iloc[-1] > 0

        print(f"\n=== Multi-Symbol Fetch ===")
        print(f"Successfully fetched: {symbols}")

    def test_fetch_long_history(self):
        """Should fetch 2+ years of data for indicator warmup."""
        end_date = date.today()
        start_date = end_date - timedelta(days=730)  # 2 years

        data = fetch("SPY", start_date, end_date)

        assert data is not None
        assert len(data) > 450  # ~504 trading days in 2 years

        print(f"\n=== Long History Fetch ===")
        print(f"Rows: {len(data)} (2 years)")


class TestMCPToolIntegration:
    """Test the MCP tools with real data."""

    @pytest.mark.asyncio
    async def test_backtest_strategy_tool(self):
        """Test the MCP backtest_strategy tool end-to-end."""
        from utss_mcp.tools import backtest_strategy

        # Use actual YAML strategy format
        strategy_yaml = """
info:
  id: mcp_integration_test
  name: MCP Integration Test
  version: "1.0"

universe:
  type: static
  symbols:
    - AAPL

signals:
  rsi_14:
    type: indicator
    indicator: RSI
    params:
      period: 14

conditions:
  oversold:
    type: comparison
    left:
      $ref: "#/signals/rsi_14"
    operator: "<"
    right:
      type: constant
      value: 30

rules:
  - name: Buy on RSI oversold
    when:
      $ref: "#/conditions/oversold"
    then:
      type: trade
      direction: buy
      sizing:
        type: percent_of_equity
        percent: 10
"""
        end_date = date.today()
        start_date = end_date - timedelta(days=180)

        result = await backtest_strategy(
            strategy_yaml=strategy_yaml,
            symbol="AAPL",
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            initial_capital=100000,
        )

        # Verify result structure
        assert "success" in result or "metrics" in result
        if "metrics" in result:
            assert "total_return_pct" in result["metrics"]

        print(f"\n=== MCP Backtest Tool Result ===")
        print(f"Result: {result}")

    @pytest.mark.asyncio
    async def test_validate_strategy_tool(self):
        """Test the MCP validate_strategy tool."""
        from utss_mcp.tools import validate_strategy

        valid_yaml = """
info:
  id: test_strategy
  name: Test Strategy
  version: "1.0"

universe:
  type: static
  symbols:
    - AAPL

rules:
  - name: Always buy
    when:
      type: always
    then:
      type: trade
      direction: buy
      sizing:
        type: percent_of_equity
        percent: 100
"""
        result = await validate_strategy(strategy_yaml=valid_yaml)

        # Tool returns a result dict with valid/errors/warnings
        assert "valid" in result
        assert "errors" in result
        print(f"\n=== MCP Validate Tool Result ===")
        print(f"Result: {result}")

    @pytest.mark.asyncio
    async def test_list_indicators_tool(self):
        """Test the MCP list_indicators tool."""
        from utss_mcp.tools import list_indicators

        result = await list_indicators()

        assert "categories" in result
        assert "total_indicators" in result
        assert result["total_indicators"] > 50  # Should have 60+ indicators

        # Categories is a dict with category_name -> indicator_list
        categories = result["categories"]
        assert isinstance(categories, dict)
        assert "Momentum" in categories or "Moving Averages" in categories

        print(f"\n=== MCP List Indicators Result ===")
        print(f"Total indicators: {result['total_indicators']}")
        for cat_name, indicators in categories.items():
            print(f"{cat_name}: {len(indicators)} indicators")


class TestEndToEndPipeline:
    """Test the complete pipeline from YAML to backtest results."""

    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_yaml_to_backtest_pipeline(self):
        """Test loading YAML, fetching data, running backtest."""
        from pathlib import Path

        import yaml

        from pyutss import BacktestConfig, BacktestEngine

        # 1. Load actual example YAML
        examples_dir = Path(__file__).parent.parent.parent / "examples"
        with open(examples_dir / "rsi-reversal.yaml") as f:
            strategy = yaml.safe_load(f)

        # 2. Validate it has expected structure
        assert "info" in strategy
        assert "signals" in strategy
        assert "conditions" in strategy
        assert "rules" in strategy

        # 3. Fetch real data
        end_date = date.today()
        start_date = end_date - timedelta(days=365)
        data = normalize_columns(fetch("AAPL", start_date, end_date))

        # 4. Run backtest
        config = BacktestConfig(initial_capital=100000)
        engine = BacktestEngine(config=config)
        result = engine.run(strategy=strategy, data=data, symbol="AAPL")

        # 5. Verify complete pipeline worked
        assert result.strategy_id == strategy["info"]["id"]
        assert result.final_equity > 0
        assert len(result.equity_curve) == len(data)

        print(f"\n=== End-to-End Pipeline ===")
        print(f"YAML → Fetch → Backtest: SUCCESS")
        print(f"Strategy: {result.strategy_id}")
        print(f"Return: {result.total_return_pct:.2f}%")
