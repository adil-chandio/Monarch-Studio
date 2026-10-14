# 16 · Complete failure → cause → fix → regression register



## L01 · Wrong artifact type

**Symptom:** A slideshow was substituted for a motion reference.

**Root cause:** Reference dynamics were not used as an acceptance constraint.

**Correction:** Inspect dense reference frames and actual changing source; separate subject motion from camera-only zoom.

**Evidence scope:** Reported prior V3 rejection + current reference/V2/V4 inspection

**Regression/review:** No-slideshow plan and source-motion review



## L02 · Codec/browser failure

**Symptom:** An earlier V3 master reportedly used yuv444p and did not play.

**Root cause:** Encoder pixel format was not explicitly constrained.

**Correction:** H264 High/yuv420p + AAC + faststart; full decode; download fallback while Drive transcodes.

**Evidence scope:** Prior transcript report; actual V5/V6 codec checks

**Regression/review:** Codec/faststart/full-decode gates



## L03 · Tiny translated overlays

**Symptom:** V4 left English, Instagram tags/end-card and tiny Urdu text.

**Root cause:** Audio replacement plus tiny overlay was treated as localization.

**Correction:** Clean source typography/tags; rebuild readable integrated titles; replace closing card.

**Evidence scope:** Direct V4 frame review

**Regression/review:** Readable-type and tag/outro review



## L04 · Unnatural pace / scene mismatch

**Symptom:** Global speed-up forced the dub into the English video timing.

**Root cause:** Picture duration was treated as fixed instead of honoring spoken phrasing.

**Correction:** Restore selected nine clips; trim quiet only; recut each semantic shot to natural 1.0x speech.

**Evidence scope:** Recovered audio and V5/V6 code

**Regression/review:** Original voice hash and pace gates



## L05 · Cloudy cleanup

**Symptom:** Large Telea patches made cloudy paper areas.

**Root cause:** Large opaque masks and restoration method interacted badly with grain/gradient.

**Correction:** Use shot-aware glyph masks and Navier–Stokes inpainting; inspect texture, not just text absence.

**Evidence scope:** Observed rejected repair experiment

**Regression/review:** Texture inspection; no claim of perfect restoration



## L06 · Missing pale objects

**Symptom:** Color-key/background replacement damaged hair, bulbs and thin supports.

**Root cause:** Pale foreground resembled the lavender background.

**Correction:** Reject destructive keyed matte; retain full changing footage and use non-destructive near/far maps.

**Evidence scope:** Rejected matte.py + preview findings

**Regression/review:** Silhouette, hair, strings, shoes and highlight review



## L07 · Wrong tag corner

**Symptom:** Masking both possible Instagram positions cut the talent stone.

**Root cause:** Tag placement was assumed instead of detected.

**Correction:** Template-match the actually active icon corner; erase its handle only.

**Evidence scope:** Observed V5 repair; match scores approximately 0.85–0.997 vs empty 0.10–0.21

**Regression/review:** Conditional-corner test/review



## L08 · Moving heading residue

**Symptom:** Animated headings moved outside static text masks; early 1915 strokes survived.

**Root cause:** A single settled-frame rectangle was used across entry animation.

**Correction:** Use time-dependent regions and inspect entry/exit frames, not just shot midpoint.

**Evidence scope:** Observed encoded V5 correction

**Regression/review:** Dense boundary samples



## L09 · Runner feet cut / SPRINT residue

**Symptom:** Broad early lower masks cut shoes; a later ramp missed top letter strokes.

**Root cause:** Mask timing ignored the runner’s abrupt rise before the lower title entered.

**Correction:** Protect early low shoes; clean the full lower title after source t>=25.70s in this case.

**Evidence scope:** Observed V5/V6 fixes; four V6 runner samples 32.10/32.23/32.35/32.46s

**Regression/review:** Case-specific threshold, not a universal rule



## L10 · Watch/flow and flow/car leaks

**Symptom:** Approximate source boundaries showed the next subject under the wrong sentence.

**Root cause:** Sparse sampling was mistaken for exact cuts.

**Correction:** Densely inspect cuts; measured source watch end 14.97s and flow end 21.03s.

**Evidence scope:** Observed repair

**Regression/review:** Semantic EDL boundary review



## L11 · Dark bag erased

**Symptom:** Purple sandbag was classified as title ink.

**Root cause:** Color alone cannot distinguish a prop from typography.

**Correction:** Protect the large connected subject component; apply masks only in intended zones.

**Evidence scope:** Observed repair

**Regression/review:** Bag/face/limb review



## L12 · Lost export after refresh

**Symptom:** Completed ignored MP4/runtime/dependency cache disappeared before upload.

**Root cause:** Receipts persisted but ignored media bytes did not.

**Correction:** Protect a bounded pending-upload spool; verify cloud copies before returning media to ignored storage.

**Evidence scope:** Actual workspace reset; V5 recovered byte-identically

**Regression/review:** Artifact-existence + size/hash delivery gates



## L13 · Premature presentation claim

**Symptom:** A parallel log said presented although present_file failed.

**Root cause:** Intent was logged before tool success.

**Correction:** Record presentation only after success; correct the journal on failed presentation.

**Evidence scope:** Actual corrected journal

**Regression/review:** Tool-result-first receipts



## L14 · Timeout mistaken for failure

**Symptom:** V6 process-log stream disconnected after stages had completed.

**Root cause:** Transport status can differ from process/artifact status.

**Correction:** Inspect process, PIPELINE_STATE, file and QA before any restart.

**Evidence scope:** Actual V6 stream error; filesystem proved exit 0

**Regression/review:** No-duplicate execution rule



## L15 · Completion archival trap

**Symptom:** Marking checkpoint status completed before CLI complete blocked archive.

**Root cause:** complete requires an active task in the legacy controller.

**Correction:** Archive via complete while active; add regression protection for completed checkpoints.

**Evidence scope:** Actual V5 archive workaround; V6 normal completion

**Regression/review:** Continuity lifecycle regression



## L16 · Technical pass is not style approval

**Symptom:** V6 passed technical checks but user rejected its lower caption pills.

**Root cause:** Readability metrics did not encode the preferred editorial hierarchy.

**Correction:** Latest feedback overrides experiments: integrated clean type default, no pill/word strip; keep originals as history.

**Evidence scope:** Explicit user feedback 2026-10-15

**Regression/review:** Caption-policy regression tests



## L17 · Repository validation noise

**Symptom:** Ignored virtualenv binaries and a CA certificate were scanned as repository files.

**Root cause:** Filesystem enumeration did not honor ignored dependency caches.

**Correction:** Validate commit-eligible files and tracked exceptions; preserve sparse-checkout behavior.

**Evidence scope:** Observed studio.py validation failure

**Regression/review:** Manifest/cache regression test



## L18 · False completeness risk

**Symptom:** Early scratch states/full pre-init conversation or V1–V3 editable sources were not all recoverable.

**Root cause:** Compacted chat and delivered filenames are not complete source archives.

**Correction:** Separate observed/reported/proposed facts; preserve available raw source and explicitly inventory gaps.

**Evidence scope:** Evidence boundary

**Regression/review:** Coverage and provenance audit
