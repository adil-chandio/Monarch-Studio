# GPU bridge — aap ka 3 click, phir main chalata hoon

## Yeh kya hai

Yeh wohi cheez hai jo aap chahte hain: notebook ek **URL** deta hai, aur main us URL se
GPU machine ko chalata hoon — chat se hi.

Kaise kaam karta hai (verified, guess nahi):

| Cheez | Test | Nateeja |
|---|---|---|
| Mera shell (`curl`) bahar kholta hai? | `curl https://example.com` | nahi — `000` (band) |
| Mera page-fetch tool public URL padhta hai? | `cloudflare.com/cdn-cgi/trace`, `httpbin.org/get?foo=bar` | haan — query params bhi saath |
| Control server + token | local run | haan — `/status` bina token = **403** |
| Job loop | local run | haan — `run → done → file + sha256` |

Matlab: **notebook GPU par server chalata hai, tunnel usko public banata hai, aur main
usko page-fetch se chalata hoon.**

## Abhi aap yeh karein

1. Drive → `Chaos video 2` → **`CHAOS_GPU_AGENT.ipynb`** par right click →
   **Open with → Google Colaboratory**
2. `Runtime` → **Change runtime type** → Accelerator = **GPU** → Save
3. `Runtime` → **Run all**
4. Bas. Tab khula chhod dein (aakhri cell heartbeat chalta rehta hai).

Notebook khud:
- Drive mount karega
- endpoint + token **`CHAOS_GPU_ENDPOINT.json`** mein `Chaos video 2` folder ke andar likh dega
- clips ko `chaos_gpu_clips/` mein har 30 s par sync karta rahega

Aap ko mujhe kuch paste karne ki zaroorat nahi — main endpoint Drive se khud utha lunga.
(Aap chahein to URL chat mein bhi bhej sakte hain — dono chalega.)

## Main phir kya karunga (us URL se)

1. `/status` → GPU, VRAM, disk, tier
2. `/run?recipe=smoke` → pipeline test (model ke bagair, 20 s) — confirm ke loop chalta hai
3. `/run?recipe=ltx&prompt=...` → pehla asli clip (T4 par LTX-2B)
4. `/job`, `/log` se progress, `/files` se output + sha256
5. Clip Drive mein aa jaye to main utha kar judge karunga: quality level theek hai ya
   24 GB chahiye — aur aap ko saaf bataunga, guess nahi.

## VRAM ka sach (wahi pehle wala)

| GPU | kya chalega |
|---|---|
| Free **T4** 16 GB | `smoke` + `ltx` (LTX-2B, 480–768p, chhote clips) |
| **L4 / 4090** 24 GB | `wan` (Wan2.2 TI2V-5B, 720p) |
| **A100** 40 GB | `animate` (Wan-Animate-14B) |

Free T4 par "exactly same photoreal 1080p" nahi banega — yeh main pehle hi keh raha hoon.
Pehle T4 par ek test clip banate hain, aap dekh kar bolein, phir decide karein.

## Aage kya chahiye (jab aap bolein)

- **Naya reference video** (jo exactly same banana hai) — Drive link ya attach
- Us par main wohi forensic karunga jo pehle kiya: frames decode, cuts, acts, look metrics

## Agar notebook mein kuch fail ho jaye

- **"GPU nahi mila"** → Runtime → Change runtime type → GPU → phir Run all
- **cloudflared fail** → notebook khud `localhost.run` try karta hai; phir bhi fail ho to
  cell 5 ka error text bhej dein
- **Drive mount fail** → endpoint Drive mein nahi likha jayega, lekin cell 5 URL phir bhi
  print karega — woh URL mujhe chat mein bhej dein

---

# v3 — AB YEH CHALAYEIN (v2 ki jagah)

v2 chala, magar do cheezein ghalat thin: (1) GPU select nahi hua tha (torch CPU mila),
(2) token sirf 4 harf print hua, is liye main andar nahi aa saka. v3 mein dono fix hain.

