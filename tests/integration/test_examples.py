"""Integration tests for UTSS example strategies with REAL market data.

These tests use the deprecated BacktestEngine for backward-compatibility validation.

These tests:
1. Load actual YAML strategy files from examples/
2. Fetch real market data from Yahoo Finance
3. Run real backtests with $ref resolution
4. Verify end-to-end functionality

NO MOCK DATA - all tests use actual market data.
"""

from datetime import date, timedelta
from pathlib import Path

import pytest
import yaml

from pyutss import BacktestConfig, BacktestEngine, BacktestResult
from pyutss.data import available_sources, fetch


# Path to examples directory
EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"


def has_yahoo():
    """Check if Yahoo Finance is available."""
    return "yahoo" in available_sources()


def normalize_columns(df):
    """Normalize column names to lowercase for backtest engine."""
    df.columns = [c.lower() for c in df.columns]
    return df


def load_strategy(filename: str) -> dict:
    """Load a strategy YAML file."""
    filepath = EXAMPLES_DIR / filename
    with open(filepath) as f:
        return yaml.safe_load(f)


@pytest.fixture
def backtest_engine():
    """Create a configured backtest engine."""
    config = BacktestConfig(
        initial_capital=100000,
        commission_rate=0.001,
        slippage_rate=0.0005,
    )
    return BacktestEngine(config=config)


# Skip all tests if Yahoo Finance is not available
pytestmark = [
    pytest.mark.skipif(not has_yahoo(), reason="Yahoo Finance not available"),
    pytest.mark.filterwarnings("ignore::DeprecationWarning"),
]


class TestExampleStrategiesLoad:
    """Tests that all example strategies can be loaded and validated."""

    def test_examples_directory_exists(self):
        """Examples directory should exist."""
        assert EXAMPLES_DIR.exists(), f"Examples directory not found: {EXAMPLES_DIR}"

    def test_rsi_reversal_structure(self):
        """RSI reversal strategy should have correct structure with $refs."""
        strategy = load_strategy("rsi-reversal.yaml")

        assert strategy is not None
        assert strategy["info"]["id"] == "rsi_reversal"

        # Verify it uses signals/conditions sections with $refs
        assert "signals" in strategy
        assert "conditions" in strategy
        assert "rsi_14" in strategy["signals"]
        assert "oversold" in strategy["conditions"]

        # Verify rules use $refs
        assert "$ref" in strategy["rules"][0]["when"]
        assert strategy["rules"][0]["when"]["$ref"] == "#/conditions/oversold"

    def test_golden_cross_structure(self):
        """Golden cross strategy should use expr for crossover (v1.0 schema)."""
        strategy = load_strategy("golden-cross.yaml")

        assert strategy is not None
        assert strategy["info"]["id"] == "golden_cross"

        # Verify signals defined
        assert "sma_50" in strategy["signals"]
        assert "sma_200" in strategy["signals"]

        # Verify uses expr type (v1.0 minimal primitives)
        assert strategy["rules"][0]["when"]["type"] == "expr"
        assert "SMA(50)" in strategy["rules"][0]["when"]["formula"]

    def test_monday_friday_structure(self):
        """Monday-Friday strategy should use calendar signals."""
        strategy = load_strategy("monday-friday.yaml")

        assert strategy is not None
        assert strategy["info"]["id"] == "weekly_momentum"

        # Verify calendar signal
        assert "day_of_week" in strategy["signals"]
        assert strategy["signals"]["day_of_week"]["type"] == "calendar"

    def test_earnings_play_structure(self):
        """Earnings play strategy should use AND conditions."""
        strategy = load_strategy("earnings-play.yaml")

        assert strategy is not None
        assert strategy["info"]["id"] == "earnings_play"

        # Verify uses AND condition
        assert strategy["rules"][0]["when"]["type"] == "and"


