---
name: wb-board-snapshots
description: Validate Kanban board counters and daily snapshots against what the UI actually shows
version: 1.1.0
---
# wb-board-snapshots

**Suggested role:** `browser-engineer`. This file is portable and does not depend on that agent existing.

## When to use
WIP boards, counters, daily snapshots, hidden cards and sprint progress.

## Procedure
1. Identify the board, columns, states and business rules; distinguish the total card count from the displayed counter.
2. Count cards in the DOM, including columns without a badge/counter and regions under overlays when accessible.
3. Compare the snapshot result with the visible count under filters and groupings.
4. Test multiple boards in isolation, resets, persistence, dates and data synchronization.

## Output
Board x column x UI count x snapshot x divergence matrix, with evidence.
