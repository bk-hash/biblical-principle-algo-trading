# Broker Requirements – South African Residents (MT5)

**Date:** 2026-03-26  
**Status:** Reference checklist  
**Audience:** Bot operator selecting a broker

---

## Important: MT5 Is Not the Broker

> **MetaTrader 5 (MT5) is a trading platform, not a broker.**  
> It is licensed to brokers who host servers that MT5 terminals connect to.  
> Whether you can open a live account from South Africa depends entirely on the **broker's** onboarding rules, regulation, and geographic restrictions — not on MT5 itself.

You must verify each item below with the specific broker before depositing funds.

---

## 1. Onboarding Acceptance Checklist

| # | Item to verify | How to verify |
|---|---|---|
| 1.1 | Broker explicitly accepts South African residents | Check T&Cs or ask support: *"Do you accept clients resident in South Africa?"* |
| 1.2 | FICA / KYC documents accepted from SA | SA ID + proof of address (utility bill / bank statement) must be accepted |
| 1.3 | No IP / geo-block for South Africa | Test signup from a South African IP; check FAQ for restricted regions |
| 1.4 | Account currency options include ZAR or USD | Avoid forced currency conversion friction |

---

## 2. Regulation

Understanding regulation protects your funds and clarifies your legal recourse.

| Regulation type | Description | What to check |
|---|---|---|
| **FSCA-regulated** (local) | Financial Sector Conduct Authority; SA-specific consumer protection; complaints handled locally | Verify FSCA licence number on [fsca.co.za](https://www.fsca.co.za) |
| **Offshore-regulated** | CySEC (Cyprus), FCA (UK), ASIC (Australia), FSA (Seychelles), etc. | Understand that local SA recourse is limited; segregated funds may still apply |
| **Unregulated** | No oversight | **Avoid** for live trading |

> **Recommendation:** For initial live trading, prefer an FSCA-regulated broker or a broker regulated by a Tier-1 authority (FCA/ASIC) that explicitly accepts SA clients. Do not treat offshore regulation as equivalent protection to local FSCA oversight.

---

## 3. Deposit and Withdrawal Methods

| Method | Items to confirm |
|---|---|
| EFT / local bank transfer | Is ZAR EFT supported? What are the fees and processing times? |
| International wire | What are the SWIFT fees? Is there a minimum deposit? |
| Card (Visa/Mastercard) | Accepted for both deposit and withdrawal? |
| E-wallets (Skrill, Neteller) | Available to SA residents? |
| Cryptocurrency | If offered, what are conversion fees? |
| **Withdrawal timeline** | How many business days? Are withdrawals processed to the same method as deposit? |
| **Minimum deposit** | What is the minimum required for a live account? |

---

## 4. Leverage and Margin

| Item | What to verify |
|---|---|
| Maximum leverage for FX majors | e.g. 1:100, 1:200, 1:500 |
| Maximum leverage for indices / metals | Often lower than FX |
| FSCA leverage caps (if FSCA-regulated) | As of 2026, FSCA limits retail leverage to 1:500 for FX majors |
| Margin call level | At what % equity/margin does a margin call trigger? |
| Stop-out level | At what % is auto-liquidation triggered? |
| Free margin requirements | Can you open multiple small positions simultaneously? |

---

## 5. Spreads and Commission

| Item | What to check |
|---|---|
| Spread type | Fixed vs floating? |
| Typical spread on your target symbols | e.g. EURUSD: 0.8–2.0 pips typical for retail |
| Spread during major news events | Spread can widen 5–20× during NFP, FOMC, etc. |
| Commission per lot (ECN/raw accounts) | Some brokers charge per-lot commission on raw-spread accounts |
| Swap / overnight rates | Cost of holding positions past 5pm NY (triple swap on Wednesday) |
| Minimum lot size | 0.01 (micro lot) is needed for small accounts |

---

## 6. Symbol List

| Item | What to verify |
|---|---|
| Your target symbols are available | e.g. EURUSD, USDZAR, XAUUSD, US30 |
| Symbol naming convention in MT5 | e.g. `EURUSD` vs `EURUSDm` vs `EURUSD.r` — this matters for your bot's config |
| Contract size | Standard lot = 100,000 units for FX; verify for indices and metals |
| Tick size and tick value | Required for accurate position sizing in your risk module |
| Trading hours per symbol | Some brokers close symbols over weekends or during holidays |

---

## 7. Execution Type

| Type | Description | Bot suitability |
|---|---|---|
| **Market Maker (Dealing Desk)** | Broker takes the other side of trades | Higher conflict of interest; may requote during news |
| **STP (Straight-Through Processing)** | Orders routed to liquidity providers | Lower conflict of interest; suitable for intraday bots |
| **ECN (Electronic Communication Network)** | Direct market access; variable spreads + commission | Best for frequent intraday trading; requires commission to be modelled in risk |
| **NDD (No Dealing Desk)** | Broad term for STP/ECN | Verify what it means for that specific broker |

> **For an intraday bot:** Prefer STP or ECN execution to minimise requotes and slippage.

---

## 8. API Restrictions

The MT5 Python package connects to the terminal via IPC, not directly to the broker server. Verify:

| Item | What to check |
|---|---|
| Automated trading allowed | Some brokers prohibit EA/bot trading in their T&Cs |
| No rate-limiting on order placement | Check if the broker imposes limits on orders per second / per minute |
| `MetaTrader5` Python package compatibility | Confirm broker's MT5 build is compatible with the `MetaTrader5` pip package (build ≥ 2410) |
| VPS trading allowed | Some brokers restrict account access from VPS IPs |
| Expert Advisors (EAs) permitted | MT5 Python bots behave like EAs; confirm EAs are not prohibited |

---

## 9. Hedging vs Netting Mode

| Mode | Description | Impact on bot |
|---|---|---|
| **Hedging** | Multiple positions per symbol allowed (opposite directions) | Position management is per-ticket; easier for strategies that open independent entries |
| **Netting** | Only one position per symbol; new orders add to / subtract from it | Simpler accounting; requires the bot to track net exposure per symbol |

> Verify which mode the broker uses **before** writing your execution and reconciliation logic. The `mt5.account_info().trade_mode` property will show this at runtime, but confirm upfront.

---

## 10. Server Time Zone

| Item | Why it matters |
|---|---|
| Broker server time zone (check `mt5.symbol_info().time`) | MT5 timestamps use broker server time; your bot must convert to UTC correctly |
| Daily candle open/close | A broker using GMT+2 will have a different "daily close" from one using GMT+0 |
| Swap rollover time | Usually 5pm New York (22:00 or 23:00 UTC depending on season) |
| Weekend gap | When does the broker open Sunday? (usually 22:00–23:00 UTC) |

---

## 11. Contract Specifications

Before trading any symbol, retrieve and log these values at startup:

```python
info = mt5.symbol_info("EURUSD")
# Key fields:
# info.trade_contract_size   # e.g. 100000
# info.trade_tick_size       # e.g. 0.00001
# info.trade_tick_value      # e.g. 1.0 (in account currency per lot)
# info.volume_min            # e.g. 0.01
# info.volume_step           # e.g. 0.01
# info.volume_max            # e.g. 500.0
# info.spread                # current spread in points
```

---

## 12. Due-Diligence Checklist (Before Going Live)

Complete all of these on a **demo account** before depositing real money.

### 12.1 Demo Account Testing
- [ ] Open a demo account with the same leverage and account size as your intended live account
- [ ] Run the bot on demo for a minimum of **10 trading days** (2 calendar weeks)
- [ ] Confirm symbol names, contract sizes, and tick values match your config
- [ ] Confirm all order types (market, limit, stop) are accepted
- [ ] Test the kill switch and circuit breaker on demo

### 12.2 Slippage Measurement
- [ ] Log `request.price` vs `result.price` for every market order
- [ ] Calculate average and maximum slippage over at least 50 fills
- [ ] Ensure average slippage is within acceptable range for your strategy's edge

### 12.3 Spread Widening During News
- [ ] Monitor spread at least 5 minutes before and after a major news release (NFP, FOMC, CPI)
- [ ] Confirm your `MAX_SPREAD_POINTS` filter blocks trades during widening
- [ ] Record worst-case spread observed

### 12.4 Weekend Gaps
- [ ] Observe at least one weekend open
- [ ] Confirm the bot detects the gap and does not misinterpret it as a signal
- [ ] Confirm stop-losses are honoured (or note broker's gap-fill policy)

### 12.5 Support Responsiveness
- [ ] Submit at least one test support query (account, withdrawal, technical)
- [ ] Measure response time and quality
- [ ] Identify the emergency contact method if your bot misbehaves and you need the account suspended immediately

### 12.6 Withdrawal Test
- [ ] Make at least one small withdrawal from the live account before deploying the bot
- [ ] Confirm funds arrive within the stated timeline
- [ ] Confirm there are no surprise fees

---

## 13. What This Document Does Not Do

This document does **not** endorse, recommend, or guarantee that any specific broker:
- accepts South African clients,
- is currently regulated,
- has competitive spreads,
- will remain solvent.

Broker terms change. Always verify directly with the broker and check the **FSCA register** at [fsca.co.za](https://www.fsca.co.za) for current licensing status.

---

*See also: [MT5_PYTHON_ARCHITECTURE.md](MT5_PYTHON_ARCHITECTURE.md) · [MVP_ROADMAP_INTRADAY.md](MVP_ROADMAP_INTRADAY.md) · [RISK_POLICY.md](RISK_POLICY.md)*
