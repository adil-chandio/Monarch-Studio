"""toonsheet.py — character sheet in the reference layout."""
import sys, math
sys.path.insert(0, '/home/user/src')
from PIL import Image, ImageDraw, ImageFont
import toon as T

BG = (250, 244, 219)
INK = (24, 22, 20)
FD = '/home/user/fonts/'
W, H = 1920, 1270


def f(sz, bold=True):
    try:
        ft = ImageFont.truetype(FD + 'Montserrat-VF.ttf', sz)
        try: ft.set_variation_by_axes([700 if bold else 500])
        except Exception: pass
        return ft
    except Exception:
        return ImageFont.load_default()


def head_only(d, cx, cy, hr, expr, blink=0.0):
    rx, ry = hr * .83, hr
    pts = T._superell(cx, cy, rx, ry, 2.7, 44)
    ow = max(2.0, hr * .085)
    d.line(pts + [pts[0]], fill=T.OUTLINE, width=int(ow * 2), joint='curve')
    d.polygon(pts, fill=T.FACE)
    T._hair(d, cx, cy, rx, ry, 0.0, ow, T.HAIR)
    T._face(d, cx, cy, rx, ry, 0.0, expr, ow, (0, 0), blink, hr * 8)


def build():
    im = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((34, 24), '1-8  FRONT VIEWS', font=f(40), fill=INK)

    fronts = [('neutral', T.p_idle(0.0)), ('happy', T.p_idle(1.3)),
              ('talk', T.p_idle(2.6)), ('shock', T.p_idle(0.7)),
              ('focus', T.p_type(1.0)), ('proud', T.p_idle(4.1)), ('sad', T.p_idle(1.9)),
              ('angry', T.p_idle(3.2))]
    for i, (ex, ps) in enumerate(fronts):
        T.toon(d, 118 + i * 228, 560, 452, ps, ex)

    d.text((34, 606), 'HEAD-ONLY EXPRESSIONS', font=f(40), fill=INK)
    heads = ['happy', 'neutral', 'shock', 'sad', 'angry', 'think', 'grin', 'worried',
             'determined', 'proud', 'focus', 'talk']
    for i, ex in enumerate(heads):
        head_only(d, 110 + i * 148, 760, 62, ex)
        d.text((110 + i * 148, 846), ex.upper(), font=f(19), fill=(96, 88, 78), anchor='ma')

    d.text((34, 892), 'FULL-BODY POSE STUDIES', font=f(40), fill=INK)
    poses = [('walk', T.p_walk(0.30), 'neutral'), ('walk', T.p_walk(0.52), 'neutral'),
             ('think', T.p_think(1.0), 'think'), ('sit type', T.p_sit_type(1.0), 'focus'),
             ('present', T.p_present(0.4), 'proud'), ('point up', T.p_point(.5, up=True), 'happy'),
             ('shake', T.p_shake(0.5), 'happy'), ('hold', T.p_hold(0.0), 'talk'),
             ('cheer', T.p_cheer(0.5), 'grin'), ('dance', T.p_dance(0.8), 'grin'),
             ('shrug', T.p_shrug(0.0), 'worried'), ('sad', T.p_sad(0.5), 'sad')]
    for i, (nm, ps, ex) in enumerate(poses):
        x = 112 + i * 150
        T.toon(d, x, 1198, 196, ps, ex)
        d.text((x, 1214), nm.upper(), font=f(17), fill=(96, 88, 78), anchor='ma')
    im.save('/home/user/toon_character_sheet.png')
    print('wrote toon_character_sheet.png')


if __name__ == '__main__':
    build()
