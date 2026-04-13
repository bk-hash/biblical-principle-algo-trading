"""
Market data fetching using yfinance.

"The plans of the diligent lead to profit as surely as haste leads to poverty."
— Proverbs 21:5
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class DataFetcher:
    """Downloads and caches OHLCV price data for one or more symbols."""

    def __init__(self, price_column: str = "Close") -> None:
        self.price_column = price_column

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch(
        self,
        symbol: str,
        start: str,
        end: str,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data for *symbol* between *start* and *end*.

        Parameters
        ----------
        symbol:   Ticker symbol (e.g. "SPY")
        start:    ISO date string "YYYY-MM-DD"
        end:      ISO date string "YYYY-MM-DD"
        interval: yfinance interval string (default "1d")

        Returns
        -------
        DataFrame with DatetimeIndex and at minimum a ``Close`` column.
        Raises ``ValueError`` if no data is returned.
        """
        logger.info("Fetching %s  %s → %s  [%s]", symbol, start, end, interval)
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start, end=end, interval=interval)

        if df.empty:
            raise ValueError(
                f"No data returned for {symbol} between {start} and {end}. "
                "Check the symbol and date range."
            )

        # Normalise column names (yfinance uses capitalised names)
        df.columns = [c.strip() for c in df.columns]
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df.index.name = "Date"
        logger.info("Fetched %d rows for %s", len(df), symbol)
        return df

    def fetch_multiple(
        self,
        symbols: List[str],
        start: str,
        end: str,
        interval: str = "1d",
    ) -> dict[str, pd.DataFrame]:
        """
        Fetch OHLCV data for multiple symbols.

        Returns a dict mapping symbol → DataFrame.
        Symbols that fail are logged and omitted.
        """
        result: dict[str, pd.DataFrame] = {}
        for sym in symbols:
            try:
                result[sym] = self.fetch(sym, start, end, interval)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skipping %s — %s", sym, exc)
        return result

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Return the most recent closing price for *symbol* (or None on error)."""
        try:
            end = datetime.today().strftime("%Y-%m-%d")
            start = (datetime.today() - timedelta(days=7)).strftime("%Y-%m-%d")
            df = self.fetch(symbol, start, end)
            return float(df[self.price_column].iloc[-1])
        except Exception as exc:  # noqa: BLE001
            logger.error("Could not get latest price for %s: %s", symbol, exc)
            return None
