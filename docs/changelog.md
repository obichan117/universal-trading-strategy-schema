# Changelog

All notable changes to the Universal Trading Strategy Schema.

---

## [2.1.0] - 2024-01

### Added

#### New Signal Types
- **PortfolioSignal** - Access position and portfolio state
  - `position_qty`, `position_value`, `position_side`
  - `unrealized_pnl`, `unrealized_pnl_pct`, `realized_pnl`
  - `days_in_position`, `bars_in_position`
  - `equity`, `cash`, `buying_power`, `margin_used`
  - `daily_pnl`, `daily_pnl_pct`
- **ExpressionSignal** - Custom formula expressions
- **ExternalSignal** - Runtime-resolved signals (webhook, file, provider)

#### New Condition Types
- **SequenceCondition** - Detect ordered patterns (A then B within N bars)
- **ChangeCondition** - Detect signal changes (increase/decrease over N bars)
- **AlwaysCondition** - Always true (for scheduled actions)

#### New Action Types
- **AlertAction** - Send notifications
  - Multiple channels: log, webhook, email, sms, telegram, discord, slack
  - Severity levels: info, warning, critical
  - Throttling support

#### New Sizing Types
- **ConditionalSizing** - Different sizing based on conditions

#### Parameters Section
- Define optimizable parameters with `$param` references
- Support for integer, number, boolean, string types
- Min/max/step for numeric optimization

#### Extended Enumerations
- **Indicators**: 50+ indicators including KAMA, HULL, ROC, Aroon, Keltner Channels, Donchian Channels
- **Fundamentals**: 30+ metrics including F_SCORE, ALTMAN_Z, INDEX_WEIGHT
- **Indices**: 30+ indices with Japan focus (TSE_PRIME, TSE_STANDARD, TSE_GROWTH, etc.)
- **Events**: SEC filings (10K, 10Q, 8K)

#### Universe Enhancements
- **DualUniverse** - Separate long and short universes for long-short strategies
- **rank_by** and **order** for index/screener universes

#### Constraints Enhancements
- `min_positions` for minimum diversification
- `max_correlation` between positions
- `time_stop` for time-based exits
- `max_daily_turnover` limit
- `min_holding_bars` minimum hold period
- `trailing_stop.activation_percent` for activated trailing stops

#### Schedule Enhancements
- `evaluate_at` for specific evaluation times
- `frequency` enum includes `tick`

#### Extensibility
- `x-` prefix pattern for platform-specific extensions

### Changed

- **Signals and Conditions** moved to top-level (previously nested under `components`)
- **CalendarSignal** now uses `field` property instead of separate fields
- **RebalanceAction** now uses `method` property

### Removed

- `components` section (replaced by top-level `signals` and `conditions`)
- TypeScript package (Python-only distribution)

---

## [2.0.0] - 2024-01

### Added

- Initial release of UTSS v2
- Core type hierarchy: Signal → Condition → Rule → Strategy
- Signal types: price, indicator, fundamental, calendar, event, constant, arithmetic, relative
- Condition types: comparison, cross, range, and, or, not, temporal
- Action types: trade, rebalance, hold
- Sizing types: fixed_amount, percent_of_equity, percent_of_position, risk_based, kelly, volatility_adjusted
- Universe types: static, index, screener
- Constraints: position limits, stop loss, take profit, trailing stop, drawdown limits
- Schedule: frequency, market hours, timezone, trading days
- JSON Schema Draft-07 specification
- Python package with Pydantic v2 models
- TypeScript package with types and AJV validation
- Example strategies

---

## Versioning

This project uses [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible schema changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

Schema version is specified in strategy documents:

```yaml
$schema: https://utss.dev/schema/v2/strategy.json
```
