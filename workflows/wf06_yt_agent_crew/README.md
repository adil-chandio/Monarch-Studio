# WF-06 · MONARCH YT AGENT CREW

**Code:** `WF-06` · **Resume key:** `CREWGO <topic>` · **Status:** structure defined (no code by design)
**Local root:** `workflows/wf06_yt_agent_crew/` · **Created:** 2026-10-16 · **Task:** `EMS-20261016-004`

> Yeh **structure** hai, implementation nahi. User ka hukum: *"sab se pehle code wagera kuch NAHI karna, bas pooora structure banao."*
> Yahan har agent ka role, input, output, gate, escalation aur reporting defined hai — aur woh **gaps** fill kiye gaye hain
> jo is crew ko tabahi level tak jaane se rok rahe thay.

---

## 0. Yeh system kya hai (ek para)

Ek YouTube video banane ka **poora office**, jisme 8 agents hain. Har agent apni ek cheez ka expert hai.
**A01 MANAGER** sab ko kaam deta hai, sab ka kaam dekhta hai, approve karta hai, aur galat hone par numbered flaws de kar
wapas bhejta hai. Sab agents **manager se live connected** rehte hain — kaam karte waqt bhi (`START` / `PROGRESS` / `BLOCKED`)
aur kaam ke baad bhi (`DONE` + 3 lines: kya kiya, kaise kiya, kyun kiya). Koi agent akela kaam nahi karta, aur koi agent
apna hi kaam approve nahi kar sakta.

---

## 1. Chain of command (org chart)

```
                    ┌──────────────────────────────────────────┐
                    │   HUMAN OWNER  (adil)                    │
                    │   • final call • presses PUBLISH         │
                    │   • can override anyone, anytime         │
                    └────────────────────┬─────────────────────┘
                                         │
                    ┌────────────────────▼─────────────────────┐
                    │   A01 · MANAGER  ("The Boss")            │
                    │   doctrine keeper · assigns · reviews    │
                    │   APPROVE / REVISE / KILL · resolves     │
                    └──┬────────┬────────┬────────┬────────────┘
                       │        │        │        │
        ┌──────────────┘        │        │        └──────────────┐
        ▼                       ▼        ▼                       ▼
  ┌───────────┐          ┌───────────┐ ┌───────────┐     ┌──────────────┐
  │ A02 HUNTER│          │A03 ARCHIT│ │A04 VOICE  │     │ A05 CRAFTSMAN│
  │ research  │          │ script   │ │ casting+VO│     │ edit/produce │
  │ + ideas   │          │ writing  │ │           │     │              │
  └─────┬─────┘          └─────┬────┘ └─────┬─────┘     └──────┬───────┘
        │                      │            │                  │
        └──────────┬───────────┴─────┬──────┴──────────┬───────┘
                   ▼                 ▼                 ▼
            ┌────────────┐   ┌──────────────┐   ┌──────────────┐
            │ A06 PACKAGER│  │ A07 WARDEN   │   │ A08 ORACLE   │
            │ title/thumb │  │ compliance   │   │ analytics +  │
            │ /metadata   │  │ ★ VETO POWER │   │ learning     │
            └────────────┘   └──────────────┘   └──────┬───────┘
                                                       │
                                        feeds back into ▼  A02 HUNTER
                                        (loop closes — the crew LEARNS)
```

**Authority rule:** A01 decides quality. **A07 decides legality** — A07 ka `FAIL` A01 ke `APPROVED` ko bhi rok deta hai.
Sirf HUMAN OWNER dono ko override kar sakta hai, aur woh override likh kar diya jayega.

---

## 2. Agents (8) — ek nazar mein

