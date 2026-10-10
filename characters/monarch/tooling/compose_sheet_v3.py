#!/usr/bin/env python3
"""MONARCH STUDIO character sheet composer (v3): single-column sheet (1376-wide strips) with an optional
HERO ROW (hero bust + a stacked side column of likeness/reference images) followed by labelled strips.
usage: python3 compose_sheet_v3.py spec.json
spec = {"out": "...png", "title": "...", "sub": "...", "sub2": "...",
        "hero_row": {"img": "hero.png", "tag": "HERO SHOT", "side": [{"img": "...", "tag": "...", "w": 432, "h": 578}, ...]} | null,
        "rows": [{"img": "path", "tag": "TURNAROUND", "labels": ["FRONT", ...], "cols": 3, "grid": 2?}],
        "notes": ["...", ...]}
Strips are pasted at native 1:1 scale (never upscaled); hero-row side images may be DOWN-scaled to the given w×h."""
import sys, json, hashlib, datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter

spec = json.load(open(sys.argv[1]))
FONT = '/home/user/fonts/Montserrat-VF.ttf'
M, GAP, HEAD, LAB = 72, 48, 226, 52
AMBER, TEAL = (255, 196, 92), (96, 214, 214)

rows = [dict(r, im=Image.open(r['img']).convert('RGB')) for r in spec['rows']]
right_w = max(r['im'].width for r in rows)
hero_row = spec.get('hero_row')
if hero_row:
    hero = Image.open(hero_row['img']).convert('RGB')
    sides = []
    for s in hero_row.get('side', []):
        im = Image.open(s['img']).convert('RGB')
        if 'w' in s and (im.width > s['w'] or im.height > s['h']):
            im = im.resize((s['w'], s['h']), Image.LANCZOS)   # down-scale only
        sides.append(dict(s, im=im))
    hero_h = hero.height
W = M + right_w + M
strips_h = sum(r['im'].height + LAB for r in rows) + GAP * (len(rows) - 1)
def _font(sz, w=600):
    f = ImageFont.truetype(FONT, sz)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
def wrap_note(n, maxw, f):
    # split over-long notes at ' · ' separators so every line fits inside the margins
    parts = n.split(' · '); lines, cur = [], ''
    for ptxt in parts:
        cand = ptxt if not cur else cur + ' · ' + ptxt
        if ImageDraw.Draw(Image.new('RGB', (8, 8))).textlength(cand, font=f) <= maxw: cur = cand
        else:
            if cur: lines.append(cur)
            cur = ptxt
    if cur: lines.append(cur)
    return lines
notes = [l for n in spec.get('notes', []) for l in wrap_note(n, W - 2 * M, _font(19, 500))]
FOOT = 70 + 32 * len(notes)
H = HEAD + (hero_h + LAB + GAP if hero_row else 0) + strips_h + FOOT

img = Image.new('RGB', (W, H), (16, 18, 20))
vig = Image.new('L', (W, H), 0); ImageDraw.Draw(vig).ellipse([-W * 0.2, -H * 0.3, W * 1.2, H * 1.3], fill=255)
img = Image.composite(Image.new('RGB', (W, H), (26, 29, 33)), img, vig.filter(ImageFilter.GaussianBlur(220)))
d = ImageDraw.Draw(img)

def font(sz, w=600):
    f = ImageFont.truetype(FONT, sz)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
def text(xy, s, sz, fill=(236, 236, 236), w=600, anchor='la'):
    d.text(xy, s, font=font(sz, w), fill=fill, anchor=anchor)
def tag(x, y, s):
    tw = d.textlength(s, font=font(20, 700))
    d.rounded_rectangle([x + 18, y + 18, x + 18 + tw + 28, y + 58], radius=8, fill=(0, 0, 0))
    text((x + 32, y + 27), s, 20, AMBER, 700)
def frame(x, y, im):
    img.paste(im, (x, y)); d.rectangle([x, y, x + im.width - 1, y + im.height - 1], outline=(70, 74, 80), width=2)

# header
text((M, 54), 'MONARCH STUDIO', 26, TEAL, 700)
text((M, 90), spec['title'], 44, (245, 245, 245), 800)
def fit(s_, sz, maxw, w=500):
    while sz > 12 and d.textlength(s_, font=font(sz, w)) > maxw: sz -= 1
    return sz
sub = spec['sub']; text((M, 142), sub, fit(sub, 20, W - 2 * M), (170, 176, 184), 500)
sub2 = spec.get('sub2', 'face identity locked to the reference videos (VID_20261010_145131 · Snapchat-1811422650 · Side face)')
text((M, 170), sub2, fit(sub2, 20, W - 2 * M), (170, 176, 184), 500)
d.line([(M, HEAD - 8), (W - M, HEAD - 8)], fill=(60, 64, 70), width=2)

y = HEAD
if hero_row:
    frame(M, y, hero); tag(M, y, hero_row.get('tag', 'HERO SHOT'))
    sx = M + hero.width + GAP; sy = y
    n = len(sides)
    free = hero_h - sum(s['im'].height for s in sides); sgap = free // max(1, n - 1) if n > 1 else 0
    for s in sides:
        frame(sx, sy, s['im']); tag(sx, sy, s['tag'])
        if s.get('caption'):
            text((sx + s['im'].width - 12, sy + s['im'].height - 14), s['caption'], 15, (200, 204, 210), 600, 'rd')
        sy += s['im'].height + sgap
    if hero_row.get('label'):
        text((M + hero.width / 2, y + hero_h + 14), hero_row['label'], 20, (220, 224, 230), 700, 'ma')
    if hero_row.get('side_label') and sides:
        text((sx + sides[0]['im'].width / 2, y + hero_h + 14), hero_row['side_label'], 18, (220, 224, 230), 700, 'ma')
        d.line([(sx - GAP / 2, y + hero_h + 10), (sx - GAP / 2, y + hero_h + LAB - 6)], fill=(60, 64, 70), width=2)
    y += hero_h + LAB + GAP

for r in rows:
    im = r['im']; x = M
    frame(x, y, im); tag(x, y, r['tag'])
    n = r.get('cols', len(r['labels'])); cw = im.width / n
    if r.get('grid'):
        rows_n = r['grid']; ch = im.height / rows_n
        for i, lab in enumerate(r['labels']):
            c, rr = i % n, i // n
            f = font(18, 700); tw = d.textlength(lab, font=f)
            bx, by = int(x + cw * c + 14), int(y + ch * rr + ch - 44)
            d.rounded_rectangle([bx, by, bx + tw + 24, by + 30], radius=6, fill=(0, 0, 0))
            d.text((bx + 12, by + 6), lab, font=f, fill=(236, 236, 236))
    else:
        for i, lab in enumerate(r['labels']):
            text((x + cw * (i + 0.5), y + im.height + 14), lab, 20 if n <= 4 else 18, (220, 224, 230), 700, 'ma')
            if i: d.line([(x + cw * i, y + im.height + 10), (x + cw * i, y + im.height + LAB - 6)], fill=(60, 64, 70), width=2)
    y += im.height + LAB + GAP

fy = y - GAP + 22
for i, n in enumerate(notes): text((M, fy + i * 32), n, 19, (180, 186, 194), 500)
text((W - M, H - 40), f'{datetime.date.today().isoformat()}  ·  MONARCH STUDIO  ·  NOIRGO MAX custom-character option', 18, (120, 126, 134), 500, 'ra')

out = spec['out']; img.save(out, optimize=True); img.save(out[:-4] + '.jpg', quality=92)
print(json.dumps(dict(out=out, size=img.size, md5=hashlib.md5(open(out, 'rb').read()).hexdigest())))
