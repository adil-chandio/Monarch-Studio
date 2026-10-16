# WF-06 · HANDOFF & BUS PROTOCOL

> User ka hukum tha: *"sab agent manager se connect honge — kaam karte waqt bhi aur kaam karne ke baad bhi —
> batayenge kya kar rahe hain, kaise, kis tarah se, kyun."*
> Yeh file wahi **live connection** ko ek protocol banati hai. Vague "chal raha hai" mana hai.

---

## 1. The bus

Ek hi shared channel: **`BUS.md`** (per video, `SHOWFILE` ke andar) + studio ka append-only journal (`tools/continuity.py log`).

Har message ka **fixed format** hai. Isse pata chalta hai kaun, kab, kya, kaise, kyun.

```
[STAGE] [AGENT] [STATUS] — 1 line summary
  WHAT  : exact kaam jo ab ho raha hai / hua
  HOW   : tareeqa, tool, source
  WHY   : yeh kyun zaroori hai (kis gate ya brief se aaya)
  ETA   : waqt (ya —)
  NEED  : kisi cheez ki zaroorat? (warna "nothing")
```

### Status vocabulary (sirf 5 allowed)

| Status | Matlab | Kis waqt |
|---|---|---|
| `START` | Kaam shuru, tareeqa fix | Har stage ke shuru mein |
| `PROGRESS` | Meaningful checkpoint, naya finding/decision | Jab koi asli cheez nikle (har 20 min nahi) |
| `BLOCKED` | Kuch rok raha hai | Turant, chupke nahi |
| `DONE` | Artifact ready | Stage ke aakhir mein |
| `REVISE-ACK` | Manager ki note mil gayi, ab theek kar raha hoon | Har revise par |

**Mana hai:** "kaam ho raha hai", "almost done", "dekhta hoon", khaali status. Jo bus par likha hai woh **artifact se match** karna chahiye.

---

## 2. START / DONE ka poora example

```
[S2] [A03-ARCHITECT] [START] — Script likhna shuru: CLOSE CALL FILES #01
  WHAT  : 3 competitor videos ka teardown + hamari 9-min script
  HOW   : transcripts (auto-captions) → beat map → apna structure; A02 ka RESEARCH_BRIEF base
  WHY   : A01 ka brief — "bear encounter ke 3 ghalat faisle"; gate: hook ≤ 3s, re-hooks 25/50/75%
  ETA   : 2 ghante
  NEED  : nothing
```

```
[S2] [A03-ARCHITECT] [PROGRESS] — Hook ka draft ready, 2.4 second
  WHAT  : "Usne bhagna chuna. Wahi uski sabse badi ghalti thi." — 2.4s par khatam
  HOW   : 4 versions likhe, sabse chhota chuna; competitor ke hook se sirf *device* liya, lafz nahi
  WHY   : gate check — 3s se kam, aur hook ke lafz video mein poore hote hain (A07 ka claim #7)
  ETA   : script 1 ghante mein
  NEED  : A02 se confirm — kis clip mein bhaagta hua aadmi hai? (clip id)
```

```
[S2] [A03-ARCHITECT] [DONE] — SCRIPT.md + TEARDOWN.md + CLAIMS.md ready
  WHAT  : 9:10 ki script, 14 beats, 3 re-hook (2:15 / 4:35 / 6:50), payoff 8:40
  HOW   : 3 competitor teardown ke baad apna structure; har beat ka purpose likha
  WHY   : brief ka promise deliver karti hai; CLAIMS.md mein 11 facts sourced
  ETA   : —
  NEED  : A01 review
  ARTIFACT: SHOWFILE/S2_SCRIPT/SCRIPT.md · TEARDOWN.md · CLAIMS.md
```

---

## 3. The SHOWFILE (ek video = ek file)

Sab kuch ek jagah. Koi agent chat memory par kaam nahi karta.

```
SHOWFILE/
  00_SHOWFILE.md          ← index + current stage + status board
  01_BRIEF.md             ← A01
  02_RESEARCH/            ← A02: RESEARCH_BRIEF.md + sources/
  03_SCRIPT/              ← A03: TEARDOWN.md · SCRIPT.md · CLAIMS.md
  04_VOICE/               ← A04: VOICE_CASTING.md · VO_MASTER.wav · VO_TIMECODES.md
  05_PRODUCTION/          ← A05: TIMELINE.json · GRAPHICS_LIST.md · SFX_LEDGER.csv · MASTER.mp4
  06_PACKAGE/             ← A06: PACKAGE.md · thumb_v1.png · thumb_v2.png · thumb_v3.png
  07_COMPLIANCE/          ← A07: COMPLIANCE_PASS.md / BLOCK.md · CLIP_SOURCES.csv
  08_ANALYTICS/           ← A08: 48h.md · 7d.md · 28d.md · LEARNING_NOTE.md
  BUS.md                  ← sara live reporting
  DECISIONS.md            ← har bara faisla + kyun + kisne
  REVISIONS.md            ← manager ki notes aur unka closure
```

### Status board (SHOWFILE.md ke top par, hamesha updated)

