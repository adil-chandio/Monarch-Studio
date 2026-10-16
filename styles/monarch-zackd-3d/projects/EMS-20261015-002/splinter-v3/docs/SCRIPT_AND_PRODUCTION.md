# KAANTA
## Skin ke andar kya hota hai?

**Monarch Studio · WF-02 · 3D anatomical explainer · Motion Edition v3**  
**Production date:** 15 October 2026, Asia/Karachi  
**Format:** 30.5 seconds · 1080 × 1920 · 30 fps  
**Narration:** Urdu with familiar English terms · user-selected current-session voice  
**Captions:** easy Roman Urdu-English

## Easy Urdu-English script

Kaanta skin mein phans jaye, to body kya karti hai?

Tip bahar ho, to nikaalna aasaan hota hai.

Lekin andar phans jaye, to defence cells uske gird jama hote hain. Soojan aa sakti hai. Infection ho, to peep bhi ban sakti hai.

Kabhi chhota kaanta skin ki satah tak aa jata hai. **Lekin har baar nahi! Iska intezaar mat karo.**

Gehra kaanta, barhti laali, dard ya peep ho, to **doctor se madad lo. Skin ko mat khodo.**

## Actual text used for Urdu speech

### 01 · Hook and surface case
کانٹا سکن میں پھنس جائے، تو باڈی کیا کرتی ہے؟ ٹِپ باہر ہو، تو نکالنا آسان ہوتا ہے۔

### 02 · Embedded fragment and response
لیکن اندر پھنس جائے، تو ڈیفینس سیلز اس کے گرد جمع ہوتے ہیں۔ سوجن آ سکتی ہے۔ انفیکشن ہو، تو پیپ بھی بن سکتی ہے۔

### 03 · Possible movement, not a promise
کبھی چھوٹا کانٹا سکن کی سطح تک آ جاتا ہے۔ لیکن ہر بار نہیں! اس کا انتظار مت کرو۔

### 04 · Safety ending
گہرا کانٹا، بڑھتی لالی، درد یا پیپ ہو، تو ڈاکٹر سے مدد لو۔ سکن کو مت کھودو۔

## Edit / shot plan

The nine narrative chapters stay, but **six internal camera resets have been removed**. From 7 seconds onward the camera follows one continuous C2 rail through the chapter markers. One intentional hand-to-cutaway scene change remains at 7 seconds, now covered by a 0.6-second perspective turn-over using the actual moving frames. All 32 cells have arrived by 10.69 seconds, during the gathering sentence. Read `data/motion.json` for editable keyframes and grip/release cues.


| Time | Animated picture | Explanatory purpose |
|---|---|---|
| 00.00–03.68 | New procedural fingertip with protruding wood; moving macro camera | Immediate same-topic hook |
| 03.68–07.00 | Steel forceps approach, close and withdraw the exposed fragment | Establish the superficial case; caption identifies clean tweezers |
| 07.00–09.46 | Hard cut into a second, embedded-fragment example; moving layered-skin cutaway | Distinguish the two examples rather than reinserting the removed splinter |
| 09.46–11.70 | Immune-cell geometry moves inward and changes shape; camera pushes closer | Defence cells gather around a foreign object |
| 11.70–15.56 | Skin dome deforms with corrected lighting normals; localized redness; conditional creamy debris | Inflammation and possible infection are not presented as identical |
| 15.56–18.98 | Fragment moves toward the surface; restrained upward annotation | Explicitly **possible**, time-compressed motion, not a prediction |
| 18.98–22.08 | Moving cutaway beneath a clear “HAR BAAR NAHI” warning | Do not wait for infection or a guaranteed expulsion |
| 22.08–25.83 | Cutaway and three warning-sign callouts | Deep fragment, increasing redness, pain or pus need attention |
| 25.83–30.50 | Forceps withdrawal labelled professional-care illustration; “Skin ko mat khodo” ending | End on safer action, not a DIY deep-extraction tutorial |

Subtitles are phrase-timed to the four generated speech clips, not a claim of word-level forced alignment. `data/timeline.json` is the timing authority; the SRT follows the burned-in captions.

## Reference study and lineage

