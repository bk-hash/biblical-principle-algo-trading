"""Tests for the RiskManager."""
import pytest

from src.risk.manager import RiskManager, Position


class TestRiskManager:
    def _make_rm(self, **kwargs) -> RiskManager:
        defaults = dict(
            initial_capital=10_000.0,
            max_risk_per_trade_pct=1.0,
            max_drawdown_pct=10.0,
            max_open_positions=5,
            min_cash_reserve_pct=20.0,
        )
        defaults.update(kwargs)
        return RiskManager(**defaults)

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def test_initial_state(self):
        rm = self._make_rm()
        assert rm.cash == 10_000.0
        assert rm.equity == 10_000.0
        assert rm.peak_equity == 10_000.0
        assert not rm.trading_halted
        assert rm.open_positions == {}

    # ------------------------------------------------------------------
    # Position sizing
    # ------------------------------------------------------------------

    def test_position_size_basic(self):
        rm = self._make_rm()
        # Entry=$100, stop=$98, risk_per_share=$2
        # risk_amount = 1% of 10_000 = 100
        # raw_shares = 100 / 2 = 50
        shares = rm.calculate_position_size(entry_price=100, stop_loss_price=98)
        assert shares > 0

    def test_position_size_zero_when_halted(self):
        rm = self._make_rm()
        rm.trading_halted = True
        shares = rm.calculate_position_size(100, 95)
        assert shares == 0.0

    def test_position_size_zero_when_max_positions(self):
        rm = self._make_rm(max_open_positions=1)
        rm.open_positions["SPY"] = Position("SPY", 100, 10, 95)
        shares = rm.calculate_position_size(100, 95)
        assert shares == 0.0

    def test_position_size_refuses_bad_stop(self):
        rm = self._make_rm()
        shares = rm.calculate_position_size(entry_price=100, stop_loss_price=105)
        assert shares == 0.0

    def test_position_size_respects_cash_reserve(self):
        # With $10k capital, 20% reserve = $2k kept back
        # deployable = $8k
        rm = self._make_rm(initial_capital=10_000, min_cash_reserve_pct=20)
        # Wide stop so risk sizing allows many shares
        shares = rm.calculate_position_size(entry_price=100, stop_loss_price=99)
        max_shares_affordable = (10_000 * 0.80) / 100  # 80 shares
        assert shares <= max_shares_affordable

    # ------------------------------------------------------------------
    # Open / close
    # ------------------------------------------------------------------

    def test_open_and_close_position(self):
        rm = self._make_rm()
        pos = rm.open_position("AAPL", entry_price=100, shares=10, stop_loss_price=95)
        assert pos is not None
        assert rm.cash == pytest.approx(10_000 - 1_000, abs=1)
        assert "AAPL" in rm.open_positions

        pnl = rm.close_position("AAPL", exit_price=110)
        assert pnl == pytest.approx(100.0, abs=0.01)  # (110-100)*10
        assert "AAPL" not in rm.open_positions

    def test_close_nonexistent_position_returns_none(self):
        rm = self._make_rm()
        result = rm.close_position("FAKE", 100)
        assert result is None

    def test_open_position_fails_insufficient_cash(self):
        rm = self._make_rm(initial_capital=1_000, min_cash_reserve_pct=20)
        # try to buy $900 of stock leaving < 20% reserve
        pos = rm.open_position("XYZ", entry_price=100, shares=9, stop_loss_price=90)
        # $900 cost > $800 deployable cash
        assert pos is None

    # ------------------------------------------------------------------
    # Stop-loss
    # ------------------------------------------------------------------

    def test_stop_loss_triggered(self):
        rm = self._make_rm()
        rm.open_position("SPY", entry_price=100, shares=5, stop_loss_price=95)
        triggered = rm.check_stop_losses({"SPY": 94})
        assert "SPY" in triggered

    def test_stop_loss_not_triggered_above(self):
        rm = self._make_rm()
        rm.open_position("SPY", entry_price=100, shares=5, stop_loss_price=95)
        triggered = rm.check_stop_losses({"SPY": 100})
        assert triggered == []

    # ------------------------------------------------------------------
    # Drawdown circuit-breaker
    # ------------------------------------------------------------------

    def test_drawdown_triggers_halt(self):
        rm = self._make_rm(initial_capital=10_000, max_drawdown_pct=10.0)
        # Artificially reduce cash to simulate 11% drawdown
        rm.cash = 8_900.0
        rm.peak_equity = 10_000.0
        halted = rm.check_drawdown()
        assert halted
        assert rm.trading_halted

    def test_drawdown_within_limit_no_halt(self):
        rm = self._make_rm(initial_capital=10_000, max_drawdown_pct=10.0)
        rm.cash = 9_500.0  # 5% drawdown, within limit
        rm.peak_equity = 10_000.0
        halted = rm.check_drawdown()
        assert not halted

    def test_reset_halt(self):
        rm = self._make_rm()
        rm.trading_halted = True
        rm.reset_halt()
        assert not rm.trading_halted

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def test_summary_keys(self):
        rm = self._make_rm()
        s = rm.summary()
        assert "equity" in s
        assert "cash" in s
        assert "drawdown_pct" in s
        assert "open_positions" in s
        assert "trading_halted" in s
