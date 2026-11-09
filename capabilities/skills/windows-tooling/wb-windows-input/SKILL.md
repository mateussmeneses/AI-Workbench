---
name: wb-windows-input
description: Debug Windows input devices, controllers, drivers and services
version: 1.1.0
---
# wb-windows-input

**Suggested role:** `windows-engineer`. This file is portable and does not depend on that agent existing.

## When to use
USB/Bluetooth input, game controllers, XInput/RawInput, Windows services or desktop portability.

## Procedure
1. Map devices and driver versions; collect logs without changing global state.
2. Reproduce with wired and wireless controllers; distinguish HID, emulation and application layers.
3. Measure latency, reconnection, duplicate events, window focus, suspend and hot-plug.
4. Check packaging, privileges, persistence and rollback of service changes.

## Output
Hardware/driver matrix, diagnosis, tests and risks.
