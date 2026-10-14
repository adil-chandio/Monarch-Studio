#!/usr/bin/env python3
"""MONARCH EDITOR BRAIN — the pro editor's working memory as a tool.

    python3 brain/concept.py status                       what is blocked / fresh right now
    python3 brain/concept.py propose --topic "..." --dur 60 [--n 3] [--mood dark] [--seed 7] [--format short|film|wtf30]
                                                          -> 3 Concept-DNA briefs (brain/briefs/*.md + brain/dna/*.json)
                                                          wtf30 = the 20–30 s impossible-moment short (MONARCH_WTF30_DOCTRINE.md)
    python3 brain/concept.py gate brain/dna/<slug>.json   freshness gate (#20) against the registry — PASS/FAIL with numbers
    python3 brain/concept.py cadence --module respect2    retention cadence of a real timeline (shots, gaps, interrupts)
    python3 brain/concept.py commit brain/dna/<slug>.json --drive-id ID --md5 MD5   remember the delivered video
    python3 brain/concept.py export                       library + registry as one JSON (for Notion/Drive)

Law: same identity, never the same video.  Novelty is a gate, not a vibe.
"""
import argparse, datetime, hashlib, json, math, os, random, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import library as L  # noqa: E402

REG_PATH = os.path.join(HERE, "registry.json")
MOODS = ["dark", "warm", "tense", "calm", "fast", "slow", "playful", "epic"]
CONTRA = {("dark", "warm"), ("fast", "slow"), ("playful", "tense")}
THEMES = ["social", "inner", "physical", "mind", "money", "status", "time", "fear"]
THEME_WORDS = {
    "money":    ["paisa", "paise", "money", "dollar", "kamai", "income", "amir", "rich", "business", "earn"],
    "status":   ["izzat", "respect", "power", "powerful", "taqat", "status", "leader", "boss", "hukumat", "alpha", "winner"],
    "time":     ["waqt", "time", "subah", "raat", "din", "discipline", "routine", "late", "jaldi", "saal", "umar"],
    "inner":    ["khud", "self", "dar", "fear", "discipline", "himmat", "confidence", "soch", "ego", "akela", "alone", "sabr"],
    "social":   ["log", "dost", "friends", "crowd", "family", "rishta", "society", "duniya", "people", "baat", "bolna"],
    "physical": ["jism", "body", "gym", "sehat", "health", "neend", "sleep", "khana", "fitness", "energy"],
    "mind":     ["dimagh", "mind", "focus", "padho", "study", "seekho", "learn", "soch", "brain", "aadat", "habit", "galti", "mistake"],
    "fear":     ["dar", "fear", "khauf", "failure", "haar", "lose", "sharam", "shame", "risk"],
}


def topic_themes(topic):
    words = re.findall(r"[a-z]+", topic.lower())
    found = [t for t, ws in THEME_WORDS.items() if any(w in ws for w in words)]
    return found or ["inner", "mind"]

# windows = number of most recent delivered videos in which the item must NOT appear (99 = never again)
RULES = {"hook": 3, "device": 3, "world": 99, "grammar": 2, "camera": 2, "sonic": 2, "type": 2, "ending": 2,
         "signature": 99, "trans_overlap_max": 0.40, "trans_new_min": 3, "sfx_new_min": 0.50}


