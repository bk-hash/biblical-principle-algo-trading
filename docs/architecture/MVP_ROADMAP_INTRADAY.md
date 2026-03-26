# MVP Roadmap – Intraday Trading Bot (MT5 + Python)

**Date:** 2026-03-26  
**Status:** Active plan  
**Target:** Retail intraday bot; demo-first; tiny live account last  
**Audience:** Bot operator / developer

---

## Overview

| Phase | Duration | Goal |
|---|---|---|
| **Week 1** | Days 1–7 | Environment, MT5 connection, live data feed |
| **Week 2** | Days 8–14 | One rule-based strategy + risk module |
| **Week 3** | Days 15–21 | Paper trading validation + logging/alerts |
| **Week 4** | Days 22–28 | Go/no-go review; tiny live deployment |

> The 4-week timeline is a guide. If any week's acceptance criteria are not met, **do not advance**. There is no deadline that justifies skipping a gate.

---

## Week 1 — Environment Setup and Live Data Feed

### Deliverables

| # | Deliverable | File / location |
|---|---|---|
| 1.1 | Python 3.11+ venv with dependencies installed | `requirements.txt` |
| 1.2 | `MetaTrader5` package connecting to MT5 terminal on Windows/VPS | `bot/data/mt5_client.py` |
| 1.3 | MT5 demo account opened with chosen broker | Broker portal |
| 1.4 | `config/config.yaml` with symbols, timeframes, credentials path | `config/config.yaml` |
| 1.5 | Script that fetches live candles and prints them to the console | `scripts/fetch_candles.py` |
| 1.6 | Script that prints account info (balance, equity, margin) | `scripts/account_info.py` |
| 1.7 | SQLite database schema created and initialised | `bot/storage/schema.sql` |

### Acceptance Criteria

- [ ] `mt5.initialize()` returns `True` without error
- [ ] `mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_M5, 0, 50)` returns 50 rows
- [ ] Account balance, equity, and currency are printed correctly
- [ ] SQLite DB file is created and tables exist
- [ ] All code is committed to the repo and tests pass (`pytest`)

---

## Week 2 — Rule-Based Strategy and Risk Module

### Strategy: Simple EMA Crossover

> **Rule (entry):** When the 9-period EMA crosses above the 21-period EMA on a 5-minute chart, generate a BUY signal. When it crosses below, generate a SELL signal.  
> **Rule (exit):** Fixed stop-loss (1× ATR below/above entry). Take-profit = 1.5× ATR.  
> This is a commonly understood, backtestable rule. It is used here for its simplicity, not because it is guaranteed to be profitable.

### Deliverables

| # | Deliverable | File / location |
|---|---|---|
| 2.1 | `strategy/ema_crossover.py` — pure function: `evaluate(ohlcv: pd.DataFrame) -> Signal` | `bot/strategy/ema_crossover.py` |
| 2.2 | `risk/risk_manager.py` — validates signal, sizes position, applies all hard limits | `bot/risk/risk_manager.py` |
| 2.3 | Unit tests for strategy (deterministic, no MT5 dependency) | `tests/test_strategy.py` |
| 2.4 | Unit tests for risk module (mock account state) | `tests/test_risk.py` |
| 2.5 | `execution/order_executor.py` — `place_order()`, `close_position()` | `bot/execution/order_executor.py` |
| 2.6 | Kill switch file detection (`KILL_SWITCH` file polling) | `bot/risk/kill_switch.py` |

### Acceptance Criteria

- [ ] `evaluate()` returns a deterministic `Signal` for a given OHLCV input (same input = same output, always)
- [ ] `risk_manager.validate()` rejects orders that exceed any hard limit (unit tested)
- [ ] `place_order()` places a market order on the demo account with SL and TP attached
- [ ] Creating a `KILL_SWITCH` file in the bot directory causes the bot loop to exit within 5 seconds
- [ ] All new code has corresponding unit tests; `pytest` passes with zero failures

---

## Week 3 — Paper Trading, Logging, and Alerts

### Deliverables

| # | Deliverable | File / location |
|---|---|---|
| 3.1 | Main bot loop (`bot/main.py`) running continuously on demo account | `bot/main.py` |
| 3.2 | Structured logging to file (JSON lines format) | `bot/monitoring/logger.py` |
| 3.3 | Alert sender (email or Telegram) for WARN and CRITICAL events | `bot/monitoring/alerts.py` |
| 3.4 | Heartbeat: bot writes a timestamp to a file every 60 seconds | `bot/monitoring/heartbeat.py` |
| 3.5 | Reconciliation module: compare local DB vs MT5 positions on startup | `bot/reconciliation/reconciler.py` |
| 3.6 | Daily summary: print/log trade count, P&L, max drawdown for the day | `bot/monitoring/daily_summary.py` |
| 3.7 | Paper trading run: bot runs live on demo for 5 full trading days | Operator observation |

