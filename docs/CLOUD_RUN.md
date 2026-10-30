# Backend run — phone band ho tab bhi film banti rahe

> Colab ka masla: tab band kiya to runtime gir jata hai. Is liye ab **GitHub Actions** chalta hai:
> GPU ka kaam Kaggle par jata hai (API se, koi notebook kholna nahi padta), jabki **master + launch
> kit GitHub ke CPU par** bante hain. Sab kuch backend me — owner ka phone band ho to bhi.

## Ek dafa ka setup (2 minute, sirf ek baar)

1. kaggle.com → Google se sign in → **Settings → API → Create New Token** (kaggle.json download hoga).
2. GitHub app/web → repo `adil-chandio/Monarch-Studio` → **Settings → Secrets and variables → Actions**
   → **New repository secret**:
   - `KAGGLE_USERNAME` = aapka Kaggle username
   - `KAGGLE_KEY` = `kaggle.json` me `"key"` ke aage wali value

Bas. Ye do cheezein **kabhi chat me nahi bhejni** — GitHub unhein encrypted rakhta hai, agent sirf
secret ke andar se use karta hai.

## Run kaise hota hai (owner: zero tap, agent: ek command)

Actions → **Kaggle film (backend)** → *Run workflow*.

Andar kya hota hai (`scripts/kaggle_chunks.sh` + `tools/make_kaggle_kernel.py`):

1. scenes 3 chunks me bante hain (default 4 + 4 + 4) — har chunk ek private Kaggle kernel,
   GPU T4, internet on, `--only` us chunk ke scenes;
2. chunk poora hone par `kaggle kernels output` se **clips download** hoti hain (GitHub Actions me);
3. chunk fail ho to **usi run me dobara** try hota hai; phir bhi na ho to baqi chunks chalte rehte hain;
4. saari clips aane par CPU par `--assemble-only` chalta hai → **master 36s + launch kit**
   (teaser, cover, subtitles, contact sheet, kit.md);
5. deliverable **artifact** + **GitHub Release** me chala jata hai: `film-r<N>`.

Session dead ho jaye beech me? Clips jo aa chuki hain woh `clips/` me hain — agli run me sirf
bachi hui scenes ka chunk daal dena (`chunks` input me), baqi skip.

## Kyun yeh Colab se behtar hai

| | Colab (phone) | GitHub Actions + Kaggle API |
|---|---|---|
| tab/phone band | runtime gir jata hai | chalta rehta hai |
| kaun chalata hai | owner | agent (`gh workflow run`) |
| GPU quota | free T4, idle disconnect | 30 GPU-h/week, session 9–12 h |
| master + kit | notebook me | Actions par, har run same |
| deliverable | Drive manual | Release + artifact + (agent Drive me daal deta hai) |

## Trigger kaise hota hai (technical)

`workflow_dispatch` sirf default branch par kaam karta hai, is liye run **push** se shuru hota hai:

- `cloud/kaggle_jobs/*.json` ka naya commit (chunks + title), ya
- pipeline file ka change (`tools/kaggle_stick_film.py`, `tools/film_factory.py`, `scripts/kaggle_chunks.sh`)

Agent `gh run rerun <id>` se bhi dobara chala sakta hai — owner ko kuch nahi karna.

## Bina secrets bhi green

Secrets na hon to workflow **dry run** karta hai: 3 keyframes ke stills se clips banata hai,
poora master + kit assemble karta hai, artifact upload karta hai — pipeline toota hua foran pakra
jata hai, aur jab secrets add ho jayein tab *wahi* run asli GPU render karta hai.

## Status

- 2026-10-30: workflow registered + dry-run green (artifact `monarch-film-3`, 26 MB).
- Baqi: owner ke 2 secrets (Kaggle username + key) — uske baad 12 scenes ka asli render.

## 2026-10-30 raat — asli render chal raha hai (state)

- Kaggle user: `compali` (verified). GPU quota: 30 h/week, ~0.2 h used at start.
- **k01 render ho gaya** (kernel `compali/monarch-s2-1`, Wan 2.2 I2V, T4).
- Seekhe hue sabak (sab fix ho chuke):
  1. kernel title ka slug = kernel id ka slug warna `409 Conflict`;
  2. `ftfy` (aur sentencepiece/safetensors/regex) chahiye — warna `NameError: ftfy`;
  3. T4 16 GB par Wan 2.2 5B + umt5 **model_cpu_offload se OOM** → `enable_sequential_cpu_offload`
     + VAE tiling; phir bhi OOM ho to canvas 384×672, phir LTX-Video 2B.
- Live status branch: `ci-status` (`status.txt`) — har kernel event wahan likha jata hai.
- Chunk 1 kernel me **2 GPU parallel** (Kaggle T4 x2): scenes aadhe ho kar dono GPU par.
- Ab chal raha: k02–k12 (3 chunks), ~5 ghante. Uske baad master + teaser + cover + srt + sheet,
  artifact + Release (`film-r<N>`) khud ban jate hain.
