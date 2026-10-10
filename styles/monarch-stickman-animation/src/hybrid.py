"""
hybrid.py — the SHADE look: paper/ink engine + the character's diagonal DNA
===========================================================================
* paper (v9 grain, soft accent fields) BELOW a charcoal wedge that covers the
  chrome + headline zone; the diagonal is the reference portrait's split
* the diagonal never rests: both ends drift (±28 px / ±22 px, two slow periods)
* a thin accent SEAM with a soft glow runs along the split — the one signature
* on the dark half the type is PAPER, the hot word ACC_HI (WCAG ≥ 4.5:1 both)
* everything that must stay ink-on-paper (props, payoff, caption, ground) lives
  below the line — wedge_y() is the contract, measured at build time
"""
import math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, '/home/user/src')
import clean as C
from clean import W, H, PAPER, PAPER_D, SOFT, INK, ACC, ACC_HI, F, cl, line

DARK   = (38, 36, 41)
DARK_L = (52, 50, 56)
PAPER_ON_DARK = (236, 232, 222)
CHROME_TRACK = (78, 76, 84)

# split geometry: y at the left edge and at the right edge (dark is ABOVE)
YL0, YR0 = 1000.0, 540.0


def wedge_ends(t):
    yl = YL0 + 28.0 * math.sin(t * 0.37 + .6)
    yr = YR0 + 22.0 * math.sin(t * 0.29 + 2.1)
    return yl, yr


def wedge_y(x, t):
    yl, yr = wedge_ends(t)
    return yl + (yr - yl) * (x / W)


def backdrop(t, si, acc):
    """Paper + accent fields (v9) with the charcoal wedge and the seam on top."""
    bg = C.backdrop(t, si, acc).convert('RGBA')
    yl, yr = wedge_ends(t)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay, 'RGBA')
    d.polygon([(0, 0), (W, 0), (W, yr), (0, yl)], fill=DARK + (255,))
    # a soft lift toward the top-left so the dark is a room, not a hole
    g = Image.new('L', (W // 8, H // 8), 0)
    gd = ImageDraw.Draw(g)
    gd.ellipse([-W // 16, -H // 16, W // 10, H // 10], fill=255)
    g = g.filter(ImageFilter.GaussianBlur(28)).resize((W, H), Image.BILINEAR)
    lift = Image.new('RGBA', (W, H), DARK_L + (255,))
    lay.paste(lift, (0, 0), g.point(lambda v: int(v * .55)))
    # a whisper of the scene accent inside the dark (never neon)
    ab = Image.new('RGBA', (W // 4, H // 4), (0, 0, 0, 0))
    ImageDraw.Draw(ab).ellipse([W // 4 * .55 - 190, -120, W // 4 * .55 + 190, 260], fill=acc + (26,))
    lay.alpha_composite(ab.filter(ImageFilter.GaussianBlur(40)).resize((W, H), Image.BILINEAR))
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).polygon([(0, 0), (W, 0), (W, yr), (0, yl)], fill=255)
    lay.putalpha(mask)
    bg.alpha_composite(lay)
    # seam: glow then hairline
    sd = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sd).line([(0, yl), (W, yr)], fill=acc + (120,), width=16)
    bg.alpha_composite(sd.filter(ImageFilter.GaussianBlur(9)))
    ImageDraw.Draw(bg, 'RGBA').line([(0, yl), (W, yr)], fill=acc + (235,), width=4)
    return bg


def _lighten_to(col, bg, target=4.8):
    c = list(col)
    for _ in range(60):
        if contrast(tuple(int(v) for v in c), bg) >= target:
            break
        c = [min(255, v * 1.04 + 4) for v in c]
    return tuple(int(v) for v in c)


# hot-word colours on the dark band, pushed until every one clears 4.8:1 (measured)
HOT = None


def hot(si):
    global HOT
    if HOT is None:
        HOT = [_lighten_to(a, DARK) for a in ACC_HI]
    return HOT[si]


def chrome(d, t, si, acc, total, chapters):
    """Progress hairline + chapter label, on the dark band."""
    y = 142
    d.rounded_rectangle([64, y - 3, W - 64, y + 3], 3, fill=CHROME_TRACK)
    fxp = 64 + (W - 128) * cl(t / total)
    hi = hot(si)
    d.rounded_rectangle([64, y - 3, fxp, y + 3], 3, fill=hi)
    d.ellipse([fxp - 9, y - 9, fxp + 9, y + 9], fill=hi)
    d.text((64, 198), f'{si + 1:02d}', font=F(34, 800), fill=hi, anchor='lm')
    d.text((108, 199), f'/ 06   {chapters[si]}', font=F(26, 600), fill=(168, 164, 158), anchor='lm')


def headline(d, words, cx, y, sz, hot_idx, si, p, rise=44, wt=800):
    """Extruded headline on the dark band: paper face, bright accent hot word."""
    line(d, words, cx, y, sz, wt, PAPER_ON_DARK, hot_idx, hot(si), p, rise)


def contrast(a, b):
    def L(c):
        r, g, b_ = [v / 255 for v in c]
        f = lambda u: u / 12.92 if u <= .03928 else ((u + .055) / 1.055) ** 2.4
        return .2126 * f(r) + .7152 * f(g) + .0722 * f(b_)
    la, lb = L(a), L(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + .05) / (lo + .05)


if __name__ == '__main__':
    print('paper-on-dark', round(contrast(PAPER_ON_DARK, DARK), 2))
    for i, a in enumerate(ACC_HI):
        print(i, 'hot on dark', hot(i), round(contrast(hot(i), DARK), 2), '| acc on paper', round(contrast(ACC[i], PAPER), 2))
