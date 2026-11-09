---
name: wb-behavior-teardown
description: Specify an existing product from observed behavior alone - screenshots, controlled probes, frame-by-frame measurement and sanitized HAR captures - producing TEARDOWN.md and a numbered SPEC.md
---

# Behavior Teardown

Rebuild-ready specifications without opening a binary: observe, intercept, decode, rebuild.

## Procedure
1. **Observe** - screenshot every screen and state (empty, loading, error, paid/locked, settings). On macOS use Accessibility Inspector, on Windows Accessibility Insights or Inspect.exe, to read the UI element tree. Check the app bundle and About/licenses page for its stack (`Contents/Frameworks`, `resources/app.asar`, bundled licenses).
2. **Probe** - run small controlled experiments that answer one question each (two clicks 0.5 s / 1 s / 2 s apart, a click near the frame edge, a fast straight mouse line). Record each probe.
3. **Measure** - split outputs into frames and measure timing, scale and easing:
   ```
   ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 export.mp4
   ffmpeg -i export.mp4 -vf fps=60 frames/%04d.png
   ffmpeg -i still.png -vf palettegen=max_colors=12 palette.png
   ```
   Write numbers with frame evidence (start/settle frame, zoom factor, easing curve, hold time).
4. **Intercept** (web apps) - DevTools -> Network -> Preserve log -> perform the action -> "Save all as HAR (sanitized)". Describe each request (trigger, method, request/response shape as types) and decide which steps can run locally.
5. **Decode** - fill `TEARDOWN.md` (what was seen) and then `SPEC.md` (what will be built): decisions worth checking, free vs paid split, features with exact numbers, data model, acceptance checks that each run in under two minutes, "needed from you", "not in v1". Stop for approval after each document.
6. **Look for an open-source base** - for the top three candidates record license, last commit, what is missing and effort to adapt (`aiwh catalog check` style metadata).
7. **Rebuild and self-test** - parallel agents own separate folders; a review agent checks anything that writes files, handles payments or touches the network; then run the app (headless browser for web), walk every acceptance check, screenshot each screen and fix failures. Do not report "works" before it was seen working.

## Templates
`wb-clean-room-rebuild/templates/TEARDOWN.md` and `SPEC.md`. Use your own name, icons and assets; keep secrets in server-side functions, never inside the app or bundle.

## Deliverables
TEARDOWN.md with probe evidence, SPEC.md with numbered acceptance checks, the rebuild, and a pass/fail table per check with screenshots.
