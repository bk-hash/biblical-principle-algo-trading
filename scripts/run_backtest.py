#!/usr/bin/env python
"""
Backtest runner script.

Runs the SMA Crossover strategy over SPY historical data and
prints a performance summary.

Usage:
    python scripts/run_backtest.py
    python scripts/run_backtest.py --symbol QQQ --start 2021-01-01 --end 2023-12-31
"""
from __future__ import annotations

import argparse
import logging
import os
import sys

# Make sure the project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config_loader import load_config
from src.data.fetcher import DataFetcher
from src.strategies.moving_average import MovingAverageCrossover
from src.strategies.rsi import RSIStrategy
from src.backtesting.engine import BacktestEngine, BacktestConfig


def parse_args() -> argparse.Namespace:
    cfg = load_config()
    t = cfg["trading"]
    d = cfg["data"]
    ma = cfg["strategies"]["moving_average_crossover"]
    rsi_cfg = cfg["strategies"]["rsi"]

    parser = argparse.ArgumentParser(description="Backtest runner")
    parser.add_argument("--symbol", default=d["default_symbols"][0], help="Ticker symbol")
    parser.add_argument("--start", default=d["default_start_date"], help="Start date YYYY-MM-DD")
    parser.add_argument("--end", default=d["default_end_date"], help="End date YYYY-MM-DD")
    parser.add_argument(
        "--strategy",
        choices=["sma", "rsi"],
        default="sma",
        help="Strategy to backtest",
    )
    parser.add_argument("--short-window", type=int, default=ma["short_window"])
    parser.add_argument("--long-window", type=int, default=ma["long_window"])
    parser.add_argument("--rsi-period", type=int, default=rsi_cfg["period"])
    parser.add_argument("--capital", type=float, default=t["initial_capital"])
    parser.add_argument("--max-risk-pct", type=float, default=t["max_risk_per_trade_pct"])
    parser.add_argument("--max-drawdown-pct", type=float, default=t["max_drawdown_pct"])
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    args = parse_args()

    print(f"\nFetching data for {args.symbol} ({args.start} → {args.end})...")
    fetcher = DataFetcher()
    data = fetcher.fetch(args.symbol, args.start, args.end)

    if args.strategy == "sma":
        strategy = MovingAverageCrossover(
            short_window=args.short_window,
            long_window=args.long_window,
        )
    else:
        strategy = RSIStrategy(period=args.rsi_period)

    cfg = BacktestConfig(
        initial_capital=args.capital,
        max_risk_per_trade_pct=args.max_risk_pct,
        max_drawdown_pct=args.max_drawdown_pct,
    )
    engine = BacktestEngine(config=cfg)

    print(f"Running backtest: strategy={strategy.name}  symbol={args.symbol}")
    result = engine.run(args.symbol, data, strategy)

    print("\n" + result.summary())

    if not result.trades.empty:
        print(f"\nSample trades (last 5):\n{result.trades.tail(5).to_string(index=False)}")


if __name__ == "__main__":
    main()
