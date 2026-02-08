"""Reference signal evaluator."""

from typing import TYPE_CHECKING, Any

import pandas as pd

from pyutss.engine.evaluator.context import EvaluationContext, EvaluationError

if TYPE_CHECKING:
    from pyutss.engine.evaluator.signal_evaluator import SignalEvaluator


def eval_ref_signal(
    signal: dict[str, Any],
    context: EvaluationContext,
    evaluator: "SignalEvaluator",
) -> pd.Series:
    """Evaluate reference signal."""
    ref = signal.get("$ref", "")
    if ref.startswith("#/signals/"):
        ref_name = ref[10:]
        if context.signal_library and ref_name in context.signal_library:
            return evaluator.evaluate_signal(context.signal_library[ref_name], context)
    raise EvaluationError(f"Signal reference not found: {ref}")
