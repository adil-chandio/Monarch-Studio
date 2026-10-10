#!/usr/bin/env python3
"""
noir.py — WF-03 · Monarch Noir Film — dark-world renderer core (look-dev v0, 2026-10-09)

World: black room, a back wall + floor in pseudo-perspective, ONE motivated amber light per scene,
bone-white line hero on the toon 3D skeleton (two-tone: lit side bone / dark side slate),
his cast shadow projected on the back wall by a 2-D homothety about the lamp (k = depth ratio),
one red villain colour (typewriter text only), serif narration, top-left SHADOW readout.
Everything is measured: every frame returns luma / dark-share / saturation.
"""
import os, sys, math, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'src'))
import toon as T          # 3-D skeleton + capsule helper (WF-01 engine, reused as a library)
import shade as S         # _solve(): skeleton → projected 2-D joints

W, H, SS = 1920, 1080, 2
FD = os.path.join(ROOT, 'fonts')
F_SERIF = '/usr/share/R/doc/html/katex/fonts/KaTeX_Main-Regular.ttf'
F_SERIF_I = '/usr/share/R/doc/html/katex/fonts/KaTeX_Main-Italic.ttf'
F_TYPE = '/usr/share/R/doc/html/katex/fonts/KaTeX_Typewriter-Regular.ttf'
F_SANS = os.path.join(FD, 'Montserrat-VF.ttf')

BLACK = np.array([7, 7, 9], np.float32)
WALL = np.array([14, 14, 15], np.float32)
FLOOR = np.array([10, 10, 11], np.float32)
BONE = (236, 232, 222)
SLATE = (96, 102, 112)
AMBER = np.array([255, 214, 170], np.float32)   # warm-grey lamp light (chroma kept low)
RED = (214, 38, 32)
INK = (3, 3, 4)


def font(path, size, var=None):
    f = ImageFont.truetype(path, int(size))
    if var:
        try:
            f.set_variation_by_name(var)
        except Exception:
            pass
    return f


# ─────────────────────────────────────────────── scene / camera
class Scene:
    """pseudo-perspective room: back wall at depth z=1 (far), camera plane z=0.
    floor line (wall/floor junction) at y_j; a point at depth z (0.3..1) has feet on
    y = y_j + (H - y_j) * (1 - z) ** 1.35 and scale s = s_near * (0.3 / z) ** 0.9."""

    def __init__(self, y_j=760, s_near=1120, cam_drift=(0.0, 0.0)):
        self.y_j = y_j * SS
        self.s_near = s_near * SS
        self.dx, self.dy = cam_drift[0] * SS, cam_drift[1] * SS

    def feet_y(self, z):
        return self.y_j + (H * SS - self.y_j) * (1 - z) ** 1.35 + self.dy

    def scale(self, z):
        return self.s_near * (0.3 / max(z, 0.05)) ** 0.9

    def x(self, u, z):
        """u in -1..1 across the room, converges toward centre with depth."""
        return (W * SS / 2) + u * (W * SS / 2) * (1.0 - 0.42 * z) + self.dx


def _rr(lo, hi, rng):
    return lo + (hi - lo) * rng.random()


# ─────────────────────────────────────────────── hero (bone-white line figure, two-tone)
LIMBS = [('shl', 'ell', 'arm_r0', 'arm_r1'), ('ell', 'hal', 'arm_r1', 'hand_r'),
         ('shr', 'elr', 'arm_r0', 'arm_r1'), ('elr', 'har', 'arm_r1', 'hand_r'),
         ('hpl', 'knl', 'leg_r0', 'leg_r1'), ('knl', 'ftl', 'leg_r1', 'leg_r1'),
         ('hpr', 'knr', 'leg_r0', 'leg_r1'), ('knr', 'ftr', 'leg_r1', 'leg_r1')]


def solve(x, y, s, pose, flip=False):
    K, J, KS, sgn = S._solve(x, y, s, pose, flip)
    return K, J, KS


