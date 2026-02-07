"""Tests for UTSS backtest configuration models."""

import pytest
from utss import ValidationError
from utss.backtest_models import (
    BacktestSpec,
    Benchmark,
    CommissionConfig,
    CommissionTier,
    DataConfig,
    ExecutionConfig,
    LotSizeConfig,
    LotSizeMatch,
    LotSizeRule,
    MarginConfig,
    MetricsConfig,
    PriceLimitsConfig,
    SlippageConfig,
)
from utss.backtest_validator import validate_backtest, validate_backtest_yaml


# =============================================================================
# BacktestSpec validation
# =============================================================================


def test_minimal_backtest_spec():
    """Test minimal valid backtest spec."""
    spec = BacktestSpec(
        strategy="./my-strategy.yaml",
        start_date="2020-01-01",
        end_date="2024-12-31",
        initial_capital=100000,
    )
    assert spec.strategy == "./my-strategy.yaml"
    assert spec.currency == "USD"
    assert spec.benchmark is None
    assert spec.execution is None


def test_full_us_backtest_spec():
    """Test complete US market backtest spec."""
    spec = BacktestSpec(
        strategy="./golden-cross.yaml",
        start_date="2020-01-01",
        end_date="2024-12-31",
        initial_capital=100000,
        currency="USD",
        benchmark=Benchmark(symbol="SPY"),
        execution=ExecutionConfig(
            commission=CommissionConfig(type="percentage", value=0.0),
            slippage=SlippageConfig(type="percentage", value=0.05),
            lot_size=LotSizeConfig(default=1),
        ),
        metrics=MetricsConfig(risk_free_rate=0.05, trading_days_per_year=252),
    )
    assert spec.currency == "USD"
    assert spec.benchmark.symbol == "SPY"
    assert spec.execution.commission.type == "percentage"
    assert spec.execution.lot_size.default == 1
    assert spec.metrics.trading_days_per_year == 252


def test_full_jp_backtest_spec():
    """Test complete Japanese market backtest spec."""
    spec = BacktestSpec(
        strategy="./rsi-reversal.yaml",
        start_date="2020-01-01",
        end_date="2024-12-31",
        initial_capital=10000000,
        currency="JPY",
        benchmark=Benchmark(symbol="1306.T"),
        execution=ExecutionConfig(
            commission=CommissionConfig(
                type="tiered",
                currency="JPY",
                tiers=[
                    CommissionTier(up_to=50000, fee=55),
                    CommissionTier(up_to=100000, fee=99),
                    CommissionTier(up_to=200000, fee=115),
                    CommissionTier(up_to=500000, fee=275),
                    CommissionTier(up_to=1000000, fee=535),
                    CommissionTier(up_to=1500000, fee=640),
                    CommissionTier(up_to=30000000, fee=1013),
                    CommissionTier(above=30000000, fee=1070),
                ],
            ),
            slippage=SlippageConfig(type="percentage", value=0.1),
            lot_size=LotSizeConfig(
                default=100,
                rules=[
                    LotSizeRule(match=LotSizeMatch(type="ETF"), size=1),
                    LotSizeRule(match=LotSizeMatch(type="REIT"), size=1),
                ],
            ),
            settlement_days=2,
            price_limits=PriceLimitsConfig(enabled=True, source="exchange"),
            margin=MarginConfig(
                enabled=False,
                requirement=0.3,
                max_leverage=3.3,
                interest_rate=0.028,
                borrow_fee=0.011,
            ),
        ),
        data=DataConfig(source="auto", timeframe="daily", warmup_period=200, adjust=True),
        metrics=MetricsConfig(risk_free_rate=0.001, trading_days_per_year=245),
    )
    assert spec.currency == "JPY"
    assert spec.initial_capital == 10000000
    assert spec.execution.commission.type == "tiered"
    assert len(spec.execution.commission.tiers) == 8
    assert spec.execution.commission.tiers[0].up_to == 50000
    assert spec.execution.commission.tiers[0].fee == 55
    assert spec.execution.commission.tiers[-1].above == 30000000
    assert spec.execution.commission.tiers[-1].fee == 1070
    assert spec.execution.lot_size.default == 100
    assert len(spec.execution.lot_size.rules) == 2
    assert spec.execution.settlement_days == 2
    assert spec.execution.price_limits.enabled is True
    assert spec.execution.margin.requirement == 0.3
    assert spec.metrics.trading_days_per_year == 245


def test_invalid_capital():
    """Test that negative capital is rejected."""
    with pytest.raises(Exception):
        BacktestSpec(
            strategy="./test.yaml",
            start_date="2020-01-01",
            end_date="2024-12-31",
            initial_capital=-1000,
        )


def test_missing_required_fields():
    """Test that missing required fields raise error."""
    with pytest.raises(Exception):
        BacktestSpec(strategy="./test.yaml")


# =============================================================================
# YAML validation
# =============================================================================


def test_validate_simple_backtest_yaml():
    """Test validating a simple backtest YAML."""
    yaml_content = """
strategy: ./golden-cross.yaml
start_date: "2020-01-01"
end_date: "2024-12-31"
initial_capital: 100000
currency: USD
benchmark:
  symbol: SPY
execution:
  commission:
    type: percentage
    value: 0.0
  slippage:
    type: percentage
    value: 0.05
  lot_size:
    default: 1
metrics:
  risk_free_rate: 0.05
  trading_days_per_year: 252
"""
    spec = validate_backtest_yaml(yaml_content)
    assert spec.strategy == "./golden-cross.yaml"
    assert spec.initial_capital == 100000
    assert spec.benchmark.symbol == "SPY"
    assert spec.execution.commission.type == "percentage"