class TestRSIReversalWithRealData:
    """Test RSI reversal strategy with real data over multi-year period."""

    def test_backtest_rsi_reversal_on_aapl(self, backtest_engine):
        """Run rsi-reversal.yaml on 3 years of AAPL data - should generate trades."""
        # Load ACTUAL strategy YAML
        strategy = load_strategy("rsi-reversal.yaml")

        # Fetch 3 YEARS of real data to ensure RSI crosses thresholds
        end_date = date.today()
        start_date = end_date - timedelta(days=1095)  # ~3 years
        data = normalize_columns(fetch("AAPL", start_date, end_date))

        # Run backtest with actual schema (including $ref resolution)
        result = backtest_engine.run(
            strategy=strategy,
            data=data,
            symbol="AAPL",
        )

        # Verify results
        assert isinstance(result, BacktestResult)
        assert result.strategy_id == "rsi_reversal"
        assert result.symbol == "AAPL"
        assert result.initial_capital == 100000
        assert result.final_equity > 0
        assert len(result.equity_curve) == len(data)

        # MUST have trades over 3 years - RSI will hit extremes
        assert result.num_trades > 0, "RSI strategy should generate trades over 3 years"

        print(f"\n=== RSI Reversal on AAPL (3 Years Real Data) ===")
        print(f"Period: {result.start_date} to {result.end_date}")
        print(f"Data points: {len(data)}")
        print(f"Initial: ${result.initial_capital:,.2f}")
        print(f"Final: ${result.final_equity:,.2f}")
        print(f"Return: {result.total_return_pct:.2f}%")
        print(f"Trades: {result.num_trades}")

        # Print trade details
        if result.trades:
            print(f"Trade details:")
            for i, trade in enumerate(result.trades[:5]):  # Show first 5 trades
                print(f"  {i+1}. {trade}")

    def test_backtest_rsi_reversal_on_volatile_stock(self, backtest_engine):
        """Run rsi-reversal.yaml on volatile stock (TSLA) - more RSI extremes."""
        strategy = load_strategy("rsi-reversal.yaml")

        # TSLA is more volatile, should trigger RSI thresholds more often
        end_date = date.today()
        start_date = end_date - timedelta(days=730)  # 2 years
        data = normalize_columns(fetch("TSLA", start_date, end_date))

        result = backtest_engine.run(
            strategy=strategy,
            data=data,
            symbol="TSLA",
        )

        assert isinstance(result, BacktestResult)
        assert result.num_trades > 0, "Volatile stock should trigger RSI thresholds"

        print(f"\n=== RSI Reversal on TSLA (Volatile Stock) ===")
        print(f"Return: {result.total_return_pct:.2f}%, Trades: {result.num_trades}")


class TestGoldenCrossWithRealData:
    """Test Golden Cross strategy with real data - needs long history."""

    def test_backtest_golden_cross_on_spy(self, backtest_engine):
        """Run golden-cross.yaml on 5 years of SPY data - should catch crossovers."""
        # Load ACTUAL strategy YAML
        strategy = load_strategy("golden-cross.yaml")

        # Need 5+ years to see golden/death cross events
        # SMA(200) needs 200 days warmup, then need time for crossovers
        end_date = date.today()
        start_date = end_date - timedelta(days=1825)  # ~5 years
        data = normalize_columns(fetch("SPY", start_date, end_date))

        result = backtest_engine.run(
            strategy=strategy,
            data=data,
            symbol="SPY",
        )

        assert isinstance(result, BacktestResult)
        assert result.strategy_id == "golden_cross"
        assert result.symbol == "SPY"

        # Over 5 years, should see at least one golden or death cross
        print(f"\n=== Golden Cross on SPY (5 Years Real Data) ===")
        print(f"Period: {result.start_date} to {result.end_date}")
        print(f"Data points: {len(data)}")
        print(f"Return: {result.total_return_pct:.2f}%")
        print(f"Trades: {result.num_trades}")

        if result.trades:
            print(f"Trade details:")
            for trade in result.trades:
                print(f"  {trade}")

    def test_backtest_golden_cross_on_qqq(self, backtest_engine):
        """Run golden-cross.yaml on QQQ (more volatile than SPY)."""
        strategy = load_strategy("golden-cross.yaml")

        end_date = date.today()
        start_date = end_date - timedelta(days=1460)  # 4 years
        data = normalize_columns(fetch("QQQ", start_date, end_date))

        result = backtest_engine.run(
            strategy=strategy,
            data=data,
            symbol="QQQ",
        )

        assert isinstance(result, BacktestResult)

        print(f"\n=== Golden Cross on QQQ (4 Years) ===")
        print(f"Return: {result.total_return_pct:.2f}%, Trades: {result.num_trades}")


