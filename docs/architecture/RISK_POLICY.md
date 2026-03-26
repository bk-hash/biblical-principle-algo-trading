# Risk Policy – Personal Intraday Trading Bot

**Date:** 2026-03-26  
**Version:** 1.0  
**Status:** Enforced  
**Audience:** Bot operator; must be read before any live deployment

---

## 1. Purpose and Scope

This policy defines enforceable risk limits for a personal intraday algorithmic trading bot running on MetaTrader 5 (MT5) via the Python `MetaTrader5` package. All limits in this document are **hard limits**. They are coded into the bot and cannot be bypassed at runtime.

This policy covers:
- Risk per trade
- Daily loss limits
- Maximum drawdown
- Leverage constraints
- Exposure caps
- Symbol whitelist
- News and spread filters
- Stop-loss requirements
- Position sizing
- Incident response
- Kill switch procedure

---

## 2. Risk Per Trade

| Parameter | Limit | Notes |
|---|---|---|
| Maximum risk per trade | **1% of account balance** | Calculated as: `(entry − stop_loss) × lots × tick_value ≤ 0.01 × balance` |
| Default risk per trade | **0.5% of account balance** | Conservative default; increase only after 30+ live trades with positive expectancy |
| Stop-loss required | **Always** | Any order without a stop-loss is rejected by the risk module; non-configurable |
| Minimum stop-loss distance | 1× ATR(14) on the signal timeframe | Prevents stop-loss from being triggered by normal noise |

**Formula (position sizing):**

```
risk_amount     = account_balance × risk_pct
stop_distance   = abs(entry_price − stop_loss_price)
lot_size        = risk_amount / (stop_distance / tick_size × tick_value)
lot_size        = min(lot_size, MAX_LOTS_PER_TRADE)
lot_size        = max(lot_size, symbol_volume_min)
lot_size        = round_to_step(lot_size, symbol_volume_step)
```

---

## 3. Maximum Daily Loss

| Parameter | Limit |
|---|---|
| Maximum daily loss | **2% of account balance at the start of the trading day** |
| Measurement | Realised P&L (closed trades) + unrealised P&L (open positions) |
| Trigger action | Bot immediately halts; no new orders placed; all open positions closed |
| Reset | Midnight UTC; daily loss counter resets to zero |

> **Example:** Account balance = $1,000 → daily loss limit = $20. If net P&L reaches −$20, the bot closes all positions and stops for the remainder of the trading day.

---

## 4. Maximum Drawdown

| Parameter | Limit | Action on breach |
|---|---|---|
| Intraday drawdown | 3% of balance at day start | Halt bot for the day |
| Rolling 7-day drawdown | 5% of balance at start of 7-day period | Halt bot; operator review required before resuming |
| Total account drawdown | 10% of initial deposit | Halt bot; operator must manually restart with written justification |

When a drawdown limit is breached:
1. Bot closes all open positions at market.
2. Bot enters `SAFE_HALT` state.
3. Alert is sent to operator.
4. Bot does not restart automatically.

---

## 5. Leverage Constraints

| Parameter | Limit |
|---|---|
| Maximum effective leverage used | **10:1** (regardless of broker offering higher) |
| Maximum lots per trade | Set in `config.yaml` (`MAX_LOTS_PER_TRADE`); must be sized so 1% risk rule is respected |
| Margin utilisation cap | Never use more than 20% of available margin across all open positions |

> **Note:** Broker may offer 1:100 or higher. This policy restricts the bot to 10:1 maximum effective leverage. Higher leverage is available to the operator manually but is not used by the bot.

---

## 6. Exposure Caps

| Parameter | Limit |
|---|---|
| Maximum open positions simultaneously | **3** |
| Maximum exposure per symbol | 1 open position per symbol at any time |
| Maximum correlated exposure | No more than 2 positions in USD-positive or USD-negative direction simultaneously |

---

## 7. Symbol Whitelist

The bot may only trade symbols explicitly listed in `config.yaml` under `ALLOWED_SYMBOLS`. Attempting to trade a symbol not on this list causes the order to be rejected.

**Default whitelist (example — operator must confirm symbols with broker):**

```yaml
ALLOWED_SYMBOLS:
  - EURUSD
  - GBPUSD
  - USDJPY
  - XAUUSD   # Gold vs USD
  - USDZAR   # Optional: USD vs South African Rand
```

To add a symbol:
1. Verify the symbol exists on the broker's MT5 platform.
2. Retrieve and record its contract spec (tick size, tick value, volume limits).
3. Add the symbol to `ALLOWED_SYMBOLS` in `config.yaml`.
4. Re-run the position sizing unit tests to confirm correct calculation.

---

## 8. News and Spread Filters

### 8.1 Spread Filter

| Parameter | Value |
|---|---|
| `MAX_SPREAD_POINTS` | Set per symbol in `config.yaml` (e.g. EURUSD = 25 points) |
| Behaviour | If current spread > `MAX_SPREAD_POINTS`, signal is discarded; order is not placed |
| Log | Every filtered signal is logged with the spread value at the time |

### 8.2 News Filter (Recommended — implement in Week 3 or later)

| Parameter | Value |
|---|---|
| No-trade window | 30 minutes before and 30 minutes after a high-impact news event |
| News source | Economic calendar API (e.g. ForexFactory, investing.com calendar) |
| Events covered | NFP, FOMC rate decision, CPI, SARB rate decision, ECB rate decision |
| Fallback if calendar is unavailable | Log a WARNING; do not halt the bot (availability risk vs safety risk) |

