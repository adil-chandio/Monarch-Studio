# CHAOS · NEXT FILM — MASTER STRUCTURE
## Forensic feasibility + production plan (approval ke liye · koi render/upload nahi hua)

**Task:** `WF04-3D-PLAN` · **Style:** WF-04 `monarch-face-chaos` · **Reference:** `VID_20261013_050529_146.mp4` (measured in `INSPECTION.md`)
**Aap ka brief:** poori video, exactly same feel, sab kuch hamara, 3D/AI jis tarah bhi — "bina kisi kami ke".
**Is document ka maqsad:** pehle sach, phir rasta, phir aap ka approval. Kuch bhi banaya nahi gaya.

---

# PART 1 — SACH (jo aaj is machine par naapa gaya)

## 1.1 GPU ka reality check

| Cheez | Result | Evidence |
|---|---|---|
| GPU device | **koi nahi** (`/dev/nvidia*` khali) | `ls /dev/nvidia*` → no devices |
| CUDA tooling | **koi nahi** (nvidia-smi nahi) | `which nvidia-smi` → nothing |
| CPU | Intel Xeon @2.60 GHz · **2 vCPU** · avx2/avx512f | `lscpu` |
| RAM | **3.8 GB** total | `free -h` |
| Disk | 15 GB free | `df -h` |
| Blender CUDA (CUEW) | init fail (expected, GPU nahi) | render log |
| Blender Cycles **CPU** | **kaam karta hai** ✅ | `bpy 5.0.1` import + render proven |

**Matlab:** main GPU "laa" nahi sakta — cloud GPU ke liye account + billing + credentials chahiye, jo mere paas nahi hain aur main aapse credentials nahi maang sakta. **Lekin** ek rasta hai jisme GPU aap ke haath mein rehta hai aur main baaki sab karta hoon → **Part 3, Track B** (main Colab/Kaggle notebook likhta hoon, aap ek click par chalate hain, output aap ke Drive folder mein aata hai, main wahan se utha kar edit/QC/deliver karta hoon — yeh Drive handoff aaj verify ho chuka hai).

## 1.2 Jo is box par **verified chalta hai** (aaj ke asli tests)

| Tool | Version | Verified | Kaam |
|---|---|---|---|
| **Blender as Python module** (`bpy`) | **5.0.1** | ✅ import + Cycles CPU render (stub X libs compile kar ke) | modeling, armature, shape keys, hair, cloth, Cycles |
| Cycles CPU + OIDN denoise | built-in | ✅ rendered 4 test frames | photoreal-ish shading |
| Mitsuba | 3.9.1 (scalar CPU) | ✅ render (+ no denoiser plugin) | alternative/experimental renders |
| **MediaPipe FaceMesh** | 0.10.21 (venv, offline) | ✅ **478 landmarks** (iris ke saath) on our own character plate | performance capture |
| OpenCV / numpy / scipy / Pillow | 5.0.0 / 2.4.6 / 1.17 / 13 | ✅ | processing, grade, QC |
| ffmpeg (imageio) | 7.0.2 | ✅ | encode, loudness, mux |
| Real-ESRGAN / RIFE | repo verified (BSD-3 / MIT) | ⏳ install+test baaki | upscale / 60fps interpolation |

## 1.3 Render speed — asli measured (2 vCPU, hair+HSS, 2 area lights, OIDN)

| Resolution | Samples | Time / frame | 1332 frames (44.4 s) |
|---|---|---|---|
| 540×960 | 16 | **14.5 s** | **5.4 h** |
| 1080×1920 | 16 | **59.1 s** | **21.9 h** |
| 1080×1920 | 32 | **104.8 s** | **38.8 h** |
| 1080×1920 | 64 | **203.2 s** | **75.2 h** |

Optimisation ke baad (hair **cards** instead of 220 curves, SSS off, 3 bounces, adaptive sampling) realistic target: **720×1280 @ 24–32 spp ≈ 18–30 s/frame → poora film 6.5–11 h**, chunks mein (har chunk 20–25 min, resumable).

## 1.4 AI video models — kya sach hai (GitHub se verify kiya)

| Project | Stars | License | Requirement | Is box par? |
|---|---|---|---|---|
| **Wan2.2** (Alibaba) | 18,194 | Apache-2.0 | **≥24 GB VRAM** (RTX 4090 class) TI2V-5B ke liye | ❌ GPU nahi |
| **LTX-Video** (Lightricks) | 11,188 | Apache-2.0 | 2B distilled = **sab se kam VRAM** variant | ❌ GPU nahi |
| **HunyuanVideo** | 12,669 | custom | bahut bhaari | ❌ |
| **LivePortrait** (face performance transfer) | 19,318 | custom (Kling) | NVIDIA GPU (RTX 4090 reference) | ❌ |
| **Hunyuan3D-2** (image→3D) | 15,205 | custom | GPU | ❌ |
| Real-ESRGAN | 37,231 | BSD-3 | **CPU chal sakta hai** | ✅ (slow) |
| Practical-RIFE | 1,030 | MIT | CPU possible | ✅ (slow) |
| SAM2 (matting/rotoscope) | 20,062 | Apache-2.0 | GPU prefer | ⚠️ |

