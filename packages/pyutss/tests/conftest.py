"""Shared fixtures for pyutss tests using real market data.

All fixtures fetch real data from Yahoo Finance to ensure
tests validate against actual market behavior.
"""

from datetime import date, timedelta

import pandas as pd
import pytest

from pyutss.data import available_sources, fetch


def has_yahoo() -> bool:
    """Check if Yahoo Finance is available."""
    return "yahoo" in available_sources()


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to lowercase for backtest engine."""
    df.columns = [c.lower() for c in df.columns]
    return df


# Skip all tests if Yahoo Finance is not available
pytestmark = pytest.mark.skipif(not has_yahoo(), reason="Yahoo Finance not available")


@pytest.fixture(scope="session")
def real_data_aapl() -> pd.DataFrame:
    """Fetch 2 years of AAPL data for testing.

    Session-scoped to avoid repeated API calls.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=730)  # 2 years
    return normalize_columns(fetch("AAPL", start_date, end_date))


@pytest.fixture(scope="session")
def real_data_spy() -> pd.DataFrame:
    """Fetch 2 years of SPY data for testing.

    Session-scoped to avoid repeated API calls.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=730)  # 2 years
    return normalize_columns(fetch("SPY", start_date, end_date))


@pytest.fixture(scope="session")
def real_data_short() -> pd.DataFrame:
    """Fetch 6 months of AAPL data for shorter tests.

    Session-scoped to avoid repeated API calls.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=180)  # 6 months
    return normalize_columns(fetch("AAPL", start_date, end_date))


@pytest.fixture
def sample_data(real_data_short: pd.DataFrame) -> pd.DataFrame:
    """Alias for backwards compatibility with existing tests.

    Uses first 100 rows of real AAPL data (or all if less than 100).
    """
    return real_data_short.iloc[:100].copy()
