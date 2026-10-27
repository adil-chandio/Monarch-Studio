# MOBILE WORKFLOW · phone se poora studio chalane ka tareeqa

Owner **mobile par** hai. Woh sirf tap karta hai. Yeh doc woh **structure + way + workflow** hai jo agent
follow karta hai — isi liye har turn ka result same rehta hai, chahe chat refresh ho jaye ya naya agent aaye.

> Companion: [`MOBILE.md`](MOBILE.md) (aap ka 3-tap card) · state machine: [`tools/mobile_ops.py`](../tools/mobile_ops.py)
> (tool id `mobileops-1.0`) · engine: [`tools/videogen.py`](../tools/videogen.py) (`viper-1.4`)

---

## 1. Contract — ek line me

**Aap tap karte ho, agent chalta hai, notebook render karta hai, Drive me sab kuch girta hai.**
Kisi bhi waqt aap ke haath me ek hi cheez hoti hai: **ek link aur ek tap**.

| Kaam | Kaun karta hai | Aap ka effort |
|---|---|---|
| Topic samajhna, prompts likhna, shots todna | agent | ek line likhna |
| `$0` estimate, engine per shot, licence check | agent | zero |
| Phone notebook banana (`viper-1.4` `mobile`) | agent | zero |
| Notebook Drive me daalna + Colab link | agent | zero |
| **Clips + voice + foley + upscale (GPU)** | **Colab notebook** | **3 tap** |
| Clips check karna (aaye ya nahi) | agent (`check`) | zero |
| Voice+foley+music ka mix, loudness | agent (`finish`) | zero |
| Height/audio/md5 verify | agent (`finish`) | zero |
| Master assemble + Drive upload + receipt | agent (`finish`, `deliver`) | zero |
| Quota ledger, continuity, checkpoint | agent | zero |

Aap ko **kabhi nahi** karna: pip install, ffmpeg, terminal, file rename, ZIP, JSON edit, md5.
Agar main kabhi aap ko command doon, woh **mera bug** hai — batao, main `mobile_ops.py doctor` se pakadta hoon.

---

## 2. State machine (yeh "structure" hai)

Har project ek **job file** banta hai: `studio/mobile/jobs/<job_id>.json`.
Wahi file batati hai kaun kya karega — is liye chat bhool jaye to bhi kaam nahi dohraya jata.

```
intake ──plan──▶ planned ──handoff(link)──▶ handed_off ──check──▶ clip_ready
                                                  │  │                 │
                                      (kuch clips)│  │(kuch nahi)      │ finish
                                                  ▼  ▼                 ▼
                                               partial  blocked ──▶ mixed ──▶ verified ──▶ assembled ──deliver──▶ delivered
```

- **blocked** se wapas kaam me aana allowed hai (`check`/`finish` dobara) — rukna mana nahi, **jhooth** mana hai.
- **delivered** terminal hai. Uske baad sirf naya job.
- Har transition `history` me hash-free timestamp ke saath likha jata hai: kaun (agent/notebook) aur kyun.

---

## 3. Gates — evidence ke bina agla step nahi

| Gate | Pass kab | Fail par |
|---|---|---|
| `plan_estimate` | `videogen plan` exit 0 + `plan.json` likha | `blocked`, plan ka asli error save |
| `notebook` | `mobile/MOBILE_<id>.ipynb` disk par maujood | `blocked`, "notebook missing" |
| `handoff` | link `https://colab.research.google.com/...` hai | refusal: notebook pehle upload karo |
| `clips` | **har shot** ki file > 0 byte (`<id>.mp4` ya `<id>-2x.mp4`) | `partial` (list) ya `blocked` (0 clips) |
| `mix` | `videogen mix --loudnorm` exit 0 | `blocked`, ffmpeg ka aakhri 6 line save |
| `verify` | `videogen verify` exit 0 (height + audio + md5) | `blocked`, assemble **nahi** chalta |
| `assemble` | `delivery/<id>_MASTER.mp4` > 0 byte | `blocked` |
| `master` | md5 + bytes + probe (w×h, fps, duration, audio codec) | `blocked` |
| `delivery` | Drive master id mil gaya | state `assembled` hi rehta hai |

