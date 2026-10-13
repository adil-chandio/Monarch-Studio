# NEXT LEVEL · Monarch Zack-D 3D Power (WF-02)

Prioritised backlog. Edit this file by hand as priorities change. Log the result of each item in VIDEO_LOG when it is done.

## P1 · Make the look real

1. **Gradient or HDRI-style world** so chrome and gold reflect something. Flat grey or dark blue kills the metal. Target: bright sky top, dark floor, one warm and one cool reflection band.
2. **Neon calibration.** Keep emission in 1 to 3 under AgX. Use a bloom-free base colour so the text stays readable. Check at 9.5 s.
3. **Text hero.** "30 HRS" should fill the upper third at 270×480. Test extrude depth and bevel. Use one bold font with a clean bevel.

## P2 · Make the motion Zack-D

4. **Whip cuts.** Rotational camera move over 6 to 8 frames before each cut, with motion blur on. Confirm Cycles motion blur cost first.
5. **Cube rhythm.** Cube landings on the 1 Hz beat, with a small settle and overshoot. Keep the drop height the same for every cube.
6. **Light movement.** Rim light sweeps across the tower during each shot.

## P3 · Make the sound and the edit

7. **Sound design.** 1 Hz pulse, whoosh per cut, a low bed under the reveal. Procedural only.
8. **Narration sync.** Align the voice-02 cues to the cut boundaries.

## P4 · Make the process fast

9. **Measured per-frame time** at 360×640 / 48 spp. Without this number a 240-frame run cannot be planned.
10. **Resumable full render** with a frame skip check (already in wf_scenes CLI). Verify on a 10-frame run first.

## Done (keep for history, do not delete)

- Tower spacing changed from 1.05 to 1.25 for readability. Lookdev only.
- Cube reveal and text reveal timing confirmed in code.