def _capsule_poly(a, b, r0, r1):
    return T._capsule(a, b, r0, r1, segs=12)


def figure_parts(J, K, KS, s):
    """list of (depth, kind, polygon/ellipse, r) in draw order (far → near)."""
    parts = []
    for a, b, ra, rb in LIMBS:
        r0, r1 = S.SP[ra] * s * KS[a] * 0.92, S.SP[rb] * s * KS[b] * 0.92
        parts.append(((KS[a] + KS[b]) / 2, 'cap', (J[a], J[b], r0, r1)))
    # torso: hip → shoulder, tapered capsule (hip narrow, chest wider)
    parts.append((KS['hipc'] + 0.001, 'cap', (J['hipc'], J['shoc'], S.SP['hip_w'] * s * 0.95, S.SP['sh_w'] * s * 0.86)))
    parts.append((KS['nek'] + 0.002, 'cap', (J['shoc'], J['nek'], S.SP['arm_r0'] * s * 0.9, S.SP['arm_r0'] * s * 0.8)))
    hrx, hry = S.SP['head_rx'] * s * KS['hctr'] * 0.98, S.SP['head_ry'] * s * KS['hctr'] * 1.04
    parts.append((KS['hctr'] + 0.003, 'head', (J['hctr'], hrx, hry, K.get('hd_a', 0.0))))
    parts.sort(key=lambda p: p[0])
    return parts


def _ellipse_poly(c, rx, ry, ang, segs=40):
    ca, sa = math.cos(ang), math.sin(ang)
    return [(c[0] + ca * rx * math.cos(t) - sa * ry * math.sin(t),
             c[1] + sa * rx * math.cos(t) + ca * ry * math.sin(t))
            for t in np.linspace(0, 2 * math.pi, segs, endpoint=False)]


def draw_hero(layer, J, K, KS, s, light, expr='neutral', scarf=True, lit=(BONE, SLATE)):
    """layer: RGBA PIL image at SS. light: (x, y) of the lamp (SS px). Two-tone capsules."""
    parts = figure_parts(J, K, KS, s)
    bone, slate = lit
    d = ImageDraw.Draw(layer)
    # scarf first (behind everything): short ribbon from the neck, cool slate, waves away from the lamp
    if scarf:
        nek = J['nek']
        away = np.array([nek[0] - light[0], nek[1] - light[1]], np.float32)
        away /= (np.linalg.norm(away) + 1e-6)
        pts = [nek]
        for i in range(1, 7):
            t = i / 6
            px = nek[0] + away[0] * t * s * 0.22 + math.sin(t * 5.1) * s * 0.018
            py = nek[1] + t * s * 0.16 + math.sin(t * 3.7 + 1) * s * 0.012
            pts.append((px, py))
        for i in range(len(pts) - 1):
            w = int(s * 0.034 * (1 - i / 8))
            d.line([pts[i], pts[i + 1]], fill=slate + (255,), width=max(2, w))
    for depth, kind, g in parts:
        if kind == 'cap':
            a, b, r0, r1 = g
            poly = _capsule_poly(a, b, r0, r1)
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            r = (r0 + r1) / 2
        else:
            c, rx, ry, ang = g
            poly = _ellipse_poly(c, rx, ry, ang)
            mid, r = c, (rx + ry) / 2
        # lit half = same shape shifted toward the lamp, intersected with the shape
        lv = np.array([light[0] - mid[0], light[1] - mid[1]], np.float32)
        lv /= (np.linalg.norm(lv) + 1e-6)
        off = (lv[0] * r * 0.55, lv[1] * r * 0.55)
        bbox = [int(min(p[0] for p in poly)) - 4, int(min(p[1] for p in poly)) - 4,
                int(max(p[0] for p in poly)) + 5, int(max(p[1] for p in poly)) + 5]
        bbox = [max(0, bbox[0]), max(0, bbox[1]), min(layer.width, bbox[2]), min(layer.height, bbox[3])]
        if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
            continue
        bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        m = Image.new('L', (bw, bh), 0)
        ImageDraw.Draw(m).polygon([(p[0] - bbox[0], p[1] - bbox[1]) for p in poly], fill=255)
        lm = Image.new('L', (bw, bh), 0)
        ImageDraw.Draw(lm).polygon([(p[0] - bbox[0] + off[0], p[1] - bbox[1] + off[1]) for p in poly], fill=255)
        lm = lm.filter(ImageFilter.GaussianBlur(r * 0.18))
        ma, la = np.asarray(m, np.float32) / 255, np.asarray(lm, np.float32) / 255
        col = np.array(slate, np.float32)[None, None, :] * (1 - la[..., None]) + np.array(bone, np.float32)[None, None, :] * la[..., None]
        tile = Image.fromarray(np.concatenate([col.clip(0, 255).astype(np.uint8), (ma * 255).astype(np.uint8)[..., None]], 2), 'RGBA')
        layer.alpha_composite(tile, dest=(bbox[0], bbox[1]))
    # eyes: two slits on the head (the only face), angle = mood
    c, rx, ry, ang = next(g for _, kind, g in parts if kind == 'head')
    yaw = K.get('yaw', 0.0)
    if abs(yaw) < 120:  # facing camera enough to see eyes
        fx = c[0] + math.sin(math.radians(yaw)) * rx * 0.55
        e_dx, e_dy = rx * 0.34, -ry * 0.08
        tilt = {'sad': 0.22, 'angry': -0.28, 'neutral': 0.0, 'calm': 0.08}.get(expr, 0.0)
        ew, eh = rx * 0.22, max(2, ry * 0.05)
        for sgn in (-1, 1):
            ex, ey = fx + sgn * e_dx, c[1] + e_dy
            a = -tilt * sgn
            p0 = (ex - ew * math.cos(a), ey - ew * math.sin(a))
            p1 = (ex + ew * math.cos(a), ey + ew * math.sin(a))
            d.line([p0, p1], fill=INK + (255,), width=int(eh * 1.6))


