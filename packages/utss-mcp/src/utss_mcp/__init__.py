"""
utss-mcp - MCP server for UTSS strategy building.

Provides MCP tools for building and backtesting trading strategies
using Claude Code or other MCP-compatible clients.
"""

__version__ = "0.2.0"

from utss_mcp.tools import (
    backtest_strategy,
    build_strategy,
    list_indicators,
    revise_strategy,
    validate_strategy,
)

__all__ = [
    "build_strategy",
    "backtest_strategy",
    "validate_strategy",
    "list_indicators",
    "revise_strategy",
]
