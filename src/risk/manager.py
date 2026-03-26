"""
Risk management module.

Implements the three core guardrails that protect capital:
  1. **Position sizing** — never risk more than N% per trade.
  2. **Stop-loss** — hard-coded exit when price moves against you.
  3. **Drawdown circuit-breaker** — halt all trading if equity drops
     more than *max_drawdown_pct* from its all-time high.

"A wise man has great power, and a man of knowledge increases strength;
 for waging war you need guidance, and for victory many advisers."
— Proverbs 24:5-6
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents an open trade."""

    symbol: str
    entry_price: float
    shares: float
    stop_loss_price: float
    direction: int = 1  # +1 long, -1 short (short not supported yet)

    @property
    def current_value(self) -> float:
        return self.shares * self.entry_price

    def unrealised_pnl(self, current_price: float) -> float:
        return (current_price - self.entry_price) * self.shares * self.direction


@dataclass
class RiskManager:
    """
    Enforces position-sizing rules and drawdown limits.

    Parameters
    ----------
    initial_capital:      Starting equity (USD).
    max_risk_per_trade_pct: Maximum fraction of equity to risk per trade
                            (expressed as a percentage, e.g. 1.0 = 1%).
    max_drawdown_pct:     Maximum peak-to-trough drawdown before all
                          trading is suspended (e.g. 10.0 = 10%).
    max_open_positions:   Hard cap on simultaneous open positions.
    min_cash_reserve_pct: Minimum cash to keep uninvested (pct of
                          initial capital, e.g. 20.0 = 20%).
    """

    initial_capital: float
    max_risk_per_trade_pct: float = 1.0
    max_drawdown_pct: float = 10.0
    max_open_positions: int = 5
    min_cash_reserve_pct: float = 20.0

    # Runtime state — not constructor arguments
    cash: float = field(init=False)
    peak_equity: float = field(init=False)
    open_positions: dict[str, Position] = field(default_factory=dict, init=False)
    trading_halted: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.cash = self.initial_capital
        self.peak_equity = self.initial_capital

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def equity(self) -> float:
        """Total equity = cash + market value of open positions (at cost)."""
        position_value = sum(p.current_value for p in self.open_positions.values())
        return self.cash + position_value

    @property
    def current_drawdown_pct(self) -> float:
        """Current drawdown from peak equity as a positive percentage."""
        if self.peak_equity <= 0:
            return 0.0
        return (self.peak_equity - self.equity) / self.peak_equity * 100.0

    @property
    def min_cash_reserve(self) -> float:
        return self.initial_capital * self.min_cash_reserve_pct / 100.0

    # ------------------------------------------------------------------
    # Core decisions
    # ------------------------------------------------------------------

    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss_price: float,
    ) -> float:
        """
        Return the number of shares to buy based on the 1% risk rule.

        Risk per trade = max_risk_per_trade_pct % of current equity.
        Shares = risk_amount / (entry_price - stop_loss_price)

        Returns 0 if the trade cannot be taken (drawdown halt, max
        positions reached, insufficient cash, or negative risk).
        """
        if self.trading_halted:
            logger.warning("Position sizing refused — trading halted (drawdown limit).")
            return 0.0

        if len(self.open_positions) >= self.max_open_positions:
            logger.warning(
                "Position sizing refused — max open positions (%d) reached.",
                self.max_open_positions,
            )
            return 0.0

        risk_per_share = entry_price - stop_loss_price
        if risk_per_share <= 0:
            logger.warning(
                "Invalid stop-loss: entry=%.4f stop=%.4f. Refusing trade.",
                entry_price,
                stop_loss_price,
            )
            return 0.0

        risk_amount = self.equity * self.max_risk_per_trade_pct / 100.0
        raw_shares = risk_amount / risk_per_share

        # Cap by available deployable cash
        deployable_cash = max(self.cash - self.min_cash_reserve, 0.0)
        max_affordable_shares = deployable_cash / entry_price
        shares = min(raw_shares, max_affordable_shares)

        logger.debug(
            "Position size: risk_amount=%.2f risk_per_share=%.4f "
            "raw_shares=%.2f capped_shares=%.2f",
            risk_amount,
            risk_per_share,
            raw_shares,
            shares,
        )
        return shares

    def open_position(
        self,
        symbol: str,
        entry_price: float,
        shares: float,
        stop_loss_price: float,
    ) -> Optional[Position]:
        """
        Record a new open position and deduct cash.

        Returns the Position object, or None if the position could not
        be opened.
        """
        if shares <= 0:
            return None

        cost = shares * entry_price
        if cost > self.cash - self.min_cash_reserve:
            logger.warning(
                "Cannot open position for %s — insufficient cash (%.2f needed, %.2f available).",
                symbol,
                cost,
                self.cash - self.min_cash_reserve,
            )
            return None

        pos = Position(
            symbol=symbol,
            entry_price=entry_price,
            shares=shares,
            stop_loss_price=stop_loss_price,
        )
        self.open_positions[symbol] = pos
        self.cash -= cost
        logger.info(
            "Opened position: %s  %.2f shares @ %.4f  stop=%.4f",
            symbol,
            shares,
            entry_price,
            stop_loss_price,
        )
        return pos

    def close_position(self, symbol: str, exit_price: float) -> Optional[float]:
        """
        Close an open position and return realised PnL (or None if not found).
        """
        pos = self.open_positions.pop(symbol, None)
        if pos is None:
            logger.warning("close_position: no open position for %s", symbol)
            return None

        proceeds = pos.shares * exit_price
        pnl = (exit_price - pos.entry_price) * pos.shares * pos.direction
        self.cash += proceeds
        self._update_peak_equity()
        logger.info(
            "Closed position: %s  %.2f shares @ %.4f  PnL=%.2f",
            symbol,
            pos.shares,
            exit_price,
            pnl,
        )
        return pnl

    def check_stop_losses(self, current_prices: dict[str, float]) -> list[str]:
        """
        Evaluate stop-loss levels for all open positions.

        Returns a list of symbols whose stop-loss has been breached.
        Call ``close_position`` for each symbol returned.
        """
        triggered: list[str] = []
        for symbol, pos in list(self.open_positions.items()):
            price = current_prices.get(symbol)
            if price is None:
                continue
            if price <= pos.stop_loss_price:
                logger.warning(
                    "Stop-loss triggered for %s: current=%.4f stop=%.4f",
                    symbol,
                    price,
                    pos.stop_loss_price,
                )
                triggered.append(symbol)
        return triggered

    def check_drawdown(self) -> bool:
        """
        Check the current drawdown against the circuit-breaker threshold.

        Sets ``self.trading_halted = True`` if the limit is breached and
        returns True to indicate trading should stop.
        """
        self._update_peak_equity()
        dd = self.current_drawdown_pct
        if dd >= self.max_drawdown_pct:
            if not self.trading_halted:
                logger.critical(
                    "DRAWDOWN CIRCUIT-BREAKER TRIGGERED: %.2f%% drawdown "
                    "(limit=%.2f%%). All trading halted.",
                    dd,
                    self.max_drawdown_pct,
                )
            self.trading_halted = True
        return self.trading_halted

    def reset_halt(self) -> None:
        """Manually re-enable trading after review (use with caution)."""
        logger.warning("Trading halt manually reset. Review your strategy before resuming.")
        self.trading_halted = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _update_peak_equity(self) -> None:
        eq = self.equity
        if eq > self.peak_equity:
            self.peak_equity = eq

    def summary(self) -> dict:
        """Return a snapshot of current risk metrics."""
        return {
            "equity": round(self.equity, 2),
            "cash": round(self.cash, 2),
            "peak_equity": round(self.peak_equity, 2),
            "drawdown_pct": round(self.current_drawdown_pct, 2),
            "open_positions": len(self.open_positions),
            "trading_halted": self.trading_halted,
        }
