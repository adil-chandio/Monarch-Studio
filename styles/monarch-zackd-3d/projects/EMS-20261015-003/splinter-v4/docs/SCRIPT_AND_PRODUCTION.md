# KAANTA · Cinema Cut v4

WF-02 / Monarch Studio · 15 October 2026, Asia/Karachi

**30.5s · native1080×1920 · 30fps**. New v4 output, not an overwrite of the user-liked earlier versions.

## The correction

The user rejected unnecessary, cheap-feeling additions and requested a premium/professional reference-led image, restrained sound, cinematic buildup, smooth motion and purposeful 3D text. The direction is **subtraction and refinement**, not more badges, effects or bigger labels.

Removed: all HUD/chapter/counter/progress framing, caption boxes and coloured emphasis, warning panels, arrows, page-turn, large floating translucent pocket, decorative duct detail, UI pings, bells, caution stings and spring wobble.

Retained/refined: real moving 3D anatomy, the original Urdu narration, medical caution, measured gripper contact, smooth camera rails, selective cell motion, two short extruded-type beats and one clean motivated scene change.

## Narration — unchanged easy Urdu-English

**Hook / simple surface case**

Kaanta skin mein phans jaye, to body kya karti hai? Tip bahar ho, to nikaalna aasaan hota hai.

**Body response**

Lekin andar phans jaye, to defence cells uske gird jama hote hain. Soojan aa sakti hai. Infection ho, to peep bhi ban sakti hai.

**Possible movement, not a guarantee**

Kabhi chhota kaanta skin ki satah tak aa jata hai. Lekin har baar nahi! Iska intezaar mat karo.

**Safe ending**

Gehra kaanta, barhti laali, dard ya peep ho, to doctor se madad lo. Skin ko mat khodo.

### Actual text in the retained Urdu voice files

1. کانٹا سکن میں پھنس جائے، تو باڈی کیا کرتی ہے؟ ٹِپ باہر ہو، تو نکالنا آسان ہوتا ہے۔
2. لیکن اندر پھنس جائے، تو ڈیفینس سیلز اس کے گرد جمع ہوتے ہیں۔ سوجن آ سکتی ہے۔ انفیکشن ہو، تو پیپ بھی بن سکتی ہے۔
3. کبھی چھوٹا کانٹا سکن کی سطح تک آ جاتا ہے۔ لیکن ہر بار نہیں! اس کا انتظار مت کرو۔
4. گہرا کانٹا، بڑھتی لالی، درد یا پیپ ہو، تو ڈاکٹر سے مدد لو۔ سکن کو مت کھودو۔

Four previously selected/generated WAVs are retained without resynthesis or time-stretching. Their hashes are locked in `data/VOICE_LOCK.json`. Main placements:0.24,7.00,15.56,22.08s. Roman Urdu captions use refined phrase timings, not claimed word-level forced alignment.

## Shot discipline

| Time | What carries the shot | Editorial restraint |
|---|---|---|
|0–3.68s|Fingertip, wood, light/skin microtexture, slow push|Only a brief real3D `KAANTA` word; no header/brand frame|
|3.68–7s|Jaws approach, measured contact, controlled tension and extraction|Soft tactile close/release sound; no impact graphics|
|7–9.46s|Reveal a separate embedded-fragment case|One clean semantic cut, not a flipping card|
|9.46–11.70s|22 selected schematic defence cells gather on individual paths|Narration and actual movement; no label box/arrow|
|11.70–15.56s|Swelling/colour change and small conditional infection details|No large translucent shield or glowing alarm cues|
|15.56–18.98s|Possible outward movement, camera follows gently|Score develops without masking speech|
|18.98–22.08s|The no-guarantee reversal|Brief real3D `NAHI.`; music deliberately steps back, no warning badge/sting|
|22.08–25.83s|Warning signs explained in voice/captions|No competing triad of graphic panels|
|25.83–30.5s|Professional-care removal illustration and safe ending|Tool appears around the doctor sentence; quiet resolve, no victory chime/end-card spam|

The 9 chapter entries in `timeline.json` are not 9 on-screen headings. Camera/actor timings are in `motion.json`; palette/type treatment is in `design.json`.

## Sound and music

