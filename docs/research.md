# Research Background

This document summarizes existing research and industry practices related to trading strategy representation, comparing code-based vs schema-based approaches with particular emphasis on LLM applications.

---

## Executive Summary

| Approach | Representation | LLM Accuracy | Portability | Validation |
|----------|---------------|--------------|-------------|------------|
| **Imperative Code** (Pine Script, Python) | Source code | ~60-77% | Platform-locked | Runtime only |
| **Schema-based** (UTSS) | JSON/YAML | ~95%+ | Universal | Static + Runtime |

**Key finding**: Research shows that **constrained, schema-based representations outperform general-purpose code by 20-40 percentage points** for LLM generation tasks, particularly for multi-step operations like trading strategies.

---

## Part 1: Industry Landscape

### 1.1 The Fragmented Ecosystem

The trading bot industry lacks a standard strategy representation. Each platform uses its own format:

```
┌─────────────────────────────────────────────────────────────────┐
│                    CURRENT INDUSTRY STATE                       │
├─────────────────────────────────────────────────────────────────┤
│  Platform          │ Format              │ Portability          │
├─────────────────────────────────────────────────────────────────┤
│  TradingView       │ Pine Script         │ TradingView only     │
│  TradeStation      │ EasyLanguage        │ TradeStation only    │
│  MetaTrader        │ MQL4/MQL5           │ MetaTrader only      │
│  Freqtrade         │ Python classes      │ Freqtrade only       │
│  QuantConnect      │ C#/Python code      │ LEAN engine only     │
│  Tradetron         │ Proprietary cloud   │ Tradetron only       │
│  3Commas           │ Proprietary JSON    │ 3Commas only         │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Typical Workflow

Most traders follow this fragmented workflow:

```
1. IDEATION              2. PROTOTYPING           3. LIVE TRADING
   ───────────────────      ─────────────────        ─────────────────
   Natural language    →    Pine Script         →    Python/Bot
   "Buy when RSI < 30"      (TradingView)            (manual rewrite)
                                  │
                                  ▼
                            Backtest results
                                  │
                                  ▼
                            Manual conversion ← No standard format!
                                  │
                                  ▼
                            Python code for
                            Freqtrade/custom bot
```

**The problem**: Strategy logic is manually rewritten between platforms, introducing errors and preventing automation.

### 1.3 Strategy Marketplaces

Several marketplaces exist, but all are platform-locked:

| Platform | Model | Strategy Format | Export? |
|----------|-------|-----------------|---------|
| [TradingView Scripts](https://www.tradingview.com/scripts/) | 150K+ public scripts | Pine Script | No (code only) |
| [QuantConnect Alpha](https://www.quantconnect.com/) | Algorithm library | C#/Python | Git-based |
| [Tradetron](https://tradetron.tech/) | Subscription marketplace | Proprietary | No |
| [Collective2](https://collective2.com/) | Signal following | Signals only | No strategy logic |

**Key insight**: No marketplace offers a portable, machine-readable strategy specification that works across platforms.

### 1.4 Webhook Signal Formats

For bridging platforms, webhooks are used—but with no standard format:

**TradersPost format**:
```json
{
  "ticker": "AAPL",
  "action": "buy",
  "quantity": 100,
  "quantityType": "fixed_quantity"
}
```

**3Commas format**:
```json
{
  "message_type": "bot",
  "bot_id": 12345,
  "email_token": "abc123",
  "delay_seconds": 0
}
```

**WunderTrading, Altrady, Growlonix**: All different formats.

This fragmentation means every integration requires custom code.

---

## Part 2: Code-Based vs Schema-Based Approaches

### 2.1 The Fundamental Trade-off

| Aspect | Code-Based | Schema-Based |
|--------|------------|--------------|
| **Expressiveness** | Turing-complete | Constrained to schema |
| **Flexibility** | Any logic possible | Limited to defined types |
| **Validation** | Runtime only | Static + runtime |
| **LLM generation** | Error-prone | Highly accurate |
| **Human authoring** | Requires programming | Declarative, simpler |
| **Machine parsing** | Requires AST analysis | Native structure |
| **Portability** | Platform-dependent | Universal |

### 2.2 Existing Trading DSLs

#### Pine Script (TradingView)

**Philosophy**: "Lightweight language for traders, not programmers"

**Design**:
- Time-series native (every variable is implicitly a series)
- Bar-by-bar execution model
- Event-driven on realtime ticks

```pine
// Pine Script example
rsi = ta.rsi(close, 14)
if rsi < 30
    strategy.entry("Buy", strategy.long)
