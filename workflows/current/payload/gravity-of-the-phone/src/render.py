#!/usr/bin/env python3
"""THE GRAVITY OF THE PHONE — WTF-30 #1 · frame renderer (camera, props, hero, FX, type, encode).

  python3 render.py --frame 5.5 --out ../render/test.jpg     # one frame at t = 5.5 s
  python3 render.py --sheet 0.5 1.6 3.0 ...  --out sheet.jpg  # contact sheet
  python3 render.py --range 0 300 --out ../render/seg_a.mp4   # frames [0, 300) to mp4 (silent)
"""
import argparse, math, pathlib, subprocess, sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import scene as S                      # noqa: E402
from scene import (W, H, FPS, DUR, NFRAMES, TL, PAPER, PAPER_D, INK, SOFT, GOLD, AMBER, AMBER_HI, WOOD,
                   ROOM_FLOOR, DESK_TOP, PHONE, LINTEL, clamp, lerp, smooth, seg, ease_in, ease_out, rot_pt)
import shade as SH                     # noqa: E402
import toon as T                       # noqa: E402

FONT_DIR = S.STYLE / "fonts"
_FONTS = {}


def font(size, weight=800, name="Montserrat-VF.ttf"):
    key = (name, int(size), weight)
    if key not in _FONTS:
        f = ImageFont.truetype(str(FONT_DIR / name), int(size))
        if weight and name.startswith("Montserrat"):
            f.set_variation_by_axes([weight])
        _FONTS[key] = f
    return _FONTS[key]


# ── camera ───────────────────────────────────────────────────────────────────
class Cam:
    def __init__(self, cx, cy, z):
        self.cx, self.cy, self.z = cx, cy, z

    def pt(self, x, y):
        return ((x - self.cx) * self.z + W / 2, (y - self.cy) * self.z + H / 2)

    def pts(self, seq):
        return [self.pt(x, y) for x, y in seq]

    def rect(self):
        hw, hh = W / 2 / self.z, H / 2 / self.z
        return (self.cx - hw, self.cy - hh, self.cx + hw, self.cy + hh)


DESK_CAM = (872.0, 1262.0, 2.3)


def handheld(t, amp=2.0):
    return (amp * (math.sin(1.3 * t) + 0.5 * math.sin(2.9 * t + 1.0) + 0.3 * math.sin(6.1 * t + 2.0)),
            amp * (math.sin(1.7 * t + 0.6) + 0.5 * math.sin(3.3 * t + 2.0) + 0.3 * math.sin(5.3 * t)))


def hit_shake(t):
    dx = dy = 0.0
    for t0, A, f in ((TL["land"], 9.0, 17.0), (TL["drop"] + 0.30, 12.0, 15.0), (TL["hot"], 5.0, 20.0), (TL["line1"], 3.0, 20.0)):
        if t0 <= t < t0 + 0.26:
            e = math.exp(-(t - t0) / 0.07)
            dx += A * e * math.sin(2 * math.pi * f * (t - t0) + 0.4)
            dy += A * 0.7 * e * math.cos(2 * math.pi * f * (t - t0))
    return dx, dy


def camera(t):
    pz = 1.0 + 0.014 * S.pump(t)              # the picture breathes with the score's kicks
    if t < TL["cut_s2"] or t >= TL["cut_s6"]:
        return Cam(DESK_CAM[0], DESK_CAM[1], DESK_CAM[2] * pz)
    if t < TL["cut_s3"]:
        u = seg(t, TL["cut_s2"], TL["cut_s3"])
        hx, hy = handheld(t, 1.6)
        return Cam(540 + hx, 1000 + hy, (1.0 + 0.012 * u) * pz)
    if t < TL["cut_s4"]:
        return Cam(540, 1000, 1.0)   # ECU handled separately
    if t < TL["cut_s5"]:
        u = seg(t, TL["cut_s4"], TL["cut_s5"])
        hx, hy = handheld(t, 2.0 + 1.5 * S.field(t))
        sx, sy = hit_shake(t)
        return Cam(540 + 48 * u + hx + sx, 1010 + 30 * u + hy + sy, (1.0 + 0.08 * u) * pz)
    tf = min(t, TL["hot"])
    u = seg(tf, TL["cut_s5"], TL["hot"])
    hx, hy = handheld(t, 1.2)
    sx, sy = hit_shake(t)
    return Cam(760 + hx + sx, 1030 + hy + sy, (1.25 + 0.09 * u) * pz)


def hero_screen_scale(t, cam):
    """Dolly-zoom in S5: the hero keeps a locked screen size while the world breathes."""
    if TL["cut_s5"] <= t < TL["cut_s6"]:
        return S.HERO_S * 1.295
    return S.HERO_S * cam.z


# ── plates ───────────────────────────────────────────────────────────────────
PX0, PY0, PX1, PY1 = -300, -200, 1380, 2120     # world rect covered by the paper plate
PS = 2                                           # plate oversampling


