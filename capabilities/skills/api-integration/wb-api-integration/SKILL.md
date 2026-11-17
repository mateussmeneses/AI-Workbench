---
name: wb-api-integration
description: Use when integrating third-party REST, GraphQL, or webhook APIs with retries, rate-limit handling, schema validation, and idempotency.
---

# API Integration

## When to apply
- Adding a new external API client, webhook consumer, or OAuth/token flow.
- Hardening flaky integrations against timeouts, pagination bugs, or rate limits.

## Procedure
1. Read the provider's official contract: auth mechanism, rate-limit headers, pagination cursor rules, and error payload formats.
2. Isolate the integration behind a thin adapter interface so business logic never depends directly on raw HTTP responses.
3. Enforce explicit connect/read timeouts, bounded exponential backoff with jitter on transient 429/5xx errors, and idempotency keys on mutations.
4. Validate incoming payloads at the boundary and verify webhook signatures before parsing bodies.
5. Test with recorded HTTP fixtures (success, 401/403, 429 Retry-After, malformed JSON, timeout) without hitting live paid endpoints in CI.

## Verification
- Contract tests cover pagination boundaries, error mapping, and secret redaction in logs.
- Credentials remain in environment/secret stores, never hardcoded or logged.