```

**Limitations** ([documented](https://www.tradingview.com/pine-script-docs/writing/limitations/)):
- 64 plot limit per script
- 40 `request.security()` calls max
- 9,000 orders in backtests
- No external libraries
- Platform-locked execution

#### EasyLanguage (TradeStation)

**Philosophy**: "English-like expressions using trading terms"

```easylanguage
if RSI(Close, 14) crosses below 30 then
    Buy next bar at market;
```

**Strengths**: Natural language syntax, 25+ years of libraries
**Limitations**: Proprietary, TradeStation-only

#### MQL5 (MetaTrader)

**Philosophy**: "C++-like power for trading applications"

```mql5
void OnTick() {
   double rsi = iRSI(_Symbol, PERIOD_H1, 14, PRICE_CLOSE);
   if (rsi < 30) {
      trade.Buy(0.1, _Symbol);
   }
}
```

**Strengths**: High performance, full OOP
**Limitations**: Platform-locked, steep learning curve

### 2.3 The Atlas Abstract Strategy Tree

The [Atlas framework](https://atlas-blog.vercel.app/ast) takes a tree-based approach similar to UTSS:

```
AllocationNode
└── ExchangeViewNode (filter: spread > 0)
    └── AssetCompNode (trend direction)
        ├── AssetIfNode (close > upper_band)
        └── AssetOpNode (upper_band = median + multiplier × ATR)
```

**Key differences from UTSS**:

| Aspect | Atlas AST | UTSS |
|--------|-----------|------|
| Format | C++ objects | JSON/YAML |
| Purpose | Runtime execution | Specification |
| Level | Low-level ops | High-level concepts |
| Portability | Compiled binary | Any platform |

---

## Part 3: LLM Parsing Research

### 3.1 The Core Problem

LLMs generating trading strategies face two challenges:

1. **Syntax errors**: Invalid code that won't parse
2. **Semantic errors**: Valid code with wrong logic

Research shows these problems are dramatically reduced with schema-based approaches.

### 3.2 Key Research Findings

#### Anka DSL Study (arXiv, Dec 2025)

The [Anka DSL research](https://arxiv.org/html/2512.23214) designed a language specifically for LLM generation:

| Metric | Anka (Schema-like) | Python (Code) | Improvement |
|--------|-------------------|---------------|-------------|
| Parse success | 99.9% | 95%+ | +4.9% |
| Simple tasks | ~95% | ~95% | No difference |
| **Multi-step tasks** | **100%** | **60%** | **+40%** |
| Overall accuracy | 95.8% | 91.2% | +4.6% |

**Critical insight**: The advantage of constrained syntax **grows with task complexity**. Trading strategies are inherently multi-step, making this finding highly relevant.

#### DSL-Mediated Trading Strategy Generation (2025)

Research from [Xi'an Jiaotong-Liverpool University](https://scholar.xjtlu.edu.cn/en/publications/formulating-financial-trading-strategies-using-llm-a-dsl-mediated/) found:

- **95.3% accuracy** mapping natural language to trading DSL
- DSL intermediary **reduces hallucinations** compared to direct code generation
- **Interpretability** maintained throughout the pipeline

#### Microsoft DSL Research (Dec 2025)

[Microsoft's study](https://devblogs.microsoft.com/all-things-azure/ai-coding-agents-domain-specific-languages/) on AI coding agents:

| Scenario | LLM Accuracy |
|----------|-------------|
| DSL without context | <20% |
| DSL with 3-5 examples | **up to 85%** |
| General-purpose language | Variable |

**Key finding**: LLMs need explicit schema examples, not training data.

### 3.3 Why Schemas Outperform Code

#### Constrained Decoding

Modern LLM frameworks use [constrained decoding](https://github.com/Saibo-creator/Awesome-LLM-Constrained-Decoding) to guarantee valid output:

```
Token Generation Process:

Unconstrained:  "Generate buy signal" → [any token] → potential errors

