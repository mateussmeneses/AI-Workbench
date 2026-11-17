---
name: wb-game-modding
description: Use when creating or debugging game mods, asset/pak overrides, script hooks, memory patches, or mod-loader compatibility.
---

# Game Modding

## When to apply
- Inspecting game archive formats, authoring Lua/C#/C++ mod scripts, or resolving load-order conflicts.
- Building non-destructive mod loaders or updating offsets after a game patch.

## Procedure
1. Identify the game engine, scripting runtime, and mod-loader contract without modifying original base game files.
2. Use pattern/signature scanning or symbol lookups rather than hardcoded fragile offsets wherever possible.
3. Isolate mod overrides into versioned, cleanly uninstallable packages with explicit load-order/dependency metadata.
4. Guard hooks against null game state, frame-rate dependence (use delta time), and save-file schema corruption.
5. Test mod installation, clean removal, and save-game compatibility on a backed-up profile.

## Verification
- Clean uninstallation restores vanilla game behavior with no leftover modified assets.
- Save files created or loaded during testing remain uncorrupted.
