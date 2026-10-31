# Game Reverse Engineering & Porting

AI Workbench offers a read-only, evidence-based project intake. It distinguishes byte-matching decompilation, static recompilation and compatibility-runtime engineering, with platform-specific tool selection.

## Select the right technical track

| Track | Purpose | Required verification |
|---|---|---|
| `matching-decomp` | Recover C/C++ reproducing the original compiler's machine bytes | Matching object/function output with the original toolchain |
| `static-recomp` | Translate a game's original ISA to native host code | ISA/ABI, runtime imports, rendering, audio, inputs and timing |
| `compatibility-runtime` | Run already-compatible CPU code with replacement OS/GPU interfaces | Runtime services, shaders, frame pacing, gameplay regression tests |
| `triage` | Gather evidence before deciding a track | Verify platform/build and define desired outcome |

**Matching decompilation is not automatically a finished PC port.** A byte-identical function doesn't establish GPU or OS compatibility.

## CLI examples (PowerShell)

```powershell
aiwh game-port "C:\projects\n64-port" --binary "C:\games\sample.z64" --track matching-decomp
aiwh game-port "C:\projects\n64-port" --binary "C:\games\sample.z64" --track static-recomp --json
aiwh game-port "C:\projects\ps4-port" --platform ps4 --goal "Fix Vulkan shader stutter"
aiwh game-port "C:\projects\ps3-port" --platform ps3 --track static-recomp --save
aiwh recommend "C:\projects\ps3-port" --area game-port --area recompilation --json
aiwh init "C:\projects\ps3-port" --agent hermes --area game-port --area recompilation --dry-run
```

By default, `aiwh game-port` does not write files. With `--save`, it creates `.ai-workbench/GAME_PORT_PLAN.md` containing the assessment for Codex/Hermes. This directory is excluded from Git by Workbench bootstrap. No ROM/executable contents are copied.

## Evidence and uncertainty

The detector reads at most **4,096 bytes** from the supplied executable/ROM/disc and records only the observed signature, architecture, size and SHA-256 of **that inspected prefix**. This is not a full-file hash or a unique build fingerprint.

Recognized evidence includes Nintendo 64 ROM byte-order variants; PS-X EXE; Xbox 360 XEX2; GameCube/Wii disc markers; Windows MZ/PE; ELF machine architecture; PSP PBP and ambiguous Sony SELF. An x86-64 ELF alone is not proof of PS4; neither is a PowerPC ELF proof of PS3. Filename extensions are not trusted. Manual `--platform` declarations are labeled and conflicts with verified signatures are rejected.

## Tool references (curated, never installed automatically)

| Platform / objective | Repository | Maturity / limitations |
|---|---|---|
| Older consoles, matching decomp | [decompdecomp](https://github.com/n-delic/decompdecomp), [decomp.me](https://github.com/decompme/decomp.me), [objdiff](https://github.com/encounter/objdiff) | Recover and verify functions, not push-button native porting |
| Nintendo 64, static recomp | [N64Recomp](https://github.com/N64Recomp/N64Recomp) | Game-specific host runtime required |
| PlayStation 1, static recomp | [PSXRecomp](https://github.com/RetroPortingToolKit/psxrecomp) | Experimental |
| PlayStation 2, static recomp | [PS2Recomp](https://github.com/ran-j/PS2Recomp) | Experimental, EE/VU and graphics integration required |
| PlayStation 3, static recomp | [ps3recomp](https://github.com/sp00nznet/ps3recomp) | Experimental and title-dependent |
| Xbox 360, static recomp | [XenonRecomp](https://github.com/hedge-dev/XenonRecomp), [ReXGlue](https://github.com/rexglue/rexglue-sdk) | Project-specific runtime and subsystem engineering |
| PlayStation 4, compatibility runtime | [shadPS4](https://github.com/shadps4-emu/shadPS4) | Emulator/runtime research reference, not a port generator |

Current `decompdecomp` helper agents run inside its own application. Legacy `decomp.wtf` commands `decomp mcp` and `decomp connect` are no longer the correct integration approach. `github` and `context7` MCP servers are suggested, not configured.

## Hermes/Codex handoff

After `--save`, the agent should read `AGENTS.md`, `AI-WORKBENCH.md` and `.ai-workbench/GAME_PORT_PLAN.md`. Select only relevant skills. Keep observed header evidence separate from user-declared platform. Record a complete original binary checksum and build ID separately, verify offsets/RVA against disassembly and run narrow, reproducible tests. Do not publish proprietary game data or secrets.

## Scope

This milestone recommends an appropriate development path; it does **not** run, decompile, recompile, port, patch or validate any actual commercial game. Compatibility remains title-specific.
