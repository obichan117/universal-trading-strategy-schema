"""Conversation state management for interactive strategy building."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ResponseType(str, Enum):
    """Type of conversation response."""

    QUESTION = "question"  # Asking for clarification
    CONFIRMATION = "confirmation"  # Confirming understanding
    COMPLETE = "complete"  # Strategy is complete
    ERROR = "error"  # Something went wrong
    PREVIEW = "preview"  # Showing partial strategy


@dataclass
class Option:
    """A selectable option for a question."""

    id: str
    label: str
    description: str | None = None
    value: Any = None  # The actual value to use if selected

    def __str__(self) -> str:
        if self.description:
            return f"{self.label} - {self.description}"
        return self.label


@dataclass
class Question:
    """A question to ask the user."""

    id: str
    text: str
    options: list[Option] = field(default_factory=list)
    allow_custom: bool = True  # Allow free-form answer
    multi_select: bool = False  # Allow multiple selections
    default: str | None = None  # Default option id

    @property
    def has_options(self) -> bool:
        return len(self.options) > 0


@dataclass
class Turn:
    """A single turn in the conversation."""

    role: str  # "user" or "assistant"
    content: str
    question: Question | None = None  # If assistant asked a question
    answer_option_id: str | None = None  # If user selected an option


@dataclass
class PartialStrategy:
    """Strategy being built incrementally."""

    # Core info
    name: str | None = None
    description: str | None = None

    # Universe
    universe_type: str | None = None  # static, screener
    symbols: list[str] = field(default_factory=list)
    index: str | None = None

    # Signals
    signals: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Conditions
    conditions: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Entry/Exit
    entry_indicator: str | None = None
    entry_params: dict[str, int | float] = field(default_factory=dict)
    entry_operator: str | None = None
    entry_threshold: float | None = None

    exit_indicator: str | None = None
    exit_params: dict[str, int | float] = field(default_factory=dict)
    exit_operator: str | None = None
    exit_threshold: float | None = None

    # Sizing
    sizing_type: str | None = None
    sizing_value: float | None = None

    # Risk management
    stop_loss_pct: float | None = None
    take_profit_pct: float | None = None
    trailing_stop_pct: float | None = None
    max_positions: int | None = None

    def to_utss_dict(self) -> dict[str, Any]:
        """Convert partial strategy to UTSS format."""
        strategy: dict[str, Any] = {
            "info": {
                "id": self._slugify(self.name) if self.name else "unnamed_strategy",
                "name": self.name or "Unnamed Strategy",
                "version": "1.0",
            }
        }

        if self.description:
            strategy["info"]["description"] = self.description

        # Universe
        if self.universe_type:
            strategy["universe"] = {"type": self.universe_type}
            if self.universe_type == "static" and self.symbols:
                strategy["universe"]["symbols"] = self.symbols
            elif self.universe_type == "screener" and self.index:
                strategy["universe"]["base"] = self.index

        # Signals
        if self.signals:
            strategy["signals"] = self.signals

        # Conditions
        if self.conditions:
            strategy["conditions"] = self.conditions

        # Rules
        rules = []
        if self.entry_indicator and self.entry_threshold is not None:
            entry_rule = self._build_entry_rule()
            if entry_rule:
                rules.append(entry_rule)

        if self.exit_indicator and self.exit_threshold is not None:
            exit_rule = self._build_exit_rule()
            if exit_rule:
                rules.append(exit_rule)

        if rules:
            strategy["rules"] = rules

        # Constraints
        constraints: dict[str, Any] = {}
        if self.stop_loss_pct:
            constraints["stop_loss"] = {"percent": self.stop_loss_pct}
        if self.take_profit_pct:
            constraints["take_profit"] = {"percent": self.take_profit_pct}
        if self.trailing_stop_pct:
            constraints["trailing_stop"] = {"percent": self.trailing_stop_pct}
        if self.max_positions:
            constraints["max_positions"] = self.max_positions

        if constraints:
            strategy["constraints"] = constraints

        return strategy

    def _build_entry_rule(self) -> dict[str, Any] | None:
        """Build entry rule from partial strategy."""
        if not self.entry_indicator:
            return None

        return {
            "name": f"Entry on {self.entry_indicator}",
            "when": {
                "type": "comparison",
                "left": {
                    "type": "indicator",
                    "indicator": self.entry_indicator,
                    "params": self.entry_params or {"period": 14},
                },
                "operator": self.entry_operator or "<",
                "right": {"type": "constant", "value": self.entry_threshold},
            },
            "then": {
                "type": "trade",
                "direction": "buy",
                "sizing": {
                    "type": self.sizing_type or "percent_of_equity",
                    "percent": self.sizing_value or 10,
                },
            },
        }

    def _build_exit_rule(self) -> dict[str, Any] | None:
        """Build exit rule from partial strategy."""
        if not self.exit_indicator:
            return None

        return {
            "name": f"Exit on {self.exit_indicator}",
            "when": {
                "type": "comparison",
                "left": {
                    "type": "indicator",
                    "indicator": self.exit_indicator,
                    "params": self.exit_params or {"period": 14},
                },
                "operator": self.exit_operator or ">",
                "right": {"type": "constant", "value": self.exit_threshold},
            },
            "then": {
                "type": "trade",
                "direction": "sell",
                "sizing": {"type": "percent_of_position", "percent": 100},
            },
        }

    def _slugify(self, text: str) -> str:
        """Convert text to slug format."""
        return text.lower().replace(" ", "_").replace("-", "_")


@dataclass
class ConversationState:
    """Current state of a strategy-building conversation."""

    partial_strategy: PartialStrategy = field(default_factory=PartialStrategy)
    history: list[Turn] = field(default_factory=list)
    current_step: str = "initial"  # Track where we are in the flow
    is_complete: bool = False
    error: str | None = None

    def add_turn(self, role: str, content: str, question: Question | None = None) -> None:
        """Add a turn to the conversation history."""
        self.history.append(Turn(role=role, content=content, question=question))

    @property
    def last_question(self) -> Question | None:
        """Get the last question asked."""
        for turn in reversed(self.history):
            if turn.question:
                return turn.question
        return None


@dataclass
class ConversationResponse:
    """Response from the conversation session."""

    type: ResponseType
    message: str
    question: Question | None = None
    strategy_yaml: str | None = None
    strategy_dict: dict[str, Any] | None = None
    preview_yaml: str | None = None

    @property
    def is_complete(self) -> bool:
        return self.type == ResponseType.COMPLETE

    @property
    def needs_input(self) -> bool:
        return self.type == ResponseType.QUESTION
