---
name: wb-web-api-recon
description: Document the HTTP API behind a web, Electron or mobile client you are authorized to analyze, producing an OpenAPI draft from captured traffic and bundled code
---

# Web/API Reconnaissance

## Scope and authorization
Use on your own services, documented public APIs, or targets with written permission. Respect terms of service and rate limits; never use captured credentials or session tokens outside the authorized test.

## Procedure
1. **Capture** - run mitmproxy (`mitmweb`) with a dedicated browser profile, emulator or test device; exercise each feature deliberately and save flows (`.mitm`).
2. **Describe** - generate a first OpenAPI draft with mitmproxy2swagger, then prune noise (analytics, CDN, third-party calls) and merge path parameters.
3. **Client code** - for web apps, deobfuscate/unbundle JavaScript with webcrack; for Electron apps, extract `app.asar` with `asar extract` and inspect the main/preload scripts. Locate endpoint builders, auth headers, request signing and feature flags.
4. **Validate** - replay a minimal set of requests with curl or an HTTP client against a test account; confirm required headers, auth flow, pagination and error shapes.
5. **Document** - finalize the OpenAPI file with examples (redacted), auth description, rate limits observed and unknowns.

## Safety
Redact tokens, cookies and personal data from saved flows before sharing. Keep captures in a gitignored `artifacts/` directory.

## Deliverables
Redacted OpenAPI specification, a list of verified vs inferred endpoints, auth flow notes and reproduction steps.
