---
name: wb-frontend-engineering
description: Use when building or refactoring web UI components, client-side state, routing, forms, responsive layouts, or bundle performance.
---

# Frontend Engineering

## When to apply
- Creating React/Vue/Svelte/vanilla UI components, client state stores, or form validation flows.
- Debugging layout shifts, unnecessary re-renders, hydration mismatches, or slow bundle loads.

## Procedure
1. Inspect existing design tokens, component primitives, routing conventions, and state management patterns first.
2. Design components with explicit loading, empty, error, and success states before wiring live data.
3. Keep server/async state separate from local UI state; avoid prop-drilling or redundant derived-state effects.
4. Verify keyboard navigation, semantic HTML landmarks, responsive breakpoints (mobile/desktop), and contrast ratios.
5. Check bundle size, lazy-load heavy routes/charts, and prevent XSS by avoiding raw HTML injection of untrusted strings.

## Verification
- Typecheck, linter, and component/UI tests pass across key viewport sizes.
- Zero console errors or unhandled promise rejections during primary user flows.
