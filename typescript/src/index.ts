/**
 * Universal Trading Strategy Schema (UTSS) v2
 *
 * A comprehensive, composable schema for expressing any trading strategy.
 * Follows the Signal -> Condition -> Rule -> Strategy hierarchy.
 *
 * @packageDocumentation
 */

// =============================================================================
// ENUMS & CONSTANTS
// =============================================================================

export type Timeframe = "1m" | "5m" | "15m" | "30m" | "1h" | "4h" | "daily" | "weekly" | "monthly";

export type DayOfWeek = "monday" | "tuesday" | "wednesday" | "thursday" | "friday";

export type PriceField = "open" | "high" | "low" | "close" | "volume" | "vwap";

export type IndicatorType =
  // Moving Averages
  | "SMA"
  | "EMA"
  | "WMA"
  | "DEMA"
  | "TEMA"
  // Momentum
  | "RSI"
  | "MACD"
  | "MACD_SIGNAL"
  | "MACD_HIST"
  | "STOCH_K"
  | "STOCH_D"
  | "STOCH_RSI"
  // Volatility
  | "BB_UPPER"
  | "BB_MIDDLE"
  | "BB_LOWER"
  | "BB_WIDTH"
  | "BB_PERCENT"
  | "ATR"
  | "ADX"
  | "PLUS_DI"
  | "MINUS_DI"
  // Volume & Other
  | "CCI"
  | "MFI"
  | "OBV"
  | "VWAP"
  | "SUPERTREND"
  | "ICHIMOKU_TENKAN"
  | "ICHIMOKU_KIJUN"
  | "ICHIMOKU_SENKOU_A"
  | "ICHIMOKU_SENKOU_B";

export type FundamentalMetric =
  // Valuation
  | "PE_RATIO"
  | "PB_RATIO"
  | "PS_RATIO"
  | "PEG_RATIO"
  | "EV_EBITDA"
  // Profitability
  | "ROE"
  | "ROA"
  | "ROIC"
  | "PROFIT_MARGIN"
  | "OPERATING_MARGIN"
  | "NET_MARGIN"
  // Dividend
  | "DIVIDEND_YIELD"
  | "PAYOUT_RATIO"
  // Size & Growth
  | "MARKET_CAP"
  | "ENTERPRISE_VALUE"
  | "REVENUE"
  | "EBITDA"
  | "NET_INCOME"
  | "DEBT_TO_EQUITY"
  | "CURRENT_RATIO"
  | "QUICK_RATIO"
  | "EPS"
  | "EPS_GROWTH"
  | "REVENUE_GROWTH";

export type EventType =
  | "EARNINGS_RELEASE"
  | "DIVIDEND_EX_DATE"
  | "DIVIDEND_PAY_DATE"
  | "STOCK_SPLIT"
  | "IPO"
  | "DELISTING"
  | "FDA_APPROVAL"
  | "PRODUCT_LAUNCH"
  | "INDEX_ADD"
  | "INDEX_REMOVE"
  | "INSIDER_BUY"
  | "INSIDER_SELL"
  | "ANALYST_UPGRADE"
  | "ANALYST_DOWNGRADE";

export type RelativeMeasure =
  | "ratio"
  | "difference"
  | "beta"
  | "correlation"
  | "percentile"
  | "z_score";

export type ArithmeticOperator = "add" | "subtract" | "multiply" | "divide" | "min" | "max" | "avg";

export type ComparisonOperator = "<" | "<=" | "=" | ">=" | ">" | "!=";

export type CrossDirection = "above" | "below";

export type TemporalModifier =
  | "for_bars"
  | "within_bars"
  | "since_bars"
  | "first_time"
  | "nth_time";

export type TradeDirection = "buy" | "sell" | "short" | "cover";

export type OrderType = "market" | "limit" | "stop" | "stop_limit";

export type TimeInForce = "day" | "gtc" | "ioc" | "fok";

