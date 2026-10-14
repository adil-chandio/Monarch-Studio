# Monarch Stickman Animation

- **Style ID:** `monarch-stickman-animation`
- **Workflow contract:** WF-01
- **Trigger:** `SHADEGO <topic>`
- **Normalized state:** **PARKED**
- **Legacy resume key:** `best video reel editing`
- **Current authority:** IZZAT v2, delivered and measured 19/19
- **Default reply language:** concise Roman Urdu

## Style definition

This style produces premium hybrid stickman animation/editing with paper/ink texture, extruded/chrome typography, a controlled 3-D SHADE hero, designed sound and measured delivery gates.

- **Short mode:** normally vertical 1080×1920, 40–90 s, new visual information every 2–3 s, target around −11.6 LUFS.
- **Film mode:** normally horizontal 1920×1080, 120–300 s, sparse 7–14 s holds, at least three callbacks, two quotable lines, no CTA, target −16.5 ±1 LUFS.

The full-autopilot grammar is:

```text
SHADEGO <topic> | short|film | <n> s | voice: <note> | <special ask> | language: <lang>
```

Only topic-if-missing and the required voice-audition click are allowed questions. Explicit trigger options override defaults.

## Delivered lineage

The checked brain registry remembers six deliveries:

1. `money` v9
2. THE SLOWEST PREDATOR
3. POWER v1
4. SHADE v2
5. IZZAT v1
6. **IZZAT v2** — current WF-01 short authority
7. TUMHARI RESERVED SEAT (WF-01 16:9 + WF-03 noir, 2026-10-11)
8. **THE GRAVITY OF THE PHONE** — WTF-30 #1, 20 s vertical impossible-moment short (2026-10-14; v2 the same day: composed score, 96-voice sound design, upside-down moral; v3: vocal-chop hook, kick-synced picture pump, god-rays, afterimages, kinetic type, 180° world roll; v4: the phone is an Apple iPhone + the comment engine — 9:41 and racing clocks, Monarch-in-the-photo, the friend who points at you, the moth, steam that bends away, spiral light) → `films/gravity-of-the-phone/`

Current IZZAT v2 authority:

- Drive `1fu_g2HTNZVRqE3XBKdUKZoj6O8tIdkpu`
- MD5 `8d91be52ab969e0b23f21bf6bab0df85`
- 75.19 s, 1080×1920, 24 fps
- 33 shots, 32 transitions, 15 transition kinds
- −11.6 LUFS
- 19/19 renderer/audio/delivery gates

## Visual, edit and sound grammar

- SHADE identity is locked: hooded black suit, 3-D rig, hybrid paper/ink world; create new poses and metaphors, not a redesigned hero.
- Nothing should be perfectly still. Motion may be subtle parallax, push, depth, light, particles or slow motion.
- Low density and subtraction define premium execution.
- Captions remain inside the vertical safe area and measured width limit; contrast is at least 4.5:1.
- Transitions are individually designed, luma-traced, beat-ended, tint-not-flood, soft-edged over figure-dense shots and deliberately eased.
- SFX must vary; avoid consecutive repeats, mono treatment, radio/static texture and a static bed.
- Voice stays centered; bed may be wide; the VO bus is padded before sidechain.
- A new build may not reuse the preceding delivery's hook device, opening shot, ending or transition set.

## End-to-end process

1. Resume exact WF-01 identities and confirm state.
2. Activate Parked → Active across all authority records.
3. Run `brain/concept.py` proposals for short and film; select by novelty × hook strength × renderer feasibility.
4. Write timeline/renderer from the IZZAT v2 pattern.
5. Audition/synthesize voice, fit VO, build SFX/ASMR bed and mix.
6. Render sequential shards; do not run heavy renders in parallel on the historical 2 GB profile.
7. Run 19 workflow gates plus the cross-video EDITOR BRAIN novelty gate.
8. Produce a 12-frame contact sheet, notes and source package.
9. Commit to the brain registry only after gates pass.
10. Upload to Drive, verify remote MD5, and update GitHub/Drive/Notion/Linear/Google Docs through the continuity outbox.

## Implementation map

| Path | Purpose |
|---|---|
| `SHADEGO.md` | full trigger/autopilot contract |
| `RESUME_STATE.md` | current imported workflow state; newest block wins |
| `brain/concept.py` | proposal, cadence, novelty gate, commit/export CLI |
| `brain/registry.json` | six-delivery concept memory |
| `src/respect2.py` | current picture renderer pattern |
| `src/timeline_respect2.py` | current IZZAT v2 timeline |
| `src/gate_respect2.py` | 19-check gate implementation |
| `src/vo_fit.py` | voice timing/fit utility |
| `src/make_asmr_respect2.py` | ASMR bed generation |
| `src/mux_respect2.sh` | final mux/mix pattern |
| `VIDEO_RESPECT_NOTES.md` | IZZAT version notes |
| `MONARCH_SKILL_MOTION_EDIT.md` | motion/edit skill ledger |
| `DRIVE_MANIFEST.md` | original detailed Drive ledger |
| `knowledge/INDEX.md` | permanent knowledge catalogue |

## Portable execution

Historical scripts use `/home/user` as their root. Never mass-edit the certified source. The studio hydrator rewrites paths only in a generated compatibility copy:

```bash
python3 ../../tools/studio.py hydrate wf01
python3 ../../tools/studio.py run wf01 -- python3 brain/concept.py status
```

Generated runtime lives under `.runtime/wf01/` and is ignored.

## Known historical traps

- Sandbox package/process state did not persist between production turns.
- x264 bytes vary across versions; remote MD5 is the delivery identity.
- Sprite-cache keys must be quantized to avoid memory growth.
- Large multi-input FFmpeg graphs can OOM on 2 GB; use sequential/streaming work.
- `_dirv` swing above 90° flips; black cloth needs explicit rim/fill.
- Pillow `alpha_composite` rejects negative destinations.
- Zoom below 1 can produce black slivers.
- Transitions must end on the beat.
- The original speech environment allowed at most ten clips per turn.

Source hubs and exact IDs are in [`../../docs/SOURCE_MAP.md`](../../docs/SOURCE_MAP.md). Do not mix in WF-02 despite overlapping naming.