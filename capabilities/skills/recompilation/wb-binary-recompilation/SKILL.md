---
name: wb-binary-recompilation
description: Use when building or debugging static recompilation pipelines, lifted IR/C translation, ABI shims, and runtime parity checks.
---

# Binary Recompilation

## When to apply
- Lifting native machine code (MIPS, PowerPC, ARM, x86) into portable C/C++ or LLVM IR.
- Resolving register-state mismatches, endianness bugs, or OS/SDK shim divergences in a recompiled target.

## Procedure
1. Verify container format, memory map, relocations, and entry symbols before generating lifted code.
2. Separate generated lifted functions from hand-written runtime/OS shims so regeneration never overwrites manual fixes.
3. Model calling conventions, stack frames, status flags, and endianness explicitly at every shim boundary.
4. Instrument differential/oracle tests comparing lifted function outputs and memory side effects against reference traces.
5. Isolate graphics/audio/input backend translation into replaceable abstraction layers rather than hardcoding host APIs.

## Verification
- Differential state checks pass on deterministic test inputs for modified functions.
- Re-running the lifter produces reproducible output without clobbering shim code.
