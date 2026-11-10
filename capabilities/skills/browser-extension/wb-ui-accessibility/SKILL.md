---
name: wb-ui-accessibility
description: Audit UI legibility and accessibility - contrast, focus states, zoom, themes and keyboard use
version: 1.2.0
---
# wb-ui-accessibility

**Suggested role:** `browser-engineer`. This file is portable and does not depend on that agent existing.

## When to use
Invisible text, low contrast, dark layouts, overlapping elements or difficult navigation.

## Procedure
1. Check contrast, hover/focus/disabled states, typography, overflow and target sizes.
2. Test 125-200% zoom, light/dark themes, keyboard use and responsiveness, without text selection as a workaround.
3. Inspect computed CSS and tokens; fix at the source, not with per-component exceptions.
4. Record a baseline for a fixed scope (screens, viewports, themes) before editing; after the fix, repeat the same scope and classify each finding as persisting, new or no longer observed.
5. An audit-only request edits nothing: report findings and stop. A fix request keeps content, colors outside the failing pairs and behavior unchanged.

## Output
Findings with selector, CSS cause and validation per viewport/theme.