export type StockIndex =
  // US
  | "SP500"
  | "NASDAQ100"
  | "DOW30"
  | "RUSSELL2000"
  | "RUSSELL1000"
  // Japan
  | "NIKKEI225"
  | "TOPIX"
  | "TOPIX100"
  | "TOPIX500"
  | "JPXNIKKEI400";

export type Visibility = "public" | "private" | "unlisted";

// =============================================================================
// SIGNALS - Produce numeric values
// =============================================================================

export interface PriceSignal {
  type: "price";
  field: PriceField;
  offset?: number;
  timeframe?: Timeframe;
}

export interface IndicatorParams {
  period?: number;
  fast_period?: number;
  slow_period?: number;
  signal_period?: number;
  std_dev?: number;
  source?: "open" | "high" | "low" | "close" | "hl2" | "hlc3" | "ohlc4";
}

export interface IndicatorSignal {
  type: "indicator";
  indicator: IndicatorType;
  params?: IndicatorParams;
  offset?: number;
  timeframe?: Timeframe;
}

export interface FundamentalSignal {
  type: "fundamental";
  metric: FundamentalMetric;
}

export interface CalendarSignal {
  type: "calendar";
  day_of_week?: DayOfWeek;
  day_of_month?: number;
  week_of_month?: number;
  month?: number;
  price?: "open" | "close";
}

export interface EventSignal {
  type: "event";
  event: EventType;
  days_before?: number;
  days_after?: number;
}

export interface RelativeSignal {
  type: "relative";
  signal: Signal;
  benchmark: string;
  measure: RelativeMeasure;
  lookback?: number;
}

export interface ConstantSignal {
  type: "constant";
  value: number;
}

export interface ArithmeticSignal {
  type: "arithmetic";
  operator: ArithmeticOperator;
  operands: Signal[];
}

export interface Reference {
  $ref: string;
}

export type Signal =
  | PriceSignal
  | IndicatorSignal
  | FundamentalSignal
  | CalendarSignal
  | EventSignal
  | RelativeSignal
  | ConstantSignal
  | ArithmeticSignal
  | Reference;

// =============================================================================
// CONDITIONS - Produce boolean values
// =============================================================================

export interface ComparisonCondition {
  type: "comparison";
  left: Signal;
  operator: ComparisonOperator;
  right: Signal;
}

export interface CrossCondition {
  type: "cross";
  signal: Signal;
  threshold: Signal;
  direction: CrossDirection;
}

export interface RangeCondition {
  type: "range";
  signal: Signal;
  min: Signal;
  max: Signal;
  inclusive?: boolean;
}

export interface AndCondition {
  type: "and";
  conditions: Condition[];
}

export interface OrCondition {
  type: "or";
  conditions: Condition[];
}

export interface NotCondition {
  type: "not";
  condition: Condition;
}

export interface TemporalCondition {
  type: "temporal";
  condition: Condition;
  modifier: TemporalModifier;
  bars?: number;
  n?: number;
}

export type Condition =
  | ComparisonCondition
  | CrossCondition
  | RangeCondition
  | AndCondition
  | OrCondition
  | NotCondition
  | TemporalCondition
  | Reference;

// =============================================================================
// SIZING - How to size positions
// =============================================================================

export interface FixedAmountSizing {
  type: "fixed_amount";
  amount: number;
  currency?: string;
}

export interface PercentEquitySizing {
  type: "percent_of_equity";
  percent: number;
}

export interface PercentPositionSizing {
  type: "percent_of_position";
  percent: number;
}

export interface RiskBasedSizing {
  type: "risk_based";
  risk_percent: number;
  stop_distance: Signal;
}

export interface KellySizing {
  type: "kelly";
  fraction?: number;
  lookback?: number;
}

export interface VolatilityAdjustedSizing {
  type: "volatility_adjusted";
  target_volatility: number;
  lookback?: number;
}

