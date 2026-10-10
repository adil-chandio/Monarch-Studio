"""
sheet_shade.py — SHADE character sheet v1 (approval artefact)
Rows: turnaround · poses · expressions · Scene-1 frame in the hybrid look + notes.
"""
import math, sys, time
sys.path.insert(0, '/home/user/src')
from PIL import Image, ImageDraw
import shade as S, toon as T, hybrid as HY
import power as PW
from clean import (W, H, PAPER, PAPER_D, SOFT, INK, ACC, F, cl, fbox, tickmark, payoff, phys, shadow, GY)

t0 = time.time()
SW, SH = 2160, 3140
im = Image.new('RGBA', (SW, SH), PAPER + (255,))
d = ImageDraw.Draw(im, 'RGBA')


def band(y0, y1, yl, yr):
    d.polygon([(0, y0), (SW, y0), (SW, y0 + yr), (0, y0 + yl)], fill=HY.DARK + (255,))
    d.line([(0, y0 + yl), (SW, y0 + yr)], fill=ACC[0] + (235,), width=4)


def label(x, y, txt, col=SOFT, sz=26, wt=600, anchor='mm'):
    d.text((x, y), txt, font=F(sz, wt), fill=col, anchor=anchor)


# ── title
d.rectangle([0, 0, SW, 150], fill=HY.DARK)
d.text((64, 58), 'SHADE', font=F(64, 800), fill=HY.PAPER_ON_DARK, anchor='lm')
d.text((300, 56), 'character sheet v1  ·  built on the toon.py 3D rig  ·  Monarch Stickman Animation',
       font=F(28, 600), fill=(168, 164, 158), anchor='lm')
d.text((64, 114), 'hooded black suit · void face · glowing wedge eyes + crescent smirk · rim-lit for black cloth · diagonal-split DNA',
       font=F(24, 500), fill=(168, 164, 158), anchor='lm')

# ── row A: turnaround (yaw sweep) on the split
yA0, yA1 = 170, 930
band(yA0, yA1, 520, 250)
label(64, yA0 + 36, 'A  TURNAROUND  (same pose, yaw −70 … +90; head follows)', (168, 164, 158), 28, 700, 'lm')
yaws = [-70, -35, 0, 35, 70, 90]
for i, yw in enumerate(yaws):
    x = 200 + i * 350
    pose = dict(phys(S.p_pocket, 2.0))
    pose.update(yaw=yw, head_t=0, head=1.5, lean=-1.0)
    S.shade(d, x, yA0 + 700, 600, pose, 'sly', blink=0.0)
    label(x, yA0 + 735, f'yaw {yw:+d}°')

# ── row B: poses
yB0 = 960
label(64, yB0 + 24, 'B  POSES  (every pose generator of the engine drives this body unchanged)', SOFT, 28, 700, 'lm')
poses = [('pocket (reference)', phys(S.p_pocket, 1.3), 'sly'),
         ('power stance', phys(PW.p_power, 1.3), 'proud'),
         ('arms crossed', phys(S.p_arms_cross, 1.3), 'determined'),
         ('walk', phys(T.p_walk, 0.9), 'focus'),
         ('squat', phys(PW.p_squat, 1.0, q=.85), 'focus'),
         ('double-biceps flex', phys(PW.p_flex, 1.0), 'grin'),
         ('reading', phys(PW.p_read, 1.0), 'think'),
         ('calm breathing', phys(PW.p_calm, 1.0), 'calm')]
for i, (nm, pose, ex) in enumerate(poses):
    x = 150 + i * 266
    gy = yB0 + 640
    shadow(d, x, gy + 8, 520 * .165, 66, 0)
    S.shade(d, x, gy, 520, pose, ex, blink=0.0)
    label(x, gy + 36, nm, SOFT, 24)

# ── row C: expressions (busts)
yC0 = 1690
label(64, yC0 + 24, 'C  EXPRESSIONS  — carried only by the eyes and the mouth (the face is a void)', SOFT, 28, 700, 'lm')
d.rectangle([0, yC0 + 60, SW, yC0 + 470], fill=HY.DARK)
ex = [('sly (default)', 'sly'), ('grin', 'grin'), ('determined', 'determined'), ('angry', 'angry'),
      ('shock', 'shock'), ('calm (eyes shut)', 'calm'), ('worried', 'worried'), ('talk', 'talk')]
for i, (nm, e) in enumerate(ex):
    x = 150 + i * 266
    S.head_only(im, x, yC0 + 240, 92, e, yaw=0)
    label(x, yC0 + 440, nm, (168, 164, 158), 24)

