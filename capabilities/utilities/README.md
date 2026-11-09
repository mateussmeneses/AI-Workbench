# Utilities by context

Tools listed here are **conditional recommendations**, never installed automatically. Install only when a task needs them. Linked tools are also indexed in `capabilities/references/catalog.json` with risk labels.

| Core | `git`, `gh`, `rg` (ripgrep), `fd`, `jq`, `python`, `node`, PowerShell 7 |
|---|---|
| QA .NET | `.NET SDK`, `dotnet test`, NUnit, Reqnroll, Selenium/Appium, logs, read-only SQL |
| Porting | RenderDoc, Vulkan SDK/Validation Layers, frametime capture, FFmpeg, RE tools per file/build |
| Extensions | Chrome/Edge DevTools, Node.js, DOM tests, Playwright, lint |
| Mobile | Android SDK/ADB, Gradle, emulators/physical devices, permission tests |
| Windows | PowerShell, Event Viewer, Windows SDK, HID/controller tools as needed |
| Reverse engineering | [Ghidra](https://github.com/NationalSecurityAgency/ghidra), [ImHex](https://github.com/WerWolv/ImHex), [x64dbg](https://github.com/x64dbg/x64dbg), [Frida](https://github.com/frida/frida), [Kaitai Struct](https://github.com/kaitai-io/kaitai_struct), [binwalk](https://github.com/ReFirmLabs/binwalk) |
| Managed/Android | [ILSpy](https://github.com/icsharpcode/ILSpy), [jadx](https://github.com/skylot/jadx), [Apktool](https://github.com/iBotPeaches/Apktool), [apk.sh](https://github.com/ax/apk.sh), [APKEditor](https://github.com/REAndroid/APKEditor) |
| Web/Electron/APIs | [webcrack](https://github.com/j4k0xb/webcrack), [asar](https://github.com/electron/asar), [mitmproxy](https://github.com/mitmproxy/mitmproxy), [mitmproxy2swagger](https://github.com/alufers/mitmproxy2swagger), [Scrapling](https://github.com/D4Vinci/Scrapling) |
| Shader/PC gaming | [SCSKiller](https://github.com/BlueHeisenberg/SCSKiller) (shader cache precompilation), [Magpie](https://github.com/Blinue/Magpie) (window upscaling) |

## Operating policy
1. Reuse existing CLIs instead of adding a redundant MCP.
2. Pin versions used for reproduction and keep `logs/`/`artifacts/` gitignored.
3. Do not install/disable services, drivers or global hooks as a side effect of setup.
4. Report commands and results; never invent measurements.