- Eight foley-inspired procedural textures: wood contact, two gentle metal closures, two soft releases, a restrained reveal air bridge, subtle cell texture and pressure texture.
- No reference sound is copied. Effects are not presented as literal recordings of microscopic biological events.
- Original piano/cello/string arrangement from individually credited FluidR3 note samples; restrained chord/motif progression and narration ducking, not a stock reference song.
- Music grows toward discovery/outward movement, provides space for “har baar nahi”, and resolves under the professional-care ending.
- Overall target −16LUFS with true-peak headroom. Actual final AAC measurements are in `data/QUALITY_REPORT.json`; pre-encode measurements are separate.
- “ASMR-style”, “cinematic” and “engaging” describe creative intent. No physiological reaction, audience-retention result or universal perfection is guaranteed by the measurements.

### Publishing credit — retain with the video

> Original score: Monarch Studio. Instrument samples: FluidR3 GM via MIDI.js Soundfonts (Benjamin Gleitzman), CC BY3.0 US. https://github.com/gleitz/midi-js-soundfonts — https://creativecommons.org/licenses/by/3.0/us/ . Samples arranged and processed for this film.

The upstream [README](https://github.com/gleitz/midi-js-soundfonts/blob/gh-pages/README.md) states the chosen FluidR3 sample library's CC BY3.0 licensing. The conversion software has a separate MIT license. Only selected instrument notes are reused; the score arrangement, processing and mix are new. Full attribution, sample hashes and upstream notices are included under `assets/music/`. Credits accompany the upload and source rather than being burned onto the clean picture.

## Provenance / honest technical scope

- Original user reference: [How Splinters Get Unstuck](https://drive.google.com/file/d/1zXgd_QnDbCcODXHyIwp4uzqRrQf0X03V/view). Recovered again for this revision because ephemeral runtime files were absent. File MD5 rechecked as `fb8eb1695788b96e0cfb81d43c077a21`; multiple visual beats were inspected, not claimed as an independent audio transcription.
- Base tissue model: existing [SPLINTER animated cutaway GLB](https://drive.google.com/file/d/1yfu7tZGut9LWcXidALvRlB9LdfxpMPM3/view), inherited through the user's v2/v3 project. It is not claimed as freshly modeled from scratch here.
- V3 parent: [KAANTA Motion Edition](https://drive.google.com/file/d/1Wl8S1M6jT3SNU6vEHJt9Kw3sePz0TH-i/view). Its source/master remain unchanged.
- V4 changes: minimal editorial treatment, new soft cell/adipose surface meshes, generic palmar micro-ridges, revised restrained materials/light, selective cut-face shadows/polygon-offset cleanup, fewer visible scene elements, revised non-oscillatory pulls, measured real extruded type and a new score/texture mix.
- Renderer: actual Three.js geometry, lights and camera animation, lossless native-pixel frame capture, H.264/AAC delivery. Hybrid physically based and direct-specular materials; not Blender/Cycles, ray-traced clinical simulation or AI still-plate animation.
- 915 frames are evaluated and rendered separately at30fps. No optical-flow interpolation or duplicated-frame conversion from v3's video.
- The original GLB remains Blender-importable, but the full v4 rig/cameras/type/material edit are in JavaScript and are not silently embedded into that earlier GLB. No `.blend` deliverable is claimed.
- True3D words are generated from the included licensed Montserrat font using fontTools and Three.js `TextGeometry`, with nonzero extrusion and separate face/side materials. They are not flat labels with a faux-3D outline.

## Medical boundaries retained

Some tiny shallow fragments can emerge with skin turnover or movement, but expulsion is not guaranteed and infection is not treatment. Organic fragments should not be left in the hope of pus forming. Deep/difficult fragments and increasing redness, pain or pus merit professional help. These are general educational points, not an individual diagnosis or procedure guide. [1](https://health.clevelandclinic.org/how-to-remove-a-splinter-and-when-to-call-the-doctor) [3](https://www.abc.net.au/news/health/2017-06-28/what-happens-if-you-dont-remove-a-splinter/8656250)

Scale, cell count, shapes and elapsed biological time are simplified for explanation. The palmar fingertip has no invented hair follicles. The forceps ending is paired with the doctor/help narration, not a recommendation to dig out a deep fragment. No clinician review is claimed.

## Delivery

[New Cinema Cut folder](https://drive.google.com/drive/folders/1Z2lk4C01uKThecQyUhbcYxINtUox34Q0), inside the confirmed [WF-02 parent](https://drive.google.com/drive/folders/1LTkHpkEUFSui8Lqyy8I0j5-1AceSziWX).

Final actual-master checks, encoded sample review, source/archive checksums and real upload IDs are recorded only after completion. Old versions are preserved. Final receipt accompanies the ZIP separately to avoid a self-referential archive hash.
