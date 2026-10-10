#!/usr/bin/env python3
"""MONARCH STUDIO · CUSTOM HERO character bible (multi-page PDF) built from the delivered sheets + master board.
Sheets are paginated 1:1 (no resampling) by cutting ONLY inside detected gap rows (rows without any panel outline,
text or figure edge), so no panel or label is ever split. usage: python3 make_bible_pdf.py bible.json"""
import sys, json, hashlib, datetime
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

spec = json.load(open(sys.argv[1]))
FONT = '/home/user/fonts/Montserrat-VF.ttf'
PW, PH = 1520, 2200            # portrait page (1520-wide sheets at 1:1)
HEAD, FOOT, M = 64, 44, 72
AMBER, TEAL = (255, 196, 92), (96, 214, 214)
TODAY = datetime.date.today().isoformat()

def font(sz, w=600):
    f = ImageFont.truetype(FONT, sz)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
def page_bg(w, h):
    img = Image.new('RGB', (w, h), (16, 18, 20))
    vig = Image.new('L', (w, h), 0); ImageDraw.Draw(vig).ellipse([-w * 0.2, -h * 0.3, w * 1.2, h * 1.3], fill=255)
    return Image.composite(Image.new('RGB', (w, h), (26, 29, 33)), img, vig.filter(ImageFilter.GaussianBlur(220)))
def fit(d, s, sz, maxw, w=500, lo=10):
    while sz > lo and d.textlength(s, font=font(sz, w)) > maxw: sz -= 1
    return sz
def chrome(img, title, right, foot):
    d = ImageDraw.Draw(img); w, h = img.size
    d.text((M, 22), 'MONARCH STUDIO  ·  CUSTOM HERO  ·  CHARACTER BIBLE', font=font(16, 700), fill=TEAL)
    d.text((M, 42), title, font=font(fit(d, title, 15, w - 2 * M - 260), 500), fill=(170, 176, 184))
    d.text((w - M, 30), right, font=font(16, 700), fill=(200, 204, 210), anchor='ra')
    d.line([(M, HEAD - 6), (w - M, HEAD - 6)], fill=(60, 64, 70), width=1)
    d.text((w - M, h - 24), foot, font=font(fit(d, foot, 13, w - 2 * M), 500), fill=(120, 126, 134), anchor='ra')

def gap_runs(im, min_run):
    """rows whose max horizontal step (on a 2-px box-blurred grey) is below the JPEG/vignette noise → page background only"""
    g = np.asarray(im.convert('L').filter(ImageFilter.BoxBlur(1)), dtype=np.int16)
    step = np.abs(np.diff(g, axis=1)).max(axis=1)
    gap = step < 8
    runs, y = [], 0
    while y < len(gap):
        if gap[y]:
            y0 = y
            while y < len(gap) and gap[y]: y += 1
            if y - y0 >= min_run: runs.append((y0, y))
        else: y += 1
    return runs