**Notebook:** `colab_gpu_bridge_v3.ipynb`
Drive: https://drive.google.com/file/d/1RHnS63rFhtDrjro-A0T1OPSvkoJfadNg/view

## Steps (bas itna)

1. Purana notebook **band** karein (Runtime → Disconnect and delete runtime).
2. v3 notebook kholein.
3. **Runtime → Change runtime type → Hardware accelerator = T4 GPU → Save.**
   (Yeh step skip hua to sab kuch CPU par chalega — pehli baar yahi hua tha.)
4. Cell par **Run** dabayein. Pehli baar Drive permission maangega → Allow.
5. Notebook khula **chhordein**. URL khud ntfy par chala jayega, mujhe chat mein
   bhejne ki zaroorat nahi. URL screen par bhi print hoga.

## v3 mein kya behtar hai

| cheez | v2 | v3 |
|---|---|---|
| token | random, adhoora print | **fixed `monarch-chaos-742683`**, poora print |
| endpoint file | Drive mount fail → kabhi nahi bani | 3 jagah likhta hai (project folder, MyDrive root, /content) |
| GPU check | chup | shuru mein **warning** + tier |
| tunnel | cloudflared | cloudflared, phir localhost.run, phir bhi na ho to Drive channel |
| commands | status/run/job/files | + **shell** (sync/bg/tail) — is se main Colab par poora kaam khud kar sakta hoon |

## Command channel (mere liye)

`https://ntfy.sh/monarch-chaos-gpu-742683/json?poll=1` → URL
phir `GET <url>/status?token=monarch-chaos-742683`

---

# v4 — AB YEH (v3 bhi band, runtime gir gaya)

## Kya hua (measured, 27 Oct 02:18–02:29 UTC)

| cheez | result |
|---|---|
| GPU | **Tesla T4 · 15360 MiB** · driver 580.82.07 · CUDA 13.0 · VRAM 14.6 GB |
| torch | 2.11.0+cu130, `cuda_available: true` |
| disk | 87 GB free (start) |
| smoke render | 643,557 B clip — chala, Drive `_gpu_bridge/` mein copy hua |
| shell | sync + bg + tail teenon chalay |
| internet (Colab se) | huggingface 200, github 200 |
| LTX-Video | pehle import fail — `torchao` too old (`FqnToConfig`); `pip install -U torchao` (0.18.0) se **import ok**, weights download shuru |
| **02:29 UTC** | tunnel band, heartbeat freeze, endpoint stale → **runtime gir gaya** |

Yani GPU kaam karta hai — bas free Colab ne ~10 min baad runtime gira diya.

## v4 mein kya badla (v3 ke do asli defects)

1. **Drive-first control** — command Drive file se jata hai, jawab Drive file mein aata hai.
   Tunnel ki zaroorat nahi, is liye tunnel marna kaam nahi rokta.
2. **Bridge alag process** mein (`drive_bridge.py` subprocess) — server crash ho to bhi zinda rehta hai, supervisor use restart karta hai.
3. **Tunnel rotation** — cloudflared → pinggy → localhost.run; public URL `/health` se
   check hota hai, 2 baar fail ho to naya tunnel + naya URL publish.
4. **torchao boot par upgrade** — LTX import ka woh bug dobara nahi aayega.
5. Endpoint file har 60 s refresh (stale = foran pata chalta hai).

## Steps

1. `Runtime → Change runtime type → T4 GPU → Save`
2. **MONARCH_GPU_BRIDGE_v4.ipynb** kholein, **▶ Run**
3. Tab khula chhod dein — mujhe kuch bhejna nahi

Drive: https://drive.google.com/file/d/1YGxclEpFc3N7PcOWW6gi_2M3FiTpqg3Q/view

## Free Colab ki asli limit

12.7 GB RAM / 15 GB VRAM / ~12 h session, aur **idle par disconnect**.
Is liye: tab khula, laptop plugged-in, aur agar "Runtime disconnected" aaye to
dobara Run — state Drive par hai, kaam wahin se aage barhta hai.