export type Sizing =
  | FixedAmountSizing
  | PercentEquitySizing
  | PercentPositionSizing
  | RiskBasedSizing
  | KellySizing
  | VolatilityAdjustedSizing;

// =============================================================================
// ACTIONS - What to do when conditions are met
// =============================================================================

export interface TradeAction {
  type: "trade";
  direction: TradeDirection;
  sizing: Sizing;
  order_type?: OrderType;
  limit_price?: Signal;
  stop_price?: Signal;
  time_in_force?: TimeInForce;
}

export interface RebalanceTarget {
  symbol: string;
  weight: number;
}

export interface RebalanceAction {
  type: "rebalance";
  targets: RebalanceTarget[];
  threshold?: number;
}

export interface HoldAction {
  type: "hold";
  reason?: string;
}

export type Action = TradeAction | RebalanceAction | HoldAction;

// =============================================================================
// RULES - Condition + Action pairs
// =============================================================================

export interface Rule {
  name: string;
  description?: string;
  when: Condition;
  then: Action;
  priority?: number;
  enabled?: boolean;
}

// =============================================================================
// UNIVERSE - Which assets to trade
// =============================================================================

export interface StaticUniverse {
  type: "static";
  symbols: string[];
}

export interface IndexUniverse {
  type: "index";
  index: StockIndex;
  filters?: Condition[];
}

export interface ScreenerUniverse {
  type: "screener";
  base?: string;
  filters: Condition[];
  limit?: number;
  sort_by?: Signal;
  sort_order?: "asc" | "desc";
}

export type Universe = StaticUniverse | IndexUniverse | ScreenerUniverse;

// =============================================================================
// CONSTRAINTS - Risk and position limits
// =============================================================================

export interface StopConfig {
  percent?: number;
  atr_multiple?: number;
}

export interface Constraints {
  max_positions?: number;
  max_position_size?: number;
  max_sector_exposure?: number;
  max_drawdown?: number;
  daily_loss_limit?: number;
  stop_loss?: StopConfig;
  take_profit?: StopConfig;
  trailing_stop?: StopConfig;
  no_shorting?: boolean;
  no_leverage?: boolean;
}

// =============================================================================
// SCHEDULE - When to evaluate
// =============================================================================

export interface Schedule {
  frequency?: Timeframe | "tick";
  market_hours_only?: boolean;
  timezone?: string;
  trading_days?: DayOfWeek[];
}

// =============================================================================
// COMPONENTS - Reusable named components
// =============================================================================

export interface Components {
  signals?: Record<string, Signal>;
  conditions?: Record<string, Condition>;
  actions?: Record<string, Action>;
}

// =============================================================================
// INFO - Strategy metadata
// =============================================================================

export interface Author {
  id: string;
  name: string;
}

export interface Info {
  id: string;
  name: string;
  version: string;
  description?: string;
  author?: Author;
  tags?: string[];
  created_at?: string;
  updated_at?: string;
  visibility?: Visibility;
}

// =============================================================================
// STRATEGY - The complete strategy definition
// =============================================================================

export interface Strategy {
  $schema?: string;
  info: Info;
  universe: Universe;
  rules: Rule[];
  constraints?: Constraints;
  schedule?: Schedule;
  components?: Components;
}

// =============================================================================
// TYPE GUARDS
// =============================================================================

// Signal type guards
export function isPriceSignal(s: Signal): s is PriceSignal {
  return "type" in s && s.type === "price";
}

export function isIndicatorSignal(s: Signal): s is IndicatorSignal {
  return "type" in s && s.type === "indicator";
}

export function isFundamentalSignal(s: Signal): s is FundamentalSignal {
  return "type" in s && s.type === "fundamental";
}

export function isCalendarSignal(s: Signal): s is CalendarSignal {
  return "type" in s && s.type === "calendar";
}

export function isEventSignal(s: Signal): s is EventSignal {
  return "type" in s && s.type === "event";
}

export function isRelativeSignal(s: Signal): s is RelativeSignal {
  return "type" in s && s.type === "relative";
}

