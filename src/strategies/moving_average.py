"""
Simple Moving Average (SMA) Crossover Strategy.

Signal logic:
  • When the short SMA crosses **above** the long SMA → BUY signal (+1)
  • When the short SMA crosses **below** the long SMA → SELL signal (-1)
  • Otherwise → hold current position (0)

"Suppose one of you wants to build a tower.  Won't you first sit down
 and estimate the cost to see if you have enough money to complete it?"
— Luke 14:28  (plan before you act)
"""
from __future__ import annotations

import logging

import pandas as pd

from src.strategies.base import BaseStrategy

logger = logging.getLogger(__name__)


class MovingAverageCrossover(BaseStrategy):
    """SMA crossover strategy parameterised by *short_window* and *long_window*."""

    def __init__(
        self,
        short_window: int = 20,
        long_window: int = 50,
        price_column: str = "Close",
    ) -> None:
        if short_window >= long_window:
            raise ValueError(
                f"short_window ({short_window}) must be less than "
                f"long_window ({long_window})."
            )
        super().__init__(
            name=f"SMA_{short_window}_{long_window}"
        )
        self.short_window = short_window
        self.long_window = long_window
        self.price_column = price_column

    # ------------------------------------------------------------------
    # BaseStrategy interface
    # ------------------------------------------------------------------

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Return +1 / -1 / 0 crossover signals."""
        if self.price_column not in data.columns:
            raise ValueError(
                f"Column '{self.price_column}' not found in data. "
                f"Available: {list(data.columns)}"
            )

        prices = data[self.price_column]
        short_ma = prices.rolling(window=self.short_window, min_periods=self.short_window).mean()
        long_ma = prices.rolling(window=self.long_window, min_periods=self.long_window).mean()

        # Raw position: 1 where short > long, 0 otherwise
        position = (short_ma > long_ma).astype(int)

        # Differentiate to find crossover events: +1 cross up, -1 cross down
        signals = position.diff().fillna(0).astype(int)

        logger.debug(
            "%s: generated %d buy and %d sell signals",
            self.name,
            (signals == 1).sum(),
            (signals == -1).sum(),
        )
        return signals

    # ------------------------------------------------------------------
    # Extra helpers (useful for analysis / plotting)
    # ------------------------------------------------------------------

    def compute_moving_averages(self, data: pd.DataFrame) -> pd.DataFrame:
        """Return a DataFrame with the price, short MA, and long MA columns."""
        prices = data[self.price_column]
        result = pd.DataFrame(index=data.index)
        result["Price"] = prices
        result[f"SMA_{self.short_window}"] = prices.rolling(
            window=self.short_window, min_periods=self.short_window
        ).mean()
        result[f"SMA_{self.long_window}"] = prices.rolling(
            window=self.long_window, min_periods=self.long_window
        ).mean()
        return result
