---
name: wb-product-discovery
description: Use when scoping new features, writing PRDs/specs, prioritizing roadmaps, or validating user problems before writing implementation code.
---

# Product Discovery

## When to apply
- Evaluating a feature request, planning a milestone, or resolving ambiguous user requirements.
- Deciding whether to build, integrate an existing tool, or defer scope.

## Procedure
1. State the concrete user problem, who experiences it, and how it is currently worked around.
2. Gather evidence from existing issues, usage friction, or codebase constraints before proposing solutions.
3. Define non-goals explicitly to prevent scope creep and keep the first slice shippable.
4. Compare at least two options (e.g., minimal CLI vs. full UI, build vs. integrate) with trade-offs and maintenance cost.
5. Write testable acceptance criteria and measurable success signals before moving to implementation.

## Verification
- Problem statement, non-goals, and acceptance criteria are unambiguous enough to derive tests directly.
- Proposed scope does not duplicate an already-implemented capability.
