# 11 · Quality gates and acceptance

## Three separate questions

1. **Technical validity:** does the output decode, match its format and frame budget, and contain usable audio?
2. **Creative fidelity:** does it actually meet the reference/brief, preserve subjects and make the argument readable through motion?
3. **User acceptance:** does it respect the latest stated preferences, including the rejected V6 lower-caption treatment?

None implies the others. V6 passed technical checks and was delivered, yet its caption pills were later rejected. A reliable workflow records both facts instead of rewriting history as a perfect success.

## Required review dimensions

| Gate | Evidence required |
|---|---|
| Correct brief/meaning | Approved script and claim ledger, not just a matching title |
| Source/rights | Real source files, attribution, rights status and hashes |
| Actual motion | Source-only temporal inspection; captions/camera alone do not prove it |
| Subject integrity | Face/hand/hair/shoe/string/prop/shadow review at entry, peak and exit |
| Typography | Readable fitted type, sensible hierarchy, no subject collision or tiny paragraph |
| Caption preference | No V6 pills/word strip in the default; plain overlay only if requested |
| Voice continuity | Matching selected files/hash; no arbitrary speed-up or wrong-topic narration |
| Semantic sync | Scene and keyword changes follow the correct spoken clauses |
| Branding | No unwanted Monarch/Instagram tags or inherited social end card |
| Export | H264 High/yuv420p, AAC stereo 48kHz, intended dimensions/FPS |
| Frame integrity | Exact frame budget, no unexpected black/missing frames, complete decode |
| Web delivery | Early moov/faststart; honest Drive processing/download fallback |
| Audio | Final decoded levels/peaks and the actual listening/content-review scope |
| Version identity | Correct output hash; not a renamed old master |
| Recovery | Full required source or verified source bundle, not only a screenshot |
| Cloud receipt | Real remote IDs; independent size/hash comparison |
| Presentation | Actual viewer success, not a planned tool call |
| Continuity | Exact next action/process status; no duplicate work or hidden restart |

This is a new operating checklist, not a retroactive claim that an old master passed a numbered set of checks that was never run.

## What the reference releases measured

V5 and V6 each had 1,893 frames, 63.1s, 1080×1920, 30fps, H264 High/yuv420p plus AAC stereo, faststart and successful full decode. Forty-two encoded samples covered fourteen shots; a separate source-motion diagnostic inspected clips before the new type. V6 verified original voice hashes and a master hash different from V5. Additional closely spaced runner frames covered a known cleanup defect.

These samples are not a mathematical proof that every pixel in every frame is flawless. Noise or a global camera move can change pixel metrics; human/agent visual interpretation still matters. Do not call RMS “LUFS,” sample peak “true peak,” or character-weighted highlighting “word-perfect speech alignment.”

## Fail closed, not indefinitely

A failed objective gate blocks delivery. A missing asset/permission or tool-required voice selection is a genuine blocker and must be named precisely. When a fix is actionable, continue working through it rather than ending with a progress promise. Preserve good work and only rerun what the changed inputs require.
