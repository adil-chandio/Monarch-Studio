# CHAOS · NEXT FILM — 3D MONARCH
## Structure / Production Plan (aap ki approval ke liye — abhi koi render nahi)

**Task:** `WF04-3D-PLAN` · **Style:** WF-04 `monarch-face-chaos` (authority `arena/d53677cc-monarch-studio`) · **Reference:** `VID_20261013_050529_146.mp4` (measured, `INSPECTION.md`)
**Aap ka brief:** "same aisi video, bas apne 3D character mein; face movement poora perfectly, correctly, accurately."
**Rule jo main follow karunga:** pehle approval → phir kaam. Har bade step par aap ka sign-off.

---

## 0. Ek nazar mein — kya banega

**44.4 s cinematic vertical film (1080×1920, 30 fps)** jo `Chaos 2 reference` ki **act structure, cutting rhythm, mood aur grade** ko match karegi — lekin **har frame asli 3D geometry se render hoga** (aap ka Monarch: mesh + rig + facial blendshapes + PBR skin/hair/wardrobe). Reference ka koi pixel master mein nahi jaayega (watermark/rights dono saaf).

Raste 3 hain (neeche §3), aur sach yeh hai: **"perfectly accurate likeness" sirf tab mumkin hai jab aap ka character 3D form mein input ho (scan/rigged avatar)**. Us ke bagair hum **movement/expression accuracy** (performance-driven) laa sakte hain, **likeness** sirf sheet se guess hogi — aur guess hi woh "jelly/mannequin" banata hai jo aap ne v2 mein reject kiya tha. Yehi is plan ka core faisla hai.

---

## 1. Reference blueprint (jo main ne measure kiya — guess nahi)

| Act | Time | Reference mein (measured) | Luma | Cut rate | Hum 3D mein kya karenge |
|---|---|---|---|---|---|
| **A — Cold open** | 0.0–9.4 s | Dark brick hall, chains, red portal/haath, 2 lambe wide shots | 9.4 | 0 cuts | 3D hall (procedural brick + chains + volumetric haze), **slow dolly-in** wide; sirf silhouette + portal glow; 2 shots |
| **B — Reveal** | 9.4–16.3 s | Doorway figure, scarlet spill, hold | 19–47 | 4 | Camera pushes through doorway; character **haath uthata hai**, rim light on; 3 shots |
| **C — Identity** | 16.3–29.2 s | Masked figure close-ups, angle variety, fast cutting | 26–33 | ~60 | Hero close-ups: 3/4, profile, low-angle; **face performance** shots (brows/eyes/jaw), 12–16 shots |
| **D — Locked wide** | 29.2–32.9 s | 3.7 s hold, red floor | 20 | 0 | Wide sovereign stance, camera drift only — **breathing + micro-head** motion |
| **E — Climax** | 32.9–42.5 s | Heaviest cutting, blade reveal, strobes | 25–33 | **83** | Fast montage: blade/portal/eye/visor inserts, 20–24 short shots, strobe flashes |
| **F — End** | 42.5–44.4 s | *Reference ka apna IG outro* | 6 | 5 | **Apna** gold crown + MONARCH STUDIO end card (WF-04 rule: crown title ke oopar) |

**Global measured targets:** mean luma curve ≈ `9 → 47 → 25 → 33`; 171 cuts total (E act sab se tez), palette cool-shadow + scarlet practical, grain/haze halka. Audio: reference sirf music bed tha (0.65 s voiced) → **hum original score + SFX design karenge**, reference audio copy nahi.

---

## 2. Pipeline — 7 stages (har stage ka artifact)

