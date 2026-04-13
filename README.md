# Biblical Principle Algo-Trading

> *"Be diligent to know the state of your flocks, and attend to your herds."*  
> — Proverbs 27:23

A **personal algorithmic trading learning project** focused on:

- **Capital preservation** above all else
- **Skills development** through iterative experimentation
- **Strict risk controls** at every layer

---

## Project Vision

This is not a "build a bot and get rich" plan.  The realistic roadmap is:

| Phase | Timeline | Goal |
|-------|----------|------|
| 1–2   | 0–6 months | Learn the basics; no meaningful profit expected |
| 3     | 6–12 months | Paper trading + small live testing; aim for *consistency* |
| 4     | 12+ months | If results are stable, scale slowly; otherwise keep as hobby project |

---

## Features

| Module | Description |
|--------|-------------|
| **Data Fetcher** (`src/data/fetcher.py`) | Downloads OHLCV data via `yfinance` |
| **SMA Crossover** (`src/strategies/moving_average.py`) | Simple Moving Average cross-over strategy |
| **RSI Strategy** (`src/strategies/rsi.py`) | RSI mean-reversion strategy |
| **Risk Manager** (`src/risk/manager.py`) | Position sizing, stop-losses, drawdown circuit-breaker |
| **Backtest Engine** (`src/backtesting/engine.py`) | Historical simulation with equity curve & metrics |
| **Paper Trader** (`src/paper_trading/simulator.py`) | Live simulation mode (no real money) |

### Biblical Principles Applied

| Principle | Implementation |
|-----------|----------------|
| *Stewardship* (Luke 19:12-27) | Max 1% risk per trade; min cash reserve |
| *Diversification* (Ecclesiastes 11:2) | Max 5 open positions; broad-market ETFs by default |
| *Patience* (James 1:4) | Paper trade first; scale only after proven consistency |
| *Wisdom / planning* (Luke 14:28) | Backtesting before live capital |
| *Prudence* (Proverbs 27:12) | Drawdown circuit-breaker halts trading automatically |

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run a backtest

```bash
python scripts/run_backtest.py
```

Optional arguments:

```
--symbol      Ticker symbol (default: SPY)
--start       Start date  YYYY-MM-DD (default: 2020-01-01)
--end         End date    YYYY-MM-DD (default: 2024-12-31)
--strategy    sma | rsi   (default: sma)
--capital     Starting capital USD (default: 10000)
```

Example:

```bash
python scripts/run_backtest.py --symbol QQQ --start 2021-01-01 --end 2023-12-31 --strategy rsi
```

### 3. Run paper trading simulation

```bash
python scripts/run_paper_trading.py
```

Same arguments as `run_backtest.py`.

---

## Project Structure

```
biblical-principle-algo-trading/
├── config/
│   └── config.yaml              # All tuneable parameters
├── src/
│   ├── config_loader.py         # YAML config loader
│   ├── data/
│   │   └── fetcher.py           # Market data download (yfinance)
│   ├── strategies/
│   │   ├── base.py              # Abstract base class
│   │   ├── moving_average.py    # SMA Crossover strategy
│   │   └── rsi.py               # RSI mean-reversion strategy
│   ├── risk/
│   │   └── manager.py           # Position sizing, stop-loss, drawdown halt
│   ├── backtesting/
│   │   └── engine.py            # Historical simulation + metrics
│   └── paper_trading/
│       └── simulator.py         # Paper trading simulator
├── tests/
│   ├── conftest.py              # Shared fixtures
│   ├── test_strategies.py
│   ├── test_risk_manager.py
│   ├── test_backtesting.py
│   ├── test_paper_trading.py
│   └── test_config.py
├── scripts/
│   ├── run_backtest.py
│   └── run_paper_trading.py
├── requirements.txt
└── README.md
```

---

## Configuration

All parameters live in `config/config.yaml`:

```yaml
trading:
  initial_capital: 10000.0
  max_risk_per_trade_pct: 1.0   # Never risk more than 1% per trade
  max_drawdown_pct: 10.0        # Halt trading if equity drops 10% from peak
  max_open_positions: 5
  min_cash_reserve_pct: 20.0    # Keep 20% cash uninvested at all times
```

---

## Risk Management Philosophy

Three layers of capital protection:

1. **Position Sizing** — Each trade risks at most `max_risk_per_trade_pct`% of current equity. Shares = `(equity × risk%) / (entry_price − stop_price)`.

2. **Stop-Loss** — Every position gets a hard stop-loss `stop_loss_pct`% below entry.  If price hits the stop, the position is closed automatically.

3. **Drawdown Circuit-Breaker** — If total equity drops more than `max_drawdown_pct`% from its all-time high, **all trading is halted** until manually reviewed and resumed.

> *"The prudent see danger and take refuge, but the simple keep going and pay the penalty."*  
> — Proverbs 27:12

---

## Running Tests

```bash
pytest tests/ -v
```

With coverage:

```bash
pytest tests/ --cov=src --cov-report=term-missing
```

---

## Learning Path

**Phase 1–2 (0–6 months)** — Learn the codebase:
- Read `src/strategies/base.py` and understand the signal interface.
- Run backtests on different symbols and time periods.
- Study the risk manager's position-sizing math.

**Phase 3 (6–12 months)** — Paper trade:
- Run `run_paper_trading.py` daily against live data.
- Keep a trading journal; note wins, losses, and lessons.
- Only proceed to live trading after ≥3 months of consistent results.

**Phase 4 (12+ months)** — Live trading (if Phase 3 is successful):
- Start with the **smallest possible position size**.
- Never deploy more capital than you can afford to lose entirely.
- Review drawdown and win-rate weekly.

---

## Disclaimer

This project is for **educational purposes only**.  It is not financial
advice.  Past performance of any backtest does not guarantee future
results.  Always do your own research and consult a qualified financial
adviser before trading real money.