def shadow_mask(size, J, K, KS, s, light, k, feather=1.0, anchor_y=None):
    """silhouette of the hero projected on the wall by a homothety about the lamp (factor k)."""
    m = Image.new('L', size, 0)
    d = ImageDraw.Draw(m)
    L = np.array(light, np.float32)
    Jk = {key: tuple(L + k * (np.array(v, np.float32) - L)) for key, v in J.items() if isinstance(v, tuple) and len(v) == 2}
    if anchor_y is not None:  # feet of the shadow stand on the wall/floor junction
        dy = anchor_y - max(Jk['ftl'][1], Jk['ftr'][1])
        Jk = {key: (v[0], v[1] + dy) for key, v in Jk.items()}
    parts = figure_parts(Jk, K, KS, s * k)
    for depth, kind, g in parts:
        if kind == 'cap':
            a, b, r0, r1 = g
            d.polygon(_capsule_poly(a, b, r0 * 1.12, r1 * 1.12), fill=255)
        else:
            c, rx, ry, ang = g
            d.polygon(_ellipse_poly(c, rx * 1.05, ry * 1.05, ang), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(3 * SS * k * feather + 1))
    return np.asarray(m, np.float32) / 255


# ─────────────────────────────────────────────── light + atmosphere (numpy, SS canvas)
def grid(size):
    ys, xs = np.mgrid[0:size[1], 0:size[0]].astype(np.float32)
    return xs, ys


def point_light(xs, ys, x, y, radius, power=1.0, aniso=1.0):
    d2 = ((xs - x) / radius) ** 2 + ((ys - y) / (radius * aniso)) ** 2
    return power / (1.0 + 2.2 * d2) ** 1.25


