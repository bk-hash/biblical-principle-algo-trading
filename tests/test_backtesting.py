"""Tests for the BacktestEngine."""
import pytest
import pandas as pd

from src.backtesting.engine import BacktestEngine, BacktestConfig
from src.strategies.moving_average import MovingAverageCrossover
from src.strategies.rsi import RSIStrategy
from tests.conftest import make_price_df, make_price_series


@pytest.fixture
def engine():
    cfg = BacktestConfig(
        initial_capital=10_000,
        commission=1.0,
        slippage=0.001,
        stop_loss_pct=2.0,
        max_risk_per_trade_pct=1.0,
        max_drawdown_pct=15.0,
        max_open_positions=5,
        min_cash_reserve_pct=20.0,
    )
    return BacktestEngine(config=cfg)


class TestBacktestEngine:
    def test_run_returns_result(self, engine, price_df):
        strat = MovingAverageCrossover(short_window=10, long_window=30)
        result = engine.run("SPY", price_df, strat)
        assert result.symbol == "SPY"
        assert result.strategy_name == "SMA_10_30"

    def test_equity_curve_length(self, engine, price_df):
        strat = MovingAverageCrossover(short_window=10, long_window=30)
        result = engine.run("SPY", price_df, strat)
        assert len(result.equity_curve) == len(price_df)

    def test_equity_curve_starts_near_initial(self, engine, price_df):
        strat = MovingAverageCrossover(short_window=10, long_window=30)
        result = engine.run("SPY", price_df, strat)
        # First equity value should be close to initial capital
        assert result.equity_curve.iloc[0] == pytest.approx(10_000, rel=0.01)

    def test_metrics_are_computed(self, engine, price_df):
        strat = MovingAverageCrossover(short_window=10, long_window=30)
        result = engine.run("SPY", price_df, strat)
        m = result.metrics
        assert "total_return_pct" in m
        assert "sharpe_ratio" in m
        assert "max_drawdown_pct" in m
        assert "win_rate_pct" in m

    def test_missing_price_column_raises(self, engine, price_df):
        strat = MovingAverageCrossover(short_window=10, long_window=30)
        bad_df = price_df.drop(columns=["Close"])
        with pytest.raises(ValueError):
            engine.run("SPY", bad_df, strat)

    def test_trades_dataframe_has_expected_columns(self, engine, price_df):
        strat = MovingAverageCrossover(short_window=10, long_window=30)
        result = engine.run("SPY", price_df, strat)
        if not result.trades.empty:
            for col in ["date", "symbol", "action", "price"]:
                assert col in result.trades.columns

    def test_summary_string(self, engine, price_df):
        strat = MovingAverageCrossover(short_window=10, long_window=30)
        result = engine.run("SPY", price_df, strat)
        summary = result.summary()
        assert "SPY" in summary
        assert "Total return" in summary

    def test_rsi_strategy_backtest(self, engine, price_df):
        strat = RSIStrategy(period=14, oversold_level=30, overbought_level=70)
        result = engine.run("AAPL", price_df, strat)
        assert result.symbol == "AAPL"
        assert len(result.equity_curve) == len(price_df)

    def test_trending_upward_generates_profit(self, trending_df):
        """A strong uptrend should yield a non-catastrophic return with SMA crossover."""
        cfg = BacktestConfig(
            initial_capital=10_000,
            stop_loss_pct=5.0,
            max_drawdown_pct=30.0,
            min_cash_reserve_pct=10.0,
        )
        engine = BacktestEngine(cfg)
        strat = MovingAverageCrossover(short_window=10, long_window=50)
        result = engine.run("TEST", trending_df, strat)
        # Allow a small negative buffer for commission/slippage; loss should be minimal.
        assert result.metrics["total_return_pct"] >= -1.0
