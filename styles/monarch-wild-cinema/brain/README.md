# brain/ — concept and novelty memory for `monarch-wild-cinema`

A03 (Architect) reads this before writing a plan. Its job is to stop the channel repeating the
same angle twice and to record which *shapes* of episode have already been made, so novelty is a
deliberate decision rather than an accident.

| File | What it holds |
|---|---|
| `concepts.json` | every concept used or reserved, with its hook, its format, the plate set it needed, and a novelty verdict |
| `plates.json` | every owned plate, what it can support (species, mood, shot role) and what it has already been used for |

**Rules**
1. A concept may be reused only if its angle changes (same animal, different question).
2. A plate may be reused across episodes — the channel's library is 14 owned images — but never
   twice in the same film for two *different* species cards.
3. Every new film appends its concepts here **before** the render (the plan's `episode` id is the
   key), so novelty is checked against what was promised, not only against what shipped.