Constrained:    "Generate buy signal" → [only valid schema tokens] → guaranteed valid
```

Tools like [Outlines](https://github.com/dottxt-ai/outlines), [Guidance](https://github.com/guidance-ai/llguidance), and [XGrammar](https://github.com/mlc-ai/xgrammar) enforce JSON schema compliance at ~50μs per token.

#### Error Reduction Mechanisms

The Anka research identified why constrained syntax works:

1. **Reduced decision space**: One canonical form per operation
2. **Explicit state**: Named intermediates prevent confusion
3. **Structural templates**: Guided sequential generation

Python error patterns in trading code:
- 42% variable shadowing
- 31% operation sequencing errors
- 27% method chaining confusion

All three are eliminated by schema constraints.

### 3.4 Structured Output Benchmarks

[JSONSchemaBench](https://arxiv.org/html/2501.10868v1) evaluated structured output generation:

| Framework | Coverage | Notes |
|-----------|----------|-------|
| Guidance | Highest on 6/8 datasets | Open source |
| Llamacpp | Highest on 2/8 datasets | C++ performance |
| OpenAI | Lower coverage | Closed source |
| Gemini | Lower coverage | Closed source |

**Recommendation**: Use open-source constrained decoding for maximum schema compliance.

### 3.5 LLM Trading Code Generation Studies

Practical experiments show:

| Model | Task | Accuracy | Notes |
|-------|------|----------|-------|
| Claude Opus 4 | Strategy generation | High | Prone to overfitting |
| GPT-4o | JSON processing | 77% | Frontier model ceiling |
| Claude 3.5 | Anka DSL | 95.8% | With schema constraints |

**Key insight**: The prompt matters more than the model. A well-designed schema + good prompt beats raw code generation.

---

## Part 4: Implications for UTSS

### 4.1 Schema Design Principles for LLMs

Based on research, UTSS should:

| Principle | Implementation | Benefit |
|-----------|----------------|---------|
| **Canonical forms** | One way to express each concept | Reduces decision errors |
| **Explicit typing** | `type` field on every node | Enables constrained decoding |
| **Named references** | `$ref` for composition | Prevents state confusion |
| **Verbose structure** | Full field names | Aligns with LLM strengths |

Example of LLM-friendly UTSS:
```yaml
# Explicit, canonical, verbose
when:
  type: comparison           # Always explicit type
  left:
    type: indicator          # Nested type required
    indicator: RSI
    params:
      period: 14
  operator: "<"              # Explicit operator
  right:
    type: constant           # Even constants typed
    value: 30
```

vs problematic alternatives:
```yaml
# Ambiguous, multiple valid forms (bad for LLMs)
when: "RSI(14) < 30"         # String parsing needed
when: { RSI: { "<": 30 } }   # Non-canonical structure
```

### 4.2 Constrained Decoding Integration

UTSS can leverage constrained decoding:

```python
from outlines import models, generate
import json

# Load UTSS JSON Schema
with open("strategy.schema.json") as f:
    schema = json.load(f)

model = models.transformers("mistralai/Mistral-7B-v0.1")
generator = generate.json(model, schema)

# Generate valid UTSS from natural language
strategy = generator("RSI mean reversion: buy when RSI < 30, sell when RSI > 70")
# Guaranteed to be valid UTSS!
```

### 4.3 Competitive Advantages

| Feature | Pine Script | Python Code | UTSS |
|---------|-------------|-------------|------|
| LLM generation accuracy | ~70% | ~60% (complex) | **95%+** |
| Validation before execution | No | No | **Yes** |
| Cross-platform | No | Partial | **Yes** |
| Version control friendly | Text diff | Text diff | **Semantic diff** |
| Constrained decoding support | No | No | **Native** |

---

## Part 5: Pine Script → UTSS Conversion

### 5.1 Existing Tools

| Tool | Function | Output |
|------|----------|--------|
| [Pynescript](https://github.com/elbakramer/pynescript) | Pine Script → Python AST | Syntax tree |
| [PineTS](https://github.com/QuantForgeOrg/PineTS) | Pine Script → JavaScript | Executable code |
| [PyneCore](https://github.com/PyneSys/pynecore) | Pine Script → Python runtime | Executable code |

**Gap**: No tool produces a semantic schema (UTSS format).

### 5.2 Proposed Conversion Pipeline

```
Pine Script Source
       │
       ▼
