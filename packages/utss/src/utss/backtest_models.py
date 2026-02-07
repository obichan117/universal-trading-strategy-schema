"""
UTSS Backtest Configuration Models

Pydantic models for the backtest configuration schema.
Separates execution parameters (commission, slippage, lot size) from strategy definition.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


# =============================================================================
# ENUMS
# =============================================================================


class DataSource(str, Enum):
    """Data source options."""

    AUTO = "auto"
    YAHOO = "yahoo"
    JQUANTS = "jquants"
    CSV = "csv"


# =============================================================================
# BASE
# =============================================================================


class BacktestBaseModel(BaseModel):
    """Base model for backtest config objects."""

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        extra="forbid",
    )


# =============================================================================
# COMMISSION
# =============================================================================


class CommissionTier(BacktestBaseModel):
    """A tier in tiered commission model.

    Use 'up_to' for capped tiers, 'above' for the final open-ended tier.
    At least one of fee/value must be provided.
    """

    up_to: float | None = Field(None, description="Trade value threshold (inclusive)")
    above: float | None = Field(None, description="Trade value floor for final tier (exclusive)")
    fee: float | None = Field(None, ge=0, description="Fixed fee for this tier")
    value: float | None = Field(None, ge=0, description="Percentage or per-share rate for this tier")

    @model_validator(mode="after")
    def _require_fee_or_value(self) -> "CommissionTier":
        if self.fee is None and self.value is None:
            raise ValueError("At least one of 'fee' or 'value' must be provided")
        return self


class CommissionConfig(BacktestBaseModel):
    """Commission model for the backtest."""

    type: Literal["per_trade", "per_share", "percentage", "tiered"]
    value: float | None = Field(None, ge=0, description="Commission value")
    currency: str | None = Field(None, description="Commission currency")
    min: float | None = Field(None, ge=0, description="Minimum commission per trade")
    max: float | None = Field(None, ge=0, description="Maximum commission per trade")
    tiers: list[CommissionTier] | None = Field(None, description="Tiered commission schedule")


# =============================================================================
# SLIPPAGE
# =============================================================================


class SlippageTier(BacktestBaseModel):
    """A tier in tiered slippage model."""

    up_to: float = Field(..., description="Order size threshold")
    value: float = Field(..., ge=0, description="Slippage for this tier")


class SlippageConfig(BacktestBaseModel):
    """Slippage model for the backtest."""

    type: Literal["percentage", "fixed", "tiered"]
    value: float | None = Field(None, ge=0, description="Slippage value")
    tiers: list[SlippageTier] | None = Field(None, description="Tiered slippage schedule")


# =============================================================================
# LOT SIZE
# =============================================================================


class LotSizeMatch(BacktestBaseModel):
    """Matching criteria for lot size rules."""

    type: str | None = Field(None, description="Instrument type (e.g., ETF, REIT)")
    symbol_pattern: str | None = Field(None, description="Regex pattern for symbol matching")


class LotSizeRule(BacktestBaseModel):
    """Lot size override for specific instrument types."""

    match: LotSizeMatch
    size: int = Field(..., ge=1, description="Lot size for matched instruments")


class FractionalConfig(BacktestBaseModel):
    """Fractional share trading configuration (e.g., S-kabu in Japan)."""

    enabled: bool = False
    commission: CommissionConfig | None = None
    order_types: list[str] | None = Field(None, description="Allowed order types")
    execution_timing: list[str] | None = Field(
        None, description="When fractional orders are executed"
    )


class LotSizeConfig(BacktestBaseModel):
    """Lot size configuration."""

    default: int = Field(..., ge=1, description="Default lot size")
    rules: list[LotSizeRule] | None = Field(None, description="Override rules")
    fractional: FractionalConfig | None = None


# =============================================================================
# PRICE LIMITS
# =============================================================================


class PriceLimitsConfig(BacktestBaseModel):
    """Daily price limit configuration (e.g., Japanese limit-up/limit-down)."""

    enabled: bool = False
    source: Literal["exchange", "custom"] = "exchange"
    upper_percent: float | None = Field(None, ge=0, description="Custom upper limit %")
    lower_percent: float | None = Field(None, ge=0, description="Custom lower limit %")


# =============================================================================
# MARGIN
# =============================================================================


class MarginConfig(BacktestBaseModel):
    """Margin trading configuration."""

    enabled: bool = False
    requirement: float | None = Field(None, ge=0, le=1, description="Margin requirement (0-1)")
    max_leverage: float | None = Field(None, ge=1, description="Maximum leverage")
    interest_rate: float | None = Field(None, ge=0, description="Annual margin interest rate")
    borrow_fee: float | None = Field(None, ge=0, description="Annual stock borrowing fee")


# =============================================================================
# EXECUTION CONFIG
# =============================================================================


class ExecutionConfig(BacktestBaseModel):
    """Execution simulation parameters."""

    commission: CommissionConfig | None = None
    slippage: SlippageConfig | None = None
    lot_size: LotSizeConfig | None = None
    settlement_days: int = Field(0, ge=0, description="Settlement period (T+N)")
    price_limits: PriceLimitsConfig | None = None
    margin: MarginConfig | None = None
    order_types: list[Literal["market", "limit", "stop", "stop_limit"]] = Field(
        default_factory=lambda: ["market", "limit"]
    )


# =============================================================================
# BENCHMARK
# =============================================================================


class Benchmark(BacktestBaseModel):
    """Benchmark for performance comparison."""

    symbol: str


# =============================================================================
# DATA CONFIG
# =============================================================================


class DataConfig(BacktestBaseModel):
    """Data source configuration."""

    source: DataSource = DataSource.AUTO
    timeframe: Literal[
        "1m", "5m", "15m", "30m", "1h", "4h", "daily", "weekly", "monthly"
    ] = "daily"
    warmup_period: int = Field(200, ge=0, description="Extra bars for indicator warmup")
    adjust: bool = Field(True, description="Use adjusted prices")


# =============================================================================
# METRICS CONFIG
# =============================================================================


class MetricsConfig(BacktestBaseModel):
    """Metrics calculation parameters."""

    risk_free_rate: float = Field(0.05, description="Annual risk-free rate")
    trading_days_per_year: int = Field(252, ge=1, description="Trading days per year")


# =============================================================================
# BACKTEST SPEC (top-level)
# =============================================================================


class BacktestSpec(BacktestBaseModel):
    """Complete backtest configuration.

    This is the top-level model for a backtest YAML file.
    It references a strategy and defines all execution parameters.

    Example (simple US):
        strategy: ./golden-cross.yaml
        start_date: "2020-01-01"
        end_date: "2024-12-31"
        initial_capital: 100000
        currency: USD
        benchmark: { symbol: SPY }
        execution:
          commission: { type: percentage, value: 0.0 }
          slippage: { type: percentage, value: 0.05 }
          lot_size: { default: 1 }

    Example (Japanese market):
        strategy: ./rsi-reversal.yaml
        start_date: "2020-01-01"
        end_date: "2024-12-31"
        initial_capital: 10000000
        currency: JPY
        benchmark: { symbol: "1306.T" }
        execution:
          commission:
            type: tiered
            currency: JPY
            tiers:
              - { up_to: 50000, fee: 55 }
              - { up_to: 100000, fee: 99 }
              - { above: 30000000, fee: 1070 }
          slippage: { type: percentage, value: 0.1 }
          lot_size:
            default: 100
            rules:
              - match: { type: ETF }
                size: 1
    """

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        extra="forbid",
    )

    schema_: str | None = Field(None, alias="$schema")
    strategy: str = Field(..., description="Path to strategy YAML file")
    start_date: str = Field(..., description="Backtest start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="Backtest end date (YYYY-MM-DD)")
    initial_capital: float = Field(..., ge=0, description="Starting capital")
    currency: str = Field("USD", description="Currency code")
    benchmark: Benchmark | None = None
    execution: ExecutionConfig | None = None
    data: DataConfig | None = None
    metrics: MetricsConfig | None = None
