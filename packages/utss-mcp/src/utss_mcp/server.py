"""MCP server implementation for UTSS."""

import asyncio
import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from utss_mcp.tools import (
    build_strategy,
    backtest_strategy,
    validate_strategy,
    list_indicators,
    revise_strategy,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("utss-mcp")

# Create server instance
server = Server("utss-mcp")


# Tool definitions
TOOLS = [
    Tool(
        name="build_strategy",
        description="""Build a trading strategy interactively.

Start a new strategy building session or continue an existing one.
The conversation will guide you through:
- Strategy type (mean reversion, trend following, etc.)
- Universe selection (specific stocks, index members, screener)
- Entry/exit conditions with technical indicators
- Position sizing and risk management

Examples:
- "I want a mean reversion strategy using RSI for tech stocks"
- Continue with option number: "1" or option id: "RSI"
- Free-form input: "AAPL, MSFT, GOOGL"

Returns structured questions with options to choose from.""",
        inputSchema={
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Your strategy description or answer to current question",
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID to continue (omit for new session)",
                },
            },
            "required": ["prompt"],
        },
    ),
    Tool(
        name="validate_strategy",
        description="Validate a UTSS strategy YAML against the schema.",
        inputSchema={
            "type": "object",
            "properties": {
                "strategy_yaml": {
                    "type": "string",
                    "description": "The UTSS strategy in YAML format",
                },
            },
            "required": ["strategy_yaml"],
        },
    ),
    Tool(
        name="backtest_strategy",
        description="""Run a backtest simulation on a UTSS strategy.

Tests the strategy against historical price data and returns
performance metrics including returns, Sharpe ratio, drawdown,
win rate, and trade history.""",
        inputSchema={
            "type": "object",
            "properties": {
                "strategy_yaml": {
                    "type": "string",
                    "description": "The UTSS strategy in YAML format",
                },
                "symbol": {
                    "type": "string",
                    "description": "Stock symbol (e.g., 'AAPL', '7203.T')",
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date (YYYY-MM-DD)",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date (YYYY-MM-DD)",
                },
                "initial_capital": {
                    "type": "number",
                    "description": "Starting capital (default: 100000)",
                    "default": 100000,
                },
            },
            "required": ["strategy_yaml", "symbol", "start_date", "end_date"],
        },
    ),
    Tool(
        name="list_indicators",
        description="List all supported technical indicators for UTSS strategies, organized by category.",
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    Tool(
        name="revise_strategy",
        description="Revise a strategy being built in an active session.",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "The session ID from build_strategy",
                },
                "instruction": {
                    "type": "string",
                    "description": "What to change (e.g., 'change RSI to 25')",
                },
            },
            "required": ["session_id", "instruction"],
        },
    ),
]


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Return list of available tools."""
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    logger.info(f"Tool called: {name} with args: {arguments}")

    try:
        if name == "build_strategy":
            result = await build_strategy(
                prompt=arguments.get("prompt", ""),
                session_id=arguments.get("session_id"),
            )
        elif name == "validate_strategy":
            result = await validate_strategy(
                strategy_yaml=arguments["strategy_yaml"],
            )
        elif name == "backtest_strategy":
            result = await backtest_strategy(
                strategy_yaml=arguments["strategy_yaml"],
                symbol=arguments["symbol"],
                start_date=arguments["start_date"],
                end_date=arguments["end_date"],
                initial_capital=arguments.get("initial_capital", 100000),
            )
        elif name == "list_indicators":
            result = await list_indicators()
        elif name == "revise_strategy":
            result = await revise_strategy(
                session_id=arguments["session_id"],
                instruction=arguments["instruction"],
            )
        else:
            result = {"error": f"Unknown tool: {name}"}

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Tool error: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


def main():
    """Run the MCP server."""
    logger.info("Starting UTSS MCP server...")
    asyncio.run(stdio_server(server))


if __name__ == "__main__":
    main()
