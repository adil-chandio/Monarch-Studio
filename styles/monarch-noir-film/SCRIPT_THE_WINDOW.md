# THE WINDOW — WF-03 · Monarch Noir Film · film #2 (topic: COMPARISON) — script v1 (2026-10-10)

Format 1920×1080 · 24 fps · target 165–180 s · full English voiceover (voice-03) + key on-screen text · NOIRGO MAX engine
(real-life world plates + human-like hero rig `human.py`).

Logline: a young man spends his nights watching the lit windows across the street — the runner, the couple, the man with two
monitors — and comparing. The night his phone dies, his own reflection appears over all of them. He does the boring work.
Forty days later somebody across the street looks up at a new lit window. Payoff: every window you ever envied has someone
standing in it, looking at yours. Light your own.

Device: WINDOWS. The opposite facade (plate `facade_night`, 31 lit windows measured by `plates/facade_windows.json`, threshold
lum>50) is the villain's body; the hero's own window (plate `facade_hero`) goes blue-flicker → dark → amber. Colour arc: cold
blue (phone / TV windows) → first amber = his own lamp (Day 9) → dawn.

## VO clips (10, voice-03) — one clip per cut group; line timings measured from the clips (`data/vo_lines.json`)

| clip | section | text |
|---|---|---|
| vo01 | S1 HOOK | It's eleven forty-eight at night. He's lying in the dark, and his face is glowing blue. ... Across the street, thirty-one windows are still lit. ... He knows exactly what's happening in every one of them. Every single one... except his own. |
| vo02 | S2 WINDOWS a | Fourth floor, by the fire escape: the guy who runs at five a.m. He's already posted the run. ... Third floor, under the laundry: the couple that cooks together. Every night. Two plates. ... Fifth floor, the blue one: the man with two monitors, and a business. |
| vo03 | S2 WINDOWS b | He has never met any of them. ... But he has compared himself to all of them. Tonight. Last night. And every night this year. |
| vo04 | S3 SCORE a | Here's the thing about watching windows. ... You only ever see the lit room. |
| vo05 | S3 SCORE b | You don't see the runner's knee, wrapped in ice. ... You don't see the couple after the dishes. The silence. |
| vo06 | S3 SCORE c | And you don't see the man with two monitors, at two in the morning, staring out of his window... at yours. ... Wondering how you stay so calm. |
| vo07 | S4 TURN | At twelve thirty, the phone dies. ... And for the first time in months, his room is darker than theirs. ... He gets up to find the charger. He stops at the window. ... And there it is. The one thing he never looked at: ... his own reflection, laid over all thirty-one of them. |
| vo08 | S5 WORK a | So he does the only thing a window can never show you. ... The boring part. ... He makes the bed. At midnight. ... The dishes. Three days old. ... The desk. Cleared. ... The shoes. By the door. |
| vo09 | S5 WORK b | Day one: the run. The slow one. The ugly one. ... Day nine: the lamp is on at six. ... Day twenty-three: the couple sees a man running past their kitchen. They don't know his name either. ... Day forty: the man with two monitors looks up... and there's a new window on the street. |
| vo10 | S6 PAYOFF | Here's what nobody tells you about comparison. ... Every window you have ever envied has someone standing in it, looking at yours. ... The only window you will ever see from the inside... is your own. ... So stop watching. ... Light it. |

## On-screen text
- Clock readout (top-left, Montserrat): `11:48 PM` → `12:30 AM` → `DAY 1` `DAY 9` `DAY 23` `DAY 40` → `5:58 AM`.
- Title card after the hook: **THE WINDOW** (serif, bone).
- Red villain lines (typewriter, red, full stops): `he's ahead.` · `they're happy.` · `you're late.` · `look at them.`
- White answers in S3/S5 (same positions): `he's hurting.` · `they're quiet.` · `it's two a.m.` · `look at you.`
- End cards: **LIGHT YOUR OWN WINDOW.** → *You only ever see the lit room.* → quiet.

## Shot plan (v1 — final times from the VO measurement; holds carried by a line, a light or a music change)
S1 HOOK 0–14: bedroom_night, hero in bed, phone glow on the face (breathing, thumb scroll) → hard cut facade_night wide (31 lit) → his window from outside (facade_hero, blue flicker) → title.
S2 WINDOWS 14–46: push-ins on B4 (runner stretching, silhouette), I3 (couple, two plates), D5 (desk man, two monitors); hero's thumb; red lines land on the glass; clock ticks.
S3 SCORE 46–74: the dark edges — runner icing the knee, couple apart, desk man at the window looking back; reverse angle: his building, the single blue window; white answers.
S4 TURN 74–100: phone dies (black), room darker than theirs; he stands (anticipation, weight shift), walks to the window; reflection over the facade (mirror text); clock stops — silence.
S5 WORK 100–140: bed, dishes, desk, shoes (hands with fingers close on real objects); DAY 1 run on street_dawn; DAY 9 lamp amber (bedroom_amber); DAY 23 kitchen window POV of the runner; DAY 40 desk man looks up → facade_hero with an amber window.
S6 PAYOFF 140–170: facade wide → his window amber, him at the desk → "Light it." → end cards → quiet.