**Rule:** 0-byte file clip nahi hai · promise master nahi hai · `verify` pass hone se pehle koi "ban gaya" nahi kehta.

---

## 4. Agent ke commands (aap ko dikhte bhi nahi)

```bash
python3 tools/mobile_ops.py doctor                       # phone ops yahan chalega?
python3 tools/mobile_ops.py start --project <id|path>     # job banao (intake)
python3 tools/mobile_ops.py plan  <job>                   # $0 estimate + notebook
python3 tools/mobile_ops.py handoff <job> --colab <link>   # owner ke 3 tap arm karo
#   ---- owner: T4 GPU → Run all → "DONE" ----
python3 tools/mobile_ops.py ingest <job> --zip <zip>       # notebook ka _outputs.zip kholo (Drive fail ho to yeh)
python3 tools/mobile_ops.py check  <job>                  # clips aaye? partial/blocked?
python3 tools/mobile_ops.py finish <job>                  # mix --loudnorm → verify → assemble (jab bytes yahan hon)
python3 tools/mobile_ops.py adopt  <job> --receipt <json>  # master Colab me bana (Drive se bytes laane ki zarurat nahi)
python3 tools/mobile_ops.py deliver <job> --master-id <drive id> --url <link>
python3 tools/mobile_ops.py status                        # sab jobs + agla kadam
python3 tools/mobile_ops.py next   <job>                  # ek hi agla action + owner card
```

Har command `--json`-able output ke qareeb hai (`status --json`), is liye agent ko guess nahi karna padta.
`REFUSED:` mile to matlab gate ne roka — error padho, usi ko fix karo, aage na badho.

---

## 5. Owner ko bhejne wale messages (templates)

Sirf **ek** message per turn, aur usme **ek** action. `mobile_ops.py card <job>` yeh text khud banata hai:

**planned → handoff**
> **{title}** ready hai. Aap ka kaam (3 tap):
> 1. **Runtime ▸ Change runtime type ▸ T4 GPU**
> 2. **Runtime ▸ Run all**
> 3. Aakhri cell me `DONE ✅` aaye to chat me `DONE` likho
> Notebook: {colab link} — baaki sab main karunga.

**partial**
> Adhe clips aa gaye. Missing: {ids}. Wahi notebook → **Runtime ▸ Run all** (jo bana hai woh skip hoga).

**blocked**
> Atak gaya: {stage}. Main fix kar raha hoon — aap kuch na karo. (internal: {blocker detail})

**delivered**
> **Master ready ✅** `{path}` · {MB} MB · {w}×{h} · {fps} fps · {sec}s · audio {codec}
> md5 `{md5}` · Drive: {link}

Yeh templates Hinglish me hain aur **command-free** hain — test `test_handoff_card_has_no_cli_for_the_owner`
isse pin karta hai (koi `python3`, `pip`, `ffmpeg`, `--flag`, `.json` owner ko nahi jata).

---

## 5b. Notebook upload rule (isse ek dafa jal chuke hain)

Colab link `https://colab.research.google.com/drive/<file_id>` sirf tab khulta hai jab Drive file ka
**naam `*.ipynb` par khatam** ho aur mimeType `application/x-ipynb+json` ho. Naam me `.ipynb` na ho to Drive
"**This file type is unsupported**" dikhata hai (mobile par bhi).

- Upload karte waqt naam **`PROJECT_phone_run_all.ipynb`** rakho (spaces ki jagah `_`, extension zaroori).
- Upload ke baad `get_file` se `mimeType` confirm karo.
- Purani ghalat-naam file: `update_file --name ...ipynb` se rename, ya delete + dobara upload; **naya link** do.