export function isConstantSignal(s: Signal): s is ConstantSignal {
  return "type" in s && s.type === "constant";
}

export function isArithmeticSignal(s: Signal): s is ArithmeticSignal {
  return "type" in s && s.type === "arithmetic";
}

export function isReference(s: Signal | Condition): s is Reference {
  return "$ref" in s;
}

// Condition type guards
export function isComparisonCondition(c: Condition): c is ComparisonCondition {
  return "type" in c && c.type === "comparison";
}

export function isCrossCondition(c: Condition): c is CrossCondition {
  return "type" in c && c.type === "cross";
}

export function isRangeCondition(c: Condition): c is RangeCondition {
  return "type" in c && c.type === "range";
}

export function isAndCondition(c: Condition): c is AndCondition {
  return "type" in c && c.type === "and";
}

export function isOrCondition(c: Condition): c is OrCondition {
  return "type" in c && c.type === "or";
}

export function isNotCondition(c: Condition): c is NotCondition {
  return "type" in c && c.type === "not";
}

export function isTemporalCondition(c: Condition): c is TemporalCondition {
  return "type" in c && c.type === "temporal";
}

// Universe type guards
export function isStaticUniverse(u: Universe): u is StaticUniverse {
  return u.type === "static";
}

export function isIndexUniverse(u: Universe): u is IndexUniverse {
  return u.type === "index";
}

export function isScreenerUniverse(u: Universe): u is ScreenerUniverse {
  return u.type === "screener";
}

// Action type guards
export function isTradeAction(a: Action): a is TradeAction {
  return a.type === "trade";
}

export function isRebalanceAction(a: Action): a is RebalanceAction {
  return a.type === "rebalance";
}

export function isHoldAction(a: Action): a is HoldAction {
  return a.type === "hold";
}

// =============================================================================
// BUILDER HELPERS
// =============================================================================

/**
 * Helper to create a price signal
 */
export function price(field: PriceField, offset?: number): PriceSignal {
  return { type: "price", field, offset };
}

/**
 * Helper to create an indicator signal
 */
export function indicator(
  ind: IndicatorType,
  params?: IndicatorParams,
  offset?: number
): IndicatorSignal {
  return { type: "indicator", indicator: ind, params, offset };
}

/**
 * Helper to create a constant signal
 */
export function constant(value: number): ConstantSignal {
  return { type: "constant", value };
}

/**
 * Helper to create a comparison condition
 */
export function compare(
  left: Signal,
  operator: ComparisonOperator,
  right: Signal | number
): ComparisonCondition {
  return {
    type: "comparison",
    left,
    operator,
    right: typeof right === "number" ? constant(right) : right,
  };
}

/**
 * Helper to create an AND condition
 */
export function and(...conditions: Condition[]): AndCondition {
  return { type: "and", conditions };
}

/**
 * Helper to create an OR condition
 */
export function or(...conditions: Condition[]): OrCondition {
  return { type: "or", conditions };
}

/**
 * Helper to create a cross condition
 */
export function crosses(
  signal: Signal,
  threshold: Signal | number,
  direction: CrossDirection
): CrossCondition {
  return {
    type: "cross",
    signal,
    threshold: typeof threshold === "number" ? constant(threshold) : threshold,
    direction,
  };
}

/**
 * Helper to create a buy action
 */
export function buy(sizing: Sizing): TradeAction {
  return { type: "trade", direction: "buy", sizing };
}

/**
 * Helper to create a sell action
 */
export function sell(sizing: Sizing): TradeAction {
  return { type: "trade", direction: "sell", sizing };
}

/**
 * Helper to create a percent of equity sizing
 */
export function percentOfEquity(percent: number): PercentEquitySizing {
  return { type: "percent_of_equity", percent };
}

// =============================================================================
// VALIDATION
// =============================================================================

export { validateStrategy, validateYAML, ValidationError } from "./validator";
