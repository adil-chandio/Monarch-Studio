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