def render_room(sc, lamp, shadow=None, lamp_power=1.0, pool=True, ambient=1.0, shaft=None, rng=None):
    """returns float32 HxWx3 (SS) base image: wall + floor + lamp light (shadow removes lamp light on the wall)."""
    size = (W * SS, H * SS)
    xs, ys = grid(size)
    img = np.empty((size[1], size[0], 3), np.float32)
    wall = ys < sc.y_j
    img[:] = FLOOR
    img[wall] = WALL
    img *= ambient
    # faint junction line
    img[int(sc.y_j):int(sc.y_j) + 2 * SS] = WALL * 1.9
    if lamp is not None and lamp_power > 0:
        lx, ly, lr = lamp
        # broad wash on the back wall: horizontal falloff from the lamp, fading upward from the junction
        wash = np.exp(-((xs - lx) / (lr * SS * 1.9)) ** 2) * np.exp(-np.abs(sc.y_j - ys) / (420 * SS)) * wall
        wash = wash * lamp_power * 0.125
        if shadow is not None:
            cut = np.where(wall, 1.0 - 0.93 * shadow, 1.0)
            wash *= cut
            img *= (1.0 - 0.55 * shadow * wall * min(1.0, lamp_power * 1.2))[..., None]
        img += AMBER[None, None, :] * wash[..., None]
        li = point_light(xs, ys, lx, ly, lr * SS * 0.8, lamp_power * 0.24)
        if shadow is not None:
            li = li * np.where(wall, 1.0 - 0.93 * shadow, 1.0)
        img += AMBER[None, None, :] * li[..., None]
        if pool:
            pl = point_light(xs, ys, lx, ly + 10 * SS, lr * SS * 0.75, lamp_power * 0.30, aniso=0.26)
            pl = np.where(wall, pl * 0.1, pl)
            img += AMBER[None, None, :] * pl[..., None]
    if shaft is not None:
        # soft diagonal light shaft (window / doorway) with dust
        (x0, y0), (x1, y1), hw, power = shaft
        vx, vy = x1 - x0, y1 - y0
        ln = math.hypot(vx, vy) + 1e-6
        t = ((xs - x0) * vx + (ys - y0) * vy) / (ln * ln)
        perp = np.abs((xs - x0) * vy - (ys - y0) * vx) / ln
        half = hw * SS * (0.35 + 0.95 * t.clip(0, 1))
        sh = np.exp(-(perp / (half + 1)) ** 2 * 2.0) * (t > 0) * (t < 1.15) * (1 - 0.65 * t.clip(0, 1))
        img += np.array([220, 190, 150], np.float32)[None, None, :] * (sh * power)[..., None]
        if rng is not None:
            for _ in range(140):
                tt, pp = rng.random(), rng.normal(0, 0.45)
                px, py = x0 + vx * tt + (-vy / ln) * pp * half.mean(), y0 + vy * tt + (vx / ln) * pp * half.mean()
                if 0 <= px < size[0] and 0 <= py < size[1]:
                    r = _rr(1.2, 3.2, rng) * SS
                    yy, xx = int(py), int(px)
                    y0_, y1_, x0_, x1_ = max(0, yy - 6), min(size[1], yy + 7), max(0, xx - 6), min(size[0], xx + 7)
                    sub = np.exp(-(((xs[y0_:y1_, x0_:x1_] - px) ** 2 + (ys[y0_:y1_, x0_:x1_] - py) ** 2) / (r * r)))
                    img[y0_:y1_, x0_:x1_] += (sub * 170 * power * _rr(0.4, 1.0, rng))[..., None]
    return img


def finish(img, rng, vignette=0.55, grain=2.4, halation=0.18):
    """vignette · halation · grain · downsample to 1920×1080 → uint8 RGB."""
    size = (img.shape[1], img.shape[0])
    xs, ys = grid(size)
    r = np.sqrt(((xs / size[0]) - 0.5) ** 2 + ((ys / size[1]) - 0.5) ** 2) / 0.7071
    img = img * (1 - vignette * r ** 2.4)[..., None]
    out = Image.fromarray(img.clip(0, 255).astype(np.uint8), 'RGB').resize((W, H), Image.LANCZOS)
    a = np.asarray(out, np.float32)
    if halation > 0:
        hi = np.asarray(out.filter(ImageFilter.GaussianBlur(18)), np.float32)
        a = a + (hi - 60).clip(0, None) * halation
    a += rng.normal(0, grain, a.shape).astype(np.float32)
    return a.clip(0, 255).astype(np.uint8)