| # | Stage | Kya hota hai | Artifact | Aap ka gate |
|---|---|---|---|---|
| 1 | **Blueprint** | reference ka shot-by-shot map → 3D camera list (lens, height, move) + act timing | `SHOTLIST_3D.json` | ✅ approve timing/camera |
| 2 | **Character** | mesh build/fit → wardrobe/hair → rig | `character.glb` + turn-around stills | ✅ **likeness approval** |
| 3 | **Face rig** | ~22 blendshapes + jaw/eye/neck + performance retarget system | `rig_test.mp4` (2–4 s) | ✅ **motion approval** |
| 4 | **Set + light** | 3D hall, portal, cables, wet floor, volumetrics; light rig | `lookdev.png` per act | ✅ look approval |
| 5 | **Animatic** | poori film, low-res (540×960), sahi timing, rough shading | `animatic.mp4` (44 s) | ✅ timing approval |
| 6 | **Final render** | path-traced hero shots + cheaper wides, chunked | `master.mp4` | ✅ frame QA |
| 7 | **Deliver** | grade/loudness QA, gates, Drive + checksums | master + gate report + receipt | ✅ accept |

---

## 3. Character: 3 raste (asli faisla yahan hai)

| | **Route A · Sheet-se sculpt** | **Route B · Performance-driven** ⭐ | **Route C · Scan/Rigged avatar** |
|---|---|---|---|
| Input | locked face sheet v5 + body sheet v2 (jo mojood hain) | + **aap ka 20–40 s selfie video** (expressions + head turns) | **rigged avatar** (.glb/.fbx + blendshapes/textures) ya 360° turntable scan |
| Geometry | guessed from 2D sheet — **yehi v2 ka masla tha** | guessed geometry + **asli facial motion** retarget | asli topology + asli likeness |
| Likeness | ⚠️ kamzor | 🟡 behtar, magar identity approx | ✅ sab se zyada |
| Face motion | 🟡 hand-keyed | ✅ **measured (478 landmarks/frame)** | ✅ |
| Compute | kam | medium | medium–heavy |
| Risk | jelly/mannequin dobara | hair/hands still manual | scan quality par depend |
| Meri sifarish | fallback (wides) | **default** (close-ups bhi) | agar aap de sakein to hero close-ups isse |

**Verified in this sandbox:** mediapipe 0.10.21 offline chalta hai aur aap ke character plate par **478 landmarks (iris ke saath)** detect hue — yani performance capture ka rasta technically ready hai.

---

## 4. Face system — "perfectly, correctly" ka technical matlab

1. **No image warping, ever.** Har frame mesh se render hoga (v2 ka `cv2.remap` jelly face **structurally** khatam).
2. **Blendshape set (~22):** jawOpen, jawLeft/Right, mouthClose, mouthFunnel/Pucker, lipsUpperUp, lipsLowerDown, lipsTogether, smile, frown, cheekPuff, browInnerUp, browDown, squint, eyeBlink L/R, eyeWide, eyeLookUp/Down/In/Out, noseSneer, visor-glow channel.
3. **Driving:** aap ki performance video → 478 points/frame → normalized features (mouth aperture, lip corner angles, brow distance, eyelid openness, iris offset, head yaw/pitch/roll) → smoothing (One-Euro) → retarget curves → blendshape weights.
4. **Verification (QA, numbers se):** landmark overlay video, `jaw aperture` trace, jitter metric (2nd derivative), blink rate, aur mesh-hash approval — **"jelly" ka metric: per-frame vertex displacement spikes**.
5. Wardrobe/hair: alag meshes (static shape + cloth-like secondary motion), hands **finger-rigged** (v2/prototype ka known fail point).

---

## 5. Set + lighting + grade

- 3D hall: brick wall (displacement), chains (curve→mesh), **red portal plane** (emissive), hanging neural cables, wet floor (roughness map + reflections), haze (volumetric).
- Light rig: portal red key, cold blue rim, overhead practicals, occasional strobe; per-act exposure matched to the reference luma curve (§1).
- Grade: cool shadows + scarlet practicals + controlled bloom (reference measured red-excess +3.7, sat ~70) — par grade **hamare** render par, reference frames par nahi.
- Grain/haze halka, 1080×1920, bt709.

---

## 6. Render/compute — asli numbers (is box par maape hue)

Sandbox: **2 vCPU · 3 GB RAM · koi GPU nahi · koi libGL nahi** (Blender/OpenGL possible nahi). Mitsuba 3.9.1 (scalar CPU) path tracing verified:

| Test | Time |
|---|---|
| 1080×1920 @ 16 spp (simple sphere scene) | **3.7 s/frame** |
| 1080×1920 @ 32 spp | **7.5 s/frame** |
| Real character scene (hair, cloth, area lights, volumetrics) | ~3–6× → **12–45 s/frame** |

