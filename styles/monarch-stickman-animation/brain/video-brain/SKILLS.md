# Monarch Stickman Animation (WF-01 Paper Cinema) · video brain

Style `monarch-stickman-animation` · workflow WF-01. Created 2026-10-13 03:17 PKT.

## Skills (append-only)

Use `tools/brain.py` to add entries. Do not edit old entries.
## K-001 · 2026-10-13 · Raking light for paper layers

- **When to use:** Paper or card layers need depth
- **How:** Narrow area light, low angle, size about 2.5, energy about 380 at 6 m. Wide bright lights wash out
- **Evidence:** Lookdev r2_wf01 vs wf01_v2

## K-002 · 2026-10-13 · Three-plane parallax with camera slide

- **When to use:** Paper cinema shots
- **How:** Three planes at different depths. Camera slides on a sine ease per cut
- **Evidence:** Lookdev r3_wf01_t6 shows depth

## K-003 · 2026-10-13 · Texture a cube face for paper cards

- **When to use:** Printed paper or timetable textures on Blender cards
- **How:** Generate the PNG with PIL in the render venv. Pre-rotate it by 90 degrees (ROTATE_90) to match the cube UV. Card = thin cube with a Bevel modifier (width 0.004, 2 segments) for edge highlight
- **Evidence:** lookdev r7b orientation corrected

## K-004 · 2026-10-13 · Run the respect2/3 pipeline outside the repo

- **When to use:** Any SHADE short rebuild
- **How:** Make /home/user/src (repo src), /home/user/fonts (repo fonts), /home/user/build and /home/user/assets (in /tmp) as symlinks. Put PATH=/tmp/venvs/render/bin first. Shards: python3 src/respect2.py A B out.mp4, about 0.35 s per frame at 1080x1920
- **Evidence:** 48-frame test shard rendered in 19 s, output 1080x1920 30 fps

## K-005 · 2026-10-13 · cut-safe camera blend

- **When to use:** any shot-based edit with a per-shot camera (zoom, pan) and a transition between shots
- **How:** in the transition window, blend the two cameras, each evaluated at its own shot progress u (clamped), with the same eased p as the picture. Never take the new shot's u=0 camera at the cut
- **Evidence:** motion-energy spike 17.4 at the cut removed; max camera step 0.0075/frame

## K-006 · 2026-10-13 · wide stereo from a mono-heavy mix

- **When to use:** stereo corr above 0.8 after music + TTS mix
- **How:** Haas 14 ms on the wide layers, detuned L/R pads, then ffmpeg extrastereo=m=3.0 on the mix (side only; mono sum unchanged). Check mid RMS before/after
- **Evidence:** lr_corr 0.95 -> 0.648; mid RMS unchanged 3334.67 before/after

## K-007 · 2026-10-14 · gate-safe impact moments (punch + flash without luma steps)

- **When to use:** Adding slams, flashes, lightning, confetti bursts or camera punches to a video that must pass max_dluma<8 and jerk_p95<2
- **How:** 1) Every added element gets a fade-in of at least 3 frames (shockwave, confetti, dust, flash ramp 5 up / 10 down). 2) Camera punch envelope: 0.10 s attack then exp decay (tau .19) - instant zoom = jerk. 3) Suppress punches inside transition windows (_trans_at) so they never stack on a cut. 4) Flash peak <= .10 of white, and never put a flash at the frame where the luma already jumps. 5) Probe with render() downscaled to 180x320 grey around each moment (dluma=|diff mean|, jerk=|diff diff motion|) before the full render; keep each < 6 to leave headroom for encoding.
- **Evidence:** kutta2.py v9 punch_at/flash_at + cinema9.ramp/punch_env; probes went crown 9.45->5.84, thunder 9.26->5.15, hook->luxury tunnel 10.9->5.48 (tunnel_long + bloom thresh 185)

## K-008 · 2026-10-14 · designed synth SFX when sample packs are unreachable (sfx9.py)

- **When to use:** Sandbox egress blocks Drive/raw hosts so licensed samples cannot be fetched, or a new cue has no sample
- **How:** sfx9.synth(name, amp) builds 48 kHz mono float32 designs from primitives (sine/sweep with exp decay, band-passed noise bursts, FM metal, sub drops): braam, impact, coin, confetti, thunder, sub_drop, stamp_ring plus the pack names (crack_flash, riser_click, digital_click, modern_shutter, gleam, conjure_charge, lighter_ignite, synth_sparkle). mux_kutta2._lib() falls back to sfx9 when /home/user/build/sfx_lib2/<name>.wav is missing and prints which names were synthesised. Rain = gusting droplet bursts (median-flatness safe at 0.42 per sheet); whoosh_air sits under the tonal sweep at .26.
- **Evidence:** mux_kutta2.py v9 run: 'synth SFX used (pack samples absent): [...8 names]'; mix LUFS -12.2, TP -2.0, bed flatness median 0.078