# ── row D: Scene-1 frame in the hybrid look + notes
yD0 = 2190
label(64, yD0 + 24, 'D  SCENE 1 "HOOK" IN THE HYBRID LOOK  (paper/ink engine + diagonal DNA)  ·  right: palette + lighting notes', SOFT, 28, 700, 'lm')
fr = HY.backdrop(1.9, 0, ACC[0])
fd = ImageDraw.Draw(fr, 'RGBA')
HY.chrome(fd, 1.9, 0, ACC[0], 42.0, PW.CHAPTER)
HY.headline(fd, ['POWERFUL'], W / 2, 318, 124, {0}, 0, 1.0, 46)
HY.headline(fd, ['BANNA', 'HAI?'], W / 2, 436, 96, None, 0, 1.0, 42)
pose = dict(phys(S.p_pocket, 4.9))
shadow(fd, W / 2, GY + 8, 600 * .165, 66, 0)
shadow(fd, W / 2, GY + 5, 600 * .070, 104, 0)
S.shade(fd, W / 2, GY, 600, pose, 'sly', look=(.6, .1))
for i in range(4):
    cx, cy = 740 + i * 92, 940
    fbox(fd, cx - 36, cy - 36, cx + 36, cy + 36, 10, PAPER, 6)
    tickmark(fd, cx, cy, 20, ACC[0], 1.0, 9)
fd.line([(300, GY), (W - 300, GY)], fill=(214, 206, 190), width=4)
payoff(fd, ['4', 'AADATEIN'], 1.0, ACC[0], {0})
PW.caption_fit(fd, 'Yeh chaar aadatein pakdo'.split(), .5, ACC[0], {1, 2})
# safe-area + split guides
fd.line([(0, 180), (W, 180)], fill=(255, 0, 0, 90), width=2)
fd.line([(0, 1500), (W, 1500)], fill=(255, 0, 0, 90), width=2)
sc = 0.44
frs = fr.resize((int(W * sc), int(H * sc)), Image.LANCZOS)
im.alpha_composite(frs, (64, yD0 + 60))
d.rectangle([64, yD0 + 60, 64 + frs.width, yD0 + 60 + frs.height], outline=INK, width=3)
label(64 + frs.width / 2, yD0 + 60 + frs.height + 26, '1080×1920 frame, 44 % · red lines = safe area 180–1500', SOFT, 22)

# notes
nx = 64 + frs.width + 70
ny = yD0 + 70
swatches = [('VOID', S.VOID), ('TURTLE', S.TURTLE), ('GLOVE', S.GLOVE), ('TROUSER', S.TROUSER),
            ('JACKET', S.JACKET), ('LAPEL', S.LAPEL), ('HOOD', S.HOOD), ('HOOD_HI', S.HOOD_HI),
            ('OUTL', S.OUTL), ('GLOW', S.GLOW), ('GLOW_T', S.GLOW_T), ('DARK (bg)', HY.DARK)]
label(nx, ny, 'PALETTE — six near-black garment steps (10–18 levels apart) + glow', INK, 26, 700, 'lm')
for i, (nm, col) in enumerate(swatches):
    sx = nx + (i % 6) * 220
    sy = ny + 40 + (i // 6) * 110
    d.rounded_rectangle([sx, sy, sx + 190, sy + 56], 10, fill=col, outline=INK, width=2)
    label(sx + 95, sy + 78, f'{nm} {col}', SOFT, 18)
ny2 = ny + 290
notes = [
    'LIGHTING FOR BLACK CLOTH (toon.py darkens a white body — useless on black):',
    '  key rim upper-left (222,226,236 · 70 %) · fill rim lower-right (122,128,142 · 34 %)',
    '  form lift on the lit side (30 %) · AO pools at neck/shoulders/hips/joints (42 %)',
    '  knit crackle on the hood only · satin sheen on the lapels · gloss line on the shoes',
    '  the eye-glow leaks onto the hood interior (cool tint, so paper never looks "lit")',
    'FACE: wedge eyes — outer end thick & high, inner tip low (the reference angle);',
    '  thin crescent smirk with the hook; 15 expressions via eye shape/openness/tilt + mouth',
    'RIG: toon.py _skeleton() with SHADE proportions (head 1/5.2, shoulders .122, arms .342):',
    '  every existing pose (walk, squat, flex, read, calm, flinch, power…) works unchanged;',
    '  new: pocket (reference stance), pocket_both, arms_cross; hand style "pocket" hides the hand',
    'HYBRID LOOK: charcoal wedge over chrome + headline (paper type, hot word ≥ 4.8:1 measured),',
    '  diagonal drifts ±28/±22 px, accent seam with glow; props / payoff / caption stay ink-on-paper',
]
for i, ln in enumerate(notes):
    label(nx, ny2 + i * 36, ln, INK if ln and ln[0] != ' ' else SOFT, 23, 700 if ln and ln[0] != ' ' else 500, 'lm')
label(nx, ny2 + len(notes) * 36 + 20, 'Open for approval: name ("SHADE"?), eye size, hood crackle amount, shoulder width, hybrid split.', ACC[0], 23, 700, 'lm')

im.convert('RGB').save('/home/user/shade_character_sheet.png', optimize=True)
fr.convert('RGB').save('/home/user/shade_scene1_preview.png')
print('sheet ok  %.1fs' % (time.time() - t0))
