"""
wide_full.py — THE FULL EPISODE.  "The Slowest Predator", 4:23, 16:9.
======================================================================
Sibling of wide.py. Imports it read-only and REUSES its eight hook scenes as
Act 1; adds twenty-six body scenes through a small layout engine.

Nothing in clean.py / toon.py / make_asmr.py / wide.py is modified.

Structure
---------
  ACT 1  THE CHASE          0:00 – 0:53   8 scenes, frame-animated, captioned
  ACT 2  THE MACHINE        0:53 – 1:57   6 scenes
  ACT 3  THE HUNT           1:57 – 3:15  11 scenes
  ACT 4  THE ARGUMENT       3:15 – 4:09   6 scenes
  ACT 5  WHAT YOU INHERITED 4:09 – 4:23   3 scenes

Why the body carries no verbatim captions: the hook needs them (the viewer has
not committed yet, and many watch muted). In the body the on-screen text IS
the content — a number, a list, a paper card — and stacking a transcript on
top of a data card is exactly the over-stuffing the brief forbids.
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, '/home/user/src')
import toon as T
import wide as WD
from wide import (W, H, FPS, PAPER, PAPER_D, SOFT, SAND, INK, GY,
                  CHIP_Y, CAP_Y, HEAD_Y, F, line, tw, cl, e_out, e_io, e_back,
                  fl, fbox, fcirc, fpoly, stroke, shadow, statchip, caption,
                  headline, antelope, hero, phys, p_run, p_jog, backdrop,
                  heat_shimmer, _GRAIN)

# ───────────────────────────────────────────── timeline
SCENE_START = [0.0, 6.9, 13.0, 19.2, 24.7, 31.0, 37.3, 45.4, 53.0, 61.27,
               73.66, 87.0, 96.25, 105.64, 117.02, 126.13, 135.28, 141.75,
               146.3, 154.74, 160.81, 171.03, 178.04, 185.2, 191.49, 195.44,
               203.01, 210.2, 215.47, 223.18, 230.79, 237.49, 249.73, 257.28]
DUR_TOTAL = 263.5
NF = int(round(DUR_TOTAL * FPS))             # 7905
SCENE_END = SCENE_START[1:] + [DUR_TOTAL]
NS = len(SCENE_START)
CUTS = SCENE_START[1:]
TDUR, TLAG = 0.42, 0.050

# VO placement. Act 1 reuses the hook's six clips untouched.
VO = [('w1', 0.350), ('w2', 7.250), ('w3', 13.350), ('w4', 19.550),
      ('w5', 25.050), ('w6', 37.750),
      ('b1', 53.450), ('b2', 74.110), ('b3', 96.700), ('b4', 117.470),
      ('b5', 135.730), ('b6', 155.190), ('b7', 178.490), ('b8', 195.890),
      ('b9', 215.920), ('b10', 237.940)]

# ───────────────────────────────────────────── acts
#   scene index (0-based) -> act number
ACT_OF = ([1] * 8 + [2] * 6 + [3] * 11 + [4] * 6 + [5] * 3)
assert len(ACT_OF) == NS, len(ACT_OF)
ACT_NAME = {1: 'THE CHASE', 2: 'THE MACHINE', 3: 'THE HUNT',
            4: 'THE ARGUMENT', 5: 'WHAT YOU INHERITED'}
# One accent per act keeps a four-minute film coherent; Act 1 keeps the hook's
# own per-scene palette because those eight beats are deliberately restless.
ACT_ACC = {2: (16, 104, 96), 3: (166, 62, 24), 4: (44, 58, 112),
           5: (26, 96, 58)}


def accent(si):
    return WD.ACC[si] if si < 8 else ACT_ACC[ACT_OF[si]]


# ───────────────────────────────────────────── chrome
def chrome(d, t, si, acc):
    y = 76
    d.rounded_rectangle([96, y - 3, W - 96, y + 3], 3, fill=(221, 211, 192))
    fxp = 96 + (W - 192) * cl(t / DUR_TOTAL)
    d.rounded_rectangle([96, y - 3, fxp, y + 3], 3, fill=acc)
    d.ellipse([fxp - 8, y - 8, fxp + 8, y + 8], fill=acc)
    # act ticks, so the viewer can see the shape of the film
    for k in range(1, 6):
        first = ACT_OF.index(k)
        xx = 96 + (W - 192) * (SCENE_START[first] / DUR_TOTAL)
        d.line([(xx, y - 11), (xx, y + 11)], fill=(198, 187, 167), width=3)
    a = ACT_OF[si]
    d.text((96, 124), f'ACT {a}', font=F(30, 800), fill=acc, anchor='lm')
    d.text((192, 125), f'/ 5   {ACT_NAME[a]}', font=F(24, 600), fill=SOFT,
           anchor='lm')
    d.text((W - 96, 125), 'PERSISTENCE HUNTING', font=F(22, 600), fill=SOFT,
           anchor='rm')


# ───────────────────────────────────────────── shared body furniture
def _title(d, lt, acc, txt, hot=None, sz=80):
    headline(d, txt.split(), cl(lt / .55), acc, hot, sz)


def _chip(d, lt, acc, txt, at=None, dur=None):
    if not txt: return
    at = (0.9 if at is None else at)
    p = cl((lt - at) / .6)
    if dur is not None:
        p *= (1 - cl((lt - at - dur) / .4))
    statchip(d, txt, p, acc)


def _rule(d, lt, acc, y, at=0.5, half=470):
    p = cl((lt - at) / .7)
    if p <= 0: return
    wd = half * e_out(p, 2.2)
    d.line([(W / 2 - wd, y), (W / 2 + wd, y)], fill=acc, width=4)


def _tick(d, cx, cy, s, col, p=1.0, w=8):
    if p <= 0: return
    a = (cx - s * .86, cy + s * .04)
    b = (cx - s * .22, cy + s * .62)
    c = (cx + s * .88, cy - s * .64)
    k = cl(p * 2)
    if k < 1:
        stroke(d, [a, (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)], col, w)
    else:
        k2 = cl(p * 2 - 1)
        stroke(d, [a, b, (b[0] + (c[0] - b[0]) * k2, b[1] + (c[1] - b[1]) * k2)],
               col, w)


def _cross(d, cx, cy, s, col, p=1.0, w=8):
    if p <= 0: return
    k = cl(p * 2)
    stroke(d, [(cx - s, cy - s), (cx - s + 2 * s * k, cy - s + 2 * s * k)], col, w)
    if p > .5:
        k2 = cl(p * 2 - 1)
        stroke(d, [(cx + s, cy - s), (cx + s - 2 * s * k2, cy - s + 2 * s * k2)],
               col, w)


# ═══════════════════════════════════════════ LAYOUTS
def L_triple(d, lt, acc, c):
    """Three options; the ones that are not the answer get struck out."""
    _title(d, lt, acc, c['title'], c.get('hot'), c.get('sz', 80))
    n = len(c['items'])
    for i, (txt, keep) in enumerate(c['items']):
        p = cl((lt - .75 - i * .40) / .5)
        if p <= 0: continue
        x = W / 2 + (i - (n - 1) / 2) * 520
        y = GY - 300 + fl(lt, i, 4.0)
        k = e_back(p, 1.10)
        col = acc if keep else (156, 146, 130)
        f = F(int(72 * k), 800)
        d.text((x, y), txt, font=f, fill=col + (int(255 * cl(p * 1.8)),),
               anchor='mm')
        if keep:
            if p > .55:
                _tick(d, x, y + 122, 30, acc, cl((p - .55) / .45), 10)
        else:
            if p > .45:
                q = cl((p - .45) / .55)
                wd = f.getlength(txt) * .62
                stroke(d, [(x - wd, y + 6), (x - wd + 2 * wd * q, y + 6)],
                       (171, 38, 30), 9)
    _chip(d, lt, acc, c.get('chip'), c.get('chip_at', 2.6))


def L_anatomy(d, lt, acc, c):
    """The figure on the left third, one body zone ringed, a callout opposite."""
    _title(d, lt, acc, c['title'], c.get('hot'), c.get('sz', 76))
    hx, hs = c.get('hx', 470), c.get('hs', 460)
    pose = {'idle': T.p_idle, 'run': p_run, 'jog': p_jog,
            'present': T.p_present}[c.get('pose', 'idle')]
    hero(d, lt, hx, hs, phys(pose, lt), c.get('expr', 'determined'),
         cl(lt / .4))

    zp = cl((lt - .70) / .6)
    if zp <= 0:
        _chip(d, lt, acc, c.get('chip'), c.get('chip_at', 3.2))
        return
    zx = hx + c['zone'][0] * hs
    zy = GY + c['zone'][1] * hs
    r = c.get('zr', 0.11) * hs
    # breathing ring
    pr = r * (1.0 + 0.045 * math.sin(lt * 2.4)) * e_back(zp, 1.2)
    d.ellipse([zx - pr, zy - pr, zx + pr, zy + pr], outline=acc + (235,), width=6)
    halo = pr * (1.0 + 0.55 * ((lt * 0.9) % 1.0))
    ha = int(90 * (1 - ((lt * 0.9) % 1.0)) * zp)
    d.ellipse([zx - halo, zy - halo, zx + halo, zy + halo],
              outline=acc + (ha,), width=3)

    lp = cl((lt - 1.10) / .55)
    if lp <= 0:
        _chip(d, lt, acc, c.get('chip'), c.get('chip_at', 3.2))
        return
    bx = c.get('bx', 1010)
    by = c.get('by', GY - 400)
    elx = zx + pr * 0.72
    ely = zy - pr * 0.72
    mx = bx - 54
    stroke(d, [(elx, ely), (elx + (mx - elx) * e_out(lp, 2.2),
                            ely + (by - ely) * e_out(lp, 2.2))], acc, 4)
    if lp > .6:
        a = int(255 * cl((lp - .6) / .4))
        d.ellipse([elx - 7, ely - 7, elx + 7, ely + 7], fill=acc + (a,))
        d.text((bx, by), c['label'], font=F(c.get('lsz', 54), 800),
               fill=INK + (a,), anchor='lm')
        yy = by + 60
        for i, ln in enumerate(c.get('lines', [])):
            q = cl((lt - 1.75 - i * .35) / .5)
            if q <= 0: break
            aa = int(255 * cl(q * 1.8))
            d.ellipse([bx + 2, yy + 11, bx + 14, yy + 23], fill=acc + (aa,))
            d.text((bx + 34, yy + 17), ln, font=F(31, 600),
                   fill=(72, 66, 58) + (aa,), anchor='lm')
            yy += 52
        if c.get('big'):
            q = cl((lt - 2.30) / .7)
            if q > 0:
                aa = int(255 * cl(q * 1.7))
                # AUTO-FIT. A fixed 96 px ran 'HEAD STAYS LEVEL' and
                # 'NO PAUSE REQUIRED' straight off the right edge.
                avail = W - 110 - bx
                bsz = 92
                while bsz > 40 and F(bsz, 800).getlength(c['big']) > avail:
                    bsz -= 3
                d.text((bx, yy + 58), c['big'], font=F(bsz, 800),
                       fill=acc + (aa,), anchor='lm')
                if c.get('bigsub'):
                    d.text((bx, yy + 124), c['bigsub'], font=F(27, 600),
                           fill=SOFT + (aa,), anchor='lm')
    _chip(d, lt, acc, c.get('chip'), c.get('chip_at', 3.2))


def L_bignum(d, lt, acc, c):
    """One number, the size of a building."""
    _title(d, lt, acc, c['title'], c.get('hot'), c.get('sz', 76))
    p = cl((lt - .55) / .75)
    if p > 0:
        a = int(255 * cl(p * 1.7))
        k = 1 + .055 * (1 - e_out(p, 2.0))
        sz = int(c.get('vsz', 210) * k)
        f = F(sz, 800)
        y = c.get('vy', GY - 330) + fl(lt, 0, 2.6)
        d.text((W / 2 + 2, y + 3), c['value'], font=f,
               fill=(199, 189, 170, a), anchor='mm')
        d.text((W / 2, y), c['value'], font=f, fill=acc + (a,), anchor='mm')
        if c.get('unit'):
            d.text((W / 2 + f.getlength(c['value']) / 2 + 52,
                    y - sz * .26), c['unit'], font=F(int(sz * .30), 800),
                   fill=INK + (a,), anchor='mm')
    q = cl((lt - 1.25) / .6)
    if q > 0:
        a = int(255 * cl(q * 1.8))
        d.text((W / 2, c.get('ly', GY - 160)), c['label'], font=F(40, 700),
               fill=INK + (a,), anchor='mm')
    r = cl((lt - 1.70) / .6)
    if r > 0 and c.get('sub'):
        a = int(255 * cl(r * 1.8))
        d.text((W / 2, c.get('sy', GY - 96)), c['sub'], font=F(30, 600),
               fill=SOFT + (a,), anchor='mm')
    _chip(d, lt, acc, c.get('chip'), c.get('chip_at', 2.6))


def L_timeline(d, lt, acc, c):
    _title(d, lt, acc, c['title'], c.get('hot'), c.get('sz', 76))
    x0, x1, y = 230, 1690, GY - 230
    p = cl((lt - .45) / .65)
    if p <= 0: return
    xe = x0 + (x1 - x0) * e_out(p, 2.2)
    d.line([(x0, y), (xe, y)], fill=(176, 164, 146), width=5)
    fpoly(d, [(xe, y - 15), (xe + 30, y), (xe, y + 15)], (176, 164, 146), 0)
    for i, (u, lab, sub, hot) in enumerate(c['marks']):
        q = cl((lt - .95 - i * .38) / .5)
        if q <= 0: break
        x = x0 + (x1 - x0) * u
        if x > xe: continue
        a = int(255 * cl(q * 1.8))
        col = acc if hot else (150, 140, 124)
        rr = 19 if hot else 11
        rr = rr * e_back(q, 1.3)
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col + (a,))
        if hot:
            d.ellipse([x - rr - 11, y - rr - 11, x + rr + 11, y + rr + 11],
                      outline=col + (int(a * .55),), width=4)
        up = (i % 2 == 0)
        ty = y - 56 if up else y + 56
        d.line([(x, y - (28 if up else -28)), (x, ty + (12 if up else -12))],
               fill=(196, 185, 165), width=3)
        d.text((x, ty - (26 if up else -2)), lab,
               font=F(34 if hot else 29, 800 if hot else 700),
               fill=(INK if hot else (108, 99, 86)) + (a,), anchor='mm')
        d.text((x, ty + (12 if up else 36)), sub, font=F(24, 600),
               fill=SOFT + (a,), anchor='mm')
    if c.get('note'):
        n = cl((lt - 2.9) / .7)
        if n > 0:
            d.text((W / 2, GY - 60), c['note'], font=F(38, 800),
                   fill=INK + (int(255 * cl(n * 1.8)),), anchor='mm')
    _chip(d, lt, acc, c.get('chip'), c.get('chip_at', 3.6))


def L_stage(d, lt, acc, c):
    """Hero and/or quarry on the horizon, with one line of consequence."""
    _title(d, lt, acc, c['title'], c.get('hot'), c.get('sz', 76))
    if c.get('sun'):
        sp = cl(lt / 1.0)
        sx, sy = c.get('sunpos', (1648, 330))
        sr = 72 * e_back(sp, 1.1)
        for i in range(14):
            a = i / 14 * math.tau + lt * .10
            l0 = sr + 24
            l1 = l0 + 34 * (0.6 + 0.4 * math.sin(lt * 2.1 + i))
            d.line([(sx + math.cos(a) * l0, sy + math.sin(a) * l0),
                    (sx + math.cos(a) * l1, sy + math.sin(a) * l1)],
                   fill=acc + (190,), width=6)
        fcirc(d, sx, sy, sr, acc, 0)
    for k in c.get('kudus', []):
        kx, ks, kg, kt = k
        antelope(d, kx + (math.sin(lt * .4) * 8 if kg else 0), GY - 6, ks,
                 lt + kt, (90, 78, 64), kg, 255, dust=bool(kg))
    if c.get('hero'):
        hx, hs, pz = c['hero']
        pose = {'idle': T.p_idle, 'run': p_run, 'jog': p_jog,
                'walk': T.p_walk, 'point': T.p_point,
                'present': T.p_present, 'think': T.p_think}[pz]
        mv = c.get('move')
        if mv:
            hx = mv[0] + (mv[1] - mv[0]) * e_io(cl(lt / mv[2]))
        hero(d, lt, hx, hs, phys(pose, lt), c.get('expr', 'determined'),
             cl(lt / .4))
    if c.get('phrase'):
        q = cl((lt - c.get('phrase_at', 1.6)) / .7)
        if q > 0:
            # The phrase sits in the band between the headline and the
            # horizon. At GY-150 it was printed straight through the hero
            # and the kudu in four of the five staged scenes.
            line(d, c['phrase'].split(), W / 2, c.get('phrase_y', GY - 470),
                 c.get('psz', 48), 800, INK, c.get('phot'), acc, q, 20)
    _chip(d, lt, acc, c.get('chip'), c.get('chip_at', 3.0))


def L_paper(d, lt, acc, c):
    """An academic paper as a physical card. The credibility beat."""
    _title(d, lt, acc, c['title'], c.get('hot'), c.get('sz', 72))
    p = cl((lt - .55) / .7)
    if p <= 0: return
    k = e_back(p, 1.08)
    cw, ch = 740 * k, 228 * k
    cx, cy = W / 2, GY - 268
    a = int(255 * cl(p * 1.8))
    d.rounded_rectangle([cx - cw, cy - ch, cx + cw, cy + ch], 18,
                        fill=(252, 249, 241), outline=INK + (a,), width=5)
    d.rounded_rectangle([cx - cw, cy - ch, cx - cw + 18, cy + ch], 9, fill=acc)
    if p < .6: return
    b = int(255 * cl((p - .6) / .4))
    d.text((cx - cw + 64, cy - ch + 50), c['journal'].upper(),
           font=F(28, 800), fill=acc + (b,), anchor='lm')
    d.text((cx + cw - 64, cy - ch + 50), c['year'], font=F(46, 800),
           fill=acc + (b,), anchor='rm')
    # title, wrapped
    f = F(42, 700)
    words, cur, rows = c['paper'].split(), '', []
    for wd in words:
        t2 = (cur + ' ' + wd).strip()
        if f.getlength(t2) > cw * 1.72:
            rows.append(cur); cur = wd
        else:
            cur = t2
    rows.append(cur)
    yy = cy - ch + 116
    for i, rw in enumerate(rows[:3]):
        q = cl((lt - 1.25 - i * .22) / .45)
        if q <= 0: break
        d.text((cx - cw + 64, yy), rw, font=f,
               fill=INK + (int(255 * cl(q * 1.8)),), anchor='lm')
        yy += 56
    q = cl((lt - 1.95) / .5)
    if q > 0:
        d.text((cx - cw + 64, cy + ch - 46), c['authors'], font=F(31, 600),
               fill=(96, 88, 76) + (int(255 * cl(q * 1.8)),), anchor='lm')
    # verdict stamp
    v = cl((lt - 2.45) / .55)
    if v > 0 and c.get('verdict'):
        ang = -6
        vw = F(34, 800).getlength(c['verdict']) / 2 + 36
        sx, sy = cx + cw - vw - 54, cy + ch - 44
        stamp = Image.new('RGBA', (int(vw * 2) + 16, 76), (0, 0, 0, 0))
        sd = ImageDraw.Draw(stamp, 'RGBA')
        aa = int(235 * cl(v * 1.8))
        sd.rounded_rectangle([4, 4, vw * 2 + 8, 68], 34,
                             outline=c['vcol'] + (aa,), width=5)
        sd.text((vw + 6, 37), c['verdict'], font=F(34, 800),
                fill=c['vcol'] + (aa,), anchor='mm')
        stamp = stamp.rotate(ang, Image.BICUBIC, expand=True)
        base = getattr(d, '_image', None)
        if base is not None:
            base.alpha_composite(stamp, (int(sx - stamp.width / 2),
                                         int(sy - stamp.height / 2)))
    _chip(d, lt, acc, c.get('chip'), c.get('chip_at', 3.3))


def L_list(d, lt, acc, c):
    _title(d, lt, acc, c['title'], c.get('hot'), c.get('sz', 76))
    rows = c['rows']
    x0 = c.get('x0', 300)
    x1 = c.get('x1', 1620)
    y = c.get('y0', GY - 390)
    gap = c.get('gap', 108)
    for i, r in enumerate(rows):
        p = cl((lt - .80 - i * .42) / .55)
        if p <= 0: break
        a = int(255 * cl(p * 1.7))
        yy = y + i * gap + fl(lt, i, 2.2)
        xe = x0 + (x1 - x0) * e_out(p, 2.4)
        d.line([(x0, yy + 44), (xe, yy + 44)], fill=(214, 203, 184), width=3)
        mk = r.get('mark', 'dot')
        if mk == 'tick':
            _tick(d, x0 + 26, yy, 22, acc, cl(p * 1.6), 8)
        elif mk == 'cross':
            _cross(d, x0 + 26, yy, 19, (171, 38, 30), cl(p * 1.6), 8)
        else:
            d.ellipse([x0 + 12, yy - 11, x0 + 34, yy + 11], fill=acc + (a,))
        d.text((x0 + 76, yy), r['label'], font=F(r.get('lsz', 38), 700),
               fill=INK + (a,), anchor='lm')
        if r.get('value'):
            d.text((x1, yy), r['value'], font=F(r.get('vsz', 48), 800),
                   fill=(r.get('vcol') or acc) + (a,), anchor='rm')
    if c.get('quote'):
        q = cl((lt - .80 - len(rows) * .42 - .35) / .7)
        if q > 0:
            a = int(255 * cl(q * 1.7))
            yq = y + len(rows) * gap + 44
            d.text((W / 2, yq), '“' + c['quote'] + '”', font=F(40, 700),
                   fill=acc + (a,), anchor='mm')
            if c.get('qsrc'):
                d.text((W / 2, yq + 48), c['qsrc'], font=F(26, 600),
                       fill=SOFT + (a,), anchor='mm')
    _chip(d, lt, acc, c.get('chip'), c.get('chip_at', 3.8))


def L_bars(d, lt, acc, c):
    _title(d, lt, acc, c['title'], c.get('hot'), c.get('sz', 76))
    bars = c['bars']
    by = GY - 150
    maxh = 330
    n = len(bars)
    for i, b in enumerate(bars):
        p = cl((lt - .80 - i * .38) / .65)
        if p <= 0: break
        x = W / 2 + (i - (n - 1) / 2) * c.get('step', 430)
        hgt = maxh * b['v'] * e_out(p, 2.2)
        col = b.get('col') or acc
        bw = c.get('bw', 190)
        d.rounded_rectangle([x - bw / 2, by - hgt, x + bw / 2, by], 10,
                            fill=col)
        a = int(255 * cl(p * 1.7))
        d.text((x, by + 38), b['label'], font=F(32, 700), fill=INK + (a,),
               anchor='mm')
        if b.get('sub'):
            d.text((x, by + 78), b['sub'], font=F(26, 600), fill=SOFT + (a,),
                   anchor='mm')
        if b.get('top'):
            d.text((x, by - hgt - 44), b['top'], font=F(46, 800),
                   fill=col + (a,), anchor='mm')
    if c.get('verdict'):
        q = cl((lt - 1.9) / .7)
        if q > 0:
            d.text((W / 2, GY - 530), c['verdict'], font=F(64, 800),
                   fill=acc + (int(255 * cl(q * 1.8)),), anchor='mm')
    _chip(d, lt, acc, c.get('chip'), c.get('chip_at', 3.2))


def L_statement(d, lt, acc, c):
    """Big centred type. Used only where the script lands a hammer."""
    ys = c.get('ys', [GY - 400, GY - 290, GY - 180])
    for i, ln in enumerate(c['lines']):
        p = cl((lt - c.get('at', .45) - i * .70) / .75)
        if p <= 0: break
        txt, hot = ln if isinstance(ln, tuple) else (ln, None)
        line(d, txt.split(), W / 2, ys[i], c.get('sz', 78), 800, INK, hot,
             acc, p, 28)
    if c.get('hero'):
        hx, hs, pz = c['hero']
        pose = {'idle': T.p_idle, 'walk': T.p_walk, 'jog': p_jog,
                'run': p_run, 'present': T.p_present}[pz]
        hero(d, lt, hx, hs, phys(pose, lt), c.get('expr', 'determined'),
             cl(lt / .4))
    _chip(d, lt, acc, c.get('chip'), c.get('chip_at', 2.8))


# ═══════════════════════════════════════════ BODY SCENE TABLE (S9…S34)
RED = (171, 38, 30)
GRN = (26, 96, 58)

BODY = [
    # ── ACT 2  THE MACHINE ────────────────────────────────────────────
    dict(L=L_triple, title='BUILT FOR ONE THING', hot={3},
         items=[('STRENGTH', False), ('SPEED', False), ('DISTANCE', True)],
         chip='STRIP A HUMAN DOWN TO THE FRAME', chip_at=3.2),

    dict(L=L_anatomy, title='THE NUCHAL LIGAMENT', hot={2}, pose='run',
         zone=(0.02, -0.78), zr=0.105, bx=1000, by=GY - 430,
         label='NUCHAL LIGAMENT',
         lines=['Absent in chimpanzees', 'Absent in Australopithecus',
                'Present in Homo'],
         big='HEAD STAYS LEVEL', bigsub='ITS ONLY JOB WHEN YOU RUN',
         chip='YOU CANNOT RUN WITH A WOBBLING HEAD', chip_at=4.4),

    dict(L=L_anatomy, title='THE ACHILLES TENDON', hot={2}, pose='idle',
         zone=(-0.07, -0.06), zr=0.085, bx=1000, by=GY - 430,
         label='ACHILLES TENDON',
         lines=['Thickest tendon in the body', 'Measured at 70 kg, 4.5 m/s'],
         big='35 OF 100 J', bigsub='STORED ON LANDING, RETURNED ON PUSH-OFF',
         chip='ENERGY RETURNED, NOT SPENT', chip_at=5.0),

    dict(L=L_bignum, title='THE ARCH OF YOUR FOOT', hot={1}, value='17%',
         vsz=230, label='OF STANCE ENERGY RETURNED, EVERY STEP',
         sub='THE SAME TRICK, A SECOND TIME',
         chip='YOU ARE NOT RUNNING ON MUSCLE — YOU ARE RUNNING ON SPRINGS',
         chip_at=3.4),

    dict(L=L_anatomy, title='AND THEN THE SKIN', hot={3}, pose='idle',
         zone=(0.00, -0.56), zr=0.17, bx=1020, by=GY - 430,
         label='ECCRINE GLANDS',
         lines=['Two to four million, on bare skin',
                'Roughly ten times a chimpanzee',
                'Cools you WHILE you keep moving'],
         big='NO PAUSE REQUIRED', bigsub='A PANTING ANIMAL HAS TO STOP',
         chip='EVAPORATION BEATS PANTING IN DRY HEAT', chip_at=4.6),

    dict(L=L_timeline, title='WHEN THE BODY ARRIVED', hot={3},
         marks=[(0.04, '6 Mya', 'LINEAGES SPLIT', False),
                (0.30, '4 Mya', 'AUSTRALOPITHECUS — WALKS', False),
                (0.63, '1.8 Mya', 'EARLY HOMO — RUNS', True),
                (0.95, '0.3 Mya', 'H. SAPIENS', False)],
         note='BEFORE THAT, NOTHING IN OUR LINE WAS BUILT TO RUN',
         chip='BRAMBLE & LIEBERMAN, NATURE 432 (2004)', chip_at=4.4),

    # ── ACT 3  THE HUNT ───────────────────────────────────────────────
    dict(L=L_stage, title='MIDDAY, ON PURPOSE', hot={1}, sun=True,
         hero=(430, 330, 'jog'), kudus=[(1430, 150, 0.0, 3.1),
                                        (1680, 132, 0.0, 7.4)],
         phrase='THE HEAT IS THE WEAPON', phot={3}, phrase_at=2.2,
         chip='THE HOTTEST HOUR OF THE DAY', chip_at=4.2),

    dict(L=L_stage, title='PICK ONE', hot={0},
         hero=(330, 420, 'point'),
         kudus=[(1230, 168, 1.0, 1.3), (1600, 150, 1.0, 4.9)],
         phrase='NOT TO CATCH IT — TO START A CLOCK', phot={5},
         phrase_at=2.4, chip='YOU ONLY HAVE TO MAKE IT RUN', chip_at=4.4),

    dict(L=L_bignum, title='IT IS FASTER THAN YOU', hot={2}, value='3×',
         vsz=250, label='AND IN NINETY SECONDS IT IS GONE',
         sub='THAT IS NOT A PROBLEM', chip_at=3.0),

    dict(L=L_stage, title='IT LEFT A TRACK', hot={2},
         hero=(1430, 380, 'think'), expr='think',
         phrase='TRACKING IS THE REAL SKILL', phot={2}, phrase_at=1.45,
         track=True, chip='YOU DO NOT NEED TO SEE IT', chip_at=2.75),

    dict(L=L_stage, title='FOUND IT. IN THE SHADE.', hot={3},
         kudus=[(1310, 215, 0.0, 2.2)], hero=(460, 380, 'jog'),
         phrase='MAKE IT RUN AGAIN, BEFORE IT HAS FINISHED', phot={1},
         phrase_at=2.2, chip='IT NEVER GETS TO DUMP THE HEAT', chip_at=4.0),

    dict(L=L_bignum, title='REPEAT', hot={0}, value='25–35',
         unit='km', vsz=190, label='COVERED IN A SINGLE PURSUIT',
         sub='TWO HOURS. THREE. SOMETIMES FIVE.',
         chip='NO WEAPON HAS BEEN USED YET', chip_at=3.6),

    dict(L=L_list, title='WHAT THE DATA ACTUALLY SAYS', hot={2},
         y0=GY - 400, gap=112,
         rows=[dict(label='Persistence hunts recorded', value='8'),
               dict(label='Mean duration', value='2 h 18 min'),
               dict(label='Kills / attempts', value='12 / 31')],
         chip='LIEBENBERG · CURRENT ANTHROPOLOGY · 2006', chip_at=4.4),

    dict(L=L_bignum, title='THE LONGEST ONE MEASURED', hot={1},
         value='3 h 35', vsz=200, label='KAROHA LANGWANE, ONE KUDU',
         sub='THIRTY-FIVE KILOMETRES OF KALAHARI SAND',
         chip='A SINGLE ANIMAL, A SINGLE AFTERNOON', chip_at=3.8),

    dict(L=L_stage, title='IT DOES NOT GET CAUGHT', hot={4},
         kudus=[(1300, 235, 0.0, 5.0)], hero=(470, 400, 'walk'),
         move=(240, 740, 5.0),
         phrase='IT STOPS', phot={0}, phrase_at=2.0, psz=64,
         phrase_y=GY - 455,
         chip='STANDING, HEAD DOWN, TONGUE OUT', chip_at=4.0),

    dict(L=L_bignum, title='CORE TEMPERATURE', hot={1}, value='44',
         unit='°C', vsz=230, label='THE POINT WHERE THE LEGS GO',
         chip_at=2.4),

    dict(L=L_statement, title='', at=.10, sz=74,
         lines=[('EX · HAUST', {0}), ('TO DRAW OUT, COMPLETELY', {3})],
         ys=[GY - 400, GY - 280],
         chip='THAT IS WHAT THE WORD ORIGINALLY MEANT', chip_at=2.35),

    # ── ACT 4  THE ARGUMENT ───────────────────────────────────────────
    dict(L=L_statement, at=.45, sz=70,
         lines=[('MOST VIDEOS WOULD STOP HERE', {4}),
                ('THIS ONE WILL NOT', {3})],
         ys=[GY - 400, GY - 280],
         chip='THERE IS AN ARGUMENT YOU DESERVE TO HEAR', chip_at=3.4),

    dict(L=L_paper, title='THE CASE FOR', hot={2},
         journal='Nature 432', year='2004',
         paper='Endurance running and the evolution of Homo',
         authors='Dennis M. Bramble  ·  Daniel E. Lieberman',
         verdict='THE CASE FOR', vcol=GRN,
         chip='ONE OF THE MOST CITED IDEAS IN HUMAN EVOLUTION',
         chip_at=3.6),

    dict(L=L_paper, title='THE CASE AGAINST', hot={2},
         journal='Journal of Human Evolution', year='2007',
         paper='The endurance running hypothesis and hunting and scavenging in savanna-woodlands',
         authors='Travis R. Pickering  ·  Henry T. Bunn',
         verdict='THE CASE AGAINST', vcol=RED,
         chip='PUBLISHED THREE YEARS LATER, AND IT LANDED',
         chip_at=3.6),

    dict(L=L_list, title='THE OBJECTION', hot={1}, y0=GY - 400, gap=112,
         rows=[dict(label='Hadza, twenty years of direct observation',
                    value='0 seen', vcol=RED, mark='cross'),
               dict(label='Persistence hunting, ethnographically',
                    value='RARE', vcol=RED, mark='cross'),
               dict(label='Restricted to very hot, very open habitat',
                    value='YES', vcol=RED, mark='cross')],
         chip='PICKERING & BUNN, 2007', chip_at=4.2),

    dict(L=L_list, title='AND IT GOT WORSE', hot={3}, y0=GY - 380, gap=108,
         rows=[dict(label="Liebenberg's running hunts, total", value='10'),
               dict(label='Arranged for film crews', value='8', vcol=RED,
                    mark='cross')],
         quote='the tyranny of ethnography',
         qsrc='— LIEBERMAN ET AL., REPLY, 2007',
         chip_at=5.0),

    dict(L=L_list, title='WHAT NOBODY DISPUTES', hot={1}, y0=GY - 420,
         gap=96, x0=420, x1=1500,
         rows=[dict(label='The nuchal ligament', value='MEASURABLE',
                    mark='tick', vsz=34),
               dict(label='The Achilles tendon', value='MEASURABLE',
                    mark='tick', vsz=34),
               dict(label='The plantar arch', value='MEASURABLE',
                    mark='tick', vsz=34),
               dict(label='Two to four million glands', value='MEASURABLE',
                    mark='tick', vsz=34)],
         chip='THE BEHAVIOUR IS ARGUED — THE HARDWARE IS NOT', chip_at=5.2),

    # ── ACT 5  WHAT YOU INHERITED ─────────────────────────────────────
    dict(L=L_bignum, title='APRIL 2026, LONDON', hot={2}, value='1:59:30',
         vsz=190, label='SABASTIAN SAWE — 42.195 KILOMETRES',
         sub='THE FIRST OFFICIAL SUB-TWO-HOUR MARATHON',
         chip='NO OTHER ANIMAL ON EARTH DOES THIS', chip_at=3.6),

    dict(L=L_list, title='MAN versus HORSE', hot={1}, y0=GY - 400, gap=112,
         x0=420, x1=1500,
         rows=[dict(label='Llanwrtyd Wells, Wales — 22 miles',
                    value='SINCE 1980', vsz=36),
               dict(label='Years a horse won', value='MOST'),
               dict(label='Times a human has won outright', value='5',
                    mark='tick', vcol=GRN)],
         chip='2004 · 2007 · 2022 · 2023 · 2025', chip_at=4.4),

    dict(L=L_statement, at=.45, sz=66, hero=(W / 2, 330, 'jog'),
         lines=[('SAME LIGAMENT. SAME TENDON. SAME ARCH.', {0, 2, 4}),
                ('MOST OF US WILL NEVER USE IT.', {5}),
                ('IT IS STILL THERE.', {3})],
         ys=[290, 372, 454],
         chip='SUBSCRIBE — THE NEXT ONE IS ALREADY RUNNING', chip_at=4.6),
]
assert len(BODY) == 26, len(BODY)


# ───────────────────────────────────────────── footprint track (S18)
_TRK = np.random.default_rng(404)
_TRKPTS = [(0.03 + i * 0.062, float(_TRK.uniform(-1, 1))) for i in range(16)]


def draw_track(d, lt, acc):
    p = cl((lt - .60) / 2.6)
    if p <= 0: return
    n = int(len(_TRKPTS) * e_out(p, 1.5))
    for i in range(n):
        u, j = _TRKPTS[i]
        x = 130 + u * 1210
        y = GY - 46 + j * 22 - u * 128
        a = int(150 * cl((n - i) / 5.0) * 0.55 + 70)
        s = 26 - u * 7
        ang = -0.34 + j * 0.10
        ca, sa = math.cos(ang), math.sin(ang)
        # a cloven hoof: two teardrops, splayed at the toe
        for sgn in (-1, 1):
            pts = []
            for q in range(13):
                th = q / 12 * math.tau
                rx, ry = s * .30, s * .62
                dx = math.cos(th) * rx + sgn * s * .32
                dy = math.sin(th) * ry * (1.18 if math.sin(th) < 0 else 0.86)
                dx += sgn * (-dy / (s * .62)) * s * .17      # splay
                pts.append((x + (dx * ca - dy * sa), y + (dx * sa + dy * ca)))
            d.polygon(pts, fill=(112, 98, 78, a))


# ───────────────────────────────────────────── scene dispatch
def scene_img(si, lt):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, 'RGBA')
    acc = accent(si)
    if si < 8:
        WD.SCENES[si](d, lt, acc)
        for t0, t1, txt, hot in WD.CAPS[si]:
            if t0 <= lt < t1:
                caption(d, txt.split(), (lt - t0) / (t1 - t0), acc, hot)
                break
    else:
        c = BODY[si - 8]
        if c.get('track'):
            draw_track(d, lt, acc)
        c['L'](d, lt, acc, c)
    return im


# ───────────────────────────────────────────── frame
_AMP = [0.024, 0.030, 0.020, 0.034, 0.026, 0.030, 0.022, 0.036]


Z0 = 1.032          # zoom floor: 30 px of pan headroom in x, 13 px in y


def _tri(x):
    """Constant-speed triangle wave in [-1, 1]; no zero-velocity points."""
    return 4.0 * abs(x - math.floor(x + .5)) - 1.0


def amp_of(si):
    if si < 8: return _AMP[si]
    return (0.022, 0.030, 0.026, 0.034, 0.020, 0.028)[(si - 8) % 6]


def render(i):
    t = i / FPS
    si = max(k for k in range(NS) if t >= SCENE_START[k])
    lt = t - SCENE_START[si]

    tp, tk = None, si
    for k, cpos in enumerate(CUTS):
        cc = cpos + TLAG
        if cc - TDUR / 2 <= t < cc + TDUR / 2:
            tp = (t - cc + TDUR / 2) / TDUR
            tk = k
            break

    show = si if tp is None else (tk if tp < .5 else tk + 1)
    slt = t - SCENE_START[show]
    if tp is not None and tp < .5:
        slt = SCENE_END[tk] - SCENE_START[tk] - .001
    acc = accent(show)

    base = backdrop(t, show, acc)
    sh = 0.0
    if show == 2: sh = 1.0
    elif show == 1: sh = 0.30 * cl(slt / 3.0)
    elif show == 3: sh = 0.35 * (1 - cl(slt / 2.2))
    elif show == 14: sh = 0.85                      # midday, Act 3 opener
    elif show == 15: sh = 0.55
    elif show == 18: sh = 0.45
    if sh > 0:
        base = heat_shimmer(base, t, sh)

    cv = base.convert('RGBA')
    cv.alpha_composite(scene_img(show, slt))
    d = ImageDraw.Draw(cv, 'RGBA')
    chrome(d, t, show, acc)

    if tp is not None:
        nacc = accent(tk + 1)
        tint = tuple(int(nacc[j] * .18 + PAPER[j] * .82) for j in range(3))
        glow = tuple(int(nacc[j] * .40 + PAPER[j] * .60) for j in range(3))
        e = e_io(tp)
        lx = W - 2 * W * e
        d.rectangle([lx + W * .028, 0, lx + W, H], fill=tint)
        d.rectangle([lx + W * .016, 0, lx + W * .028, H], fill=glow)
        d.rectangle([lx + W * .004, 0, lx + W * .016, H], fill=nacc)
        d.rectangle([lx, 0, lx + W * .004, H], fill=INK)

    frame = cv.convert('RGB')

    dur = SCENE_END[si] - SCENE_START[si]
    amp = amp_of(si)
    # Camera. Two rules learned the hard way:
    #  1) z must never drop below Z_FLOOR or the affine samples outside the
    #     source and PIL fills the gap with black (17 px slivers at 0.988).
    #  2) velocity must never reach zero, or the 10th-percentile frame-diff
    #     collapses and the shot reads as frozen. Hence a linear-dominant
    #     ramp and triangle-wave pans instead of eased sines.
    u = cl(lt / dur)
    ramp = .15 * e_io(u) + .85 * u
    if si % 2:
        ramp = 1.0 - ramp                           # odd scenes pull back
    z = Z0 + amp * ramp + math.exp(-lt * 6.4) * math.sin(lt * 16.5) * .0048
    px = 22.0 * _tri(t / 14.0)                  # 6.3 px/s, constant
    py = 10.0 * _tri(t / 20.0 + .37)                # 2.0 px/s, constant
    iz = 1.0 / z
    frame = frame.transform((W, H), Image.AFFINE,
                            (iz, 0, (W - W * iz) * .5 + px,
                             0, iz, (H - H * iz) * .5 + py), Image.BICUBIC)

    arr = np.asarray(frame).astype(np.float32)
    arr += _GRAIN
    ft = DUR_TOTAL - t
    if ft < 0.60:
        m = e_io(cl(ft / 0.60))
        arr = arr * m + np.float32(PAPER) * (1 - m)
    return np.clip(arr, 0, 255).astype(np.uint8)


def shard(a, b, path):
    import imageio_ffmpeg, time
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    os.makedirs('/home/user/build', exist_ok=True)
    p = subprocess.Popen([ff, '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-an',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '17',
                          '-pix_fmt', 'yuv420p', '-g', '30', path],
                         stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    t0 = time.time()
    for i in range(a, b):
        p.stdin.write(render(i).tobytes())
        k = i - a + 1
        if k % 100 == 0:
            el = time.time() - t0
            print(f'[{a}:{b}] {k}/{b-a} {el:.0f}s eta {el/k*(b-a-k):.0f}s',
                  flush=True)
    p.stdin.close(); p.wait()
    print(f'[{a}:{b}] DONE', flush=True)


if __name__ == '__main__':
    if len(sys.argv) == 4:
        shard(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])
