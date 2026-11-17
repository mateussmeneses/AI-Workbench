---
name: wb-decompilation-research
description: Use when reconstructing readable C/C++ from compiled binaries with matching-decomp or functional-decomp workflows and symbol recovery.
---

# Decompilation Research

## When to apply
- Recovering function signatures, structs, vtables, and control flow in Ghidra/IDA/Binary Ninja/decomp.me.
- Working toward byte-exact matching compilation or clean, verifiable C equivalents.

## Procedure
1. Identify the exact compiler, version, optimization flags, and ABI from headers, CRT startup, or build artifacts.
2. Recover data types, struct layouts, and global/rodata references first so decompiled pseudocode reflects real types.
3. Work function-by-function from leaf helpers upward, naming symbols from verified strings, assertions, or debug metadata.
4. For matching decomp, compare compiled object disassembly/bytes against target slices iteratively using diff tools.
5. Document compiler quirks, unverified type guesses, and register-allocation workarounds with exact addresses.

## Verification
- Reconstructed code compiles cleanly under the target compiler/flags without undefined behavior.
- Match percentage or behavioral equivalence checks are recorded per function.