**Nateeja:** photoreal AI-video ka rasta **GPU ke bagair band hai**. CPU par 5B/13B video models chalana practically mumkin nahi (dinon ka farq).

## 1.5 Quality ceiling — seedhi baat

| Rasta | Look | "Exactly same" score | GPU |
|---|---|---|---|
| **Pure 3D on CPU** (Blender) | stylized-high-end cinematic CG | **70–80%** (structure/light/mood match; skin micro-detail nahi) | ❌ nahi chahiye |
| **AI video (Wan/LTX) on GPU** | photoreal cinematic, reference ke qareeb | **85–95%** | ✅ chahiye |
| **Hybrid** (3D base render + AI polish/upscale/face) | sab se qareeb | **85–92%** | ⚠️ partial |

Aur ek sach jo aap ne khud v2 par bolа tha: **"jelly face" tab aata hai jab motion 2D warp se banaya jaaye**. Is plan mein **har frame mesh se render hoga** — image warp ka option hi nahi.
Likeness ke liye: agar aap **rigged avatar/scan** de dein to 90%+; sheet se sculpt karein to ~70% (isliye face par mask/visor design use karna behtar hai — reference character bhi masked hai).

---

# PART 2 — VIDEO KA STRUCTURE (reference se measured, hamara design)

**Target:** 44.4 s · 1080×1920 (master) · 30 fps · 1332 frames · 48 kHz stereo.

| Act | Time | Ref (measured) | Hamara 3D content | Shots | Camera moves |
|---|---|---|---|---|---|
| **A · COLD OPEN** | 0.0–9.4 s | 0 cuts, luma 9.4 | 3D industrial hall: brick displacement wall, chains, red portal, haze; silhouette enters | 3 | slow dolly-in ×2, crane-down |
| **B · REVEAL** | 9.4–16.3 s | 4 cuts, luma 19→47 | doorway framing, rim light, character steps forward, one hand raise | 5 | push-in, rack focus |
| **C · IDENTITY** | 16.3–29.2 s | ~60 cuts, luma 26–33 | hero close-ups: 3/4, profile, low-angle, visor/eye inserts, **face performance** | 16 | orbit, snap-zoom, handheld sway |
| **D · LOCKED WIDE** | 29.2–32.9 s | 0 cuts, luma 20 | wide sovereign stance, breathing + micro-head motion | 2 | slow drift only |
| **E · CLIMAX** | 32.9–42.5 s | 83 cuts, luma 25–33 | fast montage: blade, portal flare, eye, glove, badge, strobes | 22 | whip pans, staccato |
| **F · END CARD** | 42.5–44.4 s | ref ka IG outro (ours nahi) | **apna** crown + MONARCH STUDIO emblem, gold flare | 2 | slow push |
| | | **171 ref cuts** | **~50 shots** (hamare budget ke andar) | **50** | |

**Global measured targets jo hum match karenge:** luma curve 9→47→25→33, cool-shadow/scarlet palette, cut density (E act sab se tez), halka grain/haze, 9:16 framing.

**Audio (hamara, original):** score + SFX design, 48 kHz stereo, **−14.5 ± 0.7 LUFS**, true peak **≤ −1.5 dBFS** (WF-04 standard). Reference ka audio copy nahi.

---

# PART 3 — 3 PRODUCTION TRACKS (aap ko ek chunna hai)

### **TRACK A · "In-house 3D" — GPU ki zaroorat nahi, sab yahin** ⭐ (agar GPU nahi)
- Blender(bpy) mein: character mesh + armature + **22 facial blendshapes**, set, lights, camera; Cycles CPU render chunks mein; ffmpeg grade + audio + encode.
- **Assets:** 100% ours (procedural + MediaPipe head topology + AI-generated textures via in-platform image tool).
- **Quality:** stylized premium CG — reference ka *structure, lighting, mood, rhythm* match; photoreal skin nahi.
- **Time:** parts 1–4 (design/rig/look) ≈ 3–5 turns; render ≈ **6.5–11 h** chunked; total **~7–12 turns**.
- **Risk:** "CG look" — is liye masked/visor hero design + strong grade (reference jaisa) use karenge.

### **TRACK B · "AI cinematic" — GPU aap ke paas (Colab/Kaggle/RunPod)**
- Main likhta hoon: character sheet (AI image tool se, in-platform) → **Wan2.2 TI2V-5B** ya **LTX-Video 2B distilled** notebook → clips; **LivePortrait** se face performance; output aap ke Drive folder mein.
- Main phir: **editing, timing, transitions, grade, HUD, end card, sound, QC, delivery** — sab yahin.
- **Aap ko sirf:** notebook run karna (24 GB VRAM ya Colab Pro A100; free T4 par LTX-2B best chance).
- **Quality:** 85–95% (photoreal cinematic).
- **Time:** setup 1–2 turns; aap ka compute 1–3 h; mera edit/QC 2–4 turns.

