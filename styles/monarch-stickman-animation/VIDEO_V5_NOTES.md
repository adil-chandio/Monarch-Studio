# v5 — THE CLEAN BUILD

`stickman_money_37s_v5.mp4` · 1080×1920 · 30 fps · **37.00 s** · 10.62 MB
sha256[:16] `4c32783101d4c113` · −11.3 LUFS · stereo 48 kHz · decode-clean

---

## 1. What changed vs v4

| | v4 | **v5** |
|---|---|---|
| character | chalk stroke stickman | **filled 2D vector cartoon** — matches `STICKMAN EXPLAINER ENGINE.pdf` |
| background | dark board, grid, doodles, particles | warm paper + **one** soft accent field |
| elements/frame | 20–30 | **5–8** |
| transitions | 5 different FX kinds | **one** two-tone colour swipe, every cut |
| audio | 748 mono events | **248 stereo ASMR events** |
| camera | zoom + drift + shake | slow push only, no shake |

The brief was *clean rakho, zyada cheezen nahi bharo*. v5 is built by **subtraction**.

## 2. Character — `src/toon.py`

Rebuilt from the reference sheet in your PDF.

* **Two-pass silhouette**: pass 1 draws every body part grown by `ow` px in near-black,
  pass 2 redraws each at true size in its fill colour. One unbroken contour, zero joint seams.
* White rounded-square head (superellipse n=2.7), dark-brown swept hair, solid black oval
  eyes, light-grey collared shirt with rolled sleeves + buttons, charcoal trousers,
  white sneakers with grey soles, **solid black mitten hands**.
* 12 expressions, 12 poses. See `toon_character_sheet.png`.
* **Character colours never change.** Only the world is themed — that is what keeps it
  premium instead of cringe.

## 3. Layout — one locked grid, all six scenes

```
    0 –  150   chrome   (progress hairline + 01/06 chapter label)
  240 –  470   headline (1–2 lines, one word in the chapter accent)
  520 – 1080   graphic  (exactly one cluster)
 1080 – 1520   stage    (character, ground line GY = 1490)
 1550 – 1660   payoff   (one short line)
 1690 – 1760   caption
```
Nothing is ever drawn outside its band — that is why no text ever touches the character.
`foot_drop()` solves the leg chain analytically so the seated pose sits on the ground
instead of floating.

## 4. Chapter accents (muted, print-like — never neon)

| # | chapter | accent |
|---|---|---|
| 1 | PROBLEM | coral `226,85,70` |
| 2 | SKILL | blue `46,118,232` |
| 3 | TIME | violet `118,86,232` |
| 4 | PROOF | amber `226,118,48` |
| 5 | SELL | emerald `22,150,110` |
| 6 | GO | gold `214,158,44` |

Paper `248,244,233`, ink `26,24,22`. Three colours on screen, maximum.

## 5. Transition

A two-tone panel (thin ink bar leading a full accent panel) sweeps bottom→top.
Window is **centred on the cut**, so the full-cover frame lands exactly on the beat,
on the VO start, and on the impact/sub SFX. 0.40 s, identical every time.

## 6. ASMR audio — `src/make_asmr.py`

248 events, all stereo-panned. Ledger: `ASMR_EVENT_LEDGER.csv`.

* **No hard transients.** Every envelope is a raised-cosine attack (≥2.5 ms) into a
  smooth exponential tail. Nothing clicks.
* **Nothing above 9 kHz** survives the bus filter. Harsh air is what makes SFX feel cheap.
* Voices: soft bubble `pop`, fingertip `tap`, inharmonic glass `chime`, swelling `whoosh`,
  pure `sub` drop, `cloth`, granular `shimmer`, detuned `pad`, `pluck`.
* Bed: one warm chord per chapter, a sub pulse every 2nd beat (felt, not heard), a
  breathing filtered-noise room at −42 dB.
* Signature moment: scene 3's **30 day-ticks**, pitch rising 1300→2634 Hz, gain ramping,
  panned across the calendar grid as each cell fills.
* VO ducks the bed via `sidechaincompress` (thr .035 · ratio 7 · atk 8 · rel 300).

Every cue is locked to a reveal that actually happens on screen.

## 7. Timing — unchanged and frozen

| S | start | end | VO at | frames |
|---|---|---|---|---|
| 1 | 0.000 | 5.567 | 0.300 | 0–166 |
| 2 | 5.567 | 12.867 | 5.617 | 167–385 |
| 3 | 12.867 | 19.588 | 12.917 | 386–587 |
| 4 | 19.588 | 24.302 | 19.638 | 588–728 |
| 5 | 24.302 | 30.823 | 24.352 | 729–924 |
| 6 | 30.823 | 37.000 | 30.873 | 925–1109 |

Urdu VO atempo/adelay: 1.446/300 · 1.351/5617 · 1.441/12917 · 1.525/19638 ·
1.484/24352 · 1.487/30873.

## 8. Rebuild

```bash
python3 src/clean.py 0   555  build/c0.mp4      # ~1.5 min each, run in parallel
python3 src/clean.py 555 1110 build/c1.mp4      # 0.143 s/frame
python3 src/make_asmr.py                        # -> build/asmr_bed.wav
# concat -c copy, then the mux chain in this file's history
```
