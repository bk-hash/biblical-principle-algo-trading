#!/usr/bin/env python
"""
Paper trading runner script.

Replays recent historical data through a strategy in simulation mode —
no real money at risk.

Usage:
    python scripts/run_paper_trading.py
    python scripts/run_paper_trading.py --symbol AAPL --strategy rsi
"""
from __future__ import annotations

import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config_loader import load_config
from src.data.fetcher import DataFetcher
from src.strategies.moving_average import MovingAverageCrossover
from src.strategies.rsi import RSIStrategy
from src.paper_trading.simulator import PaperTrader


def parse_args() -> argparse.Namespace:
    cfg = load_config()
    t = cfg["trading"]
    d = cfg["data"]
    ma = cfg["strategies"]["moving_average_crossover"]
    rsi_cfg = cfg["strategies"]["rsi"]

    parser = argparse.ArgumentParser(description="Paper trading runner")
    parser.add_argument("--symbol", default=d["default_symbols"][0])
    parser.add_argument("--start", default="2023-01-01")
    parser.add_argument("--end", default="2024-12-31")
    parser.add_argument("--strategy", choices=["sma", "rsi"], default="sma")
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

    print(f"\nFetching data for {args.symbol} ({args.start} → {args.end}) ...")
    fetcher = DataFetcher()
    data = fetcher.fetch(args.symbol, args.start, args.end)

    if args.strategy == "sma":
        strategy = MovingAverageCrossover(
            short_window=args.short_window,
            long_window=args.long_window,
        )
    else:
        strategy = RSIStrategy(period=args.rsi_period)

    trader = PaperTrader(
        symbol=args.symbol,
        strategy=strategy,
        initial_capital=args.capital,
        max_risk_per_trade_pct=args.max_risk_pct,
        max_drawdown_pct=args.max_drawdown_pct,
    )
    trader.load_data(data)

    print(f"Running paper trade simulation: {strategy.name} on {args.symbol}")
    trader.run()

    print("\n" + trader.report())

    trade_log = trader.trade_log()
    if not trade_log.empty:
        print(f"\nSample trades (last 5):\n{trade_log.tail(5).to_string(index=False)}")
    else:
        print("\nNo trades were executed during this period.")


if __name__ == "__main__":
    main()
