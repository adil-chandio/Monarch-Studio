#!/usr/bin/env python3
"""MONARCH STUDIO · measured proportion + palette panel for a full-body turnaround strip.
usage: python3 measure_proportions.py <fullbody_turn.png> <hero_bust.png> <out_panel.png> [out.json]
Measures (pixels, nothing eyeballed) on the FRONT view: hair top (first Canny edge row in the head
column band), chin (bottom of the Haar frontal-face box), shoulder width (widest occupied row in the
shoulder zone), glove and sneaker extents (bright low-saturation blobs), crotch (first row where the
centre column is empty between two occupied legs), floor (last sneaker row).  Palette = median colours
sampled from fixed anatomical regions.  Draws a 1376x768 panel: front + side views with head-unit lines,
a measurement table and hex swatches.  Also writes a debug overlay next to the panel (_debug.png)."""
import sys, json, hashlib
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import median_filter, uniform_filter1d

src, hero_p, out = sys.argv[1], sys.argv[2], sys.argv[3]
out_json = sys.argv[4] if len(sys.argv) > 4 else out[:-4] + '.json'
FONT = '/home/user/fonts/Montserrat-VF.ttf'
AMBER, TEAL = (255, 196, 92), (96, 214, 214)
casc = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

strip = Image.open(src).convert('RGB'); W, H = strip.size; vw = W // 4
views = {n: strip.crop((i * vw, 0, (i + 1) * vw, H)) for i, n in enumerate(['front', 'threeq', 'side', 'back'])}

def analyse(view):
    a = np.asarray(view).astype(np.float32); h, w = a.shape[:2]
    gray = cv2.cvtColor(a.astype(np.uint8), cv2.COLOR_RGB2GRAY)
    bright = a.mean(-1); sat = a.max(-1) - a.min(-1)
    # occupancy vs. a left/right-edge background model (valid away from the head halo)
    bgL = np.median(a[:, 2:20], axis=1); bgR = np.median(a[:, -20:-2], axis=1)
    t = np.linspace(0, 1, w)[None, :, None]; bg = bgL[:, None, :] * (1 - t) + bgR[:, None, :] * t
    occ = median_filter(np.sqrt(((a - bg) ** 2).sum(-1)) > 20, size=(5, 5))
    cnt = uniform_filter1d(occ.sum(1).astype(float), 9)
    faces = casc.detectMultiScale(gray, 1.05, 3, minSize=(40, 40))
    face = max(faces, key=lambda f: f[2]) if len(faces) else None
    cx = int(face[0] + face[2] / 2) if face is not None else w // 2
    # hair top: first edge row inside the head column band
    e = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 12, 30)
    rows = np.where(e[:, max(0, cx - 30):cx + 30].sum(1) > 0)[0]; rows = rows[rows > 4]
    top = int(rows[0])
    # floor: last row with sneaker-bright pixels in the central 60 %
    sn = (bright[:, int(w * 0.2):int(w * 0.8)] > 150).sum(1); floor = int(np.max(np.where(sn > 3)[0]))
    res = dict(top=top, floor=floor, cx=cx, face=[int(v) for v in face] if face is not None else None)
    if face is not None:
        fx, fy, fw, fh = face; chin = int(fy + fh); res['chin'] = chin
        head_h = chin - top; res['head_h'] = head_h
        # head width: widest occupied row between brow line and chin
        res['head_w'] = float(cnt[fy:chin].max())
        # shoulders: widest row in the zone chin+0.1 .. chin+0.6 head heights, measured on the suit
        z0, z1 = chin + int(0.08 * head_h), chin + int(0.4 * head_h)
        ext = np.zeros(h)
        for yy in range(z0, z1):
            xs = np.where(occ[yy, max(0, cx - 130):cx + 130])[0]
            if len(xs) > 10: ext[yy] = xs[-1] - xs[0]
        ext = uniform_filter1d(ext, 5)
        # shoulder line = knee of the extent curve: first row (after the collar widening) where the
        # silhouette stops growing faster than 0.6 px/row for 6 consecutive rows (below it only the arms angle out)
        grow = np.diff(ext); srow = z1 - 1
        for yy in range(z0 + 4, z1 - 6):
            if ext[yy] > 0.6 * ext[z0:z1].max() and (grow[yy:yy + 6] < 1.0).all(): srow = yy; break
        res['shoulder_row'] = int(srow); res['shoulder_w'] = float(ext[srow])
        # dark occupancy for the near-black trousers (darker than the backdrop)
        bgb = bg.mean(-1); occ2 = occ | median_filter(bright < bgb - 4, size=(5, 5))
        # gloves: bright, low-saturation blobs between 1.5 and 3 head heights
        g0, g1 = top + int(1.5 * head_h), min(h - 1, top + int(3.2 * head_h))
        glove = (bright > 150) & (sat < 40); gr = np.where(glove[g0:g1].sum(1) > 4)[0]
        if len(gr):
            # keep only the FIRST contiguous bright run (the gloves); sneakers lower down are a separate run
            brk = np.where(np.diff(gr) > 12)[0]
            last = gr[brk[0]] if len(brk) else gr[-1]
            res['glove_top'], res['glove_bot'] = int(g0 + gr[0]), int(g0 + last)
        # crotch: first row below the hands where the centre column is empty but both sides occupied
        # crotch = first row where the near-black trousers split into two dark runs (left leg | gap | right leg)
        # and stay split for 6 consecutive rows (trousers are darker than the backdrop; shirt/blazer are lighter)
        dark = median_filter(bright < bgb - 4, size=(5, 5))
        def runs(row, m=6):
            r, st = [], None
            for i, v in enumerate(list(row) + [False]):
                if v and st is None: st = i
                if not v and st is not None:
                    if i - st >= m: r.append((st, i))
                    st = None
            return r
        for y in range(res.get('glove_top', g0) - 20, floor - 40):
            if all(len(runs(dark[yy, cx - 70:cx + 70])) == 2 for yy in range(y, y + 6)):
                res['crotch'] = y; break
        # sneaker top: first sneaker-bright row in the bottom zone
        s0 = floor - int(0.6 * head_h); sr = np.where(sn[s0:floor + 1] > 3)[0]; res['sneaker_top'] = int(s0 + sr[0])
        res['total_h'] = floor - top; res['heads_tall'] = round(res['total_h'] / head_h, 2)
    return res, occ

