"""Tests for the UTSS expression parser using real market data."""

import pandas as pd
import pytest

from pyutss import ConditionEvaluator, EvaluationContext, SignalEvaluator
from pyutss.engine.expr_parser import (
    ExpressionError,
    ExpressionLexer,
    ExpressionParser,
    TokenType,
)


# sample_data fixture is provided by conftest.py (real AAPL data)


class TestExpressionLexer:
    """Tests for the expression lexer."""

    def test_tokenize_simple_comparison(self):
        """Tokenize a simple comparison."""
        lexer = ExpressionLexer("RSI(14) < 30")
        tokens = lexer.tokenize()

        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "RSI"
        assert tokens[1].type == TokenType.LPAREN
        assert tokens[2].type == TokenType.NUMBER
        assert tokens[2].value == 14.0
        assert tokens[3].type == TokenType.RPAREN
        assert tokens[4].type == TokenType.LT
        assert tokens[5].type == TokenType.NUMBER
        assert tokens[5].value == 30.0
        assert tokens[6].type == TokenType.EOF

    def test_tokenize_logical_operators(self):
        """Tokenize logical operators."""
        lexer = ExpressionLexer("a > 1 and b < 2 or not c")
        tokens = lexer.tokenize()

        types = [t.type for t in tokens]
        assert TokenType.AND in types
        assert TokenType.OR in types
        assert TokenType.NOT in types

    def test_tokenize_comparison_operators(self):
        """Tokenize all comparison operators."""
        lexer = ExpressionLexer("a > b >= c < d <= e == f != g")
        tokens = lexer.tokenize()

        types = [t.type for t in tokens]
        assert TokenType.GT in types
        assert TokenType.GTE in types
        assert TokenType.LT in types
        assert TokenType.LTE in types
        assert TokenType.EQ in types
        assert TokenType.NEQ in types

    def test_tokenize_offset(self):
        """Tokenize historical offset."""
        lexer = ExpressionLexer("close[-1]")
        tokens = lexer.tokenize()

        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "close"
        assert tokens[1].type == TokenType.LBRACKET
        assert tokens[2].type == TokenType.MINUS
        assert tokens[3].type == TokenType.NUMBER
        assert tokens[3].value == 1.0
        assert tokens[4].type == TokenType.RBRACKET

    def test_tokenize_decimal_number(self):
        """Tokenize decimal numbers."""
        lexer = ExpressionLexer("BB(20, 2.5)")
        tokens = lexer.tokenize()

        assert tokens[4].type == TokenType.NUMBER
        assert tokens[4].value == 2.5


class TestExpressionParser:
    """Tests for the expression parser with real data."""

    def test_parse_simple_comparison(self, sample_data):
        """Parse and evaluate RSI < 30."""
        parser = ExpressionParser()
        signal_eval = SignalEvaluator()

        result = parser.evaluate("RSI(14) < 30", sample_data, signal_eval)

        assert isinstance(result, pd.Series)
        assert result.dtype == bool
        assert len(result) == len(sample_data)

    def test_parse_price_comparison(self, sample_data):
        """Parse and evaluate close > SMA(20)."""
        parser = ExpressionParser()
        signal_eval = SignalEvaluator()

        result = parser.evaluate("close > SMA(20)", sample_data, signal_eval)

        assert isinstance(result, pd.Series)
        assert result.dtype == bool

    def test_parse_indicator_comparison(self, sample_data):
        """Parse and evaluate SMA(50) > SMA(200)."""
        parser = ExpressionParser()
        signal_eval = SignalEvaluator()

        result = parser.evaluate("SMA(50) > SMA(200)", sample_data, signal_eval)

        assert isinstance(result, pd.Series)
        assert result.dtype == bool

    def test_parse_and_expression(self, sample_data):
        """Parse and evaluate AND expression."""
        parser = ExpressionParser()
        signal_eval = SignalEvaluator()

        result = parser.evaluate("RSI(14) < 70 and close > SMA(20)", sample_data, signal_eval)

        assert isinstance(result, pd.Series)
        assert result.dtype == bool

    def test_parse_or_expression(self, sample_data):
        """Parse and evaluate OR expression."""
        parser = ExpressionParser()
        signal_eval = SignalEvaluator()

        result = parser.evaluate("RSI(14) < 30 or RSI(14) > 70", sample_data, signal_eval)

        assert isinstance(result, pd.Series)
        assert result.dtype == bool

    def test_parse_not_expression(self, sample_data):
        """Parse and evaluate NOT expression."""
        parser = ExpressionParser()
        signal_eval = SignalEvaluator()

        result = parser.evaluate("not RSI(14) > 70", sample_data, signal_eval)

        assert isinstance(result, pd.Series)
        assert result.dtype == bool

    def test_parse_historical_offset(self, sample_data):
        """Parse and evaluate historical offset."""
        parser = ExpressionParser()
        signal_eval = SignalEvaluator()

        result = parser.evaluate("close > close[-1]", sample_data, signal_eval)

        assert isinstance(result, pd.Series)
        assert result.dtype == bool
        # First value should be NaN (no previous close)
        assert pd.isna(result.iloc[0]) or not result.iloc[0]

    def test_parse_crossover_pattern(self, sample_data):
        """Parse and evaluate crossover pattern (golden cross)."""
        parser = ExpressionParser()
        signal_eval = SignalEvaluator()

        # Golden cross: SMA(50) crosses above SMA(200)
        formula = "SMA(50)[-1] <= SMA(200)[-1] and SMA(50) > SMA(200)"
        result = parser.evaluate(formula, sample_data, signal_eval)

        assert isinstance(result, pd.Series)
        assert result.dtype == bool

    def test_parse_number_literal(self, sample_data):
        """Parse number literal comparisons."""
        parser = ExpressionParser()
        signal_eval = SignalEvaluator()

        result = parser.evaluate("30 < RSI(14)", sample_data, signal_eval)

        assert isinstance(result, pd.Series)
        assert result.dtype == bool

    def test_parse_parentheses(self, sample_data):
        """Parse parenthesized expressions."""
        parser = ExpressionParser()
        signal_eval = SignalEvaluator()

        result = parser.evaluate("(RSI(14) < 30) or (RSI(14) > 70)", sample_data, signal_eval)

        assert isinstance(result, pd.Series)
        assert result.dtype == bool

    def test_parse_complex_expression(self, sample_data):
        """Parse complex nested expression."""
        parser = ExpressionParser()
        signal_eval = SignalEvaluator()

        formula = "(close > SMA(20) and RSI(14) < 70) or (close < SMA(20) and RSI(14) > 30)"
        result = parser.evaluate(formula, sample_data, signal_eval)

        assert isinstance(result, pd.Series)
        assert result.dtype == bool

    def test_invalid_syntax_raises_error(self, sample_data):
        """Invalid syntax should raise ExpressionError."""
        parser = ExpressionParser()
        signal_eval = SignalEvaluator()

        with pytest.raises(ExpressionError):
            parser.evaluate("RSI(14 < 30", sample_data, signal_eval)  # Missing )

    def test_unknown_identifier_raises_error(self, sample_data):
        """Unknown identifier should raise error."""
        parser = ExpressionParser()
        signal_eval = SignalEvaluator()

        with pytest.raises(ExpressionError):
            parser.evaluate("unknown_field > 0", sample_data, signal_eval)