| Code | Name | Kaam | Output artifact | Gate |
|---|---|---|---|---|
| **A01** | **MANAGER** | doctrine, assignment, review, conflict, kill | `SHOWFILE` + review verdicts | rubric ≥ 4.0 aur koi row < 3 nahi |
| **A02** | **HUNTER** | competitor + platform reverse-engineering, idea hunting | `RESEARCH_BRIEF` (10 topics → 3 finalists) | har claim sourced; 10x-factor ≥ 4 |
| **A03** | **ARCHITECT** | script teardown + script writing | `SCRIPT` + `TEARDOWN` | hook ≤ 3s; beat map; 25/50/75 re-hooks |
| **A04** | **VOICE** | voice casting + voiceover | `VOICE_CASTING` + `VO_MASTER` | audition ≥ 2 voices; duration ±5% |
| **A05** | **CRAFTSMAN** | edit, graphics, SFX, BGM, master | `TIMELINE` + `MASTER` + `SFX_LEDGER` | measured gates (see §5) |
| **A06** | **PACKAGER** | title, thumbnail, metadata, timing, CTR | `PACKAGE` (3 titles + 3 thumbs + upload plan) | title laws; thumb readable @120px |
| **A07** | **WARDEN** | rights, policy, disclosure, claims | `COMPLIANCE_PASS` or `BLOCK` | 100% source rows; ≥ 3 original layers |
| **A08** | **ORACLE** | post-publish analytics → lessons | `LEARNING_NOTE` @48h/7d/28d | numbers only, no opinions |

---

## 3. The 10 operating laws (in ke bagair crew bikharta hai)

1. **One show file.** Har video ka ek `SHOWFILE`. Sab agents usi se parhte hain, usi mein likhte hain. Chat memory par koi bharosa nahi.
2. **Artifact-first.** "Main ne kar diya" valid nahi. Sirf file valid hai.
3. **Live bus.** Har agent kaam shuru karte waqt `START` bhejta hai, aur khatam hone par `DONE`. Manager jab chahe dekh sakta hai.
4. **No self-approval.** Koi apna kaam approve nahi karta. A03 ki script A01 dekhta hai; A05 ka edit A03 (fidelity) + A01 (quality) dekhte hain.
5. **Numbered feedback.** Manager ki har note numbered hoti hai: *kya galat hai* + *kaise theek karo* + *acceptance test*.
6. **3-strike rule.** Ek hi note par agent maximum 3 baar revise karta hai. Phir A01 decide karta hai: khud fix karo, concept simplify karo, ya KILL karo.
7. **Evidence or it didn't happen.** Research ka har claim ke saath URL + quote/screenshot + date.
8. **10x-factor mandatory.** Har concept mein ek naam-le-layak cheez honi chahiye jo doosre channels ke paas nahi. Agar jawab "behtar editing hai" hai → **KILL**.
9. **Truth in the hook.** Hook dramatic ho sakta hai, jhoota nahi. Jo hook promise kare, video woh de. (Yeh ethics nahi, **mechanism** hai — neeche §6 dekho.)
10. **Human publishes.** Agents sirf tayyari karte hain. Publish button insaan dabata hai.

---

## 4. The production pipeline (S0 → S8)

| Stage | Owner | Kya banta hai | Kaun check karta hai | Gate |
|---|---|---|---|---|
| **S0 BRIEF** | A01 | `SHOWFILE` §1: promise, audience state, ek feeling, target metric | — | promise 1 line mein, metric number mein |
| **S1 RESEARCH** | A02 | 10 topics → 3 finalists, har ek ka full teardown | A01 | sources complete; 10x ≥ 4 |
| **S2 SCRIPT** | A03 | 3 competitor teardowns + hamari script (beat map ke saath) | A01 + A07 pre-check | hook ≤ 3s, re-hooks 25/50/75%, koi claim be-source nahi |
| **S3 VOICE** | A04 | casting decision + VO master | A01 | ≥ 2 auditions, duration ±5% |
| **S4 PRODUCTION** | A05 | timeline, graphics, SFX/BGM ledger, master | A03 fidelity + A01 quality | measured gates (§5) |
| **S5 PACKAGING** | A06 | 3 titles, 3 thumbnails, metadata, upload timing | A01 | title laws + thumb legibility |
| **S6 COMPLIANCE** | A07 | `COMPLIANCE_PASS` ya `BLOCK` | — (veto) | 100% source rows |
| **S7 PUBLISH** | HUMAN | video live | A06 schedules + A08 baseline | — |
| **S8 LEARN** | A08 | 48h / 7d / 28d numbers + lessons | A01 → library | numbers only |

**S8 se S1 tak loop band hota hai.** Yeh loop is poore system ki asli jaan hai — iske bagair crew sirf mehnat karega, seekhega nahi.

---

## 5. Measured gates (numbers, "acha laga" nahi)

