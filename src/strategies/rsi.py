"""
Relative Strength Index (RSI) Strategy.

Signal logic:
  • RSI drops **below** *oversold_level* then bounces back above it  → BUY  (+1)
  • RSI rises **above** *overbought_level* then drops back below it → SELL (-1)
  • Otherwise → hold (0)

"The prudent see danger and take refuge, but the simple keep going
 and pay the penalty." — Proverbs 27:12  (don't chase extremes)
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from src.strategies.base import BaseStrategy

logger = logging.getLogger(__name__)


class RSIStrategy(BaseStrategy):
    """RSI-based mean-reversion strategy."""

    def __init__(
        self,
        period: int = 14,
        oversold_level: float = 30.0,
        overbought_level: float = 70.0,
        price_column: str = "Close",
    ) -> None:
        if oversold_level >= overbought_level:
            raise ValueError(
                f"oversold_level ({oversold_level}) must be less than "
                f"overbought_level ({overbought_level})."
            )
        super().__init__(name=f"RSI_{period}")
        self.period = period
        self.oversold_level = oversold_level
        self.overbought_level = overbought_level
        self.price_column = price_column

    # ------------------------------------------------------------------
    # BaseStrategy interface
    # ------------------------------------------------------------------

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Return +1 / -1 / 0 RSI-reversal signals."""
        if self.price_column not in data.columns:
            raise ValueError(
                f"Column '{self.price_column}' not found. "
                f"Available: {list(data.columns)}"
            )

        rsi = self._compute_rsi(data[self.price_column])

        signals = pd.Series(0, index=data.index, dtype=int)

        # Buy when RSI crosses back above the oversold level
        prev_rsi = rsi.shift(1)
        buy_condition = (prev_rsi <= self.oversold_level) & (rsi > self.oversold_level)
        sell_condition = (prev_rsi >= self.overbought_level) & (rsi < self.overbought_level)

        signals[buy_condition] = 1
        signals[sell_condition] = -1

        logger.debug(
            "%s: generated %d buy and %d sell signals",
            self.name,
            (signals == 1).sum(),
            (signals == -1).sum(),
        )
        return signals

    def compute_rsi(self, data: pd.DataFrame) -> pd.Series:
        """Public helper: return the RSI series for *data*."""
        return self._compute_rsi(data[self.price_column])

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_rsi(self, prices: pd.Series) -> pd.Series:
        """Wilder's smoothed RSI computation."""
        delta = prices.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(com=self.period - 1, min_periods=self.period).mean()
        avg_loss = loss.ewm(com=self.period - 1, min_periods=self.period).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi
