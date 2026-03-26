# Business Case: Personal Algorithmic FX Trading Project (South Africa)

**Audience:** A South African cybersecurity analyst (no coding experience, no trading knowledge) who wants to build an algorithmic trading system for personal side income.

## 1) Executive summary
Build a small, personal **algorithmic trading learning project** with the goal of generating **modest supplemental income over 12–18 months**, while prioritizing **capital preservation, skills development, and strict risk controls**.

This is not a “build a bot and get rich” plan. With no coding and no trading background, the realistic business case is:
- **Phase 1–2 (0–6 months):** invest time to learn basics; no meaningful profit expected.
- **Phase 3 (6–12 months):** paper trading + small live testing; aim for consistency, not high returns.
- **Phase 4 (12+ months):** if results are stable, scale slowly; otherwise stop or keep it as a hobby project.

## 2) The problem / opportunity
**Problem:** Salary growth is limited and inflation/cost-of-living pressure makes “side income” attractive.

**Opportunity:** Algorithmic trading can (in theory) produce income that is:
- scalable (the same system can trade daily),
- partially automated (doesn’t require constant screen time once stable),
- aligned with a cybersecurity analyst’s strengths (discipline, controls, monitoring, incident response mindset).

**Reality check:** Many retail traders lose money, and many trading bots fail due to:
- overfitting,
- unrealistic backtests,
- poor execution/slippage,
- lack of risk controls,
- emotional interference when things go wrong.

The opportunity is valid only if the project is treated like an **engineering + risk-management exercise**, not gambling.

## 3) Goals (define success in realistic terms)
**Primary goal:** Build a system that can trade automatically with strict risk controls and minimal manual intervention.

**Secondary goal:** Target *modest* returns over time, and accept that the first year may be net-zero or negative while learning.

**Success criteria (practical):**
- Runs for **30–90 days** without major failures (crashes, duplicated orders, runaway exposure).
- Clear metrics: win rate, average win/loss, drawdown, slippage, execution errors.
- Hard risk limits: max daily loss, max open positions, max leverage, kill switch.

## 4) Proposed solution (what you will build)
A simple but professional **personal trading stack**:

1. **Education layer (trading + coding basics)**
   - Trading fundamentals: orders, leverage, spread, margin, risk, position sizing.
   - Python basics (or low-code first, but Python is most practical long-term).

2. **Research & backtesting**
   - Start with **1–2 simple strategies** (e.g., moving average crossover; mean reversion with volatility filter).
   - Use realistic costs: spreads, commissions, slippage.

3. **Paper trading**
   - Run on a demo account for **1–3 months**.
   - Verify behavior in real market conditions (news spikes, widening spreads, weekends).

4. **Small-capital live trading**
   - Start tiny (money you can afford to lose).
   - Scale only after stable performance and stable operations.

5. **Operations, monitoring, and controls (cybersecurity advantage)**
   - Logging, alerts (Telegram/email), dashboards.
   - Secrets management (API keys), least privilege, locked-down VPS.
   - Incident runbooks: actions for broker disconnects, rejected orders, drawdown limit hits.

## 5) Why this makes sense for a cybersecurity analyst
Cybersecurity experience maps well to trading system reliability:
- **Threat modeling →** trading failure modes (overexposure, bad data, disconnects)
- **Controls & monitoring →** risk limits, alerts, audit trails
- **Incident response →** pre-defined kill-switch procedures

This improves the odds of building something that is **safe and robust**, even if the trading edge is small.

## 6) Costs (time + money)
**Time (realistic):**
- 5–8 hours/week for ~6 months to become minimally competent.
- Expect **150–300 hours** before you can build something you trust.

**Money (rough):**
- Learning: low cost (optional courses/books).
- Infrastructure: modest monthly VPS cost (recommended for reliability).
- Broker capital: start with a small amount you can lose (treat as tuition).
- Tools: open-source is sufficient for a first version; premium data may cost later.

## 7) Benefits (tangible and intangible)
**Tangible:**
- Potential side income if the system performs (not guaranteed).
- Reduced time requirement compared to manual trading once stable.

**Intangible:**
- Skills in Python, data analysis, automation, and cloud operations.
- A portfolio-style project (even if personal) that supports career growth.

## 8) Risks and mitigations
**Risk: losing money**
- Mitigation: demo → tiny live; strict max-loss limits; low leverage; slow scaling.

**Risk: false confidence from backtests**
- Mitigation: walk-forward testing; out-of-sample evaluation; include costs/slippage; avoid curve-fitting.

**Risk: black-swan events**
- Mitigation: hard stops, max exposure, circuit breakers, always assume gaps.

**Risk: technical failure**
- Mitigation: monitoring + alerts; idempotent order handling; reconciliation; runbooks; kill switch.

**Risk: scams / fake “signals”**
- Mitigation: avoid “guaranteed returns”; rely on transparent, testable strategies.

**Regulatory/tax risk (South Africa)**
- Mitigation: keep records; consult a tax professional if you scale; don’t market the system to others.

## 9) Options analysis
**Option A — Learn and build from scratch (recommended)**
- Pros: understanding, safer operations, transferable skills.
- Cons: slower ramp-up.

**Option B — Use a ready-made bot/EA and tweak settings**
- Pros: fast start.
- Cons: high chance of loss; hard to validate; easy to be misled.

**Option C — Copy trading**
- Pros: operationally easy.
- Cons: still risky; fees; less control.

**Recommendation:** Option A, with a very small initial scope.

## 10) Phased plan with milestones
**Phase 0 (Week 1): decision + guardrails**
- Define learning budget and maximum acceptable loss.
- Start with major FX pairs (e.g., EUR/USD, GBP/USD).
- Choose broker/API path.

**Phase 1 (Weeks 2–6): foundations**
- Learn trading basics + Python basics.
- Deliverable: script/notebook that loads data and computes indicators.

**Phase 2 (Weeks 7–12): first strategy + backtest**
- Implement one simple strategy; backtest with realistic costs.
- Deliverable: backtest report + risk metrics + documented assumptions.

**Phase 3 (Months 4–6): paper trading + operations**
- Run demo; add logs/alerts; test failure modes.
- Deliverable: 30+ days stable demo run with monitoring.

**Phase 4 (Months 7–12): tiny live trading**
- Go live with minimal capital and leverage.
- Deliverable: 3 months live results + operational stability.

**Phase 5 (Month 12+): evaluate**
- If unstable: stop or continue as learning.
- If stable: scale slowly, never exceed predefined risk.

## 11) Financial expectation
This business case does not promise a return. Treat the first year as a **controlled apprenticeship**:
- Best case: modest, consistent profits with low drawdowns.
- Likely case: break-even to small loss while learning.
- Worst case: meaningful losses if leverage/risk controls are ignored.