# ─────────────────────────────────────────────── type
def text_layer(size):
    return Image.new('RGBA', size, (0, 0, 0, 0))


def narration(layer, txt, cx, cy, size=46, col=BONE, italic=False, tracking=1.0, alpha=255):
    f = font(F_SERIF_I if italic else F_SERIF, size * SS)
    d = ImageDraw.Draw(layer)
    w = d.textlength(txt, font=f)
    d.text((cx * SS - w / 2, cy * SS - size * SS * 0.6), txt, font=f, fill=col + (alpha,))


def villain(layer, txt, x, y, size=44, alpha=255, ghost=True):
    f = font(F_TYPE, size * SS)
    d = ImageDraw.Draw(layer)
    if ghost:
        d.text((x * SS + 3 * SS, y * SS + 2 * SS), txt, font=f, fill=RED + (int(alpha * 0.35),))
    d.text((x * SS, y * SS), txt, font=f, fill=RED + (alpha,))


def readout(layer, metres, x=64, y=48, alpha=200):
    f = font(F_SANS, 20 * SS, 'Medium')
    f2 = font(F_SANS, 20 * SS, 'Light')
    d = ImageDraw.Draw(layer)
    d.text((x * SS, y * SS), 'SHADOW', font=f, fill=BONE + (alpha,))
    d.text(((x + 118) * SS, y * SS), f'{metres:.1f} m', font=f2, fill=BONE + (alpha,))
    bar = max(2, int(metres / 7.0 * 220)) * SS
    d.rectangle([x * SS, (y + 30) * SS, x * SS + bar, (y + 31) * SS], fill=BONE + (int(alpha * 0.7),))


def measure(rgb):
    a = rgb.astype(np.float32)
    luma = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    mx, mn = a.max(2), a.min(2)
    sat = np.where(mx > 0, (mx - mn) / (mx + 1e-6), 0)
    return dict(luma=round(float(luma.mean()), 1), dark_lt30=round(float((luma < 30).mean()), 3),
                p99=round(float(np.percentile(luma, 99)), 1), sat=round(float(sat.mean()), 3),
                chroma=round(float((mx - mn).mean()), 1))


