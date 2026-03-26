"""Tests for MovingAverageCrossover and RSIStrategy."""
import numpy as np
import pandas as pd
import pytest

from src.strategies.moving_average import MovingAverageCrossover
from src.strategies.rsi import RSIStrategy
from tests.conftest import make_price_df, make_price_series


class TestMovingAverageCrossover:
    def test_constructor_validates_windows(self):
        with pytest.raises(ValueError):
            MovingAverageCrossover(short_window=50, long_window=20)

    def test_signals_shape_matches_data(self, price_df):
        strat = MovingAverageCrossover(short_window=10, long_window=30)
        signals = strat.generate_signals(price_df)
        assert len(signals) == len(price_df)

    def test_signals_values_are_valid(self, price_df):
        strat = MovingAverageCrossover(short_window=10, long_window=30)
        signals = strat.generate_signals(price_df)
        assert set(signals.unique()).issubset({-1, 0, 1})

    def test_uptrend_generates_buy(self, trending_df):
        """In a pure uptrend the short MA crosses above the long MA once."""
        strat = MovingAverageCrossover(short_window=10, long_window=50)
        signals = strat.generate_signals(trending_df)
        assert (signals == 1).any(), "Expected at least one buy signal in uptrend"

    def test_missing_column_raises(self, price_df):
        strat = MovingAverageCrossover()
        bad_df = price_df.drop(columns=["Close"])
        with pytest.raises(ValueError):
            strat.generate_signals(bad_df)

    def test_compute_moving_averages_columns(self, price_df):
        strat = MovingAverageCrossover(short_window=10, long_window=30)
        ma_df = strat.compute_moving_averages(price_df)
        assert "Price" in ma_df.columns
        assert "SMA_10" in ma_df.columns
        assert "SMA_30" in ma_df.columns

    def test_repr(self):
        strat = MovingAverageCrossover(20, 50)
        assert "SMA_20_50" in repr(strat)


class TestRSIStrategy:
    def test_constructor_validates_levels(self):
        with pytest.raises(ValueError):
            RSIStrategy(oversold_level=70, overbought_level=30)

    def test_signals_shape_matches_data(self, price_df):
        strat = RSIStrategy()
        signals = strat.generate_signals(price_df)
        assert len(signals) == len(price_df)

    def test_signals_values_are_valid(self, price_df):
        strat = RSIStrategy()
        signals = strat.generate_signals(price_df)
        assert set(signals.unique()).issubset({-1, 0, 1})

    def test_missing_column_raises(self, price_df):
        strat = RSIStrategy()
        bad_df = price_df.drop(columns=["Close"])
        with pytest.raises(ValueError):
            strat.generate_signals(bad_df)

    def test_rsi_range(self, price_df):
        strat = RSIStrategy()
        rsi = strat.compute_rsi(price_df).dropna()
        assert (rsi >= 0).all() and (rsi <= 100).all()

    def test_oversold_triggers_buy(self):
        """Manually craft a price dip that drives RSI below 30 then recovers."""
        prices = [100] * 20 + [90, 85, 80, 78, 76] + [80, 85, 92, 100] + [100] * 40
        dates = pd.date_range("2023-01-01", periods=len(prices), freq="B")
        df = pd.DataFrame({"Close": prices}, index=dates)
        strat = RSIStrategy(period=5, oversold_level=35, overbought_level=65)
        signals = strat.generate_signals(df)
        # At least one buy signal should have been generated during the recovery
        assert (signals == 1).any()
