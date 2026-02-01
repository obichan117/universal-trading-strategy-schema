"""HTML report generation for tear sheets.

Generates standalone HTML reports with embedded charts and statistics.
"""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from pyutss.metrics.calculator import PerformanceMetrics
    from pyutss.results.types import BacktestResult


def _figure_to_base64(fig) -> str:
    """Convert matplotlib figure to base64 encoded PNG."""
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()

    # Close the figure to free memory
    import matplotlib.pyplot as plt
    plt.close(fig)

    return img_base64


def _format_metric(value: float, metric_name: str) -> str:
    """Format metric value for display."""
    if "%" in metric_name or "Rate" in metric_name or "Exposure" in metric_name:
        return f"{value:.2f}%"
    elif "Ratio" in metric_name or "Factor" in metric_name:
        if value == float("inf"):
            return "∞"
        return f"{value:.2f}"
    elif "Trades" in metric_name or "Duration" in metric_name:
        return f"{value:.0f}"
    elif "$" in metric_name or "P&L" in metric_name:
        return f"${value:,.2f}"
    else:
        return f"{value:.2f}"


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        header {{
            background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        header h1 {{
            font-size: 2em;
            margin-bottom: 10px;
        }}
        header .subtitle {{
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #1a365d;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #f8fafc;
            border-radius: 6px;
            padding: 15px;
            border-left: 4px solid #2c5282;
        }}
        .stat-card.positive {{
            border-left-color: #38a169;
        }}
        .stat-card.negative {{
            border-left-color: #e53e3e;
        }}
        .stat-label {{
            font-size: 0.85em;
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .stat-value {{
            font-size: 1.5em;
            font-weight: 600;
            color: #1a365d;
        }}
        .chart-container {{
            margin: 20px 0;
            text-align: center;
        }}
        .chart-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .two-column {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{
            background: #f8fafc;
            font-weight: 600;
            color: #4a5568;
        }}
        tr:hover {{
            background: #f8fafc;
        }}
        footer {{
            text-align: center;
            padding: 20px;
            color: #718096;
            font-size: 0.9em;
            border-top: 1px solid #e2e8f0;
        }}
        footer a {{
            color: #2c5282;
            text-decoration: none;
        }}
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr 1fr;
            }}
            .two-column {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <div class="subtitle">{period}</div>
        </header>

        <div class="content">
            <div class="section">
                <h2>Performance Summary</h2>
                <div class="stats-grid">
                    {stats_cards}
                </div>
            </div>

            <div class="section">
                <h2>Equity Curve</h2>
                <div class="chart-container">
                    <img src="data:image/png;base64,{equity_chart}" alt="Equity Curve">
                </div>
            </div>

            <div class="section">
                <h2>Drawdown Analysis</h2>
                <div class="chart-container">
                    <img src="data:image/png;base64,{drawdown_chart}" alt="Drawdown">
                </div>
            </div>

            <div class="section">
                <h2>Monthly Returns</h2>
                <div class="chart-container">
                    <img src="data:image/png;base64,{monthly_chart}" alt="Monthly Returns">
                </div>
            </div>

            <div class="section two-column">
                <div>
                    <h2>Rolling Metrics</h2>
                    <div class="chart-container">
                        <img src="data:image/png;base64,{rolling_chart}" alt="Rolling Sharpe">
                    </div>
                </div>
                <div>
                    <h2>Return Distribution</h2>
                    <div class="chart-container">
                        <img src="data:image/png;base64,{distribution_chart}" alt="Distribution">
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>Trade Analysis</h2>
                <div class="chart-container">
                    <img src="data:image/png;base64,{trade_chart}" alt="Trade Analysis">
                </div>
            </div>

            <div class="section">
                <h2>Detailed Metrics</h2>
                {metrics_table}
            </div>
        </div>

        <footer>
            Generated by <a href="https://github.com/obichan117/utss">pyutss</a> | {timestamp}
        </footer>
    </div>
</body>
</html>
"""


def generate_html_report(
    result: BacktestResult,
    metrics: PerformanceMetrics,
    output_path: str | Path,
    title: str,
    benchmark: pd.Series | None = None,
    risk_free_rate: float = 0.0,
) -> None:
    """Generate comprehensive HTML tear sheet report.

    Args:
        result: BacktestResult from backtesting
        metrics: Calculated PerformanceMetrics
        output_path: Path to save HTML file
        title: Report title
        benchmark: Optional benchmark for comparison
        risk_free_rate: Risk-free rate for calculations
    """
    from datetime import datetime

    from pyutss.visualization.charts import (
        plot_distribution,
        plot_drawdown,
        plot_equity_curve,
        plot_monthly_heatmap,
        plot_rolling_metrics,
        plot_trade_analysis,
    )

    # Generate charts
    equity_fig = plot_equity_curve(result, benchmark=benchmark, figsize=(11, 5))
    drawdown_fig = plot_drawdown(result, figsize=(11, 3))
    monthly_fig = plot_monthly_heatmap(result, figsize=(11, 5))
    rolling_fig = plot_rolling_metrics(result, figsize=(7, 4), risk_free_rate=risk_free_rate)
    dist_fig = plot_distribution(result, figsize=(7, 4))
    trade_fig = plot_trade_analysis(result, figsize=(11, 4))

    # Convert to base64
    equity_b64 = _figure_to_base64(equity_fig)
    drawdown_b64 = _figure_to_base64(drawdown_fig)
    monthly_b64 = _figure_to_base64(monthly_fig)
    rolling_b64 = _figure_to_base64(rolling_fig)
    dist_b64 = _figure_to_base64(dist_fig)
    trade_b64 = _figure_to_base64(trade_fig)

    # Generate stats cards
    key_stats = [
        ("Total Return", metrics.total_return_pct, "%", metrics.total_return_pct >= 0),
        ("Annualized Return", metrics.annualized_return_pct, "%", metrics.annualized_return_pct >= 0),
        ("Sharpe Ratio", metrics.sharpe_ratio, "", metrics.sharpe_ratio >= 0),
        ("Max Drawdown", -metrics.max_drawdown_pct, "%", False),
        ("Win Rate", metrics.win_rate, "%", metrics.win_rate >= 50),
        ("Profit Factor", metrics.profit_factor, "", metrics.profit_factor >= 1),
        ("Total Trades", metrics.total_trades, "", True),
        ("Volatility", metrics.volatility_annualized, "%", None),
    ]

    stats_cards = []
    for label, value, suffix, is_positive in key_stats:
        if value == float("inf"):
            display_val = "∞"
        elif isinstance(value, float):
            display_val = f"{value:.2f}{suffix}"
        else:
            display_val = f"{value}{suffix}"

        card_class = "stat-card"
        if is_positive is True:
            card_class += " positive"
        elif is_positive is False:
            card_class += " negative"

        stats_cards.append(f"""
            <div class="{card_class}">
                <div class="stat-label">{label}</div>
                <div class="stat-value">{display_val}</div>
            </div>
        """)

    stats_cards_html = "\n".join(stats_cards)

    # Generate metrics table
    all_metrics = metrics.to_dict()
    table_rows = []
    for key, value in all_metrics.items():
        formatted_key = key.replace("_", " ").title()
        if value == float("inf"):
            formatted_value = "∞"
        elif isinstance(value, float):
            formatted_value = f"{value:.4f}"
        else:
            formatted_value = str(value)
        table_rows.append(f"<tr><td>{formatted_key}</td><td>{formatted_value}</td></tr>")

    metrics_table = f"""
        <table>
            <thead>
                <tr><th>Metric</th><th>Value</th></tr>
            </thead>
            <tbody>
                {''.join(table_rows)}
            </tbody>
        </table>
    """

    # Period string
    period = f"{result.start_date} to {result.end_date}"

    # Timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Render HTML
    html = HTML_TEMPLATE.format(
        title=title,
        period=period,
        stats_cards=stats_cards_html,
        equity_chart=equity_b64,
        drawdown_chart=drawdown_b64,
        monthly_chart=monthly_b64,
        rolling_chart=rolling_b64,
        distribution_chart=dist_b64,
        trade_chart=trade_b64,
        metrics_table=metrics_table,
        timestamp=timestamp,
    )

    # Write file
    output_path = Path(output_path)
    output_path.write_text(html, encoding="utf-8")