A05 ka kaam in par judge hoga (studio ke maujooda gates inherit karta hai):

| Cheez | Target | Source of truth |
|---|---|---|
| Hook frame | 0.0s par motion, ≤ 0.8s visual question, ≤ 3s promise | `studio/editor-brain/MONARCH_EDITOR_BRAIN.md` §4 |
| Cut cadence | long-form: har 20–30s ek naya event; koi 30s khaali nahi | timeline |
| Re-hooks | 25% / 50% / 75% par | script beat map |
| First-30s retention | ≥ 70% | Studio analytics (48h) |
| AVD | ≥ 45% (long-form) | Studio analytics |
| CTR | ≥ 4% | Studio analytics |
| Loudness | −16.5 ± 1 LUFS, LRA ≈ 4.5 | master measurement |
| Thumbnail | 120px par padha jaye, 3 elements max | manual test |
| Source coverage | **100%** clips ki row `CLIP_SOURCES.csv` mein | A07 |

---

## 6. Chhupa hua sach: "brain control" ka sahi tareeqa

Voice note mein kaha gaya tha — *"unke brain ko control karke hypnotize karke rokna hai"*. Us energy ko yahan
**aisa** define kiya gaya hai jo kaam bhi kare aur channel bache bhi:

**Deceptive hook pehle din kaam karta hai, phir channel maar deta hai.**
Aapke apne channel ka data yeh saabit karta hai:
- Bear video (dramatic lekin **sach** hook) → 955,681 views
- AI-clickbait title wala video → **16 views, 0 likes**

Mechanism: jhoota hook CTR uthata hai, phir AVD girata hai. YouTube AVD dekhta hai → distribution band.
Iske sath like rate: best video par 0.36%, recent par 0.66% — healthy 2–4% hota hai.

**Isliye doctrine:** hook *tension* bechta hai, *jhoot* nahi. Video hook ka poora waada poora karti hai.
Yeh morality nahi — **yeh algorithm ka hi tareeqa hai.** Detail: `COMPLIANCE_AND_ETHICS.md`.

---

## 7. Studio integration (naya engine nahi banao)

| Crew needs | Studio already has |
|---|---|
| Live reporting bus | `tools/continuity.py log` (hash-chained journal, live + after) |
| Editor doctrine + 19+1 gates | `studio/editor-brain/MONARCH_EDITOR_BRAIN.md` |
| Idea/concept DNA + freshness gate | `studio/editor-brain/brain/concept.py` (gate #20) |
| Reference study tool | `studio/editor-brain/brain/study.py` |
| VO production | Arena `add_voice` + `generate_speech` (voice library) |
| Style engines for owned IP | `styles/monarch-stickman-animation`, `monarch-noir-film`, `premium-motion-editing` |
| Market truth (real channel data) | `channel/` (audit + plan + snapshot) |
| Clip rights register | `channel/data/CLIP_SOURCES.csv` |

---

## 8. Files in this workflow

| File | Kya hai |
|---|---|
| [`AGENT_SPECS.md`](AGENT_SPECS.md) | 8 agents ki poori spec: role, input, output, rules, escalation, "yeh kabhi nahi karega" |
| [`HANDOFF_AND_BUS.md`](HANDOFF_AND_BUS.md) | Reporting protocol, SHOWFILE format, status vocabulary, artifact formats |
| [`GATES_AND_SCORECARDS.md`](GATES_AND_SCORECARDS.md) | Stage gates, Manager ka 8-point rubric, escalation ladder, kill rules |
| [`COMPLIANCE_AND_ETHICS.md`](COMPLIANCE_AND_ETHICS.md) | Rights, policy, disclosure, claims — A07 ka rulebook |
| [`LEARNING_LOOP.md`](LEARNING_LOOP.md) | A08: 48h/7d/28d snapshots → lessons → next brief |
| [`RUNBOOK_S01E01.md`](RUNBOOK_S01E01.md) | Pehli asli video par poore crew ka exact run |

## 9. Resume

```bash
python3 tools/continuity.py resume
# read workflows/wf06_yt_agent_crew/RUNBOOK_S01E01.md
# pick the first stage whose gate has not passed
```

Next free WF code after this: **WF-07** (WF-04 was skipped historically and is not reused).
