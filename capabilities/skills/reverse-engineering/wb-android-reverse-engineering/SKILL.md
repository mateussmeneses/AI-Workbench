---
name: wb-android-reverse-engineering
description: Analyze Android APK/AAB/DEX packages you own or are authorized to test - manifest, decompiled code, native libraries, runtime behavior and network traffic
---

# Android Reverse Engineering

## Scope and authorization
Work only on apps you own, open-source apps, or targets with written authorization. Do not bypass licensing, DRM, payment or anti-cheat checks for third-party software, and never redistribute modified proprietary APKs.

## Evidence first
Record the package name, version code, SHA-256 of the original file, signing certificate digest and the device/emulator ABI before any change. `aiwh game-port --binary app.apk` reports the detected container from a bounded header read.

## Procedure
1. **Static inventory** - decode with `apktool d app.apk -o out/` (manifest, resources, smali). Note permissions, exported components, deep links, `networkSecurityConfig` and `debuggable`/`allowBackup` flags.
2. **Readable code** - open the APK in `jadx-gui` (or `jadx -d src/ app.apk`). Search entry points from the manifest, then follow API clients, crypto, storage and feature flags. Treat obfuscated names as hypotheses; rename consistently.
3. **Managed runtimes** - for Unity/Xamarin/MAUI apps, extract `assemblies/` or `Managed/*.dll` and inspect with ILSpy; for Flutter, identify `libapp.so` and the Dart version first.
4. **Native libraries** - load `lib/<abi>/*.so` in Ghidra (or the REA/Ghidra MCP when enabled). Start from `JNI_OnLoad` and `Java_*` exports; correlate with Java `native` methods.
5. **Runtime observation** - on an emulator or a test device, use Frida (`frida -U -f <package>`) to trace calls you identified statically. Keep scripts small and versioned in `artifacts/frida/`.
6. **Network** - route the emulator through mitmproxy; if certificate pinning blocks traffic on your own build, prefer a debug build with a test network-security config over generic bypass scripts. Use mitmproxy2swagger to draft an API description.
7. **Rebuild (only when needed)** - `apktool b out/ -o patched.apk`, then `zipalign` and `apksigner` with a test key. Validate install, launch and the changed behavior.

## Tooling
jadx, Apktool, apk.sh, APKEditor, ILSpy, Ghidra, Frida, mitmproxy, ADB. MCP candidates (opt-in): `apktool-mcp`, `ghidra-mcp`, `rea`.

## Deliverables
- Inventory: manifest summary, exported components, permissions, libraries and ABIs.
- Findings with file/class/method or offset references and the evidence used (static, runtime or traffic).
- Reproduction steps, scripts and hashes; clearly separate confirmed behavior from hypotheses.

Do not assume tools, devices or credentials are available; propose them for user approval.
