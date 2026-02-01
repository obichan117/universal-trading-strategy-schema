"""Expression parser for UTSS formula conditions.

Parses and evaluates formulas like:
- "SMA(50) > SMA(200)"
- "SMA(50)[-1] <= SMA(200)[-1] and SMA(50) > SMA(200)"  (crossover)
- "RSI(14) < 30"
- "close > SMA(20) and volume > SMA(volume, 20)"

Grammar (simplified):
    expr        := or_expr
    or_expr     := and_expr ("or" and_expr)*
    and_expr    := not_expr ("and" not_expr)*
    not_expr    := "not" not_expr | comparison
    comparison  := term (comp_op term)?
    term        := atom offset?
    offset      := "[" "-"? NUMBER "]"
    atom        := NUMBER | indicator_call | price_field | "(" expr ")"
    indicator_call := IDENTIFIER "(" params ")"
    params      := param ("," param)*
    param       := NUMBER | IDENTIFIER
    price_field := "close" | "open" | "high" | "low" | "volume"
    comp_op     := ">" | "<" | ">=" | "<=" | "==" | "!="
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

import pandas as pd


class TokenType(Enum):
    """Token types for the expression lexer."""

    NUMBER = auto()
    IDENTIFIER = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    MINUS = auto()
    GT = auto()
    LT = auto()
    GTE = auto()
    LTE = auto()
    EQ = auto()
    NEQ = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    EOF = auto()


@dataclass
class Token:
    """A token from the expression lexer."""

    type: TokenType
    value: Any
    position: int


class ExpressionLexer:
    """Tokenizes UTSS formula expressions."""

    # Keywords mapping
    KEYWORDS = {
        "and": TokenType.AND,
        "or": TokenType.OR,
        "not": TokenType.NOT,
    }

    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0
        self.length = len(text)

    def tokenize(self) -> list[Token]:
        """Tokenize the entire expression."""
        tokens: list[Token] = []
        while self.pos < self.length:
            token = self._next_token()
            if token:
                tokens.append(token)
        tokens.append(Token(TokenType.EOF, None, self.pos))
        return tokens

    def _next_token(self) -> Token | None:
        """Get the next token."""
        self._skip_whitespace()
        if self.pos >= self.length:
            return None

        start_pos = self.pos
        char = self.text[self.pos]

        # Two-character operators
        if self.pos + 1 < self.length:
            two_char = self.text[self.pos : self.pos + 2]
            if two_char == ">=":
                self.pos += 2
                return Token(TokenType.GTE, ">=", start_pos)
            if two_char == "<=":
                self.pos += 2
                return Token(TokenType.LTE, "<=", start_pos)
            if two_char == "==":
                self.pos += 2
                return Token(TokenType.EQ, "==", start_pos)
            if two_char == "!=":
                self.pos += 2
                return Token(TokenType.NEQ, "!=", start_pos)

        # Single-character tokens
        if char == "(":
            self.pos += 1
            return Token(TokenType.LPAREN, "(", start_pos)
        if char == ")":
            self.pos += 1
            return Token(TokenType.RPAREN, ")", start_pos)
        if char == "[":
            self.pos += 1
            return Token(TokenType.LBRACKET, "[", start_pos)
        if char == "]":
            self.pos += 1
            return Token(TokenType.RBRACKET, "]", start_pos)
        if char == ",":
            self.pos += 1
            return Token(TokenType.COMMA, ",", start_pos)
        if char == "-":
            self.pos += 1
            return Token(TokenType.MINUS, "-", start_pos)
        if char == ">":
            self.pos += 1
            return Token(TokenType.GT, ">", start_pos)
        if char == "<":
            self.pos += 1
            return Token(TokenType.LT, "<", start_pos)

        # Numbers (including decimals)
        if char.isdigit() or (char == "." and self._peek_digit()):
            return self._read_number(start_pos)

        # Identifiers and keywords
        if char.isalpha() or char == "_":
            return self._read_identifier(start_pos)

        raise ExpressionError(f"Unexpected character '{char}' at position {self.pos}")

    def _skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while self.pos < self.length and self.text[self.pos].isspace():
            self.pos += 1

    def _peek_digit(self) -> bool:
        """Check if next character is a digit."""
        return self.pos + 1 < self.length and self.text[self.pos + 1].isdigit()

    def _read_number(self, start_pos: int) -> Token:
        """Read a number token."""
        end = self.pos
        has_dot = False
        while end < self.length:
            c = self.text[end]
            if c.isdigit():
                end += 1
            elif c == "." and not has_dot:
                has_dot = True
                end += 1
            else:
                break
        value = float(self.text[self.pos : end])
        self.pos = end
        return Token(TokenType.NUMBER, value, start_pos)

    def _read_identifier(self, start_pos: int) -> Token:
        """Read an identifier or keyword token."""
        end = self.pos
        while end < self.length and (self.text[end].isalnum() or self.text[end] == "_"):
            end += 1
        value = self.text[self.pos : end]
        self.pos = end

        # Check for keywords (case-insensitive)
        lower_value = value.lower()
        if lower_value in self.KEYWORDS:
            return Token(self.KEYWORDS[lower_value], lower_value, start_pos)

        return Token(TokenType.IDENTIFIER, value, start_pos)


class ExpressionError(Exception):
    """Error during expression parsing or evaluation."""

    pass


@dataclass
class EvalContext:
    """Context for expression evaluation."""

    data: pd.DataFrame
    signal_evaluator: Any  # SignalEvaluator instance


class ExpressionParser:
    """Parses and evaluates UTSS formula expressions.

    Example usage:
        parser = ExpressionParser()
        result = parser.evaluate("SMA(50) > SMA(200)", data, signal_evaluator)
    """

    # Known price fields
    PRICE_FIELDS = {"close", "open", "high", "low", "volume", "hl2", "hlc3", "ohlc4"}

    def __init__(self) -> None:
        self.tokens: list[Token] = []
        self.pos = 0

    def evaluate(
        self,
        formula: str,
        data: pd.DataFrame,
        signal_evaluator: Any,
    ) -> pd.Series:
        """Parse and evaluate a formula expression.

        Args:
            formula: The formula string to evaluate
            data: OHLCV DataFrame
            signal_evaluator: SignalEvaluator instance for indicator evaluation

        Returns:
            Boolean Series where True indicates condition is met
        """
        # Tokenize
        lexer = ExpressionLexer(formula)
        self.tokens = lexer.tokenize()
        self.pos = 0

        # Create evaluation context
        ctx = EvalContext(data=data, signal_evaluator=signal_evaluator)

        # Parse and evaluate
        result = self._parse_expr(ctx)

        # Ensure we consumed all tokens
        if self._current().type != TokenType.EOF:
            raise ExpressionError(
                f"Unexpected token '{self._current().value}' at position {self._current().position}"
            )

        return result

    def _current(self) -> Token:
        """Get current token."""
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        """Advance to next token and return previous."""
        token = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return token

    def _expect(self, token_type: TokenType) -> Token:
        """Expect a specific token type."""
        token = self._current()
        if token.type != token_type:
            raise ExpressionError(
                f"Expected {token_type.name}, got {token.type.name} at position {token.position}"
            )
        return self._advance()

    def _parse_expr(self, ctx: EvalContext) -> pd.Series:
        """Parse expression (entry point): or_expr."""
        return self._parse_or_expr(ctx)

    def _parse_or_expr(self, ctx: EvalContext) -> pd.Series:
        """Parse: and_expr ("or" and_expr)*"""
        left = self._parse_and_expr(ctx)
        while self._current().type == TokenType.OR:
            self._advance()
            right = self._parse_and_expr(ctx)
            left = left | right
        return left

    def _parse_and_expr(self, ctx: EvalContext) -> pd.Series:
        """Parse: not_expr ("and" not_expr)*"""
        left = self._parse_not_expr(ctx)
        while self._current().type == TokenType.AND:
            self._advance()
            right = self._parse_not_expr(ctx)
            left = left & right
        return left

    def _parse_not_expr(self, ctx: EvalContext) -> pd.Series:
        """Parse: "not" not_expr | comparison"""
        if self._current().type == TokenType.NOT:
            self._advance()
            return ~self._parse_not_expr(ctx)
        return self._parse_comparison(ctx)

    def _parse_comparison(self, ctx: EvalContext) -> pd.Series:
        """Parse: term (comp_op term)?"""
        left = self._parse_term(ctx)

        comp_ops = {
            TokenType.GT: lambda a, b: a > b,
            TokenType.LT: lambda a, b: a < b,
            TokenType.GTE: lambda a, b: a >= b,
            TokenType.LTE: lambda a, b: a <= b,
            TokenType.EQ: lambda a, b: a == b,
            TokenType.NEQ: lambda a, b: a != b,
        }

        if self._current().type in comp_ops:
            op = comp_ops[self._current().type]
            self._advance()
            right = self._parse_term(ctx)
            return op(left, right)

        # If no comparison, convert to boolean (non-zero = True)
        return left != 0

    def _parse_term(self, ctx: EvalContext) -> pd.Series:
        """Parse: atom offset?"""
        value = self._parse_atom(ctx)

        # Check for offset like [-1]
        if self._current().type == TokenType.LBRACKET:
            self._advance()  # consume [
            negative = False
            if self._current().type == TokenType.MINUS:
                negative = True
                self._advance()
            offset_token = self._expect(TokenType.NUMBER)
            offset = int(offset_token.value)
            if negative:
                offset = -offset
            self._expect(TokenType.RBRACKET)
            value = value.shift(-offset)  # shift(-(-1)) = shift(1) = previous value

        return value

    def _parse_atom(self, ctx: EvalContext) -> pd.Series:
        """Parse: NUMBER | indicator_call | price_field | "(" expr ")" """
        token = self._current()

        # Parenthesized expression
        if token.type == TokenType.LPAREN:
            self._advance()
            result = self._parse_expr(ctx)
            self._expect(TokenType.RPAREN)
            return result

        # Number literal
        if token.type == TokenType.NUMBER:
            self._advance()
            return pd.Series(token.value, index=ctx.data.index)

        # Identifier: could be price field or indicator call
        if token.type == TokenType.IDENTIFIER:
            name = token.value
            self._advance()

            # Check if it's an indicator call (followed by parenthesis)
            if self._current().type == TokenType.LPAREN:
                return self._parse_indicator_call(name, ctx)

            # Otherwise it's a price field
            return self._parse_price_field(name, ctx)

        raise ExpressionError(
            f"Unexpected token '{token.value}' at position {token.position}"
        )

    def _parse_indicator_call(self, name: str, ctx: EvalContext) -> pd.Series:
        """Parse indicator call like SMA(20) or MACD(12, 26, 9)."""
        self._expect(TokenType.LPAREN)

        # Parse parameters
        params: list[Any] = []
        if self._current().type != TokenType.RPAREN:
            params.append(self._parse_param(ctx))
            while self._current().type == TokenType.COMMA:
                self._advance()
                params.append(self._parse_param(ctx))

        self._expect(TokenType.RPAREN)

        # Build signal definition and evaluate using SignalEvaluator
        signal = self._build_indicator_signal(name.upper(), params)

        # Import here to avoid circular dependency
        from pyutss.engine.evaluator import EvaluationContext

        eval_ctx = EvaluationContext(primary_data=ctx.data)
        return ctx.signal_evaluator.evaluate_signal(signal, eval_ctx)

    def _parse_param(self, ctx: EvalContext) -> Any:
        """Parse a parameter (number or identifier for source)."""
        token = self._current()
        if token.type == TokenType.NUMBER:
            self._advance()
            return token.value
        if token.type == TokenType.IDENTIFIER:
            self._advance()
            return token.value
        raise ExpressionError(
            f"Expected parameter, got {token.type.name} at position {token.position}"
        )

    def _parse_price_field(self, name: str, ctx: EvalContext) -> pd.Series:
        """Parse price field like close, open, high, low, volume."""
        name_lower = name.lower()

        if name_lower in ctx.data.columns:
            return ctx.data[name_lower]

        # Handle computed fields
        if name_lower == "hl2":
            return (ctx.data["high"] + ctx.data["low"]) / 2
        if name_lower == "hlc3":
            return (ctx.data["high"] + ctx.data["low"] + ctx.data["close"]) / 3
        if name_lower == "ohlc4":
            return (
                ctx.data["open"]
                + ctx.data["high"]
                + ctx.data["low"]
                + ctx.data["close"]
            ) / 4

        raise ExpressionError(f"Unknown price field or indicator: {name}")

    def _build_indicator_signal(self, indicator: str, params: list[Any]) -> dict:
        """Build a signal definition for an indicator call."""
        signal: dict[str, Any] = {"type": "indicator", "indicator": indicator}

        # Map common indicators to their parameter structures
        if indicator in ("SMA", "EMA", "WMA", "RSI", "ATR", "ADX", "CCI", "MFI"):
            if params:
                signal["params"] = {"period": int(params[0])}
                if len(params) > 1 and isinstance(params[1], str):
                    signal["params"]["source"] = params[1]

        elif indicator in ("STOCH", "STOCHASTIC"):
            signal["params"] = {}
            if len(params) >= 1:
                signal["params"]["k_period"] = int(params[0])
            if len(params) >= 2:
                signal["params"]["d_period"] = int(params[1])

        elif indicator == "MACD":
            signal["params"] = {}
            if len(params) >= 1:
                signal["params"]["fast_period"] = int(params[0])
            if len(params) >= 2:
                signal["params"]["slow_period"] = int(params[1])
            if len(params) >= 3:
                signal["params"]["signal_period"] = int(params[2])

        elif indicator in ("BB", "BOLLINGER"):
            signal["params"] = {}
            if len(params) >= 1:
                signal["params"]["period"] = int(params[0])
            if len(params) >= 2:
                signal["params"]["std_dev"] = float(params[1])

        elif indicator in ("WILLIAMS_R", "WILLR"):
            signal["indicator"] = "WILLIAMS_R"
            if params:
                signal["params"] = {"period": int(params[0])}

        elif indicator == "OBV":
            signal["params"] = {}

        elif indicator == "VWAP":
            signal["params"] = {}

        else:
            # Generic: assume first param is period
            if params:
                signal["params"] = {"period": int(params[0])}

        return signal