M = {n: analyse(v) for n, v in views.items()}
front = M['front'][0]; side = M['side'][0]
assert front['face'] is not None, 'no frontal face found'
hh = front['head_h']; top = front['top']; floor = front['floor']

# ---------- palette (median colours from fixed anatomical regions) ----------
hero = Image.open(hero_p).convert('RGB'); ha = np.asarray(hero).astype(np.float32)
hf = casc.detectMultiScale(cv2.cvtColor(ha.astype(np.uint8), cv2.COLOR_RGB2GRAY), 1.05, 3, minSize=(120, 120))
hf = max(hf, key=lambda f: f[2]); fx, fy, fw, fh = [int(v) for v in hf]
def med(arr): return tuple(int(round(v)) for v in np.median(arr.reshape(-1, 3), axis=0))
def hexc(c): return '#%02X%02X%02X' % c
fa = np.asarray(views['front']).astype(np.float32); cx = front['cx']
pal = {}
pal['SKIN'] = med(ha[fy + int(fh * .50):fy + int(fh * .66), fx + int(fw * .18):fx + int(fw * .34)])
pal['HAIR'] = med(ha[max(0, fy - int(fh * .38)):fy - int(fh * .12), fx + int(fw * .30):fx + int(fw * .70)])
sr = front['shoulder_row']
pal['BLAZER'] = med(fa[sr + 20:sr + 60, cx - 40:cx - 24])
pal['SHIRT'] = med(fa[sr + 20:sr + 60, cx - 5:cx + 6])
cr = front.get('crotch', floor - 200); legrow = fa[cr + 40:cr + 80]
legocc = M['front'][1][cr + 40:cr + 80]; lc = np.where(legocc[:, :cx].sum(0) > 20)[0]
pal['TROUSERS'] = med(legrow[:, lc[len(lc) // 2] - 3:lc[len(lc) // 2] + 4]) if len(lc) else med(legrow[:, cx - 30:cx - 20])
bright = fa.mean(-1); sat = fa.max(-1) - fa.min(-1)
gz = fa[front['glove_top']:front['glove_bot'] + 1]; gm = (gz.mean(-1) > 150) & ((gz.max(-1) - gz.min(-1)) < 40)
def lit(px):  # lit albedo of white items: median of the brightest 15 %
    b = px.mean(-1); return med(px[b >= np.percentile(b, 85)])
pal['GLOVE'] = lit(gz[gm])
sz = fa[front['sneaker_top']:floor + 1]; sm = sz.mean(-1) > 150; pal['SNEAKER'] = lit(sz[sm])
pal['BACKDROP'] = med(fa[int(H * .15):int(H * .4), 2:30])
teal = ha[(ha[..., 2] > ha[..., 0] + 25) & (ha[..., 1] > ha[..., 0] + 20) & (ha.mean(-1) > 60)]
pal['RIM TEAL'] = med(teal) if len(teal) > 50 else TEAL
outside = np.ones(ha.shape[:2], bool); outside[fy:fy + fh, fx:fx + fw] = False
amb = ha[outside & (ha[..., 0] > 120) & (ha[..., 0] - ha[..., 2] > 60) & (ha[..., 1] > ha[..., 2] + 15)]
pal['RIM AMBER'] = med(amb) if len(amb) > 50 else AMBER

# ---------- panel ----------
PW, PH = 1376, 768
img = Image.new('RGB', (PW, PH), (22, 24, 27)); d = ImageDraw.Draw(img)
def font(sz, w=600):
    f = ImageFont.truetype(FONT, sz)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
def text(xy, s, sz, fill=(236, 236, 236), w=600, anchor='la'): d.text(xy, s, font=font(sz, w), fill=fill, anchor=anchor)
x0 = 0
for n in ('front', 'side'):
    img.paste(views[n], (x0, 0))
    ov = Image.new('RGBA', (vw, PH), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for k in range(int(np.floor(front['heads_tall'])) + 1):
        y = top + k * hh
        for xx in range(6, vw - 6, 12): od.line([(xx, y), (xx + 6, y)], fill=TEAL + (190,), width=1)
        od.rounded_rectangle([6, y - 11, 30, y + 11], radius=5, fill=(0, 0, 0, 200)); od.text((11, y - 9), f'{k}', font=font(15, 700), fill=TEAL)
    yf = floor
    for xx in range(6, vw - 6, 12): od.line([(xx, yf), (xx + 6, yf)], fill=AMBER + (210,), width=1)
    od.rounded_rectangle([vw - 64, yf - 24, vw - 6, yf - 4], radius=5, fill=(0, 0, 0, 200)); od.text((vw - 60, yf - 23), 'FLOOR', font=font(13, 700), fill=AMBER)
    img.paste(ov, (x0, 0), ov)
    x0 += vw + 12
tx = x0 + 28
text((tx, 28), 'MEASURED PROPORTIONS', 24, AMBER, 800)
text((tx, 62), f'front view · pixels on the 1376×768 turnaround · head unit = hair top → chin', 15, (160, 166, 174), 500)
rows = [
    ('HEIGHT', f"{front['total_h']} px  =  {front['heads_tall']} heads  (hair top → floor)"),
    ('HEAD', f"{hh} px tall · {int(front['head_w'])} px wide  →  w:h {front['head_w'] / hh:.2f}"),
    ('HEAD : BODY', f"1 : {front['heads_tall'] - 1:.2f}   (head ≈ {100 / front['heads_tall']:.0f} % of height)"),
    ('SHOULDERS', f"{int(front['shoulder_w'])} px  =  {front['shoulder_w'] / hh:.2f} heads wide  ·  {front['shoulder_w'] / front['head_w']:.2f} × head width"),
    ('HANDS HANG TO', f"{(front['glove_bot'] - top) / hh:.2f} heads from top  ·  glove {front['glove_bot'] - front['glove_top']} px tall"),
    ('LEGS', f"crotch at {(front.get('crotch', 0) - top) / hh:.2f} heads  ·  leg {floor - front.get('crotch', 0)} px  =  {(floor - front.get('crotch', 0)) / hh:.2f} heads"),
    ('SNEAKERS', f"{floor - front['sneaker_top']} px tall  =  {(floor - front['sneaker_top']) / hh:.2f} heads"),
    ('SIDE VIEW', f"hair top {side['top']} px · floor {side['floor']} px  →  Δ vs front {abs(side['top'] - top)} / {abs(side['floor'] - floor)} px"),
]
y = 100
for k, v in rows:
    d.rounded_rectangle([tx, y, tx + 150, y + 30], radius=6, fill=(0, 0, 0)); text((tx + 10, y + 6), k, 14, TEAL, 700)
    text((tx + 164, y + 6), v, 16, (226, 228, 232), 500); y += 40
text((tx, y + 18), 'PALETTE  ·  median colours sampled from the renders', 20, AMBER, 800)
y += 56; sw = 100; gap = 14; per = 5
for i, (k, c) in enumerate(pal.items()):
    cxp = tx + (i % per) * (sw + gap); cyp = y + (i // per) * 108
    d.rounded_rectangle([cxp, cyp, cxp + sw, cyp + 52], radius=8, fill=c, outline=(80, 84, 90))
    text((cxp, cyp + 58), k, 13, (210, 214, 220), 700); text((cxp, cyp + 76), hexc(c), 14, (150, 156, 164), 500)
text((PW - 20, PH - 22), 'measured · not eyeballed', 13, (120, 126, 134), 500, 'ra')
img.save(out, optimize=True)

# debug overlay
dbg = strip.copy(); dd = ImageDraw.Draw(dbg)
for i, n in enumerate(['front', 'threeq', 'side', 'back']):
    r = M[n][0]; ox = i * vw
    dd.line([(ox, r['top']), (ox + vw, r['top'])], fill='cyan'); dd.line([(ox, r['floor']), (ox + vw, r['floor'])], fill='lime')
    if r.get('face'):
        x, yy, w, h = r['face']; dd.rectangle([ox + x, yy, ox + x + w, yy + h], outline='red')
        for key, col in [('shoulder_row', 'magenta'), ('glove_top', 'white'), ('glove_bot', 'white'), ('crotch', 'orange'), ('sneaker_top', 'yellow')]:
            if key in r: dd.line([(ox, r[key]), (ox + vw, r[key])], fill=col)
dbg.save(out[:-4] + '_debug.png')
report = dict(front=front, side={k: side[k] for k in ('top', 'floor')}, palette={k: hexc(v) for k, v in pal.items()},
              panel=out, panel_md5=hashlib.md5(open(out, 'rb').read()).hexdigest())
json.dump(report, open(out_json, 'w'), indent=1); print(json.dumps(report, indent=1))