class TestConditionEvaluatorExpr:
    """Test expr condition type through ConditionEvaluator."""

    def test_expr_condition_type(self, sample_data):
        """Test expr condition type works through ConditionEvaluator."""
        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)
        context = EvaluationContext(primary_data=sample_data)

        condition = {
            "type": "expr",
            "formula": "RSI(14) < 30",
        }
        result = cond_eval.evaluate_condition(condition, context)

        assert isinstance(result, pd.Series)
        assert result.dtype == bool

    def test_expr_golden_cross(self, sample_data):
        """Test golden cross formula through ConditionEvaluator."""
        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)
        context = EvaluationContext(primary_data=sample_data)

        condition = {
            "type": "expr",
            "formula": "SMA(50)[-1] <= SMA(200)[-1] and SMA(50) > SMA(200)",
        }
        result = cond_eval.evaluate_condition(condition, context)

        assert isinstance(result, pd.Series)
        assert result.dtype == bool

    def test_expr_empty_formula_raises_error(self, sample_data):
        """Empty formula should raise EvaluationError."""
        from pyutss.engine.evaluator import EvaluationError

        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)
        context = EvaluationContext(primary_data=sample_data)

        condition = {
            "type": "expr",
            "formula": "",
        }
        with pytest.raises(EvaluationError):
            cond_eval.evaluate_condition(condition, context)


class TestRealPatterns:
    """Test real trading patterns from examples/."""

    def test_rsi_oversold(self, sample_data):
        """Test RSI oversold pattern."""
        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)
        context = EvaluationContext(primary_data=sample_data)

        condition = {"type": "expr", "formula": "RSI(14) < 30"}
        result = cond_eval.evaluate_condition(condition, context)

        # RSI oversold should be rare but possible
        assert isinstance(result, pd.Series)
        # At least some values should be computed (after warmup)
        assert result.notna().sum() > 0

    def test_rsi_overbought(self, sample_data):
        """Test RSI overbought pattern."""
        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)
        context = EvaluationContext(primary_data=sample_data)

        condition = {"type": "expr", "formula": "RSI(14) > 70"}
        result = cond_eval.evaluate_condition(condition, context)

        assert isinstance(result, pd.Series)
        assert result.notna().sum() > 0

    def test_price_above_sma(self, sample_data):
        """Test price above SMA pattern."""
        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)
        context = EvaluationContext(primary_data=sample_data)

        condition = {"type": "expr", "formula": "close > SMA(50)"}
        result = cond_eval.evaluate_condition(condition, context)

        assert isinstance(result, pd.Series)
        # Should have some True and some False values
        valid = result.dropna()
        assert valid.any()  # Some days above SMA

    def test_death_cross(self, sample_data):
        """Test death cross pattern (SMA 50 crosses below SMA 200)."""
        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)
        context = EvaluationContext(primary_data=sample_data)

        condition = {
            "type": "expr",
            "formula": "SMA(50)[-1] >= SMA(200)[-1] and SMA(50) < SMA(200)",
        }
        result = cond_eval.evaluate_condition(condition, context)

        assert isinstance(result, pd.Series)
        # Death cross is rare but the pattern should evaluate

    def test_bullish_momentum(self, sample_data):
        """Test bullish momentum: price up and RSI confirming."""
        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)
        context = EvaluationContext(primary_data=sample_data)

        condition = {
            "type": "expr",
            "formula": "close > close[-1] and RSI(14) > 50 and RSI(14) < 70",
        }
        result = cond_eval.evaluate_condition(condition, context)

        assert isinstance(result, pd.Series)
