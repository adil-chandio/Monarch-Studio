# MINDSET · Monarch Zack-D 3D Power (WF-02)

## Identity

Real 3-D, rendered frame by frame in Blender Cycles, 9:16 vertical. Concept: 20 minutes × 90 days = 30 hours, shown as one cube per second building a tower, with extruded 3-D text "30 HRS". Look: chrome and gold metal, cyan neon, hard cuts, whip-style angle changes. Narration: same script as the Tumhari Reserved Seat film, Roman Urdunglish, accent-corrected voice-02 (ur-PK) after the voice-00 demo.

## Non-negotiables (from the user, in their words where possible)

- "Video images se nahi, real 3-D, frame by frame. Har second mein animation."
- "Jugaad / churane wala" approach is rejected.
- Same topic and script as the source film.
- "Tabahi, next level, premium, elite." Not cheap, not cringe.
- Each style has its own editing, animation and sound. WF-02 must not look like WF-01 or WF-03.
- Never claim premium or finished before a frame-by-frame check. Record the check in VIDEO_LOG (the review field and the status: reviewed, accepted or rejected).
- Use only open-source tools and allowed hosts. No HuggingFace, no blocked mirrors.
- Procedural sound (numpy) by default. Sample libraries only with a licence the user supplies.

## What premium means here (measurable, not vibes)

1. Chrome reads as chrome: visible reflections of an environment, not a black blob. Needs a gradient world, not a flat colour.
2. Neon reads as neon: emission in the 1 to 3 range under AgX. Above about 3 the text turns into white blocks.
3. Text is legible at 9:16 on a phone: the word "30 HRS" fills the upper third and is readable at 270×480.
4. Every second has motion: one cube lands per second, the camera moves between cuts, the light moves.
5. Cuts land on the audio beat: cut boundaries at 0 / 2.5 / 5.0 / 7.5 s in v2 (keep or justify changes in STRATEGIES).
6. No geometry tells: no floor edge at low angles, no visible area-light planes, no clipped text at the top.

## Judgement rules

- Lookdev at the time the key element is on screen (the text reveals at 6.5 s, so check at 9.5 s). A lookdev at 3.5 s shows four cubes and looks broken. It is not broken.
- A still that looks dark or grey is a failed still, even if the code runs.
- Fix one variable per lookdev iteration and log it in VIDEO_LOG.
