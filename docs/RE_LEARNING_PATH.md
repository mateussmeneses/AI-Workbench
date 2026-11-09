# Reverse engineering with agents: learning path

A practical order for learning agent-assisted reverse engineering with REA and the Workbench capabilities. Every link is in the reference catalog (`aiwh references --area reverse-engineering`).

## 1. Set up

```powershell
node -v                                   # REA 6.8.0: 22.23.4+, 24.22.1+ or 26.12.1+
npx rea-agents@latest setup               # shows a plan and backs up agent config before changing it
npx -y rea-agents@latest doctor --client claude_code --json
rea doctor --provider ghidra --json       # engine check: Ghidra version, JDK, native controls
aiwh doctor                               # reports rea, node, java, GHIDRA_INSTALL_DIR and JAVA_HOME
```

Electron, JavaScript and .NET targets need no engine. Native binaries need Ghidra 12.1.x (REA 6.8.0 verifies 12.1.4) with a 64-bit JDK 25+ (`GHIDRA_INSTALL_DIR` is the folder that contains `ghidraRun`; `JAVA_HOME` is the JDK root), Hopper or IDA. After `rea update`, rerun `rea setup` so every client registration matches the CLI version. On Windows the REA Ghidra provider is experimental and read-only. Keep REA current with `rea update`.

## 2. Progression

| Step | Target | What it teaches | Workbench support |
|---|---|---|---|
| 1 | REA Notes export example | One click traced from renderer to preload, IPC and main process | `aiwh inspect`, `wb-web-api-recon` |
| 2 | Notion clipboard showcase | Electron feature tracing in a real app | `wb-clean-room-rebuild` analyst |
| 3 | A CTF binary | Strings, xrefs, decompiler navigation | `wb-reverse-engineering`, `wb-binary-analysis` |
| 4 | Aegis APK showcase | Manifest, classes, native libraries | `wb-android-reverse-engineering` |
| 5 | DX-Ball rebuild showcase | Byte and behavior oracles (3,205 cases, 63 matching bytes) | `wb-oracle-testing` |
| 6 | A feature you use daily | Full loop: evidence -> SPEC.md -> rebuild -> verifier match rate | `aiwh cleanroom init`, `aiwh spec check` |
| 7 | Ghidra, assembly, papers | Depth for stripped native targets | courses, books and papers below |

## 3. Method in one screen

1. `aiwh inspect <file or app folder>` identifies the target type and the matching method, tools and REA tools.
2. Scope one feature in one sentence.
3. Analyst: strings first, functions ranked by cross-references, every claim tagged observation / inference / unknown with confidence 1-10.
4. Spec writer: behavior only; unknowns become open questions; `aiwh spec check` before handoff.
5. Rebuilder in the clean container; verifier compares original and rebuild and ends with `RESULT wrong=<n> crash=<n>`.
6. Prove the oracle with three planted failures before trusting a green result ("test the oracle too").
7. Update `NOTES.md` and commit; `aiwh resume` reports evidence status and suggests the next `/goal`.

Effort per phase (see `capabilities/routing/model-policy.json`): read medium, spec high, verify xhigh, pointer-heavy code max.

## 4. Study material

- **Courses:** pwn.college reverse engineering and Reversing Hell, OpenSecurityTraining2 x86-64, Malware Unicorn RE101, Nightmare, RPISEC MBE, OWASP MAS, mytechnotalent Reverse-Engineering.
- **Books:** The Ghidra Book (2nd ed.), Reverse Engineering for Beginners, Practical Binary Analysis, Practical Malware Analysis, The Android Malware Handbook, Reversing: Secrets of Reverse Engineering.
- **Papers:** LLM4Decompile, AutoDecompiler, SALT4Decompile, Decomperson, DIRTY, Automatically Attacking Software RE Agents, and the REA post on model size.
- **Lists:** morluto/awesome-reverse-engineering, rea-gems, awesome-reverse-engineered, awesome-reversing, reverseengineering-reading-list.
- **Tool order (identify -> read -> run -> open -> traffic):** Detect-It-Easy, capa, ImHex, LIEF -> Ghidra, GhidraMCP, angr -> Frida, objection -> jadx, Apktool, ILSpy, asar -> mitmproxy, Wireshark.
