---
name: wb-api-contract-qa
description: Test HTTP API contracts and their persistence effects
version: 1.1.0
---
# wb-api-contract-qa

**Suggested role:** `qa-strategist`. This file is portable and does not depend on that agent existing.

## When to use
Changes to an API, DTO, HTTP status, database, XML/JSON or validation rules.

## Procedure
1. Map request, response, schema, authentication, idempotency, transactions and database effects.
2. Compare before/after including `null`, defaults, types, removed fields and validation.
3. Test authorization, pagination, filters, ordering, edge cases, timeouts and errors.
4. Collect evidence from the API, logs and read-only queries, except for approved changes.

## Output
Contract and persistence matrix, regressions and verification scripts.