### 5c. Do link, do surat-e-haal

Drive ka preview `.ipynb` **kabhi** render nahi karta — phone par "**This file type is unsupported**" aana
normal hai (file kharab nahi hoti). Is liye do link hote hain:

| Link | Kab | Kya karta hai |
|---|---|---|
| `colab.research.google.com/drive/<id>` | jab Drive+Colab integration theek ho | Colab me seedha khulta hai |
| `colab.research.google.com/github/<owner>/<repo>/blob/<tag>/<path>.ipynb` | **default jab Drive refuse kare** | GitHub se padh kar Colab editor me kholta hai, Drive ki zarurat nahi |

GitHub link ke liye notebook repo me hona chahiye + repo public + tag (slash-free, kyunki `blob/<ref>/` me
branch ke slash URL tod dete hain). Isi liye: `git tag colab-<job> && git push origin refs/tags/colab-<job>`.

### 5c-bis. Ek cell = ek button (`--one-cell`)

Phone par har cell ka apna ▶ hota hai aur "Run all" dhoondhna mushkil — is liye `mobile --one-cell` saare
code cells ko **ek** cell me jod deta hai. Owner ko sirf ek ▶ dabana hota hai. Screenshot se pata chala tha
ke sab cells khaali `[ ]` the (kuch chala hi nahi) — ek cell se yeh confusion khatam.

```bash
python3 tools/videogen.py mobile <project.json> --one-cell
```

### 5c-ter. RAM (12.7 GB) — Wan ka text encoder 4-bit me hi load hota hai

Free Colab par **host RAM** hi asli deewar hai, VRAM nahi. UMT5-XXL (Wan ka text encoder) fp32 me
**22.7 GB** hai — `WanPipeline.from_pretrained` seedha usi par crash karta hai
("_Your session crashed after using all available RAM_").

Notebook (`viper-1.7`) me is liye:

| Cheez | Setting | Kyun |
|---|---|---|
| text encoder | **4-bit NF4** (`load_in_4bit`, `device_map={"": 0}`) | 22.7 GB → ~2.4 GB VRAM, host RAM chhua hi nahi |
| DiT transformer | native fp16 | 2.6 GB, quality poora |
| VAE | fp32 + `enable_tiling()` + `enable_slicing()` | decode ke waqt VRAM spike khatam |
| downloader | `HF_HUB_DISABLE_XET=1` | Xet ka in-memory buffer RAM kha jata hai |
| allocator | `mallopt` + `malloc_trim(0)` | glibc freed pages OS ko wapas deta hai |
| scheduler | UniPC `flow_shift=3.0` | 480p ke liye official; 5.0 sirf 720p |
| pipeline | clips ke baad `del pipe` | upscale ke liye RAM khaali |

**Measured on the owner's own free T4** (27 Oct 2026, 480×832, 33 frames, 30 steps, guidance 5.0,
4-bit text encoder): model load ≈ 3 min (first run downloads the weights once), **render 49 s**, ffmpeg ×2
upscale seconds, ZIP written to Drive. Host RAM stayed at 8.1–9.1 GB free throughout — the 4-bit encoder is
what bought that room.

| Frames | Duration | Render (measured / extrapolated) |
|---|---|---|
| 33 | ~2 s | **49 s (measured)** |
| 49 | ~3 s | ~1.5–2 min |
| 77 | ~5 s | ~2–3 min |

A 3-shot reel with voice + foley + upscale therefore lands at **~20–30 min**, not the 45–70 min first
estimated. `mobile --max-frames 33` stays the test default, `49` for real reels.
### 5c-quater. Master bhi Colab me banta hai (`RUN_FINISH`)

Sandbox Google hosts tak nahi pahunch sakta (`drive.google.com`, `googleapis.com` — dono blocked). Is liye
notebook ka **aakhri stage** khud master banata hai:

