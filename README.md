# Biblical Principle Algo Trading

A personal intraday algorithmic trading bot built with Python, connected to a broker via the MetaTrader 5 (MT5) terminal API.  
Targeted to a South African operator trading FX and CFDs.

> **No guaranteed returns.** Trading leveraged instruments involves risk of loss greater than your initial deposit. Read the risk policy before deploying any capital.

---

## Documentation

### Business Case

| Document | Description |
|---|---|
| [docs/business-case/BUSINESS_CASE.md](docs/business-case/BUSINESS_CASE.md) | Why build this bot: objectives, expected outcomes, constraints |
| [docs/business-case/EXPORT_PDF.md](docs/business-case/EXPORT_PDF.md) | How to export the business case to PDF |

### Architecture and Design

| Document | Description |
|---|---|
| [docs/architecture/BUILD_APPROACH.md](docs/architecture/BUILD_APPROACH.md) | Recommended build approach: start from a reputable engine; LLMs as sidecars only |
| [docs/architecture/MT5_PYTHON_ARCHITECTURE.md](docs/architecture/MT5_PYTHON_ARCHITECTURE.md) | System architecture, module map, sequence diagrams, safety controls, latency notes |
| [docs/architecture/BROKER_REQUIREMENTS_SA.md](docs/architecture/BROKER_REQUIREMENTS_SA.md) | Broker selection checklist for South African residents using MT5 |
| [docs/architecture/MVP_ROADMAP_INTRADAY.md](docs/architecture/MVP_ROADMAP_INTRADAY.md) | 4-week MVP plan: environment → demo trading → tiny live; go/no-go checklist |
| [docs/architecture/RISK_POLICY.md](docs/architecture/RISK_POLICY.md) | Enforceable risk policy: limits, filters, kill switch, incident response runbook |

---

## Quick-Start Summary

1. **Read the risk policy first** → [RISK_POLICY.md](docs/architecture/RISK_POLICY.md)
2. **Select a broker** using the checklist → [BROKER_REQUIREMENTS_SA.md](docs/architecture/BROKER_REQUIREMENTS_SA.md)
3. **Follow the 4-week MVP plan** → [MVP_ROADMAP_INTRADAY.md](docs/architecture/MVP_ROADMAP_INTRADAY.md)
4. **Understand the system design** → [MT5_PYTHON_ARCHITECTURE.md](docs/architecture/MT5_PYTHON_ARCHITECTURE.md)
5. **Never go live until all go/no-go checklist items are checked**

---

## Key Design Decisions

- **Python + MT5 terminal API** (IPC bridge; MT5 terminal must be running on Windows/VPS)
- **Deterministic execution** — no LLM in the trading loop; LLMs may only be used as non-trading sidecars
- **Demo-first** — minimum 10 trading days on a demo account before any live deployment
- **Hard-coded safety controls** — max daily loss, max position size, spread filter, kill switch, circuit breaker

---

## Repository Structure

```
biblical-principle-algo-trading/
├── docs/
│   ├── business-case/          # Business case and PDF export
│   └── architecture/           # System design, broker checklist, roadmap, risk policy
├── config/
│   └── config.yaml             # Bot configuration (symbols, limits, credentials path)
├── bot/                        # Main Python package (to be built in MVP weeks 1–3)
│   ├── config/
│   ├── data/
│   ├── strategy/
│   ├── risk/
│   ├── execution/
│   ├── storage/
│   ├── reconciliation/
│   └── monitoring/
├── tests/                      # Unit and integration tests
└── scripts/                    # Utility scripts (candle fetch, account info, PDF export)
```

---

*Last updated: 2026-03-26*
