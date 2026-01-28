"""
utss-llm - LLM-powered natural language to UTSS strategy parser.

Convert natural language descriptions into validated UTSS strategies.
Supports both one-shot parsing and interactive conversation-based building.
"""

from utss_llm.parser import StrategyParser, ParseResult, ParseMode

# Conversation module
from utss_llm.conversation import (
    ConversationSession,
    ConversationResponse,
    ConversationState,
    Question,
    Option,
    ResponseType,
    create_session,
    get_session,
)

__version__ = "0.1.0"

__all__ = [
    # One-shot parser
    "StrategyParser",
    "ParseResult",
    "ParseMode",
    # Conversation
    "ConversationSession",
    "ConversationResponse",
    "ConversationState",
    "Question",
    "Option",
    "ResponseType",
    "create_session",
    "get_session",
]