1. har shot ka best file uthata hai (`<id>-2x.mp4`, warna `<id>.mp4`)
2. voice/foley stems ko us shot ke saath `amix` karta hai (na hon to `anullsrc` se silence)
3. `scale`+`pad` se sab ko ek hi size/fps par laata hai, phir `concat`
4. `loudnorm I=-16 TP=-1.5 LRA=11`, `libx264 crf 18`, audio `aac 192k`, `+faststart`
5. `delivery/<project>_MASTER.mp4` Drive me likhta hai **aur** `colab_master_receipt.json`
   (md5, bytes, w×h, fps, duration, audio codec) — woh file sirf kuch KB ki hai

Agent woh receipt **connector se padh kar** `mobile_ops.py adopt <job> --receipt <json>` chalata hai:
gates `mix`, `verify`, `master` record hoti hain, job `assembled` ho jata hai, phir Drive id ke saath
`deliver`. Yani bara media kabhi sandbox me aata hi nahi — sirf saboot aata hai.

### 5c-quinquies. Finish kaise likha gaya hai (aur kyun)

Pehla version ek hi bade ffmpeg `filter_complex` graph banata tha — Colab par `Qavg: nan` ke saath fail
hua. Ab finish **per shot** chalta hai, taake error ho to pata chale kaunsa shot:

1. har shot: `scale`+`pad` → `<project>_delivery/_segments/segNN.mp4` (video + us shot ka voice/foley mix,
   na ho to `anullsrc` silence; saath me `-shortest`)
2. `concat` demuxer se jodna (`list.txt`), fail ho to re-encode fallback
3. aakhri pass: `loudnorm I=-16:TP=-1.5:LRA=11` + `aac 192k` + `+faststart`
4. probe + `colab_master_receipt.json` (md5, bytes, w×h, fps, duration, audio)

Do aur sabak jo isi run me mile:

- **`!pip` kabhi `if`/`try` block ke andar nahi.** Colab usay bash ko bhej deta hai →
  `/bin/bash: line 1: !pip: command not found`. Har install ab
  `subprocess.run([sys.executable, "-m", "pip", "install", ...])` se hota hai.
- **`DELIVERY` sirf `BASE` ke baad define ho** — warna cell `NameError: BASE` par marta hai (test isi ko pin
  karta hai).
- Template ke andar `\"\"\"` ya `\n` jaisa escape mat likho: template string toot jati hai. Isi liye concat list
  `chr(10)` se banti hai.

### 5d. Drive mount fail ho jaye to? (ZIP handoff)

`drive.mount()` phone par kabhi `Error: credential propagation was unsuccessful` deta hai (Chrome ke
third-party cookies / multiple Google accounts). Notebook ab **is par rukta nahi**:

1. mount try karta hai → fail ho to `BASE = /content/m_out/<project>` par chalta hai
2. aakhir me `<project>_outputs.zip` banata hai (`shots/`, `audio/vo/`, `audio/foley/`)
3. Drive mounted ho to ZIP Drive folder me bhi rakhta hai, warna `files.download()` se phone ke Downloads me
4. owner ZIP **chat me attach** kar deta hai → agent `mobile_ops.py ingest <job> --zip <file>` chala kar
   project folder me kholta hai (path-escape guard ke saath) → phir `check` → `finish`

Yani Drive optional hai, delivery nahi — bas ZIP ka raasta.

## 6. Jab kuch atak jaye (failure matrix)