def paginate(im, max_h, min_run=24):
    """balanced: the smallest page count k whose cuts (each the gap run nearest to the ideal k-split, never > max_h) fit"""
    runs = gap_runs(im, min_run)
    cuts = [(a + b) // 2 for a, b in runs if a > 0 and b < im.height]
    T = im.height
    for k in range(max(1, -(-T // max_h)), len(cuts) + 2):
        segs, y0, ok_all = [], 0, True
        for i in range(k - 1):
            ideal = y0 + (T - y0) / (k - i)
            ok = [c for c in cuts if y0 + 40 < c <= y0 + max_h]
            if not ok: ok_all = False; break
            c = min(ok, key=lambda c: abs(c - ideal)); segs.append((y0, c)); y0 = c
        if ok_all and T - y0 <= max_h:
            segs.append((y0, T)); return segs, runs
    raise AssertionError('no gap-row pagination fits')

pages = []
# 1 · cover = master board centred on a portrait page
board = Image.open(spec['board']).convert('RGB')
cover = page_bg(PW, PH); s = min((PH - HEAD - FOOT - 24) / board.height, (PW - 2 * M) / board.width)
b = board.resize((round(board.width * s), round(board.height * s)), Image.LANCZOS)
cover.paste(b, ((PW - b.width) // 2, HEAD + 12))
chrome(cover, spec['cover_title'], 'v1  ·  ' + TODAY, spec['foot'])
pages.append(cover)

# 3… · the sheets, paginated 1:1 (built first so the index can list real page numbers)
sheet_pages, toc = [], []
pno = 3
for sh in spec['sheets']:
    im = Image.open(sh['img']).convert('RGB')
    pw = max(PW, im.width); ph = PH if im.width <= PW else im.height + HEAD + FOOT + 24
    segs, runs = paginate(im, ph - HEAD - FOOT - 24)
    first = pno
    for i, (a, b) in enumerate(segs):
        pg = page_bg(pw, ph)
        seg = im.crop((0, a, im.width, b))
        pg.paste(seg, ((pw - im.width) // 2, HEAD + 12))
        chrome(pg, f"{sh['title']}  ·  part {i + 1}/{len(segs)}  ·  rows {a}–{b} of {im.height} px (1:1)", f'page {pno}', spec['foot'] + f"  ·  {sh['drive']}")
        sheet_pages.append(pg); pno += 1
    toc.append(dict(title=sh['title'], pages=f'{first}–{pno - 1}' if pno - 1 > first else str(first), segs=segs, gap_runs=len(runs), size=im.size))
    print(json.dumps(dict(sheet=sh['title'], size=im.size, segs=segs, gap_runs=len(runs))))

# 2 · index / identity page (contents with real page numbers + text blocks + palette swatches)
idx = page_bg(PW, PH); d = ImageDraw.Draw(idx)
y = HEAD + 30
d.text((M, y), spec['index_title'], font=font(44, 800), fill=(245, 245, 245)); y += 78
contents = ['page 1  ·  MASTER BOARD — one face, two styles (hero · expressions · full-body turnaround · poses)',
            'page 2  ·  this index — identity lock · wardrobe · measured proportions · palette · Drive ids']
for t, sh in zip(toc, spec['sheets']):
    contents.append(f"page{'s' if '–' in t['pages'] else ''} {t['pages']}  ·  {sh['title']} — {sh.get('desc', '')}")
blocks = [dict(h='CONTENTS', lines=contents)] + spec['index']
LINE, HSZ, TSZ = 36, 25, 21
for block in blocks:
    d.text((M, y), block['h'], font=font(HSZ, 700), fill=AMBER); y += HSZ + 18
    for line in block['lines']:
        if isinstance(line, list):                       # palette swatches: [name, hex] pairs on one row
            x = M + 24
            for name, hx in line:
                d.rounded_rectangle([x, y, x + 56, y + 56], radius=8, fill=tuple(int(hx[i:i + 2], 16) for i in (1, 3, 5)), outline=(90, 94, 100))
                d.text((x + 68, y + 6), name, font=font(18, 700), fill=(220, 224, 230))
                d.text((x + 68, y + 31), hx, font=font(17, 500), fill=(150, 156, 164))
                x += 56 + 68 + max(110, int(d.textlength(name, font=font(18, 700))) + 30)
            y += 76
        else:                                            # wrap at ' · ' first, shrink only a part that still does not fit
            maxw = PW - 2 * M - 24; out_lines, cur = [], ''
            for part in line.split(' · '):
                cand = part if not cur else cur + ' · ' + part
                if d.textlength(cand, font=font(TSZ, 500)) <= maxw: cur = cand
                else:
                    if cur: out_lines.append(cur)
                    cur = part
            if cur: out_lines.append(cur)
            for i, ln in enumerate(out_lines):
                sz = fit(d, ln, TSZ, maxw, 500)
                d.text((M + 24 + (28 if i else 0), y), ln, font=font(sz, 500), fill=(200, 204, 210)); y += LINE
    y += 22
assert y < PH - FOOT, f'index overflow {y}'
chrome(idx, 'index · identity lock · palette · proportions · Drive ids', 'page 2', spec['foot'])
pages.append(idx)
pages.extend(sheet_pages)

out = spec['out']
pages[0].save(out, save_all=True, append_images=pages[1:], resolution=150.0, quality=spec.get('quality', 86))
# thumbnails for QA
th = [p.resize((p.width * 300 // p.height if p.height >= p.width else 300, 300 if p.height >= p.width else p.height * 300 // p.width), Image.LANCZOS) for p in pages]
cols = 6; rows = (len(th) + cols - 1) // cols
sheet = Image.new('RGB', (cols * 320, rows * 320), (40, 40, 44))
for i, t in enumerate(th): sheet.paste(t, ((i % cols) * 320 + 10, (i // cols) * 320 + 10))
sheet.save(out[:-4] + '_thumbs.jpg', quality=80)
print(json.dumps(dict(out=out, pages=len(pages), toc=toc, md5=hashlib.md5(open(out, 'rb').read()).hexdigest())))
