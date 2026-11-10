---
name: wb-ux-research
description: Evaluate or change an interface in a declared mode (review, refine, redesign, create) with a measured baseline and a before/after comparison
version: 1.1.0
---

# UX Research

## Pick one mode and say it
| Mode | Edits files | Must stay unchanged |
|---|---|---|
| Review | No | Everything; output is findings only |
| Refine | Yes | Content, colors, layout structure and behavior |
| Redesign | Yes | Content and behavior |
| Create | Yes | Nothing existing; follow the project's tokens and components |

Mixing modes is how a requested contrast fix becomes an unrequested redesign.

## Procedure
1. **Collect context before proposing.** Read the project's design tokens, component library, existing screens and the user journey the change serves.
2. **Record a baseline** for a fixed scope (named screens, widths 1440 and 390 px, light and dark themes): contrast failures, computed font sizes below 12 px, horizontal overflow, broken images, console errors, unreachable controls by keyboard.
3. **Make the change** allowed by the mode. Fix at the token or component, not per screen.
4. **Repeat the same scope** and classify each finding as persisting, new or no longer observed. A new finding caused by the change is a regression, not a follow-up.
5. **Judge generic patterns in context.** Repeated decoration, filler copy and default layouts are findings only when they hurt the journey in step 1.

## Limits
Automated checks do not prove WCAG conformance or visual quality. Small text and repetition need a human reading of the context; say which findings were measured and which are judgment.

## Deliverables
Mode, scope, baseline, before/after table, and prioritized findings with screen, element and observed evidence.

Do not assume integrations or credentials are available; propose them for user approval.
