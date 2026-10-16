# 10 · Production runbook

The ten steps from a topic to a published episode. Nothing here is optional and
nothing here needs a decision the doctrine has not already made.

---

### 0 · Environment (once per sandbox)

The virtualenv is **not** snapshot-persisted; rebuild it.

```bash
python3 -m venv /home/user/.venv
/home/user/.venv/bin/python -m pip install pillow numpy imageio imageio-ffmpeg opencv-python-headless
```

There is no system ffmpeg and no system font on this box. `imageio-ffmpeg`
provides the binary; fonts come from `assets/fonts/`.

---

### 1 · Brief (A01)

Three lines: the topic, the length, and the one feeling the viewer must leave
with. The audit's topic hierarchy applies — bears first (54 % of channel
views), then the family that surrounds it.

---

### 2 · Research and claims (A02)

Lock the numbers **before** a word of script exists. Write `CLAIMS.md`:

| claim | value | source | on screen? |
|---|---|---|---|

Every row that will be said out loud or drawn in a chart needs a source here
first. This is the file A07 audits.

---

### 3 · Script and shot plan (A03)

Write the script, then convert it into `PLAN.json`:

```jsonc
{
  "episode": "MF-02",
  "look": "nocturne",
  "audio": { "bed": {...}, "cues": [...] },
  "shots": [
    { "id": "01", "plate": "01_hook_charge.jpg", "dur": 4.2,
      "depth": {"mode": "hybrid", "rect": [0.18,0.16,0.86,0.98]},
      "cam": {"zoom":[0.030,0.090], "orbit":26, "roll":0.45, "ramp":"linear"},
      "fx": {"rays":0.20, "motes":80, "impact":[0.05], "shake":9},
      "transition_in": "hard",
      "type": [ {"kind":"headline","text":"40 METRES.","accent_word":"40",
                 "in":0.10,"out":2.4,"anim":"extrude_tilt"} ] }
  ]
}
```

Rules that the gates will enforce, so decide them here:

- **Hook.** Frame 1 is already in motion; the visual question lands by 0.8 s;
  a contrast spike by 1.0–1.5 s; the promise by 3 s.
- **Cadence.** Something new every 2–3 s (a beat, not merely a cut); a pattern
  interrupt about every 6.5 s; a set-piece per chapter.
- **Re-hooks at 25 / 50 / 75 %** — an open loop, a callback, or a reversal.
- **Durations** come from the measured narration, not from a target runtime.

---

### 4 · Plates (A05)

One generated plate per beat. The plate must contain, by construction, the
depth cue the engine will read: **the subject sharp and lit, the environment
soft**. A plate that fights the depth heuristic will parallax badly, and no
post-process repairs that.

---

### 5 · Narration (A04)

Synthesise the voice, then **measure it** before building the picture. The
picture is cut to the voice; the voice is never time-stretched to fit a
runtime. `atempo` on narration is the single biggest giveaway of an
AI-assembled video.

---

### 6 · Render (A05)

```bash
cd styles/monarch-wild-cinema
/home/user/.venv/bin/python src/run_film.py \
    --plan projects/MF-02/PLAN.json \
    --out-dir projects/MF-02/build \
    --vertical
```

Produces `picture.mp4`, `score.wav`, `master.wav`, `<EP>_MASTER.mp4`,
`<EP>_VERTICAL.mp4`, `TIMELINE.json` and `BUILD.json`. The intermediate picture
is encoded near-lossless and cheap on purpose; the delivery master is encoded
once, at mux time (failure register T06).

---

### 7 · Gate (A07)

```bash
/home/user/.venv/bin/python src/tabahi/gates.py \
    --master projects/MF-02/build/MF-02_MASTER.mp4 \
    --plan projects/MF-02/PLAN.json \
    --out projects/MF-02/build/GATES.json
```

14 gates. `UNMEASURED` fails. A deliberate failure requires a recorded human
override naming the gate, the measured value and the reason.

---

### 8 · Package (A06)

```bash
/home/user/.venv/bin/python src/tabahi/thumbs.py \
    --plates assets/plates --out-dir projects/MF-02/build/thumbs
```

Then the package document: three title options with the recommendation
first, the description with the SOURCES block, the pinned comment, the end
screen chain, and the vertical/Shorts slices.

---

### 9 · Publish (human)

Download the master, upload, choose the title and thumbnail, paste the
description, set the schedule — and answer **"Altered or synthetic content" =
YES** whenever generated plates or synthesised narration are in the cut.

---

### 10 · Learn (A08)

At 48 h, 7 d and 28 d, pull CTR, average view duration, retention at the hook
and at any beat the plan flagged as weak, and the traffic sources. Every read
becomes either a rule change in this style or a new entry in the failure
register. A measurement that changes nothing was not a measurement.

---

## Post-mortem, three questions, every episode

1. Which second would a stranger scroll on, and why?
2. Which rule did the measurements prove wrong?
3. What did we build that the library did not already have?

Each answer becomes one new rule or one new library item. **The library must
grow faster than it is consumed — that is the entire point.**
