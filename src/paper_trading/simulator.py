"""
Paper trading simulator.

Replays live market data (or a streaming feed) and executes trades in
simulation — no real money at risk.  This is Phase 3 of the project
roadmap: build confidence in a strategy before committing real capital.

"Test everything; hold fast what is good." — 1 Thessalonians 5:21
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import pandas as pd

from src.strategies.base import BaseStrategy
from src.risk.manager import RiskManager

logger = logging.getLogger(__name__)


class PaperTrader:
    """
    Simulates live trading against a pre-loaded price series.

    Usage
    -----
    ::

        trader = PaperTrader(
            symbol="SPY",
            strategy=MovingAverageCrossover(20, 50),
            initial_capital=10_000,
        )
        trader.load_data(price_df)
        trader.run()
        print(trader.report())

    The simulator processes each bar sequentially so that forward-looking
    bias is impossible — the strategy only sees data up to the current bar.
    """

    def __init__(
        self,
        symbol: str,
        strategy: BaseStrategy,
        initial_capital: float = 10_000.0,
        commission: float = 1.0,
        slippage: float = 0.001,
        stop_loss_pct: float = 2.0,
        max_risk_per_trade_pct: float = 1.0,
        max_drawdown_pct: float = 10.0,
        max_open_positions: int = 5,
        min_cash_reserve_pct: float = 20.0,
        price_column: str = "Close",
    ) -> None:
        self.symbol = symbol
        self.strategy = strategy
        self.commission = commission
        self.slippage = slippage
        self.stop_loss_pct = stop_loss_pct
        self.price_column = price_column

        self.risk = RiskManager(
            initial_capital=initial_capital,
            max_risk_per_trade_pct=max_risk_per_trade_pct,
            max_drawdown_pct=max_drawdown_pct,
            max_open_positions=max_open_positions,
            min_cash_reserve_pct=min_cash_reserve_pct,
        )

        self._data: Optional[pd.DataFrame] = None
        self._signals: Optional[pd.Series] = None
        self._trade_log: list[dict] = []
        self._equity_log: list[dict] = []
        self._bar_index: int = 0

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def load_data(self, data: pd.DataFrame) -> None:
        """
        Load historical price data and pre-compute strategy signals.

        In a live deployment you would call ``tick()`` as new bars arrive
        instead of using this method.
        """
        if self.price_column not in data.columns:
            raise ValueError(
                f"Column '{self.price_column}' not found. "
                f"Available: {list(data.columns)}"
            )
        self._data = data.copy()
        self._signals = self.strategy.generate_signals(data)
        self._bar_index = 0
        logger.info(
            "PaperTrader loaded %d bars for %s (strategy: %s)",
            len(data),
            self.symbol,
            self.strategy.name,
        )

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Process all loaded bars sequentially."""
        if self._data is None or self._signals is None:
            raise RuntimeError("Call load_data() before run().")

        for date, row in self._data.iterrows():
            self._process_bar(date, row)

        logger.info("Paper trading simulation complete. %d trades executed.", len(self._trade_log))

    def tick(self, date: datetime, row: pd.Series) -> None:
        """Process a single bar (use in live / streaming mode)."""
        self._process_bar(date, row)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def equity_curve(self) -> pd.Series:
        """Return the equity series indexed by date."""
        if not self._equity_log:
            return pd.Series(dtype=float)
        df = pd.DataFrame(self._equity_log).set_index("date")
        return df["equity"]

    def trade_log(self) -> pd.DataFrame:
        """Return a DataFrame of all executed paper trades."""
        if not self._trade_log:
            return pd.DataFrame(columns=["date", "symbol", "action", "price", "shares", "pnl"])
        return pd.DataFrame(self._trade_log)

    def report(self) -> str:
        """Return a human-readable performance summary."""
        eq = self.equity_curve()
        if eq.empty:
            return "No data to report."

        initial = eq.iloc[0]
        final = eq.iloc[-1]
        total_return = (final / initial - 1) * 100

        trades = self.trade_log()
        total_trades = len(trades)
        wins = (trades["pnl"] > 0).sum() if not trades.empty and "pnl" in trades.columns else 0
        win_rate = wins / total_trades * 100 if total_trades > 0 else 0.0

        risk_summary = self.risk.summary()
        lines = [
            f"=== Paper Trading Report: {self.symbol} | {self.strategy.name} ===",
            f"  Initial capital   : ${initial:,.2f}",
            f"  Final equity      : ${final:,.2f}",
            f"  Total return      : {total_return:+.2f}%",
            f"  Total trades      : {total_trades}",
            f"  Win rate          : {win_rate:.1f}%",
            f"  Drawdown (current): {risk_summary['drawdown_pct']:.2f}%",
            f"  Trading halted    : {risk_summary['trading_halted']}",
        ]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _process_bar(self, date, row: pd.Series) -> None:
        price = row.get(self.price_column)
        if price is None or (isinstance(price, float) and price != price):  # NaN guard
            self._equity_log.append({"date": date, "equity": self.risk.equity})
            return

        current_prices = {self.symbol: price}

        # Stop-loss check
        triggered = self.risk.check_stop_losses(current_prices)
        for sym in triggered:
            fill = self._fill_price(price, -1)
            pnl = self.risk.close_position(sym, fill)
            if pnl is not None:
                self.risk.cash -= self.commission
                self._trade_log.append(
                    {
                        "date": date,
                        "symbol": sym,
                        "action": "stop_loss",
                        "price": fill,
                        "shares": None,
                        "pnl": pnl - self.commission,
                    }
                )

        # Signal processing
        sig = 0 if self._signals is None else self._signals.get(date, 0)

        if sig == 1 and self.symbol not in self.risk.open_positions:
            if not self.risk.check_drawdown():
                stop = price * (1 - self.stop_loss_pct / 100)
                shares = self.risk.calculate_position_size(price, stop)
                if shares > 0:
                    fill = self._fill_price(price, 1)
                    pos = self.risk.open_position(self.symbol, fill, shares, stop)
                    if pos:
                        self.risk.cash -= self.commission
                        self._trade_log.append(
                            {
                                "date": date,
                                "symbol": self.symbol,
                                "action": "buy",
                                "price": fill,
                                "shares": shares,
                                "pnl": None,
                            }
                        )
                        logger.info("PAPER BUY  %s  %.2f shares @ %.4f", self.symbol, shares, fill)

        elif sig == -1 and self.symbol in self.risk.open_positions:
            fill = self._fill_price(price, -1)
            pnl = self.risk.close_position(self.symbol, fill)
            if pnl is not None:
                self.risk.cash -= self.commission
                self._trade_log.append(
                    {
                        "date": date,
                        "symbol": self.symbol,
                        "action": "sell",
                        "price": fill,
                        "shares": None,
                        "pnl": pnl - self.commission,
                    }
                )
                logger.info("PAPER SELL %s @ %.4f  PnL=%.2f", self.symbol, fill, pnl)

        # Drawdown check
        self.risk.check_drawdown()

        self._equity_log.append({"date": date, "equity": self.risk.equity})
        self._bar_index += 1

    def _fill_price(self, price: float, direction: int) -> float:
        """Apply slippage to the fill price."""
        return price * (1 + direction * self.slippage)
