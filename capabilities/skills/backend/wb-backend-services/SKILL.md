---
name: wb-backend-services
description: Use when designing or modifying HTTP/RPC endpoints, database schemas, auth boundaries, background jobs, or service migrations.
---

# Backend Services

## When to apply
- Adding endpoints, changing persistence models, or debugging latency and concurrency issues.
- Implementing authentication, authorization, or transactional state changes.

## Procedure
1. Trace the full request lifecycle: routing, input validation, authn/authz checks, domain logic, DB transactions, and error serialization.
2. Check data-access patterns for N+1 queries, missing indexes, unbounded result sets, and lock contention.
3. Design schema migrations to be backward-compatible (expand-and-contract) with a tested rollback path.
4. Enforce structured error responses without leaking stack traces, internal SQL, or secrets to callers.
5. Add integration tests covering happy path, validation errors, unauthorized access, and concurrent/idempotent writes.

## Verification
- API contract and migration tests pass against a realistic database state.
- Resource limits (timeouts, payload caps, connection pool bounds) are explicit.
