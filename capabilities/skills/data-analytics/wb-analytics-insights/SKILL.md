---
name: wb-analytics-insights
description: Use when defining product telemetry, KPIs, cohort/funnel queries, or experiment analysis to turn raw events into verifiable decisions.
---

# Analytics and Insights

## When to apply
- Instrumenting new user flows, auditing event schemas, or investigating metric drops.
- Designing A/B tests or building executive/product dashboards.

## Procedure
1. Trace the business question to exact event definitions, user/session identifiers, and time-window boundaries.
2. Audit data quality first: check for duplicate events, bot traffic, timezone mismatches, null keys, and schema drift.
3. Write reproducible queries (SQL/notebook) with explicit denominators, cohort filters, and segment breakdowns.
4. Separate correlation from causation; state sample size, confidence intervals, and known instrumentation gaps.
5. Summarize actionable findings with links to the underlying query and raw counts, avoiding PII in shared reports.

## Verification
- Query results reconcile against source-of-truth totals (e.g., billing or auth counts).
- Event schema changes include backward-compatibility and privacy checks.