### **TRACK C · "Hybrid" — sab se behtar result, dono ka mix**
- 3D base (hamara character, sahi motion, sahi camera) → GPU milne par **AI polish**: upscale (Real-ESRGAN/Topaz-style), face detail transfer (LivePortrait), grain/grade.
- Agar GPU na ho: sirf 3D (Track A) par utar aata hai; baad mein GPU aaye to **same frames** se polish ho jaayega (kuch zaya nahi).

**Meri sifarish: Track C shuru karein Track A ke 3D base se** — kyunki woh GPU ke bagair aaj shuru ho sakta hai, aur GPU aane par wahi kaam upgrade ho jaata hai. Track B tabhi jab aap ka GPU access aaj se available ho.

---

# PART 4 — BUILD ORDER (gates ke saath, har gate par aap ka sign-off)

| # | Stage | Kya milega | Gate |
|---|---|---|---|
| **G0** | **Ye document** | structure + tracks | ✅ **abhi** |
| G1 | `SHOTLIST_3D.json` — 50 shots ka camera/action/timing blueprint | JSON + contact sheet | aap approve karein |
| G2 | Character: turnaround stills (front/45°/profile/back) + wardrobe | 4 stills | **likeness approval** |
| G3 | Face rig test: 3–4 s clip, 22 blendshapes, landmark overlay video | mp4 + metrics (jitter, jaw trace) | **motion approval** |
| G4 | Lookdev: har act ka 1 hero still (light/grade) | 6 stills | look approval |
| G5 | Animatic: poori 44 s, 540p, sahi timing, rough shading | mp4 | timing approval |
| G6 | Final render (chunked) | frames | frame QA |
| G7 | Edit/grade/audio master + gates | master | **accept** |
| G8 | Drive delivery + receipt (IDs, MD5) | link | done |

**Koi bhi stage render tab tak nahi jab tak pichla gate pass na ho.**

---

# PART 5 — AAP SE 5 CHEEZEIN (bas yeh)

1. **Track:** A (GPU nahi, stylized 3D) / B (AI, aap ka GPU) / C (hybrid — recommended).
2. **GPU access:** kya aap ke paas Colab Pro / Kaggle / 24 GB card hai? (haan → Track B/C; nahi → Track A)
3. **Character input:** locked face sheet v5 + body v2 kaafi hain (approx), ya aap **turntable/scan/rigged avatar** de sakte hain (exact likeness).
4. **Film number + length:** Chaos 4? ya Chaos 5? · **44.4 s full** ya **22–30 s tight** (render adha).
5. **Style choice:** (a) **masked/visor hero** (reference jaisa, 3D easily premium dikhta hai) ya (b) **khula face** (Monarch likeness, GPU/AI ke bagair risk zyada).

---

# PART 6 — JO MAIN NAHI KARUNGA (likha hua vaada)

- Reference footage ka recut/upscale/re-upload (jo maine ghalti se kiya tha).
- 2D image plates ya per-frame image warp (v2 ka jelly face).
- Aap ki approval ke bagair render ya Drive upload.
- Jhooti "gate pass" ya jhooti quality claim.
- Aap se password/PAT/OAuth token maangna (kabhi nahi).

---

## Appendix A — aaj ke verified commands (reproducible)

```bash
# 1) bpy headless setup (stub X libs so Blender's Cycles CPU runs without a display)
python3 -m pip install --break-system-packages bpy      # 5.0.1
gcc -shared -fPIC -o ~/.runtime/xstub/libGL.so.1 ...    # + libXrender/libXi/libXfixes/libICE/libSM/libxkbcommon stubs
LD_LIBRARY_PATH=~/.runtime/xstub python3 -c "import bpy; print(bpy.app.version_string)"
# 2) render benchmark (measured above)
LD_LIBRARY_PATH=~/.runtime/xstub python3 /tmp/bpy_bench.py
# 3) offline face tracking (478 landmarks, no network)
/tmp/mpvenv/bin/python -c "import mediapipe as mp; ..."
```

## Appendix B — reference vs our target (numbers)

| Metric | Reference (measured) | Hamara target |
|---|---|---|
| Duration / frames | 44.40 s / 1332 | 44.4 s / 1332 |
| Hard cuts | 171 | ~50 built cuts + internal motion (ya 120+ agar aap chahein) |
| Mean luma | 21.5 (act curve 9→47→33→6) | same curve |
| Palette | cool shadows + scarlet practicals (red excess +3.7) | same |
| Audio | music bed only (0.65 s voiced) · 44.1 kHz | original score · 48 kHz · −14.5 LUFS |
| Watermark | @VKTMDUBZ + uska IG outro | **koi nahi** — apna crown/emblem end card |