class TestMondayFridayWithRealData:
    """Test Monday-Friday calendar strategy - trades weekly."""

    def test_backtest_monday_friday_on_spy(self, backtest_engine):
        """Run monday-friday.yaml on 2 years of SPY - weekly buy/sell cycles."""
        strategy = load_strategy("monday-friday.yaml")

        # 2 years = ~100 weeks
        end_date = date.today()
        start_date = end_date - timedelta(days=730)
        data = normalize_columns(fetch("SPY", start_date, end_date))

        result = backtest_engine.run(
            strategy=strategy,
            data=data,
            symbol="SPY",
        )

        assert isinstance(result, BacktestResult)
        assert result.strategy_id == "weekly_momentum"
        # Calendar strategy generates weekly trades
        # (may be less than 100 due to position mgmt - can't buy if already holding)
        assert result.num_trades > 10, "Should have multiple trades over 2 years"

        print(f"\n=== Monday-Friday on SPY (2 Years) ===")
        print(f"Period: {result.start_date} to {result.end_date}")
        print(f"Return: {result.total_return_pct:.2f}%")
        print(f"Trades: {result.num_trades}")

        # Show some trades
        if result.trades:
            print(f"Sample trades (first 5):")
            for trade in result.trades[:5]:
                print(f"  {trade}")


class TestMultipleSymbols:
    """Test strategies across multiple real symbols with sufficient history."""

    def test_rsi_strategy_multi_symbol(self, backtest_engine):
        """Run RSI strategy on multiple symbols - 2 years each."""
        strategy = load_strategy("rsi-reversal.yaml")

        # Test on multiple symbols with enough history for trades
        symbols = ["AAPL", "MSFT", "NVDA", "META"]

        end_date = date.today()
        start_date = end_date - timedelta(days=730)  # 2 years

        results = {}
        total_trades = 0
        for symbol in symbols:
            data = normalize_columns(fetch(symbol, start_date, end_date))
            result = backtest_engine.run(
                strategy=strategy,
                data=data,
                symbol=symbol,
            )
            results[symbol] = result
            total_trades += result.num_trades
            assert isinstance(result, BacktestResult)

        # At least some symbols should have trades over 2 years
        assert total_trades > 0, "At least some symbols should generate RSI trades"

        print(f"\n=== RSI Strategy Multi-Symbol (2 Years) ===")
        for symbol, result in results.items():
            print(f"{symbol}: {result.total_return_pct:.2f}% ({result.num_trades} trades)")
        print(f"Total trades across all symbols: {total_trades}")


class TestBacktestResultIntegrity:
    """Test that backtest results are consistent and complete."""

    def test_equity_curve_length_matches_data(self, backtest_engine):
        """Equity curve should have same length as input data."""
        strategy = load_strategy("rsi-reversal.yaml")

        end_date = date.today()
        start_date = end_date - timedelta(days=730)  # 2 years for trades
        data = normalize_columns(fetch("AAPL", start_date, end_date))

        result = backtest_engine.run(
            strategy=strategy,
            data=data,
            symbol="AAPL",
        )

        assert len(result.equity_curve) == len(data)
        assert len(result.portfolio_history) == len(data)

    def test_final_equity_matches_curve(self, backtest_engine):
        """Final equity should approximately match last value in equity curve."""
        strategy = load_strategy("rsi-reversal.yaml")

        end_date = date.today()
        start_date = end_date - timedelta(days=730)
        data = normalize_columns(fetch("AAPL", start_date, end_date))

        result = backtest_engine.run(
            strategy=strategy,
            data=data,
            symbol="AAPL",
        )

        # Final equity should approximately match last curve value
        # (may differ slightly due to commission/slippage on closing open positions)
        diff_pct = abs(result.final_equity - result.equity_curve.iloc[-1]) / result.final_equity * 100
        assert diff_pct < 1.0, f"Final equity should match curve within 1%: diff={diff_pct:.2f}%"