# ─────────────────────────────────────────────── one shot
def shot(spec, seed=1):
    """spec: dict(hero=dict(u,z,pose,yaw,expr,flip), lamp=(u,z,radius,power), lines=[...], villain=[...],
    readout=float|None, shaft=..., ambient=float, scarf=bool)"""
    rng = np.random.default_rng(seed)
    sc = Scene(**spec.get('scene', {}))
    size = (W * SS, H * SS)
    hero = spec.get('hero')
    lamp = spec.get('lamp')
    lampxy = None
    if lamp:
        lu, lz, lr, lp = lamp
        lampxy = (sc.x(lu, lz), sc.feet_y(lz) - 26 * SS * (0.3 / lz) ** 0.9)
    J = K = KS = None
    s = 0
    if hero:
        s = sc.scale(hero['z']) * hero.get('size', 1.0)
        pose = hero['pose']
        if 'yaw' in hero:
            pose = dict(pose)
            pose['yaw'] = hero['yaw']
        K, J, KS = solve(sc.x(hero['u'], hero['z']), sc.feet_y(hero['z']), s, pose, hero.get('flip', False))
    sh = None
    k = None
    if hero and lamp and lamp[3] > 0:
        k = (1.0 - lz) / max(hero['z'] - lz, 0.08)
        k = min(k, spec.get('kmax', 2.2))
        sh = shadow_mask(size, J, K, KS, s, lampxy, k, anchor_y=sc.y_j)
    img = render_room(sc, (lampxy[0], lampxy[1], lamp[2]) if lamp else None, sh,
                      lamp_power=(lamp[3] if lamp else 0), ambient=spec.get('ambient', 1.0),
                      shaft=spec.get('shaft'), rng=rng)
    fig = text_layer(size)
    if hero:
        # contact shadow on the floor
        cx, cy = J['hipc'][0], sc.feet_y(hero['z'])
        m = Image.new('L', size, 0)
        ImageDraw.Draw(m).ellipse([cx - s * 0.22, cy - s * 0.035, cx + s * 0.22, cy + s * 0.035], fill=200)
        m = np.asarray(m.filter(ImageFilter.GaussianBlur(8 * SS)), np.float32) / 255
        img *= (1 - 0.7 * m)[..., None]
        draw_hero(fig, J, K, KS, s, lampxy or (size[0] * 0.5, 0), expr=hero.get('expr', 'neutral'), scarf=spec.get('scarf', True))
        # the hero is lit by the lamp: distance falloff on his own brightness
        if lampxy:
            dd = math.hypot(J['hipc'][0] - lampxy[0], J['hipc'][1] - lampxy[1]) / (lamp[2] * SS)
            lit = 0.55 + 0.45 / (1 + 0.9 * dd * dd)
            arr = np.asarray(fig).astype(np.float32)
            arr[..., :3] *= lit
            fig = Image.fromarray(arr.clip(0, 255).astype(np.uint8), 'RGBA')
    if lamp and lamp[3] > 0:
        # the lantern itself: a small dark body + hot core + halo (foreground if near)
        d = ImageDraw.Draw(fig)
        lx, ly = lampxy
        lsz = 58 * SS * (0.3 / lz) ** 0.9
        body = (18, 16, 14, 255)
        d.rounded_rectangle([lx - lsz * 0.46, ly - lsz * 1.05, lx + lsz * 0.46, ly + lsz * 0.5], radius=lsz * 0.12, fill=body)   # cage
        d.rounded_rectangle([lx - lsz * 0.30, ly - lsz * 0.80, lx + lsz * 0.30, ly + lsz * 0.28], radius=lsz * 0.06,
                            fill=(int(255 * min(1, lamp[3] + 0.2)), int(226 * min(1, lamp[3] + 0.2)), int(185 * min(1, lamp[3] + 0.2)), 255))  # glass
        for bx in (-0.12, 0.12):  # cage bars
            d.line([(lx + bx * lsz * 2, ly - lsz * 0.8), (lx + bx * lsz * 2, ly + lsz * 0.28)], fill=body, width=max(2, int(lsz * 0.05)))
        d.line([(lx, ly - lsz * 1.05), (lx, ly - lsz * 1.3)], fill=body, width=max(2, int(lsz * 0.09)))
        d.arc([lx - lsz * 0.42, ly - lsz * 1.9, lx + lsz * 0.42, ly - lsz * 1.1], 190, 350, fill=body, width=max(2, int(lsz * 0.07)))  # handle
        xs, ys = grid(size)
        halo = point_light(xs, ys, lx, ly - lsz * 0.25, lsz * 2.4, 1.0)
        img += AMBER[None, None, :] * (halo * 0.55 * lamp[3])[..., None]
    base = Image.fromarray(img.clip(0, 255).astype(np.uint8), 'RGB').convert('RGBA')
    base.alpha_composite(fig)
    txt = text_layer(size)
    for ln in spec.get('lines', []):
        narration(txt, *ln[:3], **ln[3] if len(ln) > 3 else {})
    for v in spec.get('villain', []):
        villain(txt, *v[:3], **v[3] if len(v) > 3 else {})
    if spec.get('readout') is not None:
        readout(txt, spec['readout'])
    base.alpha_composite(txt)
    out = finish(np.asarray(base.convert('RGB'), np.float32), rng, **spec.get('finish', {}))
    return out, measure(out), dict(k=k, s=s / SS)


if __name__ == '__main__':
    print('noir core ok; use look_v0.py')
