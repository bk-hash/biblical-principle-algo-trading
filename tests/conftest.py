"""
Shared test fixtures.
"""
import pytest
import pandas as pd
import numpy as np


def make_price_series(n: int = 200, start_price: float = 100.0, seed: int = 42) -> pd.Series:
    """Generate a synthetic price series using a random walk."""
    rng = np.random.default_rng(seed)
    daily_returns = rng.normal(0.0005, 0.01, n)
    prices = start_price * np.cumprod(1 + daily_returns)
    dates = pd.date_range("2022-01-01", periods=n, freq="B")
    return pd.Series(prices, index=dates, name="Close")


def make_price_df(n: int = 200, start_price: float = 100.0, seed: int = 42) -> pd.DataFrame:
    """Generate a synthetic OHLCV DataFrame."""
    close = make_price_series(n, start_price, seed)
    df = pd.DataFrame(
        {
            "Open": close * 0.999,
            "High": close * 1.005,
            "Low": close * 0.995,
            "Close": close,
            "Volume": np.random.default_rng(seed).integers(100_000, 1_000_000, n),
        },
        index=close.index,
    )
    return df


@pytest.fixture
def price_df() -> pd.DataFrame:
    return make_price_df()


@pytest.fixture
def trending_df() -> pd.DataFrame:
    """Price series with a clear uptrend (SMA crossover should fire)."""
    n = 200
    prices = np.linspace(80, 150, n)
    dates = pd.date_range("2022-01-01", periods=n, freq="B")
    close = pd.Series(prices, index=dates)
    return pd.DataFrame(
        {
            "Open": close * 0.999,
            "High": close * 1.005,
            "Low": close * 0.995,
            "Close": close,
        }
    )
