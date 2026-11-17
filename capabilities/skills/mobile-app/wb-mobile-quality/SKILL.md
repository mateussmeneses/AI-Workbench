---
name: wb-mobile-quality
description: Use when building, testing, or profiling Android/iOS mobile apps for offline resilience, permissions, battery/memory usage, and store readiness.
---

# Mobile Quality

## When to apply
- Implementing mobile screens, background sync, push notifications, or native device permissions.
- Diagnosing ANRs, crashes, cold-start lag, or platform-store policy rejections.

## Procedure
1. Check target OS SDK levels, permission manifests, and offline/poor-network behavior before adding features.
2. Request runtime permissions contextually at point of use with graceful degradation if denied.
3. Keep main/UI threads free of disk/network I/O; cancel in-flight work cleanly across lifecycle pauses and rotations.
4. Profile memory allocations, image caching, and wake-locks to prevent OOM crashes and battery drain.
5. Verify release builds with ProGuard/R8/strip enabled on both physical/emulator targets and check store privacy declarations.

## Verification
- Automated UI/unit tests pass on target API levels including offline and permission-denied cases.
- Release build starts cleanly with obfuscation/shrinking enabled and no leaked debug keys.
