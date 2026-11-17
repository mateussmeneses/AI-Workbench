---
name: wb-qa-automation
description: Use when designing test suites, E2E browser/API automation, fixture factories, flakiness fixes, or CI test-coverage gates.
---

# QA Automation

## When to apply
- Adding unit, integration, or end-to-end (Playwright/Selenium/API) test coverage for critical user journeys.
- Eliminating flaky tests, slow test setups, or brittle selectors/mocks.

## Procedure
1. Classify coverage by risk: put fast logic/edge cases in unit tests, contracts in integration tests, and critical paths in E2E.
2. Build isolated, deterministic fixtures (temp dirs, seeded DBs, explicit clocks) with zero dependency on global host state.
3. Replace arbitrary `sleep` waits with explicit state/condition assertions and stable `data-testid`/role selectors.
4. Test failure paths explicitly: invalid inputs, timeouts, permission denials, partial failures, and concurrency.
5. Verify tests fail when the target behavior is broken (mutation/regression check) before trusting green runs.

## Verification
- Test suite passes repeatedly in isolation and parallel/CI runs without flakes.
- No tests silently skip assertions or hit live external paid services.