---

## 9. Trading Hours

| Parameter | Value |
|---|---|
| Trading window | `TRADE_START_UTC` to `TRADE_END_UTC` (set in `config.yaml`) |
| Suggested window | 07:00–20:00 UTC (London open to 1 hour before NY close) |
| No new trades | Last 30 minutes of trading window (allow existing trades to close normally) |
| No trading at weekend open | First 30 minutes after Sunday open (gap risk) |

---

## 10. Circuit Breaker

| Parameter | Value |
|---|---|
| `CIRCUIT_BREAKER_THRESHOLD` | 4 consecutive losing trades |
| `CIRCUIT_BREAKER_PAUSE_MINUTES` | 60 minutes |
| Behaviour | After N consecutive losses, bot pauses for the specified duration; then resumes |
| Reset | Consecutive loss counter resets to zero on any winning trade or at midnight UTC |

---

## 11. Incident Response Runbook

### 11.1 Bot Crash (Unexpected Process Exit)

1. Check the log file for the last error (look for `CRITICAL` or unhandled exception).
2. Check MT5 terminal for any open positions left by the bot.
3. **Close any unintended open positions manually** in the MT5 terminal before restarting the bot.
4. Fix the root cause (if known).
5. Restart the bot.
6. Monitor for 30 minutes after restart.

### 11.2 MT5 Terminal Disconnected

1. Bot enters `SAFE_HALT` after `MAX_RECONNECT_ATTEMPTS` failed reconnections.
2. Operator receives alert.
3. Operator checks VPS connectivity and MT5 terminal state.
4. If terminal has logged out (e.g. session expired), log in manually.
5. Restart the bot after terminal is reconnected.

### 11.3 Daily Loss Limit Breached

1. Bot closes all positions and halts automatically.
2. Operator receives alert.
3. Operator reviews the day's trades in the log file.
4. Operator investigates whether the loss was due to a strategy failure, a bug, or a market event.
5. Bot does **not** restart until the next trading day.
6. If the loss is > 5% of account balance in a single day, halt the bot for the rest of the week and review the strategy.

### 11.4 Runaway Orders (Bot Places Orders It Should Not Have)

1. **Immediately create the `KILL_SWITCH` file** (see §12 below).
2. Log into MT5 terminal manually and close all open positions.
3. Note all affected trades (ticket numbers, symbols, sizes).
4. Review logs to identify the root cause.
5. Do **not** restart the bot until the root cause is understood and fixed.
6. Run the fix through unit tests before redeploying.

### 11.5 Broker Account Suspended or Login Failure

1. Bot cannot initialize; logs `CRITICAL: mt5.initialize() failed`.
2. Contact broker support immediately.
3. Do not attempt to open a parallel account or bypass the issue.
4. Review whether a regulatory event (FICA document expiry, margin call, policy change) caused the suspension.

---

## 12. Kill Switch Procedure

The kill switch is the **fastest way to stop the bot completely**.

### Method 1: File-based kill switch (primary)

```bash
# Create this file in the bot's working directory:
touch /path/to/bot/KILL_SWITCH

# The bot polls for this file every loop iteration (< 1 second delay).
# On detection:
#   1. Closes all open positions at market.
#   2. Logs "KILL_SWITCH activated" at CRITICAL level.
#   3. Sends an alert.
#   4. Exits the process.
```

### Method 2: Close positions manually in MT5 terminal (emergency)

If the bot process is unreachable (VPS inaccessible):
1. Open MT5 terminal on any computer logged in to the same account.
2. Right-click each open position → Close.
3. Or use MT5 "Close All" button (if visible).

### Method 3: Broker emergency contact

If neither method 1 nor method 2 is possible:
1. Call or email the broker's support.
2. Request that all open positions be closed and the account be suspended.
3. Have your account number and KYC information ready to verify identity.

> **Operator responsibility:** Save the broker's emergency contact number on your phone before going live.

---

## 13. Policy Review and Amendment

| Event | Action |
|---|---|
| Any live incident (crash, runaway, loss limit breach) | Review this policy within 48 hours |
| Monthly | Review `CIRCUIT_BREAKER_THRESHOLD`, `MAX_DAILY_LOSS_PCT` against actual performance |
| Strategy change | Re-validate position sizing and risk limits for the new strategy |
| Account balance changes > 50% | Recalculate absolute lot sizes to ensure percentage-based limits still apply correctly |

Changes to this policy require:
1. Edit this file with the date and a one-line description of the change.
2. Commit the change to the repository.
3. Update the corresponding values in `config.yaml`.
4. Re-run all risk module unit tests.

---

## 14. Disclaimer

This policy applies to a personal, non-commercial trading bot operated at the operator's own risk. Past performance of any strategy does not guarantee future results. Trading leveraged financial instruments involves risk of loss greater than the initial deposit.

---

*See also: [MT5_PYTHON_ARCHITECTURE.md](MT5_PYTHON_ARCHITECTURE.md) · [BROKER_REQUIREMENTS_SA.md](BROKER_REQUIREMENTS_SA.md) · [MVP_ROADMAP_INTRADAY.md](MVP_ROADMAP_INTRADAY.md)*
