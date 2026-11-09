---
name: wb-quant-research
description: Quantitative finance research, backtesting and trading-system workflows with explicit risk controls
---

# Quant Research & Trading Systems

## Evidence first
Identify data sources, licensing, survivorship bias, timezone/session rules, corporate actions and look-ahead risks before evaluating any strategy.

## Procedure
1. Inspect project documentation, data loaders, strategy code and existing backtests.
2. State the hypothesis, universe, frequency, costs (fees, slippage, spread, borrow) and benchmark.
3. Separate in-sample, out-of-sample and walk-forward periods; never tune on the evaluation window.
4. Reproduce baseline results with pinned data snapshots and seeds before changing logic.
5. Report risk-adjusted metrics (drawdown, exposure, turnover, Sharpe/Sortino) with their limits.
6. Keep paper trading and live execution behind explicit, separate user approval.

## Safety
- Never place orders, move funds or store exchange/broker keys without explicit authorization.
- LLM or model signals are hypotheses, not guarantees; label backtests as simulations.
- Nothing produced is financial advice.

## Templates
Use `templates/backtest-report.md` for every reported result and `templates/data-provenance-checklist.md` before trusting a dataset.

## Deliverables
Produce reproducible backtest reports, data-provenance notes, risk assumptions and a list of unvalidated claims.

Do not assume integrations or credentials are available; propose them for user approval.