### Acceptance Criteria

- [ ] Bot runs for 5 consecutive trading days on demo without crashing
- [ ] Every order placed is logged with: timestamp, symbol, direction, lots, SL, TP, fill price, slippage
- [ ] At least one alert is received via email or Telegram during testing (trigger manually)
- [ ] Heartbeat file timestamp is never more than 120 seconds old during a live run
- [ ] Reconciliation module detects and logs a manually introduced discrepancy
- [ ] No order is placed without a stop-loss (verified in logs)
- [ ] Daily loss limit is respected: bot halts when limit is breached (tested on demo by forcing a large loss)

### Paper Trading Observation Log (to be completed by operator)

| Day | Trades placed | Signals generated | Fills vs signals | Avg slippage | Notes |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

---

## Week 4 — Go/No-Go Review and Tiny Live Deployment

### Deliverables

| # | Deliverable | Description |
|---|---|---|
| 4.1 | Go/no-go checklist completed and signed off | See checklist below |
| 4.2 | Live account opened with minimum viable deposit | Operator action |
| 4.3 | Bot config updated for live account (`LIVE=true`, reduced lot sizes) | `config/config.yaml` |
| 4.4 | First live day: bot supervised by operator at all times | Operator observation |
| 4.5 | Post-week review: compare live fills vs demo fills | Written comparison |

### Acceptance Criteria

- [ ] All items on the go/no-go checklist are checked
- [ ] First live session runs without incident
- [ ] No position exceeds `MAX_LOTS_PER_TRADE` on the live account
- [ ] Daily loss limit is not breached in week 4
- [ ] Operator can manually halt the bot within 30 seconds at any time

---

## Go/No-Go Checklist (Before Any Live Deployment)

Complete every item. If any item is **NO**, do not deploy. Fix it first.

### Infrastructure

- [ ] MT5 terminal is running on a dedicated Windows VPS with auto-login enabled
- [ ] VPS has at least 2 GB RAM and a stable internet connection (< 1% packet loss)
- [ ] Bot auto-restarts on crash (Windows Task Scheduler or equivalent)
- [ ] VPS auto-reboots into a ready state (MT5 + bot start on Windows login)
- [ ] Operator can access VPS remotely (RDP) from any location

### Broker and Account

- [ ] Broker is confirmed to accept South African residents (verified in T&Cs)
- [ ] FICA/KYC documents submitted and verified
- [ ] At least one successful withdrawal tested on the account
- [ ] Demo account traded for a minimum of 10 days with the same bot
- [ ] Broker's symbol names and contract specs confirmed in `config.yaml`

### Bot Functionality

- [ ] All unit tests pass (`pytest` with zero failures)
- [ ] Kill switch tested: bot halts and closes positions when `KILL_SWITCH` file is created
- [ ] Circuit breaker tested: bot pauses after N consecutive losses (verified on demo)
- [ ] Daily loss limit tested: bot halts when limit is reached (verified on demo)
- [ ] Spread filter tested: bot skips orders when spread is above threshold
- [ ] Reconciliation tested: bot correctly identifies an open position it did not place
- [ ] Alerts verified: at least one alert received via email/Telegram

### Risk and Capital

- [ ] `MAX_DAILY_LOSS_PCT` is set to ≤ 2% of live account balance
- [ ] `MAX_LOTS_PER_TRADE` is set to a size where maximum loss per trade ≤ 1% of account
- [ ] Total capital at risk (live account) is an amount you can afford to lose entirely
- [ ] No borrowed money, no essential funds, no credit are in the trading account

### Operator Readiness

- [ ] Operator has read and understood `RISK_POLICY.md` in full
- [ ] Operator knows how to manually close all positions in MT5 terminal directly (without the bot)
- [ ] Operator has set a personal monthly loss limit above which they will stop the bot
- [ ] Operator has a written incident response plan (see `RISK_POLICY.md` §8)

---

## Milestone Summary

```
Week 1: [ENV] ──► [MT5 connection + data feed] ──► acceptance gate
Week 2: [STRATEGY] ──► [risk module + kill switch] ──► acceptance gate
Week 3: [PAPER TRADING x5 days] ──► [logging + alerts] ──► acceptance gate
Week 4: [GO/NO-GO checklist] ──► [tiny live if all gates passed]
```

---

*See also: [MT5_PYTHON_ARCHITECTURE.md](MT5_PYTHON_ARCHITECTURE.md) · [BROKER_REQUIREMENTS_SA.md](BROKER_REQUIREMENTS_SA.md) · [RISK_POLICY.md](RISK_POLICY.md)*