# ───────────────────────────────────────────── registry / usage
def load_reg():
    with open(REG_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_reg(reg):
    with open(REG_PATH, "w", encoding="utf-8") as f:
        json.dump(reg, f, ensure_ascii=False, indent=2)


def usage(reg):
    """slot -> id -> recency rank list (0 = most recent video)."""
    vids = list(reversed(reg["videos"]))
    u = {s: {} for s in L.SLOTS}
    u["signature"] = {}
    for rank, v in enumerate(vids):
        for s in L.SLOTS:
            val = v["slots"].get(s)
            if val:
                u[s].setdefault(val, []).append(rank)
        for w in v.get("worlds_also", []):
            u["world"].setdefault(w, []).append(rank)
        sig = v.get("signature")
        if sig:
            u["signature"].setdefault(sig, []).append(rank)
    return u


def blocked(slot, item_id, u):
    ranks = u.get(slot, {}).get(item_id)
    return bool(ranks) and min(ranks) < RULES[slot]


def all_prev_kinds(reg):
    return set(k for v in reg["videos"] for k in v.get("transitions", []))


def all_prev_sfx(reg):
    return set(k for v in reg["videos"] for k in v.get("sfx_voices", []))


# ───────────────────────────────────────────── targets derived from duration
def load_refs():
    fp = os.path.join(HERE, "references.json")
    if os.path.exists(fp):
        with open(fp, encoding="utf-8") as f:
            return json.load(f).get("studies", [])
    return []


FORMATS = {
    # short: the vertical v9 identity (default).  film: 16:9 short film 2–4 min, text-narration allowed, holds allowed.
    # wtf30: the 20–30 s impossible-moment short (MONARCH_WTF30_DOCTRINE.md) — one physical law broken once, in one uncut shot,
    #        legible muted, loop-seamed, platform-normalised loudness.  Density unit = physical events (beats), not cuts.
    "short": {"aspect": "1080x1920", "shot_div": 2.4, "max_still_s": 0.4, "new_every": "2–3", "lufs": "-11.6 ± 0.9 (gate −12.5..−10.5)", "holds": "none > 4 s"},
    "film":  {"aspect": "1920x1080", "shot_div": 3.6, "max_still_s": 1.5, "new_every": "3–6 (a hold must carry a line, a light or a music change)", "lufs": "-16.5 ± 1.0, LRA ≈ 4.5, last 10 s ≤ −26 dB RMS", "holds": "7–14 s allowed when carried; bursts on the beat between them"},
    "wtf30": {"aspect": "1080x1920 (4:5 safe centre y 285–1635)", "shot_div": 4.0, "max_still_s": 0.4, "new_every": "≤ 2.5 (a physical event: light, prop, scale, readout, line — measured as beats)", "lufs": "-14.0 ± 1.0, TP ≤ −1.0 dBTP, no noise floor", "holds": "exactly one uncut set-piece ≥ 3 s containing the impossible moment; no other shot > 4 s"},
}

# WTF-30 constants (doctrine §3/§11) — windows are fractions of the duration so 20 s and 30 s scale correctly.
WTF30 = {
    "duration_range_s": (20.0, 30.0),
    "wtf_onset_window": (0.24, 0.40),      # 6–10 s of 25 s; the share-thumb must arrive before the ≈12 s scroll cliff
    "wtf_onset_hard_max_s": 12.0,
    "wtf_uncut_min_s": 3.0,
    "beat_div": 1.5,                       # beats ≥ dur / 1.5
    "max_beat_gap_s": 2.5,
    "on_screen_words_max": 7,              # excluding the meaning line
    "meaning_words_max": 7,
    "meaning_snap_window": (0.70, 0.90),
    "silence_before_wtf_s": (0.3, 0.6),
    "transition_kinds_min": 3,
    "new_transition_kinds_min": 1,         # the impossible transition itself is the new kind
    "lufs": (-15.0, -13.0),
    "true_peak_max_db": -1.0,
}


def targets(dur, device, fmt="short"):
    F = FORMATS.get(fmt, FORMATS["short"])
    shots = max(6, int(round(dur / F["shot_div"])))
    trans = shots - 1
    t = {
        "format": fmt, "aspect": F["aspect"], "loudness": F["lufs"], "holds": F["holds"],
        "callbacks_min": 3 if fmt == "film" else 1,
        "quotable_payoff_lines": 2,
        "duration_s": dur,
        "shots_min": shots,
        "transitions": trans,
        "transition_kinds_min": (4 if fmt == "film" else max(8 if dur >= 40 else 5, math.ceil(trans / 4))),
        "transition_kinds_note": ("film: cut-grammar kinds (hard cut, dip, flash cut, montage accelerando, micro-cuts, insert cutaway…) — no 3-D wipes" if fmt == "film" else "3-D transition kinds, one per boundary"),
        "new_transition_kinds_min": RULES["trans_new_min"],
        "transition_overlap_max": RULES["trans_overlap_max"],
        "pattern_interrupts_min": (int(dur // 12) if fmt == "film" else int(dur // 6.5)),
        "wtf_moments_min": (max(2, int(round(dur / 60))) if fmt == "film" else max(2, int(round(dur / 30)))),
        "rehook_at_s": [round(dur * q, 1) for q in (0.25, 0.5, 0.75)],
        "sfx_new_share_min": RULES["sfx_new_min"],
        "chapters": device[5].split(","),
        "voice_word_one_by_s": 0.6,
        "visual_question_by_s": 0.8,
        "promise_by_s": 3.0,
        "new_on_screen_every_s": F["new_every"],
        "max_still_s": F["max_still_s"],
        "gates": "19 measured gates of IZZAT v2 + gate #20 freshness",
    }
    if fmt == "wtf30":
        W = WTF30
        t.update({
            "shots_min": max(4, int(round(dur / F["shot_div"]))),
            "transitions": max(3, int(round(dur / F["shot_div"])) - 1),
            "transition_kinds_min": W["transition_kinds_min"],
            "transition_kinds_note": "wtf30: cut grammar + the impossible transition itself; never a cut inside the WTF window",
            "new_transition_kinds_min": W["new_transition_kinds_min"],
            "pattern_interrupts_min": max(2, int(dur // 6.5)),
            "wtf_moments_min": 2,              # 1 primary impossible moment (uncut) + ≥ 1 aftershock in the consequence window
            "beats_min": int(math.ceil(dur / W["beat_div"])),
            "max_beat_gap_s": W["max_beat_gap_s"],
            "duration_range_s": list(W["duration_range_s"]),
            "wtf_onset_window_s": [round(dur * W["wtf_onset_window"][0], 1), round(min(dur * W["wtf_onset_window"][1], W["wtf_onset_hard_max_s"]), 1)],
            "wtf_uncut_min_s": W["wtf_uncut_min_s"],
            "silence_before_wtf_s": list(W["silence_before_wtf_s"]),
            "on_screen_words_max": W["on_screen_words_max"],
            "meaning_words_max": W["meaning_words_max"],
            "meaning_snap_window_s": [round(dur * W["meaning_snap_window"][0], 1), round(dur * W["meaning_snap_window"][1], 1)],
            "loop_seam": "last frame rejoins frame 1 (≤ 6/255 mean abs difference or a designed match-cut)",
            "law_broken": "exactly one of " + ", ".join(L.LAW_IDS),
            "cta": "none in picture (caption only)",
            "gates": "19 measured gates + gate #20 freshness + the 13 WTF gates (doctrine §11)",
        })
    return t


# ───────────────────────────────────────────── scoring
def mood_tally(items):
    t = {m: 0 for m in MOODS}
    for it in items:
        for tag in it[3]:
            if tag in t:
                t[tag] += 1
    return t


def score(card, want_mood=None, themes=()):
    items = [card[s] for s in L.SLOTS]
    t = mood_tally(items)
    total = sum(t.values()) or 1
    top = sorted(t.items(), key=lambda kv: -kv[1])
    coherence = (top[0][1] + top[1][1]) / total
    for a, b in CONTRA:
        if t[a] >= 2 and t[b] >= 2:
            coherence -= 0.15
    novelty = sum(1 for s in L.SLOTS if card["_fresh"][s]) / len(L.SLOTS)
    moodfit = 1.0 if (want_mood is None or top[0][0] == want_mood or (top[1][0] == want_mood and top[1][1] > 0)) else 0.0
    themed = sum(1 for it in (card["hook"], card["device"], card["world"]) if set(it[3]) & set(themes))
    themefit = themed / 3.0
    return round(0.40 * coherence + 0.30 * novelty + 0.15 * moodfit + 0.15 * themefit, 3), top[0][0], top[1][0]


def never_used(slot, item_id, u):
    return item_id not in u.get(slot, {})


# ───────────────────────────────────────────── propose
def propose(topic, dur, n=3, mood=None, seed=None, out=True, fmt="short"):
    reg = load_reg()
    u = usage(reg)
    pools = L.pools()
    allowed = {}
    for s in L.SLOTS:
        allowed[s] = [it for it in pools[s] if not blocked(s, it[0], u)]
        if s == "device":
            allowed[s] = [it for it in allowed[s] if it[4][0] <= dur <= it[4][1]] or allowed[s]
        if fmt == "wtf30" and s in ("hook", "device"):
            # the impossible-moment short needs visual-first hooks (muted autoplay) and one-law spines, never list/lesson devices
            allowed[s] = [it for it in allowed[s] if "wtf" in it[3]] or allowed[s]
        if mood:
            pref = [it for it in allowed[s] if mood in it[3]]
            if len(pref) >= 2:
                allowed[s] = pref + [it for it in allowed[s] if it not in pref]
    sigs = [sm for sm in L.SIGNATURE_MOVES if not blocked("signature", sm[0], u)]
    by_id = {s: {it[0]: it for it in pools[s]} for s in L.SLOTS}
    if fmt == "wtf30":
        # the impossible moment is the video: prefer set-pieces whose world is still fresh; the signature then drives world/law/device
        wsigs = [sm for sm in sigs if sm[0] in L.WTF_SETPIECES and not blocked("world", L.WTF_SETPIECES[sm[0]][0], u)]
        sigs = wsigs or sigs
    themes = topic_themes(topic)
    rnd = random.Random(seed if seed is not None else int(hashlib.md5(topic.encode()).hexdigest(), 16) % 10**6)
    cands = []
    for _ in range(600):
        card = {s: rnd.choice(allowed[s]) for s in L.SLOTS}
        card["signature"] = rnd.choice(sigs)
        card["law"] = None
        if fmt == "wtf30" and card["signature"][0] in L.WTF_SETPIECES:
            world_id, law_id, device_id = L.WTF_SETPIECES[card["signature"][0]]
            if world_id in by_id["world"] and not blocked("world", world_id, u):
                card["world"] = by_id["world"][world_id]
            if device_id in by_id["device"] and not blocked("device", device_id, u):
                card["device"] = by_id["device"][device_id]
            card["law"] = law_id
        card["_fresh"] = {s: never_used(s, card[s][0], u) for s in L.SLOTS}
        sc, m1, m2 = score(card, mood, themes)
        card["_score"], card["_moods"], card["_themes"] = sc, (m1, m2), themes
        cands.append(card)
    cands.sort(key=lambda c: -c["_score"])
    picked = []
    DIV = ("hook", "device", "world", "camera", "sonic", "type", "ending")
    for c in cands:
        if any(c[k][0] == p[k][0] for p in picked for k in DIV) or any(c["signature"][0] == p["signature"][0] for p in picked):
            continue
        picked.append(c)
        if len(picked) == n:
            break
    stamp = datetime.date.today().isoformat()
    slug = "".join(ch if ch.isalnum() else "_" for ch in topic.lower()).strip("_")[:40] or "topic"
    briefs = []
    for i, c in enumerate(picked, 1):
        tg = targets(dur, c["device"], fmt)
        md = render_brief(topic, dur, c, tg, i, stamp)
        briefs.append(md)
        if out:
            os.makedirs(os.path.join(HERE, "briefs"), exist_ok=True)
            os.makedirs(os.path.join(HERE, "dna"), exist_ok=True)
            with open(os.path.join(HERE, "briefs", f"{slug}_{stamp}_option{i}.md"), "w", encoding="utf-8") as f:
                f.write(md)
            with open(os.path.join(HERE, "dna", f"{slug}_{stamp}_option{i}.json"), "w", encoding="utf-8") as f:
                json.dump(dna_from_card(topic, dur, c, tg), f, ensure_ascii=False, indent=2)
    return picked, briefs, slug


def dna_from_card(topic, dur, c, tg):
    d = {
        "topic": topic, "duration_s": dur, "date": datetime.date.today().isoformat(),
        "slots": {s: c[s][0] for s in L.SLOTS},
        "signature": c["signature"][0],
        "targets": tg,
        "_fill_before_gate": {
            "transitions": "list of transition kind ids actually in PLAN (existing + new)",
            "sfx_voices": "list of SFX voice names actually in the bed ledger",
            "shots": 0, "pattern_interrupts": 0, "wtf_moments": 0,
            "rehooks_s": [], "hook_text": ""
        },
        "transitions": [], "sfx_voices": [], "shots": 0, "pattern_interrupts": 0, "wtf_moments": 0, "rehooks_s": [], "hook_text": "",
    }
    if tg.get("format") == "wtf30":
        d["format"] = "wtf30"
        d["_fill_before_gate"].update({
            "law_broken": "exactly one of " + ", ".join(L.LAW_IDS),
            "impossible_moment": "one sentence: what is physically impossible and when it lands",
            "meaning_line": "≤ 7 words, one hot word, full stop",
            "wtf_onset_s": "measured onset of the impossible moment", "wtf_uncut_s": "uncut length of the WTF shot",
            "beats": "physical events", "max_beat_gap_s": "longest gap between beats",
            "on_screen_words": "total words on screen excluding the meaning line", "meaning_snap_s": "when the meaning line appears",
            "loop_seam": "how the last frame rejoins frame 1",
            "measured": {"lufs": "integrated LUFS of the master", "true_peak_db": "dBTP", "duration_s": "master length"},
        })
        d.update({"law_broken": c.get("law") or "", "impossible_moment": "", "meaning_line": "", "wtf_onset_s": None, "wtf_uncut_s": None,
                  "beats": 0, "max_beat_gap_s": None, "on_screen_words": None, "meaning_snap_s": None, "loop_seam": "", "measured": {}})
    return d


def render_brief(topic, dur, c, tg, i, stamp):
    L_ = []
    a = L_.append
    a(f"# CONCEPT DNA — option {i} — \"{topic}\" · {dur:g} s · {stamp}")
    a(f"score {c['_score']} · dominant moods: {c['_moods'][0]} + {c['_moods'][1]} · "
      f"fresh slots {sum(c['_fresh'].values())}/8 (never used before in any delivered video)\n")
    a("| slot | pick | how it is built on this engine | fresh |")
    a("|---|---|---|---|")
    names = {"hook": "Hook archetype", "device": "Narrative device", "world": "Visual world / metaphor", "grammar": "Editing grammar",
             "camera": "Camera language", "sonic": "Sonic identity", "type": "Typographic twist", "ending": "Ending device"}
    for s in L.SLOTS:
        it = c[s]
        a(f"| {names[s]} | **{it[1]}** (`{it[0]}`) | {it[2]} | {'NEW' if c['_fresh'][s] else 'reused (outside window)'} |")
    a(f"| Signature move (never built before) | **{c['signature'][1]}** (`{c['signature'][0]}`) | one set-piece shot; becomes a new engine capability | NEW |")
    a("")
    a("## Measured targets for the build (carried into the gates)")
    a(f"- chapters: {' → '.join(tg['chapters'])}")
    a(f"- shots ≥ {tg['shots_min']} (something new on screen every {tg['new_on_screen_every_s']} s), transitions = {tg['transitions']}, "
      f"kinds ≥ {tg['transition_kinds_min']} with ≥ {tg['new_transition_kinds_min']} kinds never used before, overlap with the last video ≤ {int(tg['transition_overlap_max']*100)} %")
    a(f"- pattern interrupts ≥ {tg['pattern_interrupts_min']} (one every ≈6.5 s), 'wtf' set-pieces ≥ {tg['wtf_moments_min']}, re-hooks (open loop / callback) at ≈ {tg['rehook_at_s']} s")
    a(f"- hook: word one by {tg['voice_word_one_by_s']} s, a visual question by {tg['visual_question_by_s']} s, the promise by {tg['promise_by_s']} s; frame 1 already in motion")
    a(f"- sound: ≥ {int(tg['sfx_new_share_min']*100)} % of SFX voices new to the catalogue, one matched cue per transition kind, no noise floor, no repeated cue")
    a(f"- stillness never longer than {tg['max_still_s']} s; identity constants unchanged (palette, type, SHADE rig, grid, safe area, 19 gates)")
    a(f"- format {tg['format']} ({tg['aspect']}): loudness {tg['loudness']}; holds: {tg['holds']}; callbacks planted and returned ≥ {tg['callbacks_min']}; payoff written as {tg['quotable_payoff_lines']} quotable lines")
    if tg.get("format") == "wtf30":
        a("")
        a("## WTF-30 law (MONARCH_WTF30_DOCTRINE.md) — ek qanoon todo, sirf ek; baqi duniya sach rehne do")
        law = c.get("law")
        if law:
            lawrow = next((x for x in L.IMPOSSIBLE_LAWS if x[0] == law), None)
            a(f"- **law broken: `{law}` — {lawrow[1]}** ({lawrow[2]}; tends to mean: {lawrow[3]}) — set by the signature move; the world and the spine follow it")
        a(f"- duration {tg['duration_range_s'][0]:g}–{tg['duration_range_s'][1]:g} s; `law_broken` = {tg['law_broken']}")
        a(f"- the impossible moment lands between {tg['wtf_onset_window_s'][0]} s and {tg['wtf_onset_window_s'][1]} s, in ONE uncut shot ≥ {tg['wtf_uncut_min_s']} s, "
          f"preceded by a silence hole of {tg['silence_before_wtf_s'][0]}–{tg['silence_before_wtf_s'][1]} s; no text over it; the trick is never explained or repeated")
        a(f"- density = physical events: beats ≥ {tg['beats_min']}, max gap ≤ {tg['max_beat_gap_s']} s; shots ≥ {tg['shots_min']} (cuts are few; events are many)")
        a(f"- muted-pass: ≤ {tg['on_screen_words_max']} on-screen words in total; meaning line ≤ {tg['meaning_words_max']} words, one hot word, full stop, "
          f"between {tg['meaning_snap_window_s'][0]} s and {tg['meaning_snap_window_s'][1]} s")
        a(f"- loop seam: {tg['loop_seam']}; CTA: {tg['cta']}")
        a("- consistency law: everything except the one broken law obeys physics — light vs shadow, contact shadows, parallax order, cloth lag, anticipation/settle")
        a("- the ten laws: " + " · ".join(f"`{i}` {n}" for i, n, _, _ in L.IMPOSSIBLE_LAWS))
    refs = load_refs()
    if refs:
        a("")
        a("## Story architecture first (reference lessons, brain/references.json)")
        for r in refs:
            for line in r.get("principles", [])[:6]:
                a(f"- {line}")
        a("- (references are lessons, never templates: hero, palette, type, grid and gates stay ours)")
    a("")
    a("## Why this combination")
    a(f"Topic themes read as {', '.join(c['_themes'])}. Opening: {c['hook'][1].lower()} → story device: {c['device'][1].lower()}, told inside '{c['world'][1]}'; "
      f"{c['grammar'][1].lower()} with {c['camera'][1].lower()} keeps the picture changing while the voice flows; "
      f"the bed is {c['sonic'][1].lower()}, the type does {c['type'][1].lower()}, and it closes with {c['ending'][1].lower()}. "
      f"Dominant mood {c['_moods'][0]}/{c['_moods'][1]}. Every slot is checked against the registry; nothing here repeats a delivered video inside its window.")
    a("")
    a("## Next steps")
    a("1. User picks an option (or asks for a fresh set: `--seed` or `--mood`).  2. Script in that device's chapter template, VO measured first.  "
      "3. Build the signature move + ≥3 new transition kinds, luma-trace each.  4. Fill `transitions`, `sfx_voices`, `shots`, `pattern_interrupts`, `wtf_moments`, `rehooks_s` in the DNA json.  "
      "5. `concept.py gate <dna>` must PASS before the final mux.  6. After delivery: `concept.py commit <dna> --drive-id … --md5 …`.")
    return "\n".join(L_) + "\n"


# ───────────────────────────────────────────── WTF-30 rows inside gate #20 (doctrine §11; the frame/mix rows live in gate_wtf30.py)
def _words(text):
    return [w for w in re.findall(r"[A-Za-z0-9'’\-]+", text or "") if w]


def wtf30_rows(d, tg, dur):
    W = WTF30
    rows = []
    lo_d, hi_d = W["duration_range_s"]
    rows.append((f"G-W13 duration = {dur:g} s ({lo_d:g}–{hi_d:g})", lo_d <= dur <= hi_d, ""))
    law = d.get("law_broken")
    laws = [x.strip() for x in str(law or "").replace(",", " ").split() if x.strip()]
    rows.append((f"G-W12 law_broken = {law or 'not set'} (exactly one of the ten)", len(laws) == 1 and laws[0] in L.LAW_IDS, ", ".join(L.LAW_IDS)))
    rows.append(("impossible_moment written", bool(d.get("impossible_moment")), (d.get("impossible_moment") or "")[:70]))
    win = tg.get("wtf_onset_window_s") or [round(dur * W["wtf_onset_window"][0], 1), round(min(dur * W["wtf_onset_window"][1], W["wtf_onset_hard_max_s"]), 1)]
    onset = d.get("wtf_onset_s")
    rows.append((f"G-W3 wtf_onset_s = {onset} ({win[0]}–{win[1]} s)", onset is not None and win[0] <= float(onset) <= win[1], "share-thumb before the scroll cliff"))
    uncut = d.get("wtf_uncut_s")
    rows.append((f"G-W4 wtf_uncut_s = {uncut} (≥ {W['wtf_uncut_min_s']} s, no cut inside)", uncut is not None and float(uncut) >= W["wtf_uncut_min_s"], "a cut lets the brain say 'edit trick'"))
    osw = d.get("on_screen_words")
    rows.append((f"G-W7 on_screen_words = {osw} (≤ {W['on_screen_words_max']}, none over the WTF)", osw is not None and int(osw) <= W["on_screen_words_max"], "muted-pass comprehension"))
    ml = d.get("meaning_line") or ""
    mw = _words(ml)
    snap = d.get("meaning_snap_s")
    sw = tg.get("meaning_snap_window_s") or [round(dur * W["meaning_snap_window"][0], 1), round(dur * W["meaning_snap_window"][1], 1)]
    ok_line = bool(ml) and len(mw) <= W["meaning_words_max"] and ml.strip().endswith(".")
    ok_snap = snap is not None and sw[0] <= float(snap) <= sw[1]
    rows.append((f"G-W8 meaning line = {len(mw)} words, full stop {'yes' if ml.strip().endswith('.') else 'no'}, at {snap} s ({sw[0]}–{sw[1]})", ok_line and ok_snap, ml[:60]))
    rows.append(("G-W9 loop seam described", bool(d.get("loop_seam")), (d.get("loop_seam") or "")[:60]))
    m = d.get("measured") or {}
    lufs, tp = m.get("lufs"), m.get("true_peak_db")
    ok_loud = isinstance(lufs, (int, float)) and W["lufs"][0] <= lufs <= W["lufs"][1] and isinstance(tp, (int, float)) and tp <= W["true_peak_max_db"]
    rows.append((f"G-W11 loudness = {lufs} LUFS / TP {tp} dBTP ({W['lufs'][0]}..{W['lufs'][1]}, ≤ {W['true_peak_max_db']})", ok_loud, "platform-normalised master"))
    return rows


# ───────────────────────────────────────────── freshness gate (#20)
def gate(dna_path, verbose=True):
    with open(dna_path, encoding="utf-8") as f:
        d = json.load(f)
    reg = load_reg()
    me = [v for v in reg["videos"] if v.get("signature") == d.get("signature") and abs(float(v.get("duration_s", 0)) - float(d.get("duration_s", 0))) < 0.5]
    if me:   # gate re-run after commit (e.g. the film gates measured on the delivered file): compare with the OTHER videos only
        reg = dict(reg, videos=[v for v in reg["videos"] if v not in me])
    u = usage(reg)
    rows = []
    for s in L.SLOTS:
        val = d["slots"].get(s)
        ok = bool(val) and not blocked(s, val, u)
        why = "not set" if not val else ("used in the last %d video(s)" % (min(u[s][val]) + 1) if (val in u[s] and not ok) else "fresh")
        rows.append((f"slot {s} = {val}", ok, why))
    sig = d.get("signature")
    rows.append((f"signature = {sig}", bool(sig) and sig not in u["signature"], "unique" if sig and sig not in u["signature"] else "already built"))
    kinds = list(dict.fromkeys(d.get("transitions", [])))
    fmt = d.get("targets", {}).get("format", d.get("format", "short"))
    same_fmt = [v for v in reg["videos"] if v.get("format", "short") == fmt]
    prev = set(same_fmt[-1].get("transitions", [])) if same_fmt else set()
    everk = all_prev_kinds(reg)
    dur = float(d.get("duration_s", 0))
    if fmt == "film":
        kmin = 4
    elif fmt == "wtf30":
        kmin = WTF30["transition_kinds_min"]
    else:
        kmin = max(8 if dur >= 40 else 5, math.ceil(max(0, int(d.get("shots", 0)) - 1) / 4))
    new_min = WTF30["new_transition_kinds_min"] if fmt == "wtf30" else RULES["trans_new_min"]
    overlap = (len(set(kinds) & prev) / len(kinds)) if kinds else 1.0
    newk = [k for k in kinds if k not in everk]
    rows.append((f"transition kinds = {len(kinds)} (min {kmin})", len(kinds) >= kmin, ", ".join(kinds) or "none listed"))
    rows.append((f"overlap with last {fmt} = {overlap:.2f} (max {RULES['trans_overlap_max']})", overlap <= RULES['trans_overlap_max'], f"shared: {sorted(set(kinds) & prev)}"))
    rows.append((f"new kinds = {len(newk)} (min {new_min})", len(newk) >= new_min, ", ".join(newk) or "none"))
    sfx = list(dict.fromkeys(d.get("sfx_voices", [])))
    evers = all_prev_sfx(reg)
    share = (sum(1 for v in sfx if v not in evers) / len(sfx)) if sfx else 0.0
    rows.append((f"new SFX voices share = {share:.2f} (min {RULES['sfx_new_min']})", share >= RULES['sfx_new_min'], f"{len(sfx)} voices listed"))
    tg = d.get("targets", {})
    for k, lab in (("shots", "shots_min"), ("pattern_interrupts", "pattern_interrupts_min"), ("wtf_moments", "wtf_moments_min")):
        need = tg.get(lab, 0)
        have = int(d.get(k, 0))
        if k == "shots" and fmt == "film":
            # film: holds are allowed when carried — the density unit is the BEAT (cut, line reveal, light change,
            # music entry, readout change, voice line), not the cut.  max gap between beats must stay ≤ 6.5 s.
            beats = int(d.get("beats", 0)); gap = float(d.get("max_beat_gap_s", 99))
            rows.append((f"beats = {beats} (min {need}; shots {have}) · max gap {gap:.1f} s (≤ 6.5)", beats >= need and gap <= 6.5, "film density = carried beats"))
            continue
        if k == "shots" and fmt == "wtf30":
            # wtf30: few cuts, many physical events — shots ≥ 4 AND beats ≥ dur/1.5 with no gap > 2.5 s.
            bmin = int(tg.get("beats_min", math.ceil(dur / WTF30["beat_div"]))); gmax = float(tg.get("max_beat_gap_s", WTF30["max_beat_gap_s"]))
            beats = int(d.get("beats", 0)); gap = float(d.get("max_beat_gap_s") or 99)
            rows.append((f"shots = {have} (min {need})", have >= need, "cuts are few"))
            rows.append((f"beats = {beats} (min {bmin}) · max gap {gap:.1f} s (≤ {gmax})", beats >= bmin and gap <= gmax, "wtf30 density = physical events"))
            continue
        rows.append((f"{k} = {have} (min {need})", have >= need, ""))
    rh = d.get("rehooks_s", [])
    rows.append((f"re-hooks logged = {len(rh)} (min 3 for ≥ 40 s)", len(rh) >= (3 if dur >= 40 else 1), str(rh)))
    rows.append(("hook text logged", bool(d.get("hook_text")), d.get("hook_text", "")[:60]))
    if fmt == "wtf30":
        rows.extend(wtf30_rows(d, tg, dur))
    passed = all(r[1] for r in rows)
    if verbose:
        print(f"FRESHNESS GATE (#20) — {os.path.basename(dna_path)} — {'PASS' if passed else 'FAIL'} ({sum(r[1] for r in rows)}/{len(rows)})")
        for name, ok, why in rows:
            print(f"  [{'PASS' if ok else 'FAIL'}] {name}  {('— ' + why) if why else ''}")
    return passed, rows


# ───────────────────────────────────────────── cadence (retention map of a real timeline)
def cadence(module=None, shots=None, dur=None, interrupts=None):
    if module:
        sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
        m = __import__(module)
        t0 = [float(s["t0"]) for s in m.SHOTS]
        if not dur:
            for name in ("DUR", "DUR_TOTAL"):
                if getattr(m, name, None):
                    dur = float(getattr(m, name)); break
            else:
                for tl in ("TL2", "TL", "timeline"):
                    if getattr(getattr(m, tl, None), "DUR_TOTAL", None):
                        dur = float(getattr(m, tl).DUR_TOTAL); break
                else:
                    dur = t0[-1] + 3.0
        plan = list(getattr(m, "PLAN", []))
    else:
        t0 = [float(x) for x in shots]
        plan = []
    gaps = [b - a for a, b in zip(t0, t0[1:])] + [dur - t0[-1]]
    worst = max(gaps)
    over3 = sum(1 for g in gaps if g > 3.0)
    print(f"CADENCE — {module or 'shots'} — {len(t0)} shots in {dur:.2f} s, median shot {sorted(gaps)[len(gaps)//2]:.2f} s, "
          f"longest {worst:.2f} s, shots > 3.0 s: {over3}, transition kinds {len(set(plan))}")
    bar = ""
    for i, g in enumerate(gaps):
        bar += ("█" if g <= 3.0 else "▒") * max(1, int(round(g)))
    print("  " + bar)
    for q in (0.25, 0.5, 0.75):
        tq = dur * q
        near = min(t0, key=lambda x: abs(x - tq))
        print(f"  re-hook window {int(q*100)} % ≈ {tq:5.1f} s → nearest cut {near:5.1f} s")
    if interrupts is not None:
        print(f"  pattern interrupts logged {interrupts}, target ≥ {int(dur // 6.5)}")
    return {"shots": len(t0), "longest_gap": worst, "over3": over3, "kinds": len(set(plan))}


# ───────────────────────────────────────────── commit / status / export
def commit(dna_path, drive_id, md5, title=None, key=None):
    with open(dna_path, encoding="utf-8") as f:
        d = json.load(f)
    ok, _ = gate(dna_path, verbose=False)
    if not ok:
        print("refusing to commit: freshness gate FAIL — run `gate` for the list")
        return False
    reg = load_reg()
    entry = {
        "key": key or f"v{len(reg['videos']) + 1}_{''.join(ch if ch.isalnum() else '_' for ch in d['topic'].lower())[:24]}",
        "title": title or d["topic"], "date": datetime.date.today().isoformat(), "duration_s": d["duration_s"],
        "drive_id": drive_id, "md5": md5, "slots": d["slots"], "signature": d["signature"],
        "transitions": d.get("transitions", []), "sfx_voices": d.get("sfx_voices", []), "hook_text": d.get("hook_text", ""),
        "format": d.get("targets", {}).get("format", d.get("format", "short")), "workflow": d.get("workflow", "WF-01"),
    }
    for k in ("worlds_also", "callbacks", "quotable_lines", "measured"):
        if d.get(k):
            entry[k] = d[k]
    reg["videos"].append(entry)
    save_reg(reg)
    print("committed", entry["key"], "→ registry now", len(reg["videos"]), "videos")
    return True


def status():
    reg = load_reg()
    u = usage(reg)
    print(f"EDITOR BRAIN — {len(reg['videos'])} delivered videos in memory; last = {reg['videos'][-1]['key']} ({reg['videos'][-1]['date']})")
    print("library:", json.dumps(L.counts()))
    for s, pool in L.pools().items():
        blk = [it[0] for it in pool if blocked(s, it[0], u)]
        fresh = [it[0] for it in pool if never_used(s, it[0], u)]
        print(f"  {s:8s} total {len(pool):2d} · blocked now {len(blk):2d} {blk} · never used {len(fresh):2d}")
    sigs = [sm[0] for sm in L.SIGNATURE_MOVES if not blocked("signature", sm[0], u)]
    print(f"  signature moves available {len(sigs)}/{len(L.SIGNATURE_MOVES)}")
    print(f"  transition kinds ever used {len(all_prev_kinds(reg))}; to_build families {len(L.TRANSITION_KINDS['to_build'])}")
    print(f"  SFX voices ever used {len(all_prev_sfx(reg))}; fresh catalogue {len(L.SFX_VOICES['fresh'])}")


def export(path):
    data = {"rules": RULES, "library": {k: v for k, v in vars(L).items() if k.isupper() and not k.startswith("_")}, "registry": load_reg()}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, default=str)
    print("exported", path, os.path.getsize(path), "bytes")


# ───────────────────────────────────────────── cli
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("status")
    p = sp.add_parser("propose"); p.add_argument("--topic", required=True); p.add_argument("--dur", type=float, required=True)
    p.add_argument("--n", type=int, default=3); p.add_argument("--mood", choices=MOODS); p.add_argument("--seed", type=int); p.add_argument("--format", choices=list(FORMATS), default="short")
    g = sp.add_parser("gate"); g.add_argument("dna")
    c = sp.add_parser("cadence"); c.add_argument("--module"); c.add_argument("--shots"); c.add_argument("--dur", type=float); c.add_argument("--interrupts", type=int)
    k = sp.add_parser("commit"); k.add_argument("dna"); k.add_argument("--drive-id", required=True); k.add_argument("--md5", required=True); k.add_argument("--title"); k.add_argument("--key")
    e = sp.add_parser("export"); e.add_argument("--out", default=os.path.join(HERE, "brain_export.json"))
    a = ap.parse_args()
    if a.cmd == "status":
        status()
    elif a.cmd == "propose":
        picked, briefs, slug = propose(a.topic, a.dur, a.n, a.mood, a.seed, fmt=a.format)
        print("\n\n".join(briefs))
        print(f"written: brain/briefs/{slug}_*_option1..{len(picked)}.md and brain/dna/{slug}_*_option1..{len(picked)}.json")
    elif a.cmd == "gate":
        ok, _ = gate(a.dna); sys.exit(0 if ok else 1)
    elif a.cmd == "cadence":
        cadence(a.module, a.shots.split(",") if a.shots else None, a.dur, a.interrupts)
    elif a.cmd == "commit":
        sys.exit(0 if commit(a.dna, a.drive_id, a.md5, a.title, a.key) else 1)
    elif a.cmd == "export":
        export(a.out)


if __name__ == "__main__":
    main()
