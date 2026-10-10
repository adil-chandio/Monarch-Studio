#!/usr/bin/env python3
"""MONARCH STUDIO · CUSTOM HERO master board (1080×1920, studio reel frame).
Two columns — 1 REALISTIC | 2 ANIMATION · STICKMAN — four rows (hero · expressions · full-body turnaround · poses).
Every panel is a DOWN-scaled copy of an approved PNG master (nothing regenerated, no crops inside a panel).
usage: python3 compose_master_board.py board.json
board = {"out": "...png", "title": "...", "sub": "...", "cols": [{"head": "...", "detail": "...",
          "panels": [{"img": "...png", "tag": "...", "src": "...", "labels": "..."}, ×4]}, ×2], "foot": "..."}"""
import sys, json, hashlib, datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter

spec = json.load(open(sys.argv[1]))
FONT = '/home/user/fonts/Montserrat-VF.ttf'
W, H = 1080, 1920
ML, CG, CW = 30, 20, 500                     # left margin, column gap, column width  (30+500+20+500+30 = 1080)
AMBER, TEAL = (255, 196, 92), (96, 214, 214)
CAP, ROWGAP, TOP = 34, 10, 200               # caption block under each panel, gap between rows, first panel y

img = Image.new('RGB', (W, H), (16, 18, 20))
vig = Image.new('L', (W, H), 0); ImageDraw.Draw(vig).ellipse([-W * 0.2, -H * 0.3, W * 1.2, H * 1.3], fill=255)
img = Image.composite(Image.new('RGB', (W, H), (26, 29, 33)), img, vig.filter(ImageFilter.GaussianBlur(220)))
d = ImageDraw.Draw(img)

def font(sz, w=600):
    f = ImageFont.truetype(FONT, sz)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
def fit(s, sz, maxw, w=500, lo=10):
    while sz > lo and d.textlength(s, font=font(sz, w)) > maxw: sz -= 1
    return sz
def text(xy, s, sz, fill=(236, 236, 236), w=600, anchor='la', maxw=None):
    if maxw: sz = fit(s, sz, maxw, w)
    d.text(xy, s, font=font(sz, w), fill=fill, anchor=anchor)
def frame(x, y, im):
    img.paste(im, (x, y)); d.rectangle([x, y, x + im.width - 1, y + im.height - 1], outline=(70, 74, 80), width=2)

# header
text((ML, 34), 'MONARCH STUDIO', 20, TEAL, 700)
text((ML, 60), spec['title'], 38, (245, 245, 245), 800, maxw=W - 2 * ML)
text((ML, 110), spec['sub'], 16, (170, 176, 184), 500, maxw=W - 2 * ML)
d.line([(ML, 140), (W - ML, 140)], fill=(60, 64, 70), width=2)

cols = spec['cols']; assert len(cols) == 2
xs = [ML, ML + CW + CG]
for ci, c in enumerate(cols):
    x = xs[ci]
    text((x, 152), c['head'], 22, AMBER if ci else (245, 245, 245), 800, maxw=CW)
    text((x, 181), c['detail'], 14, (170, 176, 184), 500, maxw=CW)
# vertical divider between the columns
d.line([(ML + CW + CG // 2, 150), (ML + CW + CG // 2, H - 40)], fill=(50, 54, 60), width=1)

# panels: both columns share row heights (same master sizes in both styles)
n_rows = len(cols[0]['panels'])
y = TOP
ims = [[Image.open(p['img']).convert('RGB') for p in c['panels']] for c in cols]
for r in range(n_rows):
    row_h = 0
    for ci in range(2):
        im = ims[ci][r]
        if im.width != CW:
            im = im.resize((CW, round(im.height * CW / im.width)), Image.LANCZOS)   # down-scale only (masters are ≥ 896 wide)
        ims[ci][r] = im; row_h = max(row_h, im.height)
    for ci in range(2):
        im, p = ims[ci][r], cols[ci]['panels'][r]
        x = xs[ci]
        frame(x, y, im)
        cy = y + im.height + 7
        text((x, cy), p['tag'], 14, AMBER, 700)
        if p.get('src'): text((x + CW, cy + 1), p['src'], 12, (140, 146, 154), 500, 'ra', maxw=CW - d.textlength(p['tag'], font=font(14, 700)) - 16)
        text((x, cy + 19), p['labels'], 12, (200, 204, 210), 500, maxw=CW)
    y += row_h + CAP + ROWGAP

y -= ROWGAP
assert y <= H - 36, f'layout overflow: content ends at {y} > {H - 36}'
text((W - ML, H - 22), f"{datetime.date.today().isoformat()}  ·  MONARCH STUDIO  ·  {spec.get('foot', '')}", 13, (120, 126, 134), 500, 'ra', maxw=W - 2 * ML)

out = spec['out']; img.save(out, optimize=True); img.save(out[:-4] + '.jpg', quality=92)
print(json.dumps(dict(out=out, size=img.size, content_end=y, md5=hashlib.md5(open(out, 'rb').read()).hexdigest())))