┌──────────────────┐
│  Pynescript      │ ← ANTLR-based parser
│  (Parse)         │
└────────┬─────────┘
         │
         ▼
   Python AST Nodes
         │
         ▼
┌──────────────────┐
│  Semantic        │ ← Pattern matching + type inference
│  Analyzer        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  UTSS            │ ← JSON Schema validation
│  Schema          │
└──────────────────┘
```

### 5.3 Mapping Examples

| Pine Script | UTSS Equivalent |
|-------------|-----------------|
| `ta.rsi(close, 14)` | `{ type: indicator, indicator: RSI, params: { period: 14 } }` |
| `ta.crossover(a, b)` | `{ type: expr, formula: "a[-1] <= b[-1] and a > b" }` |
| `strategy.entry("Buy", strategy.long)` | `{ type: trade, direction: buy }` |
| `if cond` | `{ when: cond, then: action }` |

### 5.4 Conversion Challenges

| Challenge | Difficulty | UTSS Coverage |
|-----------|------------|---------------|
| Simple indicators | Easy | Full support |
| Crossovers/comparisons | Easy | Full support |
| Basic entry/exit | Easy | Full support |
| Custom functions | Medium | Via `expression` type |
| State variables (`var`) | Hard | Not supported |
| Arbitrary loops | Hard | Not supported |
| Drawing operations | N/A | Out of scope |

**Estimated coverage**: ~80% of Pine Script strategies can map to UTSS.

---

## Part 6: Future Research Directions

### 6.1 LLM Integration

1. **Fine-tuning on UTSS**: Train models specifically on UTSS examples
2. **Constrained generation**: Integrate with Outlines/Guidance for guaranteed validity
3. **Natural language interface**: "Create a strategy that..." → UTSS

### 6.2 Formal Verification

UTSS's declarative nature enables:
- **Property checking**: "Does this strategy ever short?"
- **Consistency validation**: "Are all referenced signals defined?"
- **Risk analysis**: "What's the maximum position size?"

### 6.3 Ecosystem Development

Priority areas:
1. **Execution adapters**: UTSS → Freqtrade, QuantConnect, etc.
2. **Visual builders**: Drag-and-drop → UTSS
3. **Conversion tools**: Pine Script → UTSS

---

## References

### Academic Papers

1. **Anka DSL** (2025): [arXiv:2512.23214](https://arxiv.org/html/2512.23214) - LLM-optimized DSL design
2. **DSL-Xpert 2.0** (2025): [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0950584925002939) - Grammar prompting for DSLs
3. **JSONSchemaBench** (2025): [arXiv:2501.10868](https://arxiv.org/html/2501.10868v1) - Structured output benchmarks
4. **Trading Strategy DSL** (2025): [XJTLU](https://scholar.xjtlu.edu.cn/en/publications/formulating-financial-trading-strategies-using-llm-a-dsl-mediated/) - DSL-mediated approach

### Industry Standards

1. **FIX Protocol**: [fixtrading.org](https://www.fixtrading.org/standards/) - Message transport
2. **FIXatdl**: [Wikipedia](https://en.wikipedia.org/wiki/FIXatdl) - Algorithmic trading parameters
3. **FIBO**: [spec.edmcouncil.org](https://spec.edmcouncil.org/fibo/) - Financial ontology

### Tools & Frameworks

1. **Pynescript**: [GitHub](https://github.com/elbakramer/pynescript) - Pine Script parser
2. **Outlines**: [GitHub](https://github.com/dottxt-ai/outlines) - Constrained LLM generation
3. **llguidance**: [GitHub](https://github.com/guidance-ai/llguidance) - Fast structured output
4. **Atlas AST**: [Blog](https://atlas-blog.vercel.app/ast) - Strategy tree approach

### Platforms

1. **TradingView**: [tradingview.com](https://www.tradingview.com/) - Pine Script ecosystem
2. **QuantConnect**: [quantconnect.com](https://www.quantconnect.com/) - LEAN engine
3. **Freqtrade**: [freqtrade.io](https://www.freqtrade.io/) - Open source crypto bot
4. **Tradetron**: [tradetron.tech](https://tradetron.tech/) - No-code strategy builder
