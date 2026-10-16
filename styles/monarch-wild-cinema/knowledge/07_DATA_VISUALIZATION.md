# 07 · Data visualization — and the honesty law

## Why charts are in an editing engine

Because they are the differentiator. The channel's forensic audit states the
gap directly: the audience has seen ten thousand clips of a bear charging.
Nobody has shown them **what the literature actually measured** about bear
charges — and the channel already has the data, because episode 01 required it.

Every clip compilation skips this. It is the one thing a footage-free
production can do *better* than a footage-rich one, and it is also what makes
the video worth subscribing for: a viewer who learns something they can repeat
at dinner is a viewer who comes back.

## The available objects

| object | function | file |
|---|---|---|
| `bar_chart` | labelled comparison, animated reveal | `viz.bar_chart` |
| `range_chart` | a value with a low–high **span**, plus optional point mark | `viz.range_chart` |
| `gauge` | a single proportion as an arc | `viz.gauge` |
| `callout` | "here is the thing I mean", bracketed inside the frame | `viz.callout` |
| `source_stamp` | the citation card | `viz.source_stamp` |

All are pure PIL renderers returning an RGBA layer, so they composite through
the same pipeline as type and inherit the same contrast and safe-band rules.

## The honesty law

> A chart may not imply a comparison the sources do not support.

This is not a stylistic preference. It is the failure mode that turns a
knowledge channel into a misinformation channel, and it is *easy* to commit
accidentally.

### The worked example from episode 01

The obvious chart was:

```
BEAR SPRAY   ██████████████████████  92 %
FIREARMS     ███████████████████     76 %
```

It appeared in the first draft of the narration. It is **wrong**, and here is
exactly why:

- The 92 % figure comes from Smith & Herrero's Alaska field sample of **people
  who carried spray and used it**.
- The 76 % figure comes from a different sample of **people who carried
  firearms and used them**.
- Neither is a controlled comparison. The samples are not matched, the
  circumstances differ, and the firearms figure is drawn from a documented,
  self-selected population.
- The honest statement is: *"bear spray was effective in about 92 % of the
  encounters in that dataset; the firearms figure in the comparable study is
  about 76 % — these are two different samples and the studies do not claim one
  is better than the other."*

The production therefore **refused the comparison on screen** and the narration
states both numbers without ranking them. `range_chart` exists precisely so a
value with a genuine range can be drawn as a range: it accepts `lo`/`hi` and an
optional `mark`, and it carries a `note` field for exactly this disclaimer.

`gauge(0.92, "BEAR SPRAY", "effective in Alaska field data")` is what the proof
uses — one number, its source, no ranking.

## Rules

1. **Every number on screen has a source in the source stamp or the
   description.** No exceptions, including numbers the narrator says out loud.
2. **Round honestly.** "About 92 %" or "nine in ten", not "92.0 %".
3. **Never invent a data point to make a chart symmetrical.**
4. **A point estimate is not a range.** Use the tick mark for a point, the bar
   for a range.
5. **Name the dataset on screen**, not just in the description. `source_stamp`
   exists so the audience can see the provenance while the claim is live.
6. **Charts are episodes, not decoration.** A chart that repeats the narration
   verbatim is a slide. A chart that shows a relationship the narration only
   asserts is television.