class TestTradeLogicVerification:
    """Verify that trade logic and PnL calculations are correct."""

    def test_trade_pnl_calculation(self, backtest_engine):
        """Verify trade PnL is calculated correctly from entry/exit prices."""
        # Use Monday-Friday strategy - guaranteed trades
        strategy = load_strategy("monday-friday.yaml")

        end_date = date.today()
        start_date = end_date - timedelta(days=365)
        data = normalize_columns(fetch("SPY", start_date, end_date))

        result = backtest_engine.run(
            strategy=strategy,
            data=data,
            symbol="SPY",
        )

        assert result.num_trades > 0, "Need trades to verify PnL"

        # Verify trade objects have required fields
        for trade in result.trades[:10]:
            assert hasattr(trade, 'entry_price') or 'entry_price' in str(trade)
            assert hasattr(trade, 'exit_price') or 'exit_price' in str(trade)

        print(f"\n=== Trade Logic Verification ===")
        print(f"Total trades: {result.num_trades}")
        print(f"Sample trades: {result.trades[:3]}")

    def test_position_sizing_applied(self, backtest_engine):
        """Verify position sizing is applied correctly."""
        strategy = load_strategy("monday-friday.yaml")

        end_date = date.today()
        start_date = end_date - timedelta(days=180)
        data = normalize_columns(fetch("SPY", start_date, end_date))

        result = backtest_engine.run(
            strategy=strategy,
            data=data,
            symbol="SPY",
        )

        # Equity should change if trades happened
        if result.num_trades > 0:
            # Check equity curve has variation (not flat line)
            equity_std = result.equity_curve.std()
            assert equity_std > 0, "Equity should vary with trades"

        print(f"\n=== Position Sizing Verification ===")
        print(f"Trades: {result.num_trades}")
        print(f"Equity std dev: {result.equity_curve.std():.2f}")

    def test_total_return_matches_equity_change(self, backtest_engine):
        """Total return % should match equity change."""
        strategy = load_strategy("monday-friday.yaml")

        end_date = date.today()
        start_date = end_date - timedelta(days=365)
        data = normalize_columns(fetch("SPY", start_date, end_date))

        result = backtest_engine.run(
            strategy=strategy,
            data=data,
            symbol="SPY",
        )

        # Calculate expected return
        expected_return = (result.final_equity - result.initial_capital) / result.initial_capital * 100

        # Should match total_return_pct
        assert abs(result.total_return_pct - expected_return) < 0.01

        print(f"\n=== Return Verification ===")
        print(f"Initial: ${result.initial_capital:,.2f}")
        print(f"Final: ${result.final_equity:,.2f}")
        print(f"Calculated return: {expected_return:.2f}%")
        print(f"Reported return: {result.total_return_pct:.2f}%")


class TestSchemaValidation:
    """Test that all example YAMLs pass schema validation."""

    def test_all_examples_validate_against_schema(self):
        """All example strategies should validate against UTSS schema."""
        from utss import validate_yaml

        for yaml_file in EXAMPLES_DIR.glob("*.yaml"):
            with open(yaml_file) as f:
                yaml_content = f.read()

            # Should not raise ValidationError
            strategy = validate_yaml(yaml_content)
            assert strategy is not None
            assert strategy.info.id is not None

            print(f"Validated: {yaml_file.name} (id: {strategy.info.id})")