- Supplied reference: **How Splinters Get Unstuck**, Drive file [`1zXgd_QnDbCcODXHyIwp4uzqRrQf0X03V`](https://drive.google.com/file/d/1zXgd_QnDbCcODXHyIwp4uzqRrQf0X03V/view). Its native metadata is 1080 × 1920, approximately 30.36 seconds, 29.97 fps.
- The reference was inspected visually through extracted frames and its visible English captions. This is **not** a claim of independently transcribing the original audio.
- The live WF-02 folder already contained a **SPLINTER — Monarch 3D** project. Its animated GLB, [`1yfu7tZGut9LWcXidALvRlB9LdfxpMPM3`](https://drive.google.com/file/d/1yfu7tZGut9LWcXidALvRlB9LdfxpMPM3/view), was recovered and reused. Layered tissue, vessels, sweat ducts, fat, cells, cutaway splinter and cutaway forceps derive from that asset. They are **not newly modelled from scratch in this task**.
- V2 base is retained: the fingertip, tissue geometry, licensed font, Urdu voice WAVs and medical explanation. New in v3: C2 continuous camera rails, a joined/beveled forceps rig with actual jaw closing, local fingertip deformation, controlled resistance/release, newly timed curved cell paths, smoother swelling/annotations, phrase-timing refinements, native 30fps and 23 new original sound-design cues. The original v2 is preserved unchanged.
- No reference video frames, original narration, original soundtrack or original creator logo are embedded in the new film. No AI-generated still-image plates are used.
- The human pad cutaway intentionally has no hair follicles; coiled sweat ducts are retained. Cells and tissue proportions are enlarged/simplified for legibility.

## Medical accuracy boundaries

**Educational visualization, not personalized medical advice or a clinically validated simulation.** Shapes, scale, color and time are illustrative.

Very small, shallow, painless splinters can sometimes emerge with natural skin shedding. Deeper, painful and organic fragments are not things to leave in place waiting for this to happen. Infection signs such as redness, swelling or pus are reasons to seek care. [1](https://health.clevelandclinic.org/how-to-remove-a-splinter-and-when-to-call-the-doctor)

Immune-cell migration and a local reaction may also contribute to expulsion, but a retained fragment can instead remain or be walled off. The outward arrow shows a possible outcome, **not a measured pressure vector or a reliable treatment**. [3](https://www.abc.net.au/news/health/2017-06-28/what-happens-if-you-dont-remove-a-splinter/8656250)

The video therefore does **not** claim that wood dissolves, that pus is desirable, that every splinter comes out on its own, or that the illustrated event happens within a specified number of hours. The final deeper-fragment extraction is explicitly labelled a **professional-care illustration**.

## Honest technical description

- Both moving 3D and typography are rendered at **native 1080 × 1920**. There is no 720p enlargement, frame interpolation or duplicated-frame conversion to fake a higher frame rate.
- **30 fps, 915 individually rendered frames**, 30.5-second picture timeline.
- Three.js 0.170.0 with PBR shading, shadow mapping, morph animation, instanced cells, filmic tone mapping and native-resolution FXAA. Offline headless Chromium/SwiftShader rendering; **not a Blender/Cycles render**.
- Recovered GLB is Blender-importable. The final edit, new hand mesh construction, captions and camera animation are implemented in JavaScript, not a supplied `.blend` scene.
- V3 sound bed and 23 cue-based effects are synthesized from code. The dive-sound envelope peaks at the 7-second turn-over center. The four user-liked Urdu WAVs are unchanged from v2; the raw voice timeline is byte-identical. Grip/release cues read the same timing controls as their 3D actions.
- The stereo mix targets −16 LUFS integrated. Actual measured audio/video results are in `data/QUALITY_REPORT.json` and `data/AUDIO_REPORT.json` after the master is checked.
- This is a **reference-informed stylized anatomical short**, not a perfect frame-for-frame or photoreal replica of the supplied video.

## Delivery location

Parent: [WF-02 · Zack d 3d animation](https://drive.google.com/drive/folders/1LTkHpkEUFSui8Lqyy8I0j5-1AceSziWX)  
New version folder: [KAANTA — Motion Edition v3 · Smooth 3D](https://drive.google.com/drive/folders/1mK5uWa-34OjxYhvrujG0E5Odb5s6Nu3z)

Earlier files are preserved. No sharing permissions have been broadened by this task.

## Enhancement verification

`data/MOTION_QA.json` records 9 controller checks, including shared knot velocities/accelerations, cell arrival, cue synchronization and finite frame-by-frame poses. `data/DETERMINISM_REPORT.json` verifies complete-frame returns after out-of-order evaluation. An initial tiny brand-mark rasterization discrepancy was fixed by explicitly choosing a stable 2D canvas backend; its diagnostic is retained. None of these measurements claims universal artistic perfection or an exact match to the reference.
