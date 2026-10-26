# WF-05 · Intake — "yehi kaam yahan se" (26 Oct 2026)

**Task:** `WF05-20261026-REF-INTAKE` · **Style:** `premium-motion-editing` · **Repo:** `adil-chandio/Monarch-Studio` · **Branch:** `arena/faa9119c-monarch-studio`

---

## 1. Ek nazar mein (short version)

Aapki chat transcript (PDF) padh li. Us chat mein agent ne aapka Drive reference video download kiya tha (26 MB, portrait 720×1280). Main ne wohi file **Drive connector se verify kar li hai** — file asli hai, ID aur size match karte hain.

**Lekin:** is sandbox se `drive.google.com` reachable nahi hai. Yani main reference ke **bytes** yahan nahi laa sakta, is liye abhi tak **koi frame nahi dekh paya**. Jo cheez main dekhe bagair likh doon, woh guess hoga — aur repo ka rule hai: guess ko evidence nahi likhna.

Baaki sab ready hai: is repo mein WF-05 ka poora pipeline mojood hai aur maine is environment ko chala kar test kar liya hai (ffmpeg 7.0.2, OpenCV 5.0.0, Pillow 13, numpy, scipy — sab kaam kar rahe hain, `studio.py validate` = 21 pass / 1 warning / 0 error).

**Ek cheez chahiye: video file khud is chat mein attach kar dein** (Drive link ke bajaye MP4). Us ke baad analysis se delivery tak sab yahin hoga.

---

## 2. Jo actually verify hua (hard facts)

| Field | Value | Source |
|---|---|---|
| Drive file | `VID_20261013_050529_146.mp4` | `google_drive.get_file` |
| File ID | `1sYYhXs9fbHeHcQGOmH5IR7CvUSVr9Tmx` | above |
| Size | 26,397,151 bytes (~25.2 MiB) | above |
| Duration | 44.399 s | above |
| Resolution | 720 × 1280 (portrait 9:16) | above |
| Derived avg bitrate | ~4.76 Mbps | size × 8 ÷ duration |
| Parent folder | `1uGPfl4pwPoL-D0VIag3hIejmbR__ochC` | above |
| Modified | 2026-10-26 14:39 UTC | above |

Machine-readable record: `REFERENCE.json` (same folder).

---

## 3. Deewar (why the video is not analysed yet)

| Check | Result |
|---|---|
| `curl https://drive.google.com/uc?export=download&id=…` | `SSL_ERROR_SYSCALL` — egress allowlist |
| `curl https://lh3.googleusercontent.com/` | same block |
| Connector `download_file` | returns base64 in-context only (26 MB → unusable) |
| Local `ffmpeg` at session start | not installed → **fixed**: `imageio-ffmpeg` 7.0.2 binary installed |

Is liye reference par koi bhi statement (style, shots, subject, audio, text) **abhi tak record nahi kiya** — `REFERENCE.json` ka `claim_boundary` yehi kehta hai.

---

## 4. Aage do raaste

**Raasta A — recommended (2 minute).** Aap yahi MP4 is chat mein attach kar dein. File `/tmp/arena-coding-uploads/` mein aati hai, phir main:
frames decode → shot/motion/cleanup breakdown → script + narration → timeline → clean compositor render → QA → verified delivery (Drive upload + checksum). Sab kuch is repo ke task/journal ke andar.

**Raasta B.** Video bhejna mumkin nahi → to aap topic/script dein, main WF-05 ka naya project scaffold kar ke narration + plan se shuru karta hoon, footage baad mein aaye. (Is case mein reference-based breakdown nahi hoga.)

---

## 5. Yahan se kaam karne ka exact runbook (jo main chalaunga)

```bash
python3 tools/continuity.py resume                    # state
python3 styles/premium-motion-editing/src/wf05.py inspect
python3 styles/premium-motion-editing/src/wf05.py new \
  --project-dir workflows/current/payload/<project> \
  --project-id WF05-<date>-<name> --topic "<topic>"
python3 styles/premium-motion-editing/src/wf05.py validate workflows/current/payload/<project> --plan-only
python3 styles/premium-motion-editing/src/wf05.py render  workflows/current/payload/<project>
python3 styles/premium-motion-editing/src/wf05.py verify  workflows/current/payload/<project> --video <master>
python3 tools/studio.py validate
```

Policy jo binding hai (`data/approved-profile.json`): 1080×1920 · 30 fps · H.264 crf 18 · yuv420p · AAC 48 kHz stereo · faststart. Integrated kinetic headings default; **V6 bottom caption pills aur active-word strip rejected**; subtitle default off. 2.5D camera + real temporal motion — slideshow nahi.

---

## 6. Mujhe 3 cheezein chahiye (bas)

1. **MP4 attach** (Raasta A) — warna Raasta B confirm karein.
2. **Maqsad:** isi footage ka full motion edit, ya pehle sirf style/shot breakdown report?
3. **Narration:** Roman Urdu voice-over chahiye ya silent/sound-design only? (agar voice chahiye to is session mein pehle voice audition karna hoga)

---

## 7. Jo main abhi tak *nahi* karunga (claim discipline)

- Reference ke content/style ke baare mein koi baat, jab tak frames decode na hon.
- "Render ho gaya / upload ho gaya" nahi kahunga jab tak file + Drive ID + size/checksum verify na ho.
- Is environment ki 2 vCPU / 3 GB limit ko chhupa kar "background mein ban raha hai" nahi kahunga — render blocking chalega aur main result de kar hi dum loonga.

---

## 9. Update — proof clip ban gaya (is turn mein)

Reference ke bytes nahi mile, is liye maine apna waqt waste nahi kiya: WF-05 ka **approve shuda compositor** is sandbox mein chala kar dikha diya ke decode → 2.5D camera → integrated type → H.264 encode → decode-verify sab kaam karta hai.

- File: [`demo/engine-check/WF05_ENGINE_CHECK_demo.mp4`](../../../../demo/engine-check/WF05_ENGINE_CHECK_demo.mp4) · 6.0 s · 1080×1920 · 30 fps · H.264 High yuv420p bt709 + AAC 48 kHz stereo · 6,086,106 bytes · MD5 `85274e610d7141cb64bada011352a4ef`
- Verify: 180/180 frames full decode, audio peak −2.85 dBFS, motion measured (1.17s shot mein Δluma 4.8–15.6; slideshow nahi).
- Policy: bottom caption pills aur active-word strip **nahi** (production module mein woh renderer mojood hi nahi), subtitle off, integrated headings.
- Scope note: plates procedural hain — **aapka reference nahi**. Yeh sirf capability proof hai, delivery master nahi.

Details: [`demo/engine-check/README.md`](../../../../demo/engine-check/README.md) · receipt: `engine-check/ENGINE_CHECK_RECEIPT.json` · script: `engine-check/render_engine_check.py`.
