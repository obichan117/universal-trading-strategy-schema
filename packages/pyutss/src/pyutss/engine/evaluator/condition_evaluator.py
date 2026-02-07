"""Condition evaluator for UTSS strategies."""

from typing import Any

import pandas as pd

from pyutss.engine.evaluator.context import (
    EvaluationContext,
    EvaluationError,
)
from pyutss.engine.evaluator.signal_evaluator import SignalEvaluator


class ConditionEvaluator:
    """Evaluates UTSS conditions against signals.

    UTSS v1.0 Condition Types:
    - comparison: Compare signal to value (>, <, =, etc.)
    - and/or/not: Logical combinations
    - expr: Formula expressions for complex patterns
    - always: Always true

    Example:
        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)
        context = EvaluationContext(primary_data=ohlcv_df)

        condition = {
            "type": "comparison",
            "left": {"type": "indicator", "indicator": "RSI", "params": {"period": 14}},
            "operator": "<",
            "right": {"type": "constant", "value": 30}
        }
        result = cond_eval.evaluate_condition(condition, context)
    """

    def __init__(self, signal_evaluator: SignalEvaluator) -> None:
        """Initialize condition evaluator."""
        self.signal_eval = signal_evaluator

    def evaluate_condition(
        self,
        condition: dict[str, Any],
        context: EvaluationContext,
    ) -> pd.Series:
        """Evaluate a condition to get boolean series."""
        # Check for $ref first (can appear without explicit type field)
        if "$ref" in condition:
            return self._eval_ref(condition, context)

        cond_type = condition.get("type", "comparison")

        if cond_type == "comparison":
            return self._eval_comparison(condition, context)
        elif cond_type == "and":
            return self._eval_and(condition, context)
        elif cond_type == "or":
            return self._eval_or(condition, context)
        elif cond_type == "not":
            return self._eval_not(condition, context)
        elif cond_type == "expr":
            return self._eval_expr(condition, context)
        elif cond_type == "always":
            return pd.Series(True, index=context.get_data().index)
        elif cond_type == "$ref":
            return self._eval_ref(condition, context)
        else:
            raise EvaluationError(f"Unsupported condition type: {cond_type}")

    def _eval_comparison(
        self, condition: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate comparison condition."""
        left = self.signal_eval.evaluate_signal(condition["left"], context)
        right = self.signal_eval.evaluate_signal(condition["right"], context)
        operator = condition.get("operator", "=")

        if operator == "<" or operator == "lt":
            return left < right
        elif operator == "<=" or operator == "lte":
            return left <= right
        elif operator == "=" or operator == "==" or operator == "eq":
            return left == right
        elif operator == ">=" or operator == "gte":
            return left >= right
        elif operator == ">" or operator == "gt":
            return left > right
        elif operator == "!=" or operator == "ne":
            return left != right
        else:
            raise EvaluationError(f"Unknown comparison operator: {operator}")

    def _eval_and(
        self, condition: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate AND condition."""
        conditions = condition.get("conditions", [])
        if not conditions:
            return pd.Series(True, index=context.get_data().index)

        result = self.evaluate_condition(conditions[0], context)
        for cond in conditions[1:]:
            result = result & self.evaluate_condition(cond, context)
        return result

    def _eval_or(
        self, condition: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate OR condition."""
        conditions = condition.get("conditions", [])
        if not conditions:
            return pd.Series(False, index=context.get_data().index)

        result = self.evaluate_condition(conditions[0], context)
        for cond in conditions[1:]:
            result = result | self.evaluate_condition(cond, context)
        return result

    def _eval_not(
        self, condition: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate NOT condition."""
        inner = condition.get("condition", {})
        return ~self.evaluate_condition(inner, context)

    def _eval_expr(
        self, condition: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate expression condition."""
        formula = condition.get("formula", "")
        if not formula:
            raise EvaluationError("Expression condition requires 'formula' field")

        from pyutss.engine.expr_parser import ExpressionError, ExpressionParser

        parser = ExpressionParser()
        try:
            return parser.evaluate(formula, context.get_data(), self.signal_eval)
        except ExpressionError as e:
            raise EvaluationError(f"Expression evaluation error: {e}") from e

    def _eval_ref(
        self, condition: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate reference condition."""
        ref = condition.get("$ref", "")
        if ref.startswith("#/conditions/"):
            ref_name = ref[13:]
            if context.condition_library and ref_name in context.condition_library:
                return self.evaluate_condition(
                    context.condition_library[ref_name], context
                )
        raise EvaluationError(f"Condition reference not found: {ref}")
