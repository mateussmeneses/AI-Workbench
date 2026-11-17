---
name: wb-desktop-apps
description: Use when building or debugging native or cross-platform desktop applications (Win32, WPF, Qt, Tauri, Electron) including packaging and IPC.
---

# Desktop Applications

## When to apply
- Implementing UI threads, native filesystem/OS dialogs, IPC bridges, auto-updaters, or installers (MSIX/NSIS/DMG).
- Fixing DPI scaling, window lifecycle, memory leaks, or Windows/macOS path-encoding bugs.

## Procedure
1. Separate UI-thread rendering from blocking I/O or CPU work using async workers or message queues.
2. Validate all IPC messages between renderer/UI and privileged native backends as untrusted input.
3. Handle OS-specific paths, Unicode filenames, high-DPI scaling, and single-instance locks explicitly.
4. Keep user state and caches in standard OS app-data directories rather than the application install folder.
5. Test cold start, window resize/minimize, offline behavior, and clean uninstall/upgrade in a clean environment.

## Verification
- Packaged installer/binary launches outside the dev tree without missing runtime DLLs or assets.
- No sensitive capabilities are exposed to untrusted webviews or renderer scripts.
