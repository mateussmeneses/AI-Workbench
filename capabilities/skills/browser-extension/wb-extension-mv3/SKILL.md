---
name: wb-extension-mv3
description: Review Manifest V3 browser extension architecture, permissions and lifecycle
version: 1.1.0
---
# wb-extension-mv3

**Suggested role:** `browser-engineer`. This file is portable and does not depend on that agent existing.

## When to use
Chrome/Edge extensions, Manifest V3, service workers, content scripts and injection.

## Procedure
1. Inspect `manifest.json`, host-permission scope, the service worker and content scripts.
2. Identify messaging, lifecycle, persistence, API version and CSP.
3. Test with mutating DOM, SPA navigation, reloaded tabs, duplicate injection and denied permissions.
4. Validate accessibility, contrast, isolation and graceful degradation.

## Output
Permission/state risks, manual and automated tests, and minimal recommendations.
