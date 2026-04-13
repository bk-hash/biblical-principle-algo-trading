"""Tests for the PaperTrader simulator."""
import pytest
import pandas as pd

from src.paper_trading.simulator import PaperTrader
from src.strategies.moving_average import MovingAverageCrossover
from src.strategies.rsi import RSIStrategy
from tests.conftest import make_price_df


@pytest.fixture
def trader(price_df):
    strat = MovingAverageCrossover(short_window=10, long_window=30)
    t = PaperTrader(
        symbol="SPY",
        strategy=strat,
        initial_capital=10_000,
        commission=1.0,
        slippage=0.001,
        stop_loss_pct=2.0,
        max_risk_per_trade_pct=1.0,
        max_drawdown_pct=15.0,
        min_cash_reserve_pct=20.0,
    )
    t.load_data(price_df)
    return t


class TestPaperTrader:
    def test_run_completes(self, trader):
        trader.run()

    def test_equity_curve_length_after_run(self, trader, price_df):
        trader.run()
        eq = trader.equity_curve()
        assert len(eq) == len(price_df)

    def test_initial_equity_near_capital(self, trader):
        trader.run()
        eq = trader.equity_curve()
        assert eq.iloc[0] == pytest.approx(10_000, rel=0.01)

    def test_trade_log_structure(self, trader):
        trader.run()
        log = trader.trade_log()
        if not log.empty:
            for col in ["date", "symbol", "action", "price"]:
                assert col in log.columns

    def test_report_contains_key_strings(self, trader):
        trader.run()
        report = trader.report()
        assert "SPY" in report
        assert "Initial capital" in report
        assert "Final equity" in report

    def test_load_data_requires_close_column(self, price_df):
        strat = MovingAverageCrossover(10, 30)
        t = PaperTrader("SPY", strat)
        with pytest.raises(ValueError):
            t.load_data(price_df.drop(columns=["Close"]))

    def test_run_without_load_raises(self):
        strat = MovingAverageCrossover(10, 30)
        t = PaperTrader("SPY", strat)
        with pytest.raises(RuntimeError):
            t.run()

    def test_tick_mode(self, price_df):
        """Tick-by-tick mode should produce the same equity as batch run."""
        strat = MovingAverageCrossover(10, 30)
        t = PaperTrader("SPY", strat, initial_capital=10_000)
        t.load_data(price_df)
        for date, row in price_df.iterrows():
            t.tick(date, row)
        eq = t.equity_curve()
        assert len(eq) == len(price_df)

    def test_rsi_strategy_paper_trade(self, price_df):
        strat = RSIStrategy(period=14)
        t = PaperTrader("AAPL", strat, initial_capital=10_000)
        t.load_data(price_df)
        t.run()
        eq = t.equity_curve()
        assert len(eq) == len(price_df)