def make_paper():
    rng = np.random.default_rng(20261014)
    pw, ph = (PX1 - PX0) * PS, (PY1 - PY0) * PS
    small = rng.normal(0, 3.6, (ph // 24, pw // 24, 1)).astype(np.float32)
    noise = np.array(Image.fromarray(np.clip(small[..., 0] * 8 + 128, 0, 255).astype(np.uint8)).resize((pw, ph), Image.BICUBIC), np.float32)
    noise = (noise - 128) / 8
    arr = np.empty((ph, pw, 3), np.float32)
    arr[:] = PAPER
    arr += noise[..., None]
    # wall: a touch darker at the very top; floor band: PAPER_D with a slow darkening downward
    yy = (np.arange(ph) / PS + PY0)[:, None, None]
    arr -= np.clip((500 - yy) / 700, 0, 1) * 7
    fl = np.clip((yy - ROOM_FLOOR) / 6, 0, 1)
    arr = arr * (1 - fl) + (np.array(PAPER_D, np.float32) + noise[..., None] - np.clip((yy - ROOM_FLOOR) / 420, 0, 1) * 10) * fl
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    for _ in range(9000):      # speckles
        x, y = rng.integers(0, pw), rng.integers(0, ph)
        g = int(rng.integers(150, 215))
        d.point((x, y), fill=(g, g - 6, g - 14))
    for _ in range(300):       # fibres
        x, y = rng.integers(0, pw), rng.integers(0, ph)
        a = rng.uniform(0, math.pi)
        l = rng.uniform(6, 20)
        d.line([(x, y), (x + l * math.cos(a), y + l * math.sin(a))], fill=(205, 197, 180), width=1)
    return img


PAPER_IMG = make_paper()


def paper_crop(cam):
    x0, y0, x1, y1 = cam.rect()
    box = ((x0 - PX0) * PS, (y0 - PY0) * PS, (x1 - PX0) * PS, (y1 - PY0) * PS)
    return PAPER_IMG.resize((W, H), Image.BILINEAR, box=box, reducing_gap=3.0)


def make_vignette():
    yy, xx = np.mgrid[0:H, 0:W]
    dx = (xx - W / 2) / (W / 2); dy = (yy - H / 2) / (H / 2)
    a = np.clip((dx * dx + dy * dy - .30) * 26, 0, 30).astype(np.uint8)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = (20, 16, 14)
    arr[..., 3] = a
    return Image.fromarray(arr, "RGBA")


VIGNETTE = make_vignette()
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG_K = np.clip((((_xx - W / 2) / (W * 0.62)) ** 2 + ((_yy - H / 2) / (H * 0.60)) ** 2) ** 0.5 - 0.35, 0, 1) ** 1.6
del _yy, _xx
_rng = np.random.default_rng(7)
GRAIN = [(_rng.normal(0, 2.6, (H, W, 1))).astype(np.float32) for _ in range(4)]


def make_glow_tiles():
    n = 900
    yy, xx = np.mgrid[0:n, 0:n] - n / 2
    r = np.sqrt(xx * xx + yy * yy)
    halo = np.exp(-(r / 190.0) ** 1.6) * 255
    disc = Image.fromarray(np.clip(halo, 0, 255).astype(np.uint8), "L")
    # desk-surface pool: a wide ellipse that sits on the desk top (anchor at the bottom-centre of the phone)
    pool = Image.new("L", (n, n), 0)
    ImageDraw.Draw(pool).ellipse([n / 2 - 300, n / 2 - 40, n / 2 + 300, n / 2 + 46], fill=255)
    pool = pool.filter(ImageFilter.GaussianBlur(34))
    return disc, pool


GLOW_DISC, GLOW_POOL = make_glow_tiles()
SPR = S.sprites()


# ── sprite pasting ───────────────────────────────────────────────────────────
def place_tile(tile, anchor, sx, sy, scale, rot_cw=0.0, flip_x=False, scale_x=1.0):
    """Scale/rotate a 2x tile and return (img, paste_xy) so `anchor` lands on screen (sx, sy)."""
    tw, th = tile.size
    nw, nh = max(1, int(round(tw * scale * scale_x))), max(1, int(round(th * scale)))
    img = tile.resize((nw, nh), Image.BILINEAR if scale < 0.9 else Image.BICUBIC)
    ax, ay = anchor[0] * scale * scale_x, anchor[1] * scale
    if flip_x:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
        ax = nw - ax
    if abs(rot_cw) > 0.05:
        cx, cy = nw / 2, nh / 2
        img = img.rotate(-rot_cw, resample=Image.BICUBIC, expand=True)
        vx, vy = rot_pt(ax - cx, ay - cy, rot_cw)
        ax, ay = img.size[0] / 2 + vx, img.size[1] / 2 + vy
    return img, (int(round(sx - ax)), int(round(sy - ay)))


def paste_smear(frame, img, xy, v, strength=1.0):
    """Directional smear: ghost copies trailing the velocity vector (screen px / frame)."""
    speed = math.hypot(*v)
    if speed < 14:
        frame.alpha_composite(img, xy)
        return
    n = 3 if speed < 60 else 4
    for i in range(n, 0, -1):
        f = i / (n + 1)
        g = img.copy()
        a = g.getchannel("A").point(lambda p, k=(0.34 * (1 - f) + 0.06) * strength: int(p * k))
        g.putalpha(a)
        frame.alpha_composite(g, (int(xy[0] - v[0] * f * 0.9), int(xy[1] - v[1] * f * 0.9)))
    frame.alpha_composite(img, xy)


def contact_shadow(frame, cam, x, y, rx, ry, alpha=70):
    sx, sy = cam.pt(x, y)
    rx *= cam.z; ry *= cam.z
    if rx < 2:
        return
    pad = int(rx * 0.4) + 4
    tile = Image.new("RGBA", (int(2 * rx + 2 * pad), int(2 * ry + 2 * pad)), (0, 0, 0, 0))
    ImageDraw.Draw(tile).ellipse([pad, pad, pad + 2 * rx, pad + 2 * ry], fill=INK + (alpha,))
    tile = tile.filter(ImageFilter.GaussianBlur(max(1, rx * 0.12)))
    frame.alpha_composite(tile, (int(sx - rx - pad), int(sy - ry - pad)))


# ── world drawing ────────────────────────────────────────────────────────────
def draw_floor(frame, cam, tau):
    d = ImageDraw.Draw(frame, "RGBA")
    k = S.field_vis(tau)
    x0, y0, x1, y1 = cam.rect()
    cxw, cyw = PHONE[0], ROOM_FLOOR
    lw = max(1, int(round(1.4 * cam.z)))

    def warp(x, y):
        if k <= 0:
            return x, y
        dx, dy = cxw - x, cyw - y
        r = math.hypot(dx, dy) + 1e-6
        m = k * 180 * math.exp(-r / 260) * (1 - math.exp(-r / 40))
        return x + dx / r * m, y + dy / r * m

    if y1 > ROOM_FLOOR:
        for i in range(1, 12):
            yl = ROOM_FLOOR + 44 * i
            if yl > y1 + 60:
                break
            pts = [cam.pt(*warp(x, yl)) for x in np.arange(max(x0, PX0) - 40, min(x1, PX1) + 80, 36)]
            d.line(pts, fill=INK + (20,), width=lw, joint="curve")
        for j in range(-4, 18):
            xl = -300 + 216 * j
            if xl < x0 - 60 or xl > x1 + 60:
                continue
            pts = [cam.pt(*warp(xl, y)) for y in np.arange(ROOM_FLOOR, min(y1, PY1) + 60, 30)]
            d.line(pts, fill=INK + (13,), width=lw, joint="curve")
    # baseboard
    d.line(cam.pts([(PX0, ROOM_FLOOR), (PX1, ROOM_FLOOR)]), fill=INK + (235,), width=max(2, int(5 * cam.z)))
    d.line(cam.pts([(PX0, ROOM_FLOOR + 14), (PX1, ROOM_FLOOR + 14)]), fill=INK + (60,), width=max(1, int(2 * cam.z)))


def draw_door(frame, cam):
    d = ImageDraw.Draw(frame, "RGBA")
    z = cam.z
    # hallway seen through the open door
    d.polygon(cam.pts([(60, 930), (250, 930), (250, ROOM_FLOOR), (60, ROOM_FLOOR)]), fill=(214, 206, 190, 255))
    d.polygon(cam.pts([(60, 930), (250, 930), (250, 1120), (60, 1120)]), fill=(200, 192, 176, 255))
    d.line(cam.pts([(60, 1120), (250, 1120)]), fill=INK + (50,), width=max(1, int(2 * z)))
    d.line(cam.pts([(60, ROOM_FLOOR), (250, ROOM_FLOOR)]), fill=INK + (200,), width=max(1, int(3 * z)))
    # frame (two jambs + lintel), thick ink outline
    for poly in ([(36, 906), (272, 906), (272, 930), (36, 930)],
                 [(36, 906), (60, 906), (60, ROOM_FLOOR), (36, ROOM_FLOOR)],
                 [(250, 906), (272, 906), (272, ROOM_FLOOR), (250, ROOM_FLOOR)]):
        d.polygon(cam.pts(poly), fill=WOOD + (255,), outline=INK + (255,), width=max(2, int(3 * z)))
    d.line(cam.pts([(48, 918), (48, ROOM_FLOOR)]), fill=INK + (70,), width=max(1, int(2 * z)))
    d.line(cam.pts([(261, 918), (261, ROOM_FLOOR)]), fill=INK + (70,), width=max(1, int(2 * z)))


def draw_shelf(frame, cam):
    d = ImageDraw.Draw(frame, "RGBA")
    z = cam.z
    d.polygon(cam.pts([(740, 960), (1030, 960), (1030, 974), (740, 974)]), fill=WOOD + (255,), outline=INK + (255,), width=max(2, int(3 * z)))
    for bx in (770, 1000):
        d.polygon(cam.pts([(bx - 6, 974), (bx + 6, 974), (bx, 1004)]), fill=INK + (255,))
    # the clock's nail
    nx, ny = cam.pt(430, 690)
    d.ellipse([nx - 3 * z, ny - 3 * z, nx + 3 * z, ny + 3 * z], fill=INK + (255,))


def draw_desk(frame, cam):
    d = ImageDraw.Draw(frame, "RGBA")
    z = cam.z
    ow = max(2, int(3 * z))
    for lx in (704, 1010):
        d.polygon(cam.pts([(lx, DESK_TOP + 12), (lx + 16, DESK_TOP + 12), (lx + 16, ROOM_FLOOR), (lx, ROOM_FLOOR)]),
                  fill=WOOD + (255,), outline=INK + (255,), width=ow)
    d.polygon(cam.pts([(690, DESK_TOP - 12), (1040, DESK_TOP - 12), (1040, DESK_TOP), (690, DESK_TOP)]),
              fill=(238, 232, 218, 255), outline=INK + (255,), width=ow)
    d.polygon(cam.pts([(690, DESK_TOP), (1040, DESK_TOP), (1040, DESK_TOP + 14), (690, DESK_TOP + 14)]),
              fill=WOOD + (255,), outline=INK + (255,), width=ow)
    # drawer line
    d.line(cam.pts([(712, DESK_TOP + 7), (770, DESK_TOP + 7)]), fill=INK + (90,), width=max(1, int(2 * z)))


def draw_rug(frame, cam, tau):
    d = ImageDraw.Draw(frame, "RGBA")
    x0, x1, u = S.rug_state(tau)
    z = cam.z
    poly = [(x0, ROOM_FLOOR - 12), (x1, ROOM_FLOOR - 12), (x1 + 6, ROOM_FLOOR), (x0 - 6, ROOM_FLOOR)]
    d.polygon(cam.pts(poly), fill=(222, 212, 192, 255), outline=INK + (255,), width=max(2, int(3 * z)))
    # pattern bands
    for xb in np.linspace(x0 + 20, x1 - 20, 5):
        d.line(cam.pts([(xb, ROOM_FLOOR - 10), (xb, ROOM_FLOOR - 2)]), fill=INK + (90,), width=max(1, int(2 * z)))
    # folds when bunched
    if u > 0.05:
        for i, fx in enumerate(np.linspace(x1 - 150 * u, x1 - 30, 3)):
            h = 10 + 10 * u + 4 * i
            p1 = cam.pt(fx - 16, ROOM_FLOOR - 12); p2 = cam.pt(fx + 16, ROOM_FLOOR - 12)
            d.chord([p1[0], p1[1] - h * z, p2[0], p2[1] + h * z], 180, 360, fill=(222, 212, 192, 255), outline=INK + (255,), width=max(2, int(3 * z)))
    # fringe
    for xe, sgn in ((x0 - 6, -1), (x1 + 6, 1)):
        for i in range(5):
            yy = ROOM_FLOOR - 11 + i * 2.6
            d.line(cam.pts([(xe, yy), (xe + sgn * 12, yy + 1)]), fill=INK + (150,), width=max(1, int(1.6 * z)))


def draw_lamp(frame, cam, tau):
    d = ImageDraw.Draw(frame, "RGBA")
    z = cam.z
    base, e, h, hang = S.lamp_geometry(tau)
    lw = max(2, int(7 * z))
    bx, by = cam.pt(*base)
    d.ellipse([bx - 28 * z, by - 8 * z, bx + 28 * z, by + 6 * z], fill=(60, 56, 58, 255), outline=INK + (255,), width=max(1, int(2 * z)))
    post = (base[0], DESK_TOP - 46)
    d.line(cam.pts([base, post]), fill=INK + (255,), width=lw)
    d.line(cam.pts([post, e]), fill=INK + (255,), width=lw)
    d.line(cam.pts([e, h]), fill=INK + (255,), width=lw)
    for jx, jy in (post, e):
        px, py = cam.pt(jx, jy)
        d.ellipse([px - 6 * z, py - 6 * z, px + 6 * z, py + 6 * z], fill=INK + (255,))
    # shade: trapezoid along the arm2 direction, tilted further by `hang`
    dx, dy = h[0] - e[0], h[1] - e[1]
    L = math.hypot(dx, dy) + 1e-6
    ux, uy = dx / L, dy / L
    ux, uy = rot_pt(ux, uy, hang)
    px, py = -uy, ux
    shade = [(h[0] - px * 14, h[1] - py * 14), (h[0] + px * 14, h[1] + py * 14),
             (h[0] + ux * 40 + px * 34, h[1] + uy * 40 + py * 34), (h[0] + ux * 40 - px * 34, h[1] + uy * 40 - py * 34)]
    d.polygon(cam.pts(shade), fill=(52, 48, 50, 255), outline=INK + (255,), width=max(2, int(3 * z)))
    d.line(cam.pts([shade[2], shade[3]]), fill=(120, 112, 104, 255), width=max(1, int(2 * z)))


def draw_page(frame, cam, x, y, rot, flat, v=(0, 0)):
    d = ImageDraw.Draw(frame, "RGBA")
    z = cam.z
    hgt = lerp(86, 9, flat)
    skew = 22 * flat
    pts = [(-30, 0), (30, 0), (30 + skew, -hgt), (-30 + skew, -hgt)]
    pts = [rot_pt(px, py, rot) for px, py in pts]
    scr = [cam.pt(x + px, y + py) for px, py in pts]
    d.polygon(scr, fill=(252, 249, 242, 255), outline=INK + (255,), width=max(1, int(2.4 * z)))
    if flat < 0.6:
        for f in (0.3, 0.5, 0.7):
            a = (pts[0][0] * (1 - f) + pts[3][0] * f, pts[0][1] * (1 - f) + pts[3][1] * f)
            b = (pts[1][0] * (1 - f) + pts[2][0] * f, pts[1][1] * (1 - f) + pts[2][1] * f)
            d.line([cam.pt(x + a[0] * 0.8, y + a[1]), cam.pt(x + b[0] * 0.8, y + b[1])], fill=SOFT + (int(120 * (1 - flat)),),
                   width=max(1, int(1.5 * z)))


def draw_pencil(frame, cam, tau):
    d = ImageDraw.Draw(frame, "RGBA")
    z = cam.z
    x = S.pencil_x(tau)
    y = DESK_TOP - 4
    ang = -27.0
    L, wd = 96, 12
    ph = (x / 7.0) % 1.0           # roll phase -> facet shading scrolls
    body = [(-L / 2 + 12, -wd / 2), (L / 2 - 10, -wd / 2), (L / 2 - 10, wd / 2), (-L / 2 + 12, wd / 2)]
    tip = [(-L / 2 + 12, -wd / 2), (-L / 2 - 10, 0), (-L / 2 + 12, wd / 2)]
    lead = [(-L / 2 - 10, 0), (-L / 2 - 4, -2.2), (-L / 2 - 4, 2.2)]
    fer = [(L / 2 - 10, -wd / 2), (L / 2 - 2, -wd / 2), (L / 2 - 2, wd / 2), (L / 2 - 10, wd / 2)]
    era = [(L / 2 - 2, -wd / 2 + 1), (L / 2 + 6, -wd / 2 + 1), (L / 2 + 6, wd / 2 - 1), (L / 2 - 2, wd / 2 - 1)]

    def P(poly):
        return [cam.pt(x + a, y + b) for a, b in (rot_pt(px, py, ang) for px, py in poly)]
    d.polygon(P(body), fill=(236, 190, 70, 255), outline=INK + (255,), width=max(1, int(2 * z)))
    # facets: a light band and a dark band; the light band breathes with the roll phase
    yl = -wd / 2 + 2.5 + 1.5 * math.sin(2 * math.pi * ph)
    d.line(P([(-L / 2 + 14, yl), (L / 2 - 12, yl)]), fill=(250, 214, 110, 255), width=max(1, int(2.2 * z)))
    d.line(P([(-L / 2 + 14, wd / 2 - 3), (L / 2 - 12, wd / 2 - 3)]), fill=(190, 140, 40, 255), width=max(1, int(2.2 * z)))
    d.polygon(P(tip), fill=(232, 220, 196, 255), outline=INK + (255,), width=max(1, int(2 * z)))
    d.polygon(P(lead), fill=INK + (255,))
    d.polygon(P(fer), fill=(150, 150, 150, 255), outline=INK + (255,), width=max(1, int(2 * z)))
    d.polygon(P(era), fill=(214, 160, 150, 255), outline=INK + (255,), width=max(1, int(2 * z)))
    contact_shadow(frame, cam, x, y + 3, 44, 5, 50)


def draw_phone(frame, cam, tau):
    ps = S.phone_state(tau)
    x, y = PHONE
    rot = 0.0
    if ps["buzz"]:
        x += 2.2 * math.sin(2 * math.pi * 25 * tau)
        rot = 1.6 * math.sin(2 * math.pi * 25 * tau + 1.0)
    y -= ps["lift"]
    sx = 1.0
    if ps["p"] > 0:
        sx = max(0.08, abs(math.cos(math.pi * ps["p"])))
    tile, anc = SPR["phone_up" if ps["face"] > 0.5 else "phone_down"]
    contact_shadow(frame, cam, PHONE[0], PHONE[1], 70, 7, 60 if ps["lift"] < 4 else 30)
    img, xy = place_tile(tile, anc, *cam.pt(x, y), cam.z / S.S2, rot_cw=rot, scale_x=sx)
    frame.alpha_composite(img, xy)


def draw_glow(rgb, cam, tau, extra=0.0):
    """Additive amber light from the phone screen (the only colour in the film)."""
    g = S.glow(tau) + extra
    if g <= 0.001:
        return rgb
    z = cam.z
    sx, sy = cam.pt(PHONE[0], PHONE[1] - 30)
    n = int(900 * z * 1.15)
    disc = GLOW_DISC.resize((n, n), Image.BILINEAR)
    pool = GLOW_POOL.resize((n, n), Image.BILINEAR)
    mask = Image.new("L", (W, H), 0)
    mask.paste(disc, (int(sx - n / 2), int(sy - n / 2)))
    m2 = Image.new("L", (W, H), 0)
    m2.paste(pool, (int(sx - n / 2), int(sy + 30 * z - n / 2)))
    m = np.asarray(mask, np.float32) / 255 * 0.95 + np.asarray(m2, np.float32) / 255 * 0.55
    m = np.clip(m, 0, 1.4)[..., None] * g
    arr = np.asarray(rgb, np.float32)
    arr = arr + m * np.array([96, 52, -22], np.float32)
    arr += (m ** 2) * np.array([20, 24, 10], np.float32)
    # v3 — god-rays: the planet's light turns slowly in the dust while the field is on
    k = S.field_vis(tau)
    if k > 0.03 and g > 0.05:
        rays = god_rays(sx, sy, tau, z)[..., None] * (0.30 * min(1.0, k) * min(1.0, g))
        arr += rays * np.array([92, 50, -18], np.float32)
    # v3 — anamorphic streak: a flash when the screen wakes (1.55 s), then a faint pulse on the kicks
    flash = math.exp(-max(0.0, tau - TL["glow_on"] - 0.08) / 0.22) if tau >= TL["glow_on"] + 0.08 else seg(tau, TL["glow_on"], TL["glow_on"] + 0.08)
    streak_k = min(1.0, g) * (0.10 + 0.55 * flash + 0.28 * S.pump(tau))
    if streak_k > 0.03:
        arr += streak(sy - 18 * z, 0.5 * W * (0.6 + 0.4 * min(1.0, g)) * (1 + 0.5 * flash))[..., None] * streak_k * np.array([120, 70, -10], np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


_RAY_CACHE = {}


def god_rays(sx, sy, tau, z, n_rays=14):
    """Soft wedge rays from the phone screen (quarter-res mask, blurred, upscaled); rotate 7°/s, breathe with the grid."""
    q = 4
    small = Image.new("L", (W // q, H // q), 0)
    d = ImageDraw.Draw(small)
    cx, cy = sx / q, sy / q
    Lr = (1.15 * H) / q * z / 2.3 * 1.6
    a0 = 7.0 * tau
    for i in range(n_rays):
        a = math.radians(a0 + i * 360.0 / n_rays + 11 * math.sin(0.7 * tau + i))
        hw = math.radians(2.2 + 1.4 * S.hash01(i, 77))
        bright = 120 + int(100 * S.hash01(i, 78))
        bright = int(bright * (0.75 + 0.25 * math.sin(2 * math.pi * (tau / (2 * S.BEAT)) + i)))
        pts = [(cx, cy), (cx + Lr * math.cos(a - hw), cy + Lr * math.sin(a - hw)), (cx + Lr * math.cos(a + hw), cy + Lr * math.sin(a + hw))]
        d.polygon(pts, fill=bright)
    small = small.filter(ImageFilter.GaussianBlur(5))
    # fade with distance from the screen
    yy, xx = np.mgrid[0:H // q, 0:W // q].astype(np.float32)
    dist = np.hypot(xx - cx, yy - cy) / (Lr + 1e-6)
    fall = np.clip(1.0 - dist, 0, 1) ** 1.3 * np.clip(dist * 9, 0, 1)
    arr = np.asarray(small, np.float32) / 255 * fall
    return np.asarray(Image.fromarray((arr * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32) / 255


def streak(y, half_len):
    """Horizontal anamorphic streak mask centred on the phone row: bright thin core + soft halo, tapered ends."""
    yy = np.arange(H, dtype=np.float32)[:, None] - y
    xx = np.arange(W, dtype=np.float32)[None, :] - W / 2
    core = np.exp(-(yy / 2.2) ** 2) * 1.0 + np.exp(-(yy / 14.0) ** 2) * 0.35
    taper = np.clip(1.0 - (np.abs(xx) / half_len) ** 1.6, 0, 1)
    return core * taper


def draw_pulse_rings(frame, cam, tau):
    """Amber shock-rings leaving the phone: field onset + the three dings (the pull made visible)."""
    d = ImageDraw.Draw(frame, "RGBA")
    z = cam.z
    cx, cy = cam.pt(PHONE[0], PHONE[1] - 28)
    for t0, big in ((TL["field_on"], 1.6), (TL["ding1"], 1.0), (TL["ding2"], 1.0), (TL["ding3"], 1.0)):
        if not (t0 <= tau < t0 + 0.55):
            continue
        u = (tau - t0) / 0.55
        for j in range(2):
            uu = clamp(u - 0.12 * j)
            if uu <= 0:
                continue
            r = (40 + 300 * big * ease_out(uu, 1.6)) * z
            a = int(150 * (1 - uu) ** 1.5 / (1 + j))
            d.ellipse([cx - r, cy - r * 0.42, cx + r, cy + r * 0.42], outline=AMBER + (a,), width=max(2, int((5 - 2 * uu) * z)))


def draw_prop(frame, cam, name, tau):
    x, y, rot, phase, jit, u = S.prop_state(name, tau)
    if jit > 0:
        x += 0.9 * jit * math.sin(2 * math.pi * 23 * tau + S.hash01(name) * 6)
        y += 0.6 * jit * math.sin(2 * math.pi * 29 * tau + S.hash01(name, 2) * 6)
    v = S.prop_vel(name, tau)
    vs = (v[0] * cam.z, v[1] * cam.z)
    if name.startswith("page"):
        flat = {"home": 1.0, "fly": 1 - smooth(u), "pile": 0.0, "fall": smooth(u), "down": 1.0}[phase]
        if phase == "home" and rot != 0:
            flat = 1 - min(0.5, abs(rot) / 14)
        if phase == "fall":
            x += 10 * math.sin(math.pi * u * 3) * (1 - u)
        draw_page(frame, cam, x, y, rot, flat)
        return
    if name == "hbook":
        if phase == "home":
            return  # still in the hero's hand
    tile, anc = SPR[name]
    grounded = phase in ("home", "pile", "down") and not (name == "clock" and phase == "home")
    if grounded and name not in ("chair",) or (name == "chair" and phase in ("home", "down")):
        rx = {"cup": 26, "sbook0": 30, "sbook1": 30, "sbook2": 30, "hbook": 36, "clock": 60, "chair": 70,
              "fbook0": 60, "fbook1": 56, "fbook2": 50, "plant": 40}.get(name, 30)
        if name == "clock" and phase == "down":
            rx = 70
        if phase != "home" or name in ("chair", "plant", "fbook0", "cup"):
            contact_shadow(frame, cam, x, y, rx, 6, 55)
    sx, sy = cam.pt(x, y)
    img, xy = place_tile(tile, anc, sx, sy, cam.z / S.S2, rot_cw=rot)
    if name == "clock":
        # pendulum: hangs from the clock's bottom (rotates with the clock), drawn before the face
        draw_pendulum(frame, cam, x, y, rot, tau)
    if phase in ("fly", "fall"):
        paste_smear(frame, img, xy, vs)
    else:
        frame.alpha_composite(img, xy)


def draw_pendulum(frame, cam, cx, cy, rot, tau):
    d = ImageDraw.Draw(frame, "RGBA")
    z = cam.z
    x, y, _, phase, _, _ = S.prop_state("clock", tau)
    if phase == "home":
        ang = S.pendulum_angle(tau)
    else:
        # points toward the phone while the field is on, else hangs along the clock's own down axis
        k = S.field(tau)
        tox = math.degrees(math.atan2(PHONE[0] - cx, PHONE[1] - cy))
        ang = lerp(rot, tox, k)
    piv = rot_pt(0, 72, rot)
    piv = (cx + piv[0], cy + piv[1])
    L = 96 if phase != "down" else 40
    end = (piv[0] + L * math.sin(math.radians(ang)), piv[1] + L * math.cos(math.radians(ang)))
    d.line([cam.pt(*piv), cam.pt(*end)], fill=INK + (255,), width=max(1, int(4 * z)))
    ex, ey = cam.pt(*end)
    d.ellipse([ex - 13 * z, ey - 13 * z, ex + 13 * z, ey + 13 * z], fill=(238, 232, 218, 255), outline=INK + (255,), width=max(1, int(3 * z)))


def draw_dust(frame, cam, tau):
    d = ImageDraw.Draw(frame, "RGBA")
    z = cam.z
    for i, (t0, x, y, size, strength) in enumerate(S.dust_events()):
        if not (t0 <= tau < t0 + 0.75):
            continue
        u = (tau - t0) / 0.75
        tile_n = int(size * 2.4 * z)
        if tile_n < 8:
            continue
        tile = Image.new("RGBA", (tile_n, tile_n), (0, 0, 0, 0))
        td = ImageDraw.Draw(tile, "RGBA")
        for j in range(6):
            h1, h2 = S.hash01(i, j, 1), S.hash01(i, j, 2)
            ang = math.pi + (h1 - 0.5) * math.pi * 1.1
            dist = size * (0.25 + 0.75 * h2) * ease_out(u, 1.8)
            px = tile_n / 2 + math.cos(ang) * dist * z
            py = tile_n / 2 + math.sin(ang) * dist * z * 0.55
            r = size * (0.12 + 0.22 * ease_out(u, 1.5)) * z * (0.6 + 0.5 * h1)
            a = int(150 * strength * (1 - u) ** 1.4)
            td.ellipse([px - r, py - r, px + r, py + r], fill=SOFT + (a,))
        tile = tile.filter(ImageFilter.GaussianBlur(max(1, size * 0.07 * z)))
        sx, sy = cam.pt(x, y)
        frame.alpha_composite(tile, (int(sx - tile_n / 2), int(sy - tile_n / 2)))


# ── field FX: flow specks, onset speed lines, strain sweat ──────────────────
def draw_flow(frame, cam, tau):
    parts = S.flow_particles(tau)
    if not parts:
        return
    d = ImageDraw.Draw(frame, "RGBA")
    z = cam.z
    for x, y, vx, vy, a in parts:
        sx, sy = cam.pt(x, y)
        spd = math.hypot(vx, vy) * z
        L = clamp(spd * 0.045, 4, 70)
        if spd > 1:
            ux, uy = vx * z / (spd + 1e-9), vy * z / (spd + 1e-9)
            d.line([(sx - ux * L, sy - uy * L), (sx, sy)], fill=SOFT + (int(95 * a),), width=2)
            d.line([(sx - ux * L * 0.45, sy - uy * L * 0.45), (sx, sy)], fill=INK + (int(70 * a),), width=2)
        r = (1.4 + 1.2 * a) * z
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=INK + (int(170 * a),))


def draw_speed_lines(frame, cam, tau):
    """Ink focus lines converging on the phone at the field onset (0.42 s); falling lines at the drop."""
    d = ImageDraw.Draw(frame, "RGBA")
    z = cam.z
    if TL["field_on"] <= tau < TL["field_on"] + 0.42:
        u = (tau - TL["field_on"]) / 0.42
        cx, cy = cam.pt(PHONE[0], PHONE[1] - 24)
        for i in range(34):
            h1, h2, h3 = S.hash01(i, 31), S.hash01(i, 32), S.hash01(i, 33)
            ang = math.pi * (0.5 + 2.0 * h1)
            r_in = (180 + 160 * h2) * z
            r_out = (640 + 760 * h3) * z
            r_out = r_in + (r_out - r_in) * (1 - ease_in(u, 1.4))      # the outer end rushes inward
            if r_out <= r_in + 4:
                continue
            a = int(140 * (1 - u) ** 1.1 * (0.5 + 0.5 * h2))
            w = max(1, int((1.5 + 2.5 * h3) * z * (1 - 0.5 * u)))
            d.line([(cx + math.cos(ang) * r_in, cy + math.sin(ang) * r_in * 0.7),
                    (cx + math.cos(ang) * r_out, cy + math.sin(ang) * r_out * 0.7)], fill=INK + (a,), width=w)
    if TL["drop"] + 0.06 <= tau < TL["drop"] + 0.34:
        u = (tau - TL["drop"] - 0.06) / 0.28
        for i in range(18):
            h1, h2 = S.hash01(i, 41), S.hash01(i, 42)
            x = 120 + 940 * h1
            y0 = 380 + 600 * h2 + 700 * ease_in(u, 1.3)
            L = (60 + 90 * h2) * (1 - u)
            sx, sy = cam.pt(x, y0)
            if sy < ROOM_FLOOR * z:
                d.line([(sx, sy - L * z), (sx, sy)], fill=SOFT + (int(110 * (1 - u)),), width=max(1, int(2 * z)))


def hero_head_world(t):
    """World position of the hero's head centre at time t (follows the flag rotation)."""
    st = S.hero_state(t)
    if st is None:
        return None
    J = S.solve(st["pose"], S.HERO_S, st["flip"])
    if st["pivot"]:
        if st["pivot"] == "hands":
            pv = ((J["hand_l"][0] + J["hand_r"][0]) / 2, (J["hand_l"][1] + J["hand_r"][1]) / 2)
        else:
            pv = J["hip"]
        dx, dy = J["head"][0] - pv[0], J["head"][1] - pv[1]
        th = math.radians(st["rot"])
        return (st["pivot_world"][0] + dx * math.cos(th) + dy * math.sin(th),
                st["pivot_world"][1] - dx * math.sin(th) + dy * math.cos(th))
    return (st["feet"][0] + J["head"][0], st["feet"][1] + J["head"][1])


_HEAD_CACHE = {}


def draw_sweat(frame, cam, tau):
    """Strain drops leave his head and are pulled to the phone (0.5 s flights)."""
    if not (6.9 <= tau < TL["letgo"] + 0.5):
        return
    d = ImageDraw.Draw(frame, "RGBA")
    z = cam.z
    for t0, j in S.sweat_drops(tau):
        if not (t0 <= tau < t0 + 0.5):
            continue
        if t0 not in _HEAD_CACHE:
            _HEAD_CACHE[t0] = hero_head_world(t0)
        hw = _HEAD_CACHE[t0]
        if hw is None:
            continue
        u = (tau - t0) / 0.5
        h1, h2 = S.hash01(j, 51), S.hash01(j, 52)
        x0 = hw[0] + (h1 - 0.5) * 70
        y0 = hw[1] - 30 + (h2 - 0.5) * 60
        f = ease_in(u, 1.9)
        x = lerp(x0, PHONE[0], f)
        y = lerp(y0, PHONE[1] - 20, f) - 40 * math.sin(math.pi * u) * (1 - f)
        sx, sy = cam.pt(x, y)
        r = (6.0 + 3.0 * h2) * z * (1 - 0.45 * f)
        a = int(230 * min(1, u / 0.1) * (1 - f * 0.6))
        # streak toward the phone + the drop itself
        vx, vy = PHONE[0] - x, PHONE[1] - 20 - y
        n = math.hypot(vx, vy) + 1e-9
        L = (10 + 46 * f) * z
        d.line([(sx, sy), (sx - vx / n * L, sy - vy / n * L)], fill=SOFT + (int(a * 0.5),), width=max(1, int(2 * z)))
        d.ellipse([sx - r, sy - r * 1.25, sx + r, sy + r * 1.25], fill=(236, 240, 246, a), outline=INK + (a,), width=max(1, int(1.6 * z)))


# ── hero ─────────────────────────────────────────────────────────────────────
def draw_hero(frame, cam, tau, t_abs, alpha_mul=1.0, ghost=False):
    st = S.hero_state(tau)
    if st is None:
        return
    s_px = hero_screen_scale(t_abs, cam)
    n = int(3.0 * s_px)
    tile = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile, "RGBA")
    fx, fy = n / 2, 2.3 * s_px
    J = SH.shade(td, fx, fy, s_px, st["pose"], expr=st["expr"], look=st["look"], blink=st["blink"], flip=st["flip"])
    if st["book"]:
        btile, banc = SPR["hbook"]
        hx, hy = J["hand_l"]
        img, xy = place_tile(btile, banc, hx + 0.03 * s_px, hy + 0.09 * s_px, s_px / S.HERO_S / S.S2 * 1.0, rot_cw=-14)
        tile.alpha_composite(img, xy)
    z = cam.z
    if ghost:
        tile.putalpha(tile.split()[3].point(lambda v: int(v * alpha_mul)))
    if st["shadow"] and not ghost:
        contact_shadow(frame, cam, st["feet"][0], st["surface"], 0.26 * S.HERO_S, 0.045 * S.HERO_S, 70)
    if st["pivot"]:
        if st["pivot"] == "hands":
            pv = ((J["hand_l"][0] + J["hand_r"][0]) / 2, (J["hand_l"][1] + J["hand_r"][1]) / 2)
        else:
            pv = J["hip"]
        rotated = tile.rotate(st["rot"], resample=Image.BICUBIC, center=pv)
        sx, sy = cam.pt(*st["pivot_world"])
        xy = (int(round(sx - pv[0])), int(round(sy - pv[1])))
        vs = (st["smear"][0] * z, st["smear"][1] * z)
        if ghost:
            frame.alpha_composite(rotated, xy)
            return
        paste_smear(frame, rotated, xy, (vs[0] * 3, vs[1] * 3), 0.8)
    else:
        sx, sy = cam.pt(*st["feet"])
        qx, qy = S.land_squash(tau)
        if abs(qx - 1) > 0.004 or abs(qy - 1) > 0.004:
            nw, nh = max(2, int(n * qx)), max(2, int(n * qy))
            tile = tile.resize((nw, nh), Image.BILINEAR)
            fx, fy = fx * qx, fy * qy
        xy = (int(round(sx - fx)), int(round(sy - fy)))
        vs = (st["smear"][0] * z, st["smear"][1] * z)
        if abs(vs[0]) + abs(vs[1]) > 2 and not ghost:
            paste_smear(frame, tile, xy, (vs[0] * 3, vs[1] * 3), 0.6)
        else:
            frame.alpha_composite(tile, xy)


GHOST_WINDOWS = ((TL["lunge"], TL["grab"] + 0.08), (TL["slip1"], TL["slip1"] + 0.12), (TL["slip2"], TL["slip2"] + 0.12),
                 (TL["letgo"], TL["land"] + 0.06))


def draw_hero_ghosts(frame, cam, tau, t_abs):
    """Two afterimages (−2 and −1 frames) on the fast moves: lunge, slips, the fall. Smooth, cinematic motion."""
    if not any(a <= tau < b for a, b in GHOST_WINDOWS):
        return
    for dt, am in ((2 / FPS, 0.16), (1 / FPS, 0.34)):
        draw_hero(frame, cam, tau - dt, t_abs - dt, alpha_mul=am, ghost=True)


# ── ECU insert (S3) ──────────────────────────────────────────────────────────
def ecu_frame(t):
    u = seg(t, TL["cut_s3"], TL["cut_s4"])
    cam = Cam(430 + 10 * u, 1050, 3.2)
    bg = paper_crop(cam).convert("RGBA")
    # a soft out-of-focus door jamb edge on the left for depth
    d = ImageDraw.Draw(bg, "RGBA")
    d.rectangle([0, 0, 120, H], fill=WOOD + (255,))
    d.line([(122, 0), (122, H)], fill=INK + (255,), width=10)
    bg = bg.filter(ImageFilter.GaussianBlur(3))
    hr = 222 + 20 * u
    expr = "think" if t < 4.15 else "shock"
    jolt = 6 * math.exp(-(t - 4.15) / 0.05) * math.sin(2 * math.pi * 16 * (t - 4.15)) if t >= 4.15 else 0.0
    look = (0.85 - 0.1 * u, 0.35 - 0.05 * u)
    blink = 1.0 if 4.08 <= t < 4.15 else 0.0
    SH.head_only(bg, 560 + 24 * u + jolt, 1010 - 10 * u, hr, expr=expr, look=look, blink=blink, ang=-0.06 + 0.03 * u, yaw=16)
    # v3 — the phone's light reaches his face from frame-right: an amber rim that swells with the pulse and the shock
    k = 0.22 + 0.30 * S.pump(t) + (0.35 * seg(t, 4.15, 4.45) if t >= 4.15 else 0.0)
    arr = np.asarray(bg.convert("RGB"), np.float32)
    xx = np.arange(W, dtype=np.float32)[None, :]
    yy = np.arange(H, dtype=np.float32)[:, None]
    rim = np.clip((xx - 520) / 560, 0, 1) ** 1.6 * np.exp(-((yy - 1010) / 520) ** 2)
    arr += (rim * k)[..., None] * np.array([96, 52, -22], np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")


# ── type ─────────────────────────────────────────────────────────────────────
def text_extruded(layer, xy, text, size, col=INK, anchor="mm", depth=7, glow=None, alpha=255, weight=800):
    d = ImageDraw.Draw(layer, "RGBA")
    f = font(size, weight)
    x, y = xy
    if glow:
        tmp = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        ImageDraw.Draw(tmp).text((x, y), text, font=f, fill=glow + (120,), anchor=anchor, stroke_width=3)
        tmp = tmp.filter(ImageFilter.GaussianBlur(18))
        layer.alpha_composite(tmp)
    side = tuple(int(c * .45) for c in col)
    for k in range(depth, 0, -1):
        d.text((x + k * .85, y + k * 1.1), text, font=f, fill=side + (int(alpha * .9),), anchor=anchor)
    d.text((x, y), text, font=f, fill=col + (alpha,), anchor=anchor,
           stroke_width=max(1, size // 55), stroke_fill=(246, 241, 231, min(alpha, 210)))


LETTER_STAGGER = 0.018   # s between letters of the meaning line (the audio 'ink ticks' use the same grid)
LETTER_DUR = 0.12


def text_cascade(layer, x_left, y, text, size, t, t0, col=INK, depth=7, i_off=0):
    """Kinetic type: each letter drops in on its own (stagger LETTER_STAGGER, ease-out LETTER_DUR) — the line still
    lands inside 0.35 s so the slam reads as one event with a live edge. Returns the x after the last letter."""
    f = font(size, 800)
    for i, ch in enumerate(text):
        if ch == " ":
            continue
        ti = t0 + (i + i_off) * LETTER_STAGGER
        u = seg(t, ti, ti + LETTER_DUR)
        if u <= 0:
            continue
        xi = x_left + f.getlength(text[:i])
        dy = (1 - ease_out(u, 2.5)) * -70
        sc = 1.0 + 0.16 * (1 - ease_out(u, 2.0))
        text_extruded(layer, (xi, y + dy), ch, int(size * sc), col, anchor="lm", depth=depth, alpha=int(255 * min(1, u * 2.5 + 0.1)))
    return x_left + f.getlength(text)


def draw_type(frame, t):
    if not (TL["line1"] <= t < TL["cut_s6"]):
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    size = 108
    f = font(size, 800)
    # line 1: "Phone ulta."  — letters cascade in from above on the word slam
    wl1 = f.getlength("Phone ulta.")
    text_cascade(layer, W / 2 - wl1 / 2, 440, "Phone ulta.", size, t, TL["line1"])
    if t >= TL["line2"]:
        # line 2 cascades in with the VO word "Zindagi"; the hot word turns amber and pops on "seedhi."
        w1 = f.getlength("Zindagi ")
        w2 = f.getlength("seedhi.")
        x0 = W / 2 - (w1 + w2) / 2
        text_cascade(layer, x0, 580, "Zindagi", size, t, TL["line2"])
        if t < TL["hot"]:
            text_cascade(layer, x0 + w1, 580, "seedhi.", size, t, TL["line2"], i_off=8)
        else:
            u3 = seg(t, TL["hot"], TL["hot"] + 0.12)
            sc = 1.0 + 0.22 * (1 - ease_out(u3, 2.0))
            text_extruded(layer, (x0 + w1, 580), "seedhi.", int(size * sc), GOLD, anchor="lm", depth=9, glow=AMBER)
    frame.alpha_composite(layer)


def draw_moral(frame, t):
    """S6 punchline over the desk: 'Warna' · 'tum' · 'ulte.' — the last word is upside-down. Snaps out on the buzz."""
    if not (TL["moral1"] <= t < TL["moral_out"] + 0.07):
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    size = 94
    f = font(size, 800)
    wa, wt = f.getlength("Warna "), f.getlength("tum")
    x0 = 1012 - (wa + wt)              # right-aligned block on the empty wall right of the lamp
    yA, yB = 668, 812
    xB = x0 + (wa + wt) / 2 + 60
    u1 = seg(t, TL["moral1"], TL["moral1"] + 0.14)
    dy1 = (1 - ease_out(u1, 2.5)) * -80
    text_extruded(layer, (x0, yA + dy1), "Warna", size, INK, anchor="lm", alpha=int(255 * min(1, u1 * 2 + 0.2)))
    if t >= TL["moral2"]:
        u2 = seg(t, TL["moral2"], TL["moral2"] + 0.12)
        dx2 = (1 - ease_out(u2, 2.5)) * 90
        text_extruded(layer, (x0 + wa + dx2, yA), "tum", size, INK, anchor="lm", alpha=int(255 * min(1, u2 * 2 + 0.2)))
    if t >= TL["moral3"]:
        # 'ulte.' flips over as it lands — the word does what it says
        u3 = seg(t, TL["moral3"], TL["moral3"] + 0.16)
        ang = 180 * ease_out(u3, 2.2)
        sc = 1.0 + 0.3 * (1 - ease_out(u3, 2.0))
        wl = Image.new("RGBA", (int(size * 4.2), int(size * 1.9)), (0, 0, 0, 0))
        text_extruded(wl, (wl.width / 2, wl.height / 2), "ulte.", int(size * 1.08 * sc), GOLD, anchor="mm", depth=9, glow=AMBER)
        wl = wl.rotate(ang, resample=Image.BICUBIC, center=(wl.width / 2, wl.height / 2))
        layer.alpha_composite(wl, (int(xB - wl.width / 2), int(yB - wl.height / 2)))
    if t >= TL["moral_out"]:
        # 2-frame snap-out: the buzz wipes the words
        k = 1 - seg(t, TL["moral_out"], TL["moral_out"] + 0.07)
        bbox = layer.getbbox()
        if bbox and k > 0.02:
            cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
            nw, nh = max(1, int(W * k)), max(1, int(H * k))
            small = layer.resize((nw, nh), Image.BILINEAR)
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            layer.alpha_composite(small, (int(cx - cx * k), int(cy - cy * k)))
        else:
            return
    frame.alpha_composite(layer)


# ── frame assembly ───────────────────────────────────────────────────────────
def render_frame(fi):
    t = fi / FPS
    tau = S.world_time(t)
    if TL["cut_s3"] <= t < TL["cut_s4"]:
        frame = ecu_frame(t)
    else:
        cam = camera(t)
        frame = paper_crop(cam).convert("RGBA")
        draw_floor(frame, cam, tau)
        draw_door(frame, cam)
        draw_shelf(frame, cam)
        draw_rug(frame, cam, tau)
        # back props (floor + wall)
        for name in ("plant", "fbook0", "fbook1", "fbook2", "chair", "clock"):
            draw_prop(frame, cam, name, tau)
        draw_desk(frame, cam)
        draw_lamp(frame, cam, tau)
        for name in ("sbook0", "sbook1", "sbook2", "page0", "page1", "page2", "hbook"):
            draw_prop(frame, cam, name, tau)
        draw_pencil(frame, cam, tau)
        draw_phone(frame, cam, tau)
        draw_pulse_rings(frame, cam, tau)
        draw_speed_lines(frame, cam, tau)
        draw_prop(frame, cam, "cup", tau)
        draw_flow(frame, cam, tau)
        draw_hero_ghosts(frame, cam, tau, t)
        draw_hero(frame, cam, tau, t)
        draw_sweat(frame, cam, tau)
        draw_dust(frame, cam, tau)
        rgb = frame.convert("RGB")
        rgb = draw_glow(rgb, cam, tau, extra=0.10 * S.beat_pulse(tau))
        frame = rgb.convert("RGBA")
        draw_type(frame, t)
        draw_moral(frame, t)
    # 1-frame amber tint flash on the hook cut (tint, never a flood)
    if fi == int(round(TL["cut_s2"] * FPS)):
        frame.alpha_composite(Image.new("RGBA", (W, H), AMBER + (64,)))
    # 1-frame paper-white impact tint when the room hits the floor (gravity restored)
    if fi == int(round((TL["drop"] + 0.30) * FPS)):
        frame.alpha_composite(Image.new("RGBA", (W, H), (255, 252, 244, 30)))
    # v3 — the world rolls 180° on 'ulte.' (3 sub-samples per frame = motion blur on the whip)
    ang, zoom = S.frame_roll(t)
    if ang != 0.0 or zoom != 1.0:
        frame = roll_frame(frame, t)
    frame.alpha_composite(VIGNETTE)
    arr = np.asarray(frame.convert("RGB"), np.float32) + GRAIN[fi % 4]
    k = S.field_vis(tau)
    if k > 0.01:   # the field narrows the eye: edges darken with the pull (released over 0.2 s after the drop)
        arr *= 1.0 - (0.30 * min(1.0, k)) * VIG_K[..., None]
    # v3 — chroma split on the kicks (≤ 3 px, decays with the pump): the lens flinches with the beat
    dpx = int(round(3.0 * S.pump(t)))
    if dpx >= 1:
        arr[..., 0] = np.roll(arr[..., 0], dpx, axis=1)
        arr[..., 2] = np.roll(arr[..., 2], -dpx, axis=1)
    return np.clip(arr, 0, 255).astype(np.uint8)


def roll_frame(frame, t, subs=12):
    """Rotate + zoom the finished frame about its centre per S.frame_roll, averaging `subs` sub-frame samples."""
    acc = None
    rgb = frame.convert("RGB")
    for k in range(subs):
        ts = t + (k - (subs - 1) / 2) / (FPS * subs)
        ang, zoom = S.frame_roll(ts)
        th = math.radians(ang)
        c, s_ = math.cos(th) / zoom, math.sin(th) / zoom
        cx, cy = W / 2, H / 2
        # output (x, y) → input: rotate by -ang about the centre, scaled 1/zoom
        a, b, cc = c, s_, cx - c * cx - s_ * cy
        d, e, ff = -s_, c, cy + s_ * cx - c * cy
        img = rgb.transform((W, H), Image.AFFINE, (a, b, cc, d, e, ff), resample=Image.BICUBIC, fillcolor=(236, 231, 219))
        arr = np.asarray(img, np.float32)
        acc = arr if acc is None else acc + arr
    out = Image.fromarray(np.clip(acc / subs, 0, 255).astype(np.uint8))
    return out.convert("RGBA")


def ffmpeg_exe():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def render_range(a, b, out, crf=17, preset="slow"):
    cmd = [ffmpeg_exe(), "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-an", "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p",
           "-g", "60", "-keyint_min", "30", "-movflags", "+faststart", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for fi in range(a, b):
        p.stdin.write(render_frame(fi).tobytes())
        if (fi - a) % 30 == 0:
            el = time.time() - t0
            done = fi - a + 1
            print(f"[{out.name}] frame {fi} ({done}/{b - a}) {el:.0f}s elapsed, {el / done * (b - a - done):.0f}s left", flush=True)
    p.stdin.close()
    p.wait()
    print(f"[{out.name}] done in {time.time() - t0:.0f}s rc={p.returncode}", flush=True)
    return p.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frame", type=float, help="render one frame at time t (s)")
    ap.add_argument("--sheet", type=float, nargs="*", help="contact sheet at these times")
    ap.add_argument("--range", type=int, nargs=2, help="frame range [a, b) to mp4")
    ap.add_argument("--out", type=str, default="../render/test.jpg")
    ap.add_argument("--crf", type=int, default=17)
    ap.add_argument("--preset", type=str, default="slow")
    args = ap.parse_args()
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if args.frame is not None:
        t0 = time.time()
        arr = render_frame(int(round(args.frame * FPS)))
        Image.fromarray(arr).save(out, quality=92)
        print(f"frame {args.frame}s -> {out} in {time.time() - t0:.2f}s")
    elif args.sheet:
        times = args.sheet
        cols = 4
        rows = (len(times) + cols - 1) // cols
        tw, th = 360, 640
        sheet = Image.new("RGB", (cols * tw, rows * th), (40, 40, 40))
        d = ImageDraw.Draw(sheet)
        t0 = time.time()
        for i, tt in enumerate(times):
            arr = render_frame(int(round(tt * FPS)))
            im = Image.fromarray(arr).resize((tw, th), Image.LANCZOS)
            sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
            d.text(((i % cols) * tw + 8, (i // cols) * th + 6), f"{tt:.2f}s", fill=(255, 80, 80))
        sheet.save(out, quality=88)
        print(f"sheet {len(times)} frames -> {out} in {time.time() - t0:.1f}s ({(time.time() - t0) / len(times):.2f}s/frame)")
    elif args.range:
        render_range(args.range[0], args.range[1], out, args.crf, args.preset)


if __name__ == "__main__":
    main()
