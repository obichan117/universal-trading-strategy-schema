"""
utss-mcp - MCP server for UTSS strategy building.

Provides MCP tools for building and backtesting trading strategies
using Claude Code or other MCP-compatible clients.
"""

__version__ = "0.1.0"

from utss_mcp.tools import (
    build_strategy,
    backtest_strategy,
    validate_strategy,
    list_indicators,
)

__all__ = [
    "build_strategy",
    "backtest_strategy",
    "validate_strategy",
    "list_indicators",
]
