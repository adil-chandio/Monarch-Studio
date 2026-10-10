# BUDDY — Character Spec v1
Companion to `character_sheet_1..4.png`. Source of truth: `/home/user/src/character.py`.

## 1. Why this exists
The shipped film has **no consistent character**. Every scene calls `stick()`
with a different seed — 31, 33, 37, 39, 43, 47, 53 — so the hand-drawn wobble
is different each time. Technically it is a **different person in all six
scenes**. That is the single biggest reason the film reads as "a nice
animation" instead of "a story about someone."

`character.py` fixes this with one locked identity.

## 2. The lock
| Thing | Value | Rule |
|---|---|---|
| `HERO_SEED` | `101` | one seed, every scene, forever |
| `HERO_COL` | `CHALK (238,242,250)` | brightest body in frame |
| `ACC_COL` | `GOLD (255,201,60)` | marker only |
| `HERO_W` | `10 @ s=600` | `w = 10 * s / 600` |
| marker | **`cap` — backwards snapback** | locked; strongest "hustler" read at thumbnail size |
| hoodie | on | collar + drawstrings + side seams + pocket |

> ⚠ **Seed collision:** `101–110` is currently used by the *brain* object in
> scene 2. Before wiring the hero in, the brain must move to a free block
> (suggest `401–410`). Flagged, not yet done.

## 3. Proportions (all fractions of `s`, total height)
```
hip 0.42   neck 0.36 above hip   head_r 0.115   head_gap 0.035
shoulder 0.03 below neck
arm 0.19 + 0.18      leg 0.22 + 0.22      foot 0.055      hand_r 0.022
```
One rig serves every size. Change `s`, nothing else.

## 4. Expressions (10)
`neutral · sad · worried · shock · think · focus · determined · proud · happy · celebrate`

Built from three dials: **eyebrow angle + height**, **eye shape**
(`open` solid dot / `wide` outlined + floating pupil / `squint` flat lens /
`happy` ^ ^ / `closed`), and **8 mouth shapes**
(`line smile bigsmile frown o flat grit open`).

Eyebrows carry ~70% of the read. If an expression is not landing, move the brows.

`blink_at(t)` — period 3.1 s, lid shut 0.14 s, pure function of `t`, so it can
never desync on a re-render or a shard.

## 5. Scene assignment
| Scene | Beat | Pose | Expression |
|---|---|---|---|
| 1 | hook — jeb khali | `walk` → `sad` | worried → sad |
| 2 | SKILL SEEKHO | `think` → `type` | think → focus |
| 3 | ROZ 2 GHANTE | `type` | determined |
| 4 | SAMPLE BANAO | `point up` | proud |
| 5 | SERVICE BECHO | `shake` | happy |
| 6 | CTA | `cheer` / `dance` | celebrate |

## 6. Cast hierarchy — never break
1. **BUDDY** — `s=520–600`, seed 101, cap + hoodie + full face + motion trails
2. **THE CLIENT** — `s=420`, seed 211, open collar, no marker, 25% dimmer. S5 only.
3. **THE CROWD** — `s=320`, seeds 231+, no marker, no hoodie, flattest. Background only.

## 7. The seven laws
1. ONE hero. Same seed (101), same marker, same hoodie, every scene.
2. The hero is always the LARGEST figure in frame.
3. Only the hero gets an identity marker. Extras never do.
4. Only the hero gets motion trails.
5. Extras are 25% dimmer and 2 px thinner than the hero.
6. The hero looks AT whatever the viewer should read next.
7. Expression changes land on a beat, never mid-word.

## 8. Decisions taken
- **Identity marker: `cap`** (option A). Backwards snapback, GOLD.
- **No on-screen name.** `CHAR['name']` stays `BUDDY` as an internal handle only —
  the hero is never named in the film so the viewer projects themselves onto him.
- **Seed collision resolved:** the scene-2 brain moved `101-110` -> `401-410`
  in `stick3.py`. The hero owns `101` alone; his motion ghosts use `601+`.

## 9. Status
- Hero is wired into **all six scenes** of `src/stick3.py`.
- Shipped in `stickman_money_37s_v4.mp4`.
- `stick2.py`, `stickbase.py`, `timeline.py`, `make_audio4.py` are **untouched** —
  all four sha256 values still match `BUILD_MANIFEST.json`, so GATE S and
  GATE 5 for the v2 build still pass. v4 is additive, not a mutation.
