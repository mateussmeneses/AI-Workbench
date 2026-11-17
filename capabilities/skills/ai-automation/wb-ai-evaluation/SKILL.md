---
name: wb-ai-evaluation
description: Use when evaluating LLM prompts, RAG retrieval, embeddings, or agent tool-use workflows for accuracy, latency, cost, and fallback behavior.
---

# AI Evaluation

## When to apply
- Measuring prompt, retrieval, or model-routing changes before shipping.
- Comparing local models (Ollama/ONNX) against deterministic baselines or cloud APIs.

## Procedure
1. Lock a fixed evaluation dataset of representative inputs, edge cases, and expected invariants (separate from training/tuning examples).
2. Define quantitative metrics: exact/semantic pass rate, p95 latency, token/VRAM budget, and structured-output schema validity.
3. Run the deterministic or baseline system first, then evaluate candidate prompts/models under identical seeds and temperature settings.
4. Inspect failure modes (hallucinations, schema violations, prompt-injection susceptibility, timeout/offline fallbacks) before tuning.
5. Record observed scores, dataset version, and hardware/model identifiers; never report mock adapter runs as live inference.

## Verification
- Reproducible evaluation script or fixture suite with pass/fail thresholds.
- Documented fallback behavior when the model or local runtime is unavailable.
