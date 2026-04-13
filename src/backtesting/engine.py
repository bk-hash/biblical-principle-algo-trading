"""
Backtesting engine.

Runs a strategy over historical price data and produces a performance
report with equity curve, returns, and key metrics.

"By wisdom a house is built, and through understanding it is established."
— Proverbs 24:3  (know your edge before risking real money)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from src.strategies.base import BaseStrategy
from src.risk.manager import RiskManager

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Configuration for a single backtest run."""

    initial_capital: float = 10_000.0
    commission: float = 1.0          # USD per trade (flat)
    slippage: float = 0.001          # fraction of price
    stop_loss_pct: float = 2.0       # % below entry price
    max_risk_per_trade_pct: float = 1.0
    max_drawdown_pct: float = 10.0
    max_open_positions: int = 5
    min_cash_reserve_pct: float = 20.0
    price_column: str = "Close"


@dataclass
class BacktestResult:
    """Holds the output of a completed backtest."""

    symbol: str
    strategy_name: str
    config: BacktestConfig
    equity_curve: pd.Series                  # equity at each bar
    trades: pd.DataFrame                     # one row per closed trade
    metrics: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.metrics = self._compute_metrics()

    # ------------------------------------------------------------------
    # Metric computation
    # ------------------------------------------------------------------

    def _compute_metrics(self) -> dict:
        eq = self.equity_curve
        if eq.empty:
            return {}

        total_return = (eq.iloc[-1] / eq.iloc[0] - 1) * 100
        daily_returns = eq.pct_change().dropna()

        # Annualised metrics (assume ~252 trading days per year)
        ann_factor = 252
        ann_return = (1 + daily_returns.mean()) ** ann_factor - 1
        ann_vol = daily_returns.std() * (ann_factor ** 0.5)
        sharpe = (ann_return / ann_vol) if ann_vol != 0 else 0.0

        # Max drawdown
        rolling_max = eq.cummax()
        drawdowns = (eq - rolling_max) / rolling_max * 100
        max_drawdown = drawdowns.min()

        # Win rate
        if not self.trades.empty and "pnl" in self.trades.columns:
            wins = (self.trades["pnl"] > 0).sum()
            total_trades = len(self.trades)
            win_rate = wins / total_trades * 100 if total_trades > 0 else 0.0
        else:
            win_rate = 0.0
            total_trades = 0

        return {
            "total_return_pct": round(total_return, 2),
            "annualised_return_pct": round(ann_return * 100, 2),
            "annualised_volatility_pct": round(ann_vol * 100, 2),
            "sharpe_ratio": round(sharpe, 3),
            "max_drawdown_pct": round(max_drawdown, 2),
            "total_trades": total_trades,
            "win_rate_pct": round(win_rate, 2),
            "final_equity": round(eq.iloc[-1], 2),
        }

    def summary(self) -> str:
        """Pretty-print the key metrics."""
        lines = [
            f"=== Backtest: {self.symbol} | {self.strategy_name} ===",
            f"  Total return      : {self.metrics.get('total_return_pct', 0):+.2f}%",
            f"  Annualised return : {self.metrics.get('annualised_return_pct', 0):+.2f}%",
            f"  Sharpe ratio      : {self.metrics.get('sharpe_ratio', 0):.3f}",
            f"  Max drawdown      : {self.metrics.get('max_drawdown_pct', 0):.2f}%",
            f"  Total trades      : {self.metrics.get('total_trades', 0)}",
            f"  Win rate          : {self.metrics.get('win_rate_pct', 0):.1f}%",
            f"  Final equity      : ${self.metrics.get('final_equity', 0):,.2f}",
        ]
        return "\n".join(lines)


class BacktestEngine:
    """
    Event-driven backtesting engine.

    For each bar the engine:
      1. Checks stop-losses on open positions.
      2. Applies commission + slippage to any fill.
      3. Processes new signals from the strategy.
      4. Checks the drawdown circuit-breaker.
      5. Records equity.
    """

    def __init__(self, config: Optional[BacktestConfig] = None) -> None:
        self.config = config or BacktestConfig()

    def run(
        self,
        symbol: str,
        data: pd.DataFrame,
        strategy: BaseStrategy,
    ) -> BacktestResult:
        """
        Execute a backtest for one *symbol* and *strategy*.

        Parameters
        ----------
        symbol:   Ticker symbol (informational only).
        data:     OHLCV DataFrame indexed by date.
        strategy: Concrete strategy instance.

        Returns
        -------
        BacktestResult with equity curve, trade log, and metrics.
        """
        cfg = self.config
        price_col = cfg.price_column

        if price_col not in data.columns:
            raise ValueError(f"Column '{price_col}' not found in data.")

        signals = strategy.generate_signals(data)
        prices = data[price_col]

        risk = RiskManager(
            initial_capital=cfg.initial_capital,
            max_risk_per_trade_pct=cfg.max_risk_per_trade_pct,
            max_drawdown_pct=cfg.max_drawdown_pct,
            max_open_positions=cfg.max_open_positions,
            min_cash_reserve_pct=cfg.min_cash_reserve_pct,
        )

        equity_values: list[float] = []
        trade_records: list[dict] = []

        for date, price in prices.items():
            if np.isnan(price):
                equity_values.append(risk.equity)
                continue

            current_prices = {symbol: price}

            # 1. Check stop-losses
            stopped_symbols = risk.check_stop_losses(current_prices)
            for sym in stopped_symbols:
                fill_price = self._apply_slippage(price, direction=-1)
                pnl = risk.close_position(sym, fill_price)
                if pnl is not None:
                    cost = cfg.commission
                    risk.cash -= cost
                    trade_records.append(
                        {
                            "date": date,
                            "symbol": sym,
                            "action": "stop_loss",
                            "price": fill_price,
                            "pnl": pnl - cost,
                        }
                    )

            # 2. Process new signal
            sig = signals.get(date, 0)
            if sig == 1 and symbol not in risk.open_positions:
                stop = price * (1 - cfg.stop_loss_pct / 100)
                shares = risk.calculate_position_size(price, stop)
                if shares > 0:
                    fill_price = self._apply_slippage(price, direction=1)
                    pos = risk.open_position(symbol, fill_price, shares, stop)
                    if pos:
                        risk.cash -= cfg.commission
                        trade_records.append(
                            {
                                "date": date,
                                "symbol": symbol,
                                "action": "buy",
                                "price": fill_price,
                                "pnl": None,
                            }
                        )

            elif sig == -1 and symbol in risk.open_positions:
                fill_price = self._apply_slippage(price, direction=-1)
                pnl = risk.close_position(symbol, fill_price)
                if pnl is not None:
                    risk.cash -= cfg.commission
                    trade_records.append(
                        {
                            "date": date,
                            "symbol": symbol,
                            "action": "sell",
                            "price": fill_price,
                            "pnl": pnl - cfg.commission,
                        }
                    )

            # 3. Drawdown circuit-breaker
            risk.check_drawdown()

            equity_values.append(risk.equity)

        equity_curve = pd.Series(equity_values, index=prices.index, name="Equity")
        trades_df = pd.DataFrame(trade_records) if trade_records else pd.DataFrame(
            columns=["date", "symbol", "action", "price", "pnl"]
        )

        result = BacktestResult(
            symbol=symbol,
            strategy_name=strategy.name,
            config=cfg,
            equity_curve=equity_curve,
            trades=trades_df,
        )
        logger.info("Backtest complete:\n%s", result.summary())
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _apply_slippage(self, price: float, direction: int) -> float:
        """Add slippage: buys fill slightly higher, sells slightly lower."""
        return price * (1 + direction * self.config.slippage)
