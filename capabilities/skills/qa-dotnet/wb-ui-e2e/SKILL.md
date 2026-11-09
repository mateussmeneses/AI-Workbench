---
name: wb-ui-e2e
description: Automate UI tests with stable locators and condition-based waits
version: 1.1.0
---
# wb-ui-e2e

**Suggested role:** `qa-strategist`. This file is portable and does not depend on that agent existing.

## When to use
Selenium, Appium or Playwright tests, or intermittent UI failures.

## Procedure
1. Choose stable locators (`data-testid` when available); avoid indexing and fixed sleeps.
2. Synchronize on observable conditions; keep tests isolated, without implicit state.
3. Record console, network, screenshots, timings and real state only when relevant.
4. Run tests repeatedly in the pipeline/locally and distinguish flakes from regressions.

## Output
Reproducible tests, selector quality and stability evidence.
