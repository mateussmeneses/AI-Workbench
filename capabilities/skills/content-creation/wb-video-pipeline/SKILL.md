---
name: wb-video-pipeline
description: Plan and build reproducible short-form video pipelines - script, voice, visuals, editing and publishing - with licensing checks
---

# Video Production Pipeline

## Rights first
Confirm rights for every input: footage, music, fonts, voices and generated media. Voice cloning requires the speaker's consent. Label AI-generated or synthetic content where platforms or law require it.

## Procedure
1. **Brief** - audience, platform (aspect ratio, max length, caption style), hook, call to action and success metric.
2. **Script** - beats with timestamps; keep a source list for factual claims.
3. **Voice** - choose recorded narration or local TTS (e.g. Kokoro); pin the model/version and export WAV at a fixed sample rate.
4. **Visuals** - stock/licensed footage, screen captures, code-driven motion graphics or generated images; keep an asset manifest with source and license per file.
5. **Assembly** - scripted (FFmpeg, MoneyPrinterTurbo-style pipelines) for batch output or an editor (OpenCut) for manual polish. Version the project file and render settings.
6. **Captions and QA** - burn-in or sidecar subtitles; check loudness (around -14 LUFS for most social platforms), safe areas, spelling and timing on a real device.
7. **Publish and measure** - export per platform, record upload metadata and collect retention metrics for the next iteration.

## Deliverables
Script, asset manifest with licenses, reproducible render command/project, final exports and a short performance review.

Do not assume tools, accounts or credentials are available; propose them for user approval.
