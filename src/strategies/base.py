"""
Base strategy class that all concrete strategies must extend.

Every strategy receives a price DataFrame and must return a Series of
signals: +1 (buy), -1 (sell), 0 (hold/flat).
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class BaseStrategy(ABC):
    """Abstract base class for trading strategies."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Compute entry/exit signals from price data.

        Parameters
        ----------
        data : pd.DataFrame
            OHLCV DataFrame with a DatetimeIndex and at minimum a ``Close``
            column.

        Returns
        -------
        pd.Series
            Integer signal series aligned to *data*'s index:
            +1 = enter/hold long, -1 = exit/short, 0 = flat/no change.
        """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
