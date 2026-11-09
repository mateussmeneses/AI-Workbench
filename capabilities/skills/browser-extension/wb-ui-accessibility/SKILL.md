---
name: wb-ui-accessibility
description: Audit UI legibility and accessibility - contrast, focus states, zoom, themes and keyboard use
version: 1.1.0
---
# wb-ui-accessibility

**Suggested role:** `browser-engineer`. This file is portable and does not depend on that agent existing.

## When to use
Invisible text, low contrast, dark layouts, overlapping elements or difficult navigation.

## Procedure
1. Check contrast, hover/focus/disabled states, typography, overflow and target sizes.
2. Test 125-200% zoom, light/dark themes, keyboard use and responsiveness, without text selection as a workaround.
3. Inspect computed CSS and tokens; fix at the source, not with per-component exceptions.
4. Collect before/after comparisons and a visual smoke test.

## Output
Findings with selector, CSS cause and validation per viewport/theme.