def test_validate_jp_backtest_yaml():
    """Test validating a Japanese market backtest YAML."""
    yaml_content = """
strategy: ./rsi-reversal.yaml
start_date: "2020-01-01"
end_date: "2024-12-31"
initial_capital: 10000000
currency: JPY
benchmark:
  symbol: "1306.T"
execution:
  commission:
    type: tiered
    currency: JPY
    tiers:
      - up_to: 50000
        fee: 55
      - up_to: 100000
        fee: 99
      - up_to: 200000
        fee: 115
      - above: 30000000
        fee: 1070
  slippage:
    type: percentage
    value: 0.1
  lot_size:
    default: 100
    rules:
      - match:
          type: ETF
        size: 1
  settlement_days: 2
  price_limits:
    enabled: true
    source: exchange
  margin:
    enabled: false
    requirement: 0.3
    max_leverage: 3.3
metrics:
  risk_free_rate: 0.001
  trading_days_per_year: 245
"""
    spec = validate_backtest_yaml(yaml_content)
    assert spec.currency == "JPY"
    assert spec.execution.commission.type == "tiered"
    assert len(spec.execution.commission.tiers) == 4
    assert spec.execution.lot_size.default == 100
    assert spec.execution.settlement_days == 2
    assert spec.metrics.trading_days_per_year == 245


def test_validate_minimal_backtest_yaml():
    """Test validating minimal backtest YAML."""
    yaml_content = """
strategy: ./test.yaml
start_date: "2023-01-01"
end_date: "2023-12-31"
initial_capital: 50000
"""
    spec = validate_backtest_yaml(yaml_content)
    assert spec.strategy == "./test.yaml"
    assert spec.currency == "USD"
    assert spec.execution is None
    assert spec.data is None


def test_validate_invalid_yaml():
    """Test that invalid YAML raises ValidationError."""
    with pytest.raises(ValidationError):
        validate_backtest_yaml("not: [valid: yaml: structure")


def test_validate_missing_strategy():
    """Test that missing strategy field raises error."""
    yaml_content = """
start_date: "2020-01-01"
end_date: "2024-12-31"
initial_capital: 100000
"""
    with pytest.raises(ValidationError):
        validate_backtest_yaml(yaml_content)


def test_validate_extra_fields_rejected():
    """Test that extra fields are rejected."""
    yaml_content = """
strategy: ./test.yaml
start_date: "2020-01-01"
end_date: "2024-12-31"
initial_capital: 100000
unknown_field: true
"""
    with pytest.raises(ValidationError):
        validate_backtest_yaml(yaml_content)


# =============================================================================
# Dict validation
# =============================================================================


def test_validate_backtest_dict():
    """Test validating a backtest dict."""
    data = {
        "strategy": "./test.yaml",
        "start_date": "2020-01-01",
        "end_date": "2024-12-31",
        "initial_capital": 100000,
    }
    spec = validate_backtest(data)
    assert spec.strategy == "./test.yaml"


def test_validate_backtest_dict_with_schema():
    """Test that $schema field is accepted."""
    data = {
        "$schema": "https://utss.dev/schema/v1/backtest.json",
        "strategy": "./test.yaml",
        "start_date": "2020-01-01",
        "end_date": "2024-12-31",
        "initial_capital": 100000,
    }
    spec = validate_backtest(data)
    assert spec.schema_ == "https://utss.dev/schema/v1/backtest.json"


# =============================================================================
# Component models
# =============================================================================


def test_commission_per_trade():
    """Test per-trade commission model."""
    config = CommissionConfig(type="per_trade", value=9.99)
    assert config.type == "per_trade"
    assert config.value == 9.99


def test_commission_tiered():
    """Test tiered commission model."""
    config = CommissionConfig(
        type="tiered",
        tiers=[
            CommissionTier(up_to=50000, fee=55),
            CommissionTier(up_to=100000, fee=99),
            CommissionTier(above=30000000, fee=1070),
        ],
    )
    assert config.type == "tiered"
    assert len(config.tiers) == 3


def test_slippage_percentage():
    """Test percentage slippage model."""
    config = SlippageConfig(type="percentage", value=0.1)
    assert config.type == "percentage"
    assert config.value == 0.1


def test_lot_size_with_rules():
    """Test lot size with override rules."""
    config = LotSizeConfig(
        default=100,
        rules=[
            LotSizeRule(match=LotSizeMatch(type="ETF"), size=1),
        ],
    )
    assert config.default == 100
    assert config.rules[0].size == 1


def test_margin_config():
    """Test margin configuration."""
    config = MarginConfig(
        enabled=True,
        requirement=0.3,
        max_leverage=3.3,
        interest_rate=0.028,
        borrow_fee=0.011,
    )
    assert config.enabled is True
    assert config.max_leverage == 3.3


def test_data_config_defaults():
    """Test data config defaults."""
    config = DataConfig()
    assert config.source == "auto"
    assert config.timeframe == "daily"
    assert config.warmup_period == 200
    assert config.adjust is True


def test_metrics_config_jp():
    """Test Japanese market metrics config."""
    config = MetricsConfig(risk_free_rate=0.001, trading_days_per_year=245)
    assert config.risk_free_rate == 0.001
    assert config.trading_days_per_year == 245


def test_execution_config_order_types():
    """Test execution config with custom order types."""
    config = ExecutionConfig(order_types=["market"])
    assert config.order_types == ["market"]


def test_price_limits_config():
    """Test price limits configuration."""
    config = PriceLimitsConfig(enabled=True, source="custom", upper_percent=30, lower_percent=30)
    assert config.enabled is True
    assert config.source == "custom"
    assert config.upper_percent == 30