```
VIDEO : CLOSE CALL FILES #01 · "Usne bhagna chuna"
STAGE : S2 SCRIPT — REVISE (round 2/3)
BOARD :
  S0 BRIEF      ✅ APPROVED      A01
  S1 RESEARCH   ✅ APPROVED      A01 (10→3 finalists)
  S2 SCRIPT     🔁 REVISE 2/3    A01 note: hook good, beat 7-9 dheele hain
  S3 VOICE      ⏸ BLOCKED       waiting for script lock
  S4 PROD       ⏸ idle
  S5 PACKAGE    ⏸ idle
  S6 COMPLIANCE ⏸ idle
  S7 PUBLISH    ⏸ idle
  S8 LEARN      ⏸ idle
```

**Rule:** jo agent apna stage shuru karta hai, woh board khud update karta hai — manager ko poochhna nahi padta.

---

## 4. Manager ka verdict format

Manager **kabhi** free-text feedback nahi deta. Yeh format hai:

```
[VERDICT] S2 SCRIPT — REVISE (round 2/3, agent A03)
  SCORE: Hook 5 · Curiosity 4 · Retention 3 · Payoff 4 · Brand 5 · Policy 5 · Polish 4 · Uniqueness 4
  AVERAGE: 4.25   |   RESULT: REVISE (row < 3 rule triggered: RETENTION 3 is at floor, beat map gap)

  FLAW 1 — Beat 7 se 9 tak 45 second khaali hai, koi event nahi.
    FIX  : 7 aur 8 ke darmiyan ek replay insert karo (1.2s slow-mo + freeze + number card).
    TEST : timeline par us 45s mein ≥ 2 naye events count hon.

  FLAW 2 — Payoff hook ka jawab nahi de raha.
    FIX  : payoff ko hook ke exact lafz se jodo ("bhagna = chase trigger") — wahi line end par lautao.
    TEST : hook ki line aur payoff ki line, dono mein ek lafz common hona chahiye.

  FLAW 3 — Claim #6 (bite force) ka source missing hai.
    FIX  : A02 se source lo ya claim hatao.
    TEST : CLAIMS.md mein row ka source URL bhara hua.
```

**Rules:**
- Har flaw **numbered**.
- Har flaw ke saath `FIX` (exactly kya karna hai) aur `TEST` (kaise pata chalega ke theek hua).
- Koi flaw "better karo", "thoda improve karo" jaisa nahi.
- Har verdict `DECISIONS.md` aur `REVISIONS.md` mein likha jata hai.

---

## 5. 3-strike rule (kaam atakne se bachne ke liye)

| Round | Kya hota hai |
|---|---|
| Round 1 | Manager note deta hai → agent fix karta hai |
| Round 2 | Manager dobara dekhta hai → re-note (agar zaroori) |
| Round 3 | Aakhri round. Yahan sirf **chhote, specific** flaws allowed. |
| Round 3 ke baad | A01 teen mein se ek karta hai: **(a)** concept ko simplify karo (kam cheezein, kam minute) **(b)** khud scope fix karo **(c)** KILL karo aur A02 ko wapas bhejo |

**Yeh rule crew ko "infinite polish" se bachata hai.** 3 round ke baad bhi cheez na sudhre to masla agent mein nahi, **concept mein** hai.

---

## 6. Escalation ladder

```
Agent ko masla mila
   │
   ├─ Technical / chhota        → khud hal karo, bus par note karo
   ├─ Dependency (kisi aur ka kaam) → turant BLOCKED + jise chahiye usay tag karo
   ├─ Quality par shak          → A01 ko bhejo verdict ke liye (khud approve mat karo)
   ├─ Rights / policy ka shak   → A07 ko bhejo. A07 ka BLOCK final hai.
   └─ Brand / direction / paisa  → HUMAN ko. A01 bhi yahan ruk jata hai.
```

**Response time expectation (spirit, tool nahi):** `BLOCKED` message 1 ghante ke andar raise ho — chupke intezaar karna mana hai. Jo agent blocked hai aur nahi batata, woh sabse bara nuqsaan hai.

---

## 7. Doosre agents se "bond" kaise formal hota hai

User ne kaha: *"sab bhaiyon ki tarah ek group mein kaam karenge."* Woh yahan **teen cheezon** mein convert hota hai:

1. **Shared file, shared truth.** Koi apni private copy nahi banata. Sab ek `SHOWFILE` par kaam karte hain.
2. **Cross-review.** A03 A05 ka edit dekhta hai (kahani waisi hi hai ya nahi?), A02 A06 ke package ko dekhta hai (demand match hai ya nahi?). Manager final hai.
3. **Handoff respect.** Jo agent agla hai, usay pichle agent ka kaam **poora** milta hai — adhoora kaam aage nahi jata. Adhoora bhejna = bus par `BLOCKED`, chupke aage badhna nahi.

Aur ek rule: **koi agent doosre agent ka kaam chupke se "theek" nahi karta.** Jo badalna hai, bus par likho aur owner se karwao. Warna pata nahi chalta kaun ghalat tha, aur crew seekh nahi paati.

---

## 8. Studio ke saath wiring

| Protocol ka hissa | Studio ka tool |
|---|---|
| Live bus + after-report | `python3 tools/continuity.py log --kind <action\|result\|error\|decision>` |
| Showfile ke checkpoints | `python3 tools/continuity.py checkpoint --summary … --next-action …` |
| Stage board | `workflows/current/ACTIVE_TASK.json` + `RESUME.md` |
| Faislay | `DECISIONS.md` + journal `--kind decision` |
| Long-running renders | `python3 tools/continuity.py process` (process IDs track) |

Yani crew ka bus **naya system nahi** hai — studio ka maujooda hash-chained journal hi bus hai. Isse history permanent rehti hai.