Is liye **tiered render plan** (jo budget ke andar rehta hai):

| Tier | Resolution / spp | Kaam | Est. time |
|---|---|---|---|
| Preview / animatic | 540×960 @ 8 spp | poori 44 s film ka timing check | **25–40 min** |
| Wides & mid shots | 1080×1920 @ 12–16 spp + denoise | acts A, B, D, F | **1.5–3 h** |
| Hero close-ups | 1080×1920 @ 24–32 spp | ~25–30 shots (act C, E inserts) | **1–2 h** |
| Total final master (chunked, 3–4 turns) | | | **~4–7 h wall-clock** |

Renders chunked + resumable honge (frame ranges), taake turn/timeout se kuch zaya na ho.

---

## 7. Audio

- 48 kHz stereo master, target **−14.5 ± 0.7 LUFS**, true peak **≤ −1.5 dBFS** (WF-04 standard; Chaos 2 = −14.87, Chaos 3 = −16.15).
- Original score + SFX design: sub drops cut clusters par, riser climax se pehle, metallic cable whips, portal hum, impact strobes.
- **Reference ka audio copy nahi** hoga (rights). Music: ya main synth-design karoon, ya aap licensed track dein.

---

## 8. Honest risks (jo main chhupa nahi raha)

| Risk | Sach | Mitigation |
|---|---|---|
| Likeness "perfect" nahi hogi | sheet se 3D guess = approx; scan hi exact deta hai | Route C agar aap dein, warna Route B + visual sign-off |
| Hair / hands | sab se mushkil parts, prototype mein fail hue | alag meshes + dedicated QA shots |
| Compute | 2 vCPU, 3 GB; photoreal 1332 frames mehnga | tiering (upar), chunked renders, preview pehle |
| Reference rights | @VKTMDUBZ watermark + uska outro | hum sirf structure/mood lete hain; koi reference pixel master mein nahi |
| Time | 1 turn mein poori film nahi banti | gates: character → motion proof → animatic → master |
| "Chaos number" | main khud number invent nahi karunga | aap batayein (Chaos 4? 5?) |

---

## 9. Aapse chahiye (minimal, magar zaroori)

1. **Route** ka faisla (A / B / C) — §3.
2. Route B/C ke liye:
   - **Face performance video:** 20–40 s, selfie camera, neutral light, bina filter, expressions: smile, brow raise, frown, jaw open, blink ×3, eye look left/right, head yaw/pitch ~30°, phir neutral. (Phone portrait theek hai.)
   - **Turntable (Route C):** front / 45° / profile / back, neutral expression, evenly lit.
   - Wardrobe/texture ka faisla: **photo-PBR** (asli skin texture) ya **stylized** (clean CG look) — v2 ke baad yeh aap ka call hai.
3. **Film number/naam** (Chaos 4? Chaos 5?) aur **length** (44.4 s full ya 20–30 s tighter cut).
4. Music: main design karoon ya aap track dein.

---

## 10. Timeline (agar aap aaj route + inputs dein)

| Turn | Deliverable |
|---|---|
| **1 (agla)** | `SHOTLIST_3D.json` — 44.4 s ka shot-by-shot 3D plan (camera, action, timing) → aap approve karein |
| **2** | Character stills: front/45°/profile + wardrobe — **likeness approval** |
| **3** | 3–4 s **rig + face motion proof** (numbers ke saath) — **motion approval** |
| **4** | Lookdev stills per act (light/grade) |
| **5** | 44 s **animatic** (low-res, sahi timing) |
| **6–8** | Final render (chunked) + QA |
| **9** | Drive delivery + gate report + receipt |

Agar aap ke paas scan/avatar hai to **Turn 2–3** ek hi turn mein combine ho jayenge (kai hafte ka farq).

---

## 11. Is plan mein jaan-boojh kar shaamil NAHI

- Reference footage ka recut / upscale (wahi cheez jo maine ghalti se ki thi — ab nahi).
- v2-style 2.5D image plates ya per-frame image warp.
- Bina approval koi render, koi Drive upload.