| Nazar aa raha hai | Asli matlab | Kaun fix karta hai | Fix |
|---|---|---|---|
| Aakhri cell `ADHURA ⚠️` | kuch stage fail hua, baaki skip | sheet/notebook | `check` chalao → missing list owner ko, dobara Run all |
| Colab disconnect | runtime gaya, Drive par jo likha tha bacha | owner + agent | wahi notebook dobara Run all (skip-if-exists), phir `check` |
| CUDA out of memory | model + offload ka masla | agent | notebook me `mmaudio_small_44k` / smaller frames; owner dobara Run all |
| `Runtime ▸ Run all` bahut slow | free T4 throttled / quota | agent | Kaggle ~30 h/week par shift (`quota --use kaggle <h>`) |
| `check` 0 clips | notebook chala hi nahi, ya mount fail | owner | T4 select confirm, dobara Run all (ab mount fail hone par bhi chalta hai) |
| `drive.mount … credential propagation` | phone ke Chrome me third-party cookies band / 2 account login | nobody | ignore karo — notebook local disk par chalta hai, aakhir me ZIP |
| `verify` exit 3 | height/audio/md5 fail | agent | `finish` dobara, ya upscale stage chalao |
| `REFUSED: illegal transition` | state machine ne roka | agent | `status` dekho, sahi command chalao |
| "This file type is unsupported" | Drive file ke naam me `.ipynb` nahi | agent | rename to `*.ipynb` (mimeType `application/x-ipynb+json`), phir wahi file id ka Colab link |
| Link kholte hi "not found" | notebook Drive me nahi / sharing off | agent | dobara upload + fresh link |

---

## 7. Turn-end checklist (agent har turn ke aakhir me)

1. `mobile_ops.py status` — koi job `blocked` ya `partial` bacha to aap ko bataya?
2. Job file save + `history` me transition likha?
3. Master hua to md5 + probe + Drive id `receipt` me?
4. `continuity.py checkpoint` + git commit/push?
5. Owner ko sirf **ek** action diya (3 tap / `DONE` / link kholo)?
6. `mobile_ops.py doctor` pass?

---

## 8. "Done" ki definition

Ek reel tab **done** hai jab:

- [ ] job state = `delivered`
- [ ] `delivery/<id>_MASTER.mp4` maujood, > 0 byte, md5 recorded
- [ ] probe: height ≥ 960 (×2 upscale), audio codec = `aac`, duration ≈ shots ka jod
- [ ] `verify` ke saare gates `ok: true`
- [ ] Drive `06 · Masters & Receipts` me master + `05 · Projects/<id>/receipts.json`
- [ ] owner ko link + md5 mila

Isse kam kuch bhi "ban gaya" nahi kehlata.

---

## 9. Hafta-war routine ($0 ko intact rakhne ke liye)

| Kab | Kya |
|---|---|
| har reel se pehle | `quota` dekho (Kaggle counter Sunday 00:00 UTC reset) |
| har reel ke baad | `quota --use <provider> <hours>`, master + receipt Drive me |
| hafte me ek baar | `mobile_ops.py status` — purane `delivered` jobs archive, `blocked` clean |
| quota khatam | Kaggle/Lightning par shift, ya sirf audio+edit (CPU) kaam |
| mahine me ek baar | licence check: MMAudio/MusicGen weights **non-commercial** — client kaam ke liye ThinkSound (Apache) |

Paid route sirf tab, jab aap khud bolo — default zero-spend guard ON rehta hai
(`MONARCH_ALLOW_PAID=1` ke bina koi paid step nahi).

---

## 10. Files kahan hain

```
studio/mobile/jobs/<job_id>.json     # kaun kya karega (state machine, committed)
tools/mobile_ops.py                  # state machine + gates + owner cards
tools/videogen.py                    # engine: plan/mobile/mix/verify/assemble
docs/MOBILE.md                       # aap ka 3-tap card
docs/MOBILE_WORKFLOW.md              # yeh doc (agent ka SOP)
tests/test_mobile_ops.py             # gates + refusals pinned
Drive 05 · Projects/<id>/             # project.json, shots/, audio/, delivery/
Drive 06 · Masters & Receipts/        # <id>_MASTER.mp4
Drive 03 · Colab Notebooks/           # MOBILE_<id>.ipynb (aap ka link)
```
