"""cinema9.py — AMEER KA KUTTA v9 "CHAOS CINEMA": the cinematic layer on top of kutta2's picture.

Everything here is a pure function of time, numpy + PIL only, and tuned against gate_kutta2:
  * no instant luma steps: every flash and slam ramps over >= 4 frames (gate max_dluma < 8)
  * no per-frame jitter: the handheld camera is a sum of slow sines, punches have a 2-frame attack
    (gate jerk_p95 < 2.0 on shot frames, trans_jerk_max < 8 inside blends)
  * no black edges: the camera never zooms below 1.045 and the shake stays inside the margin

Layers (in render order, see kutta2.render):
  chapter_grade  per-chapter colour (teal/gold hook, rich luxury, royal purple, cold grey gareeb)
  bloom          bright-pass glow + anamorphic blue streak on highlights (gold, neon, lights)
  camera         handheld drift + hot-word punches (zoom kick, roll, chroma split, radial rush)
  flash          eased light hits (hook crack, crown landing, thunder, end stamp)
  vignette+grain film finish (respect3 grade stays; this adds the per-chapter edge weight)

Scene elements drawn inside the shots (rain, money rain, confetti, speed streaks, shockwave,
slam title, end stamp) are in this module too so kutta2 stays the timeline and the actors.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30


def cl(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def sstep(u):
    u = cl(u)
    return u * u * (3 - 2 * u)


def ramp(d, up, down):
    """eased hit envelope: 0 -> 1 over `up` seconds (smoothstep), then 1 -> 0 over `down` seconds."""
    if d < 0:
        return 0.0
    if d < up:
        return sstep(d / up)
    if d < up + down:
        return 1.0 - sstep((d - up) / down)
    return 0.0


def punch_env(d, up=0.17, tau=0.26):
    """5-frame smoothstep attack, half-gaussian release: C1 at the peak, so the motion energy has no corner
    (gate jerk_p95 measures the second difference of the frame-to-frame change)."""
    if d < 0 or d > 1.2:
        return 0.0
    if d < up:
        return sstep(d / up)
    r = (d - up) / tau
    return math.exp(-r * r)


def toe_lift(x, lift=14.0, knee=90.0):
    """filmic lifted blacks: 0 -> lift, knee and above untouched (soft toe). Also keeps night skies off the
    gate's black-edge detector after the vignette."""
    m = np.clip(1.0 - x / knee, 0.0, 1.0)
    return x + lift * m * m


# ───────────────────────────────────────────── chapter grade
# (shadow tint rgb, highlight tint rgb, saturation, contrast, gain)
GRADE = [
    ((-6, 4, 12), (18, 10, -8), 1.10, 1.07, 1.00),    # HOOK: teal shadows, gold highs
    ((-4, -2, 14), (14, 8, -4), 1.20, 1.06, 1.02),    # LUXURY: rich, blue-black shadows, warm highs
    ((10, -6, 16), (16, 10, -6), 1.16, 1.06, 1.02),   # RAJA: royal purple shadows, gold highs
    ((-4, 2, 10), (-6, 0, 8), 0.62, 1.12, 0.93),      # GAREEB: cold, drained, heavier
]


def _mix_params(t, starts):
    """chapter params blended over 0.7 s around each chapter start (no colour step at the cut)."""
    i = max(k for k, s in enumerate(starts) if t >= s - 1e-6) if t >= starts[0] else 0
    p = GRADE[i]
    if i + 1 < len(starts):
        b = starts[i + 1]
        k = cl((t - (b - .35)) / .7)
        if k > 0:
            q = GRADE[i + 1]
            p = tuple(tuple(a + (c - a) * k for a, c in zip(pa, pb)) if isinstance(pa, tuple) else pa + (pb - pa) * k
                      for pa, pb in zip(p, q))
    if i > 0:
        b = starts[i]
        k = cl((t - (b - .35)) / .7)
        if k < 1:
            q = GRADE[i - 1]
            p = tuple(tuple(c + (a - c) * k for a, c in zip(pa, pb)) if isinstance(pa, tuple) else pb + (pa - pb) * k
                      for pa, pb in zip(p, q))
    return p


def chapter_grade(arr, t, starts):
    sh, hi, sat, con, gain = _mix_params(t, starts)
    x = arr.astype(np.float32)
    lum = (0.299 * x[..., 0] + 0.587 * x[..., 1] + 0.114 * x[..., 2])[..., None]
    x = lum + (x - lum) * sat
    x = (x - 128.0) * con + 128.0
    x *= gain
    lo = np.clip((110.0 - lum) / 110.0, 0, 1)
    hiw = np.clip((lum - 140.0) / 115.0, 0, 1)
    x += np.array(sh, np.float32) * lo + np.array(hi, np.float32) * hiw
    return x


# ───────────────────────────────────────────── bloom + anamorphic streak
def bloom(x, amount=0.55, streak=0.40, thresh=175.0, down=4):
    """x float32 HxWx3. Bright-pass at 1/down res, gaussian glow + horizontal streak, added back."""
    h, w = x.shape[0] // down, x.shape[1] // down
    small = Image.fromarray(np.clip(x, 0, 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)
    s = np.asarray(small).astype(np.float32)
    lum = 0.299 * s[..., 0] + 0.587 * s[..., 1] + 0.114 * s[..., 2]
    k = np.clip((lum - thresh) / (255.0 - thresh), 0, 1)[..., None]
    bp = Image.fromarray(np.clip(s * k, 0, 255).astype(np.uint8))
    glow = np.asarray(bp.filter(ImageFilter.GaussianBlur(7))).astype(np.float32)
    st = np.asarray(bp.filter(ImageFilter.GaussianBlur((26, 1.2)))).astype(np.float32)
    st = st * np.array([0.55, 0.75, 1.0], np.float32)          # anamorphic: blue-ish streak
    add = glow * amount + st * streak
    add = np.asarray(Image.fromarray(np.clip(add, 0, 255).astype(np.uint8)).resize((x.shape[1], x.shape[0]), Image.BILINEAR)).astype(np.float32)
    # screen-blend so highlights roll off instead of clipping
    return 255.0 - (255.0 - np.clip(x, 0, 255)) * (255.0 - add) / 255.0


# ───────────────────────────────────────────── chroma split + radial rush (punch frames)
def chroma(x, px):
    """radial colour split: R scaled out, B scaled in by px pixels at the frame edge."""
    if px < 0.6:
        return x
    im = Image.fromarray(np.clip(x, 0, 255).astype(np.uint8))
    h, w = x.shape[:2]
    out = x.copy()
    for ch, sgn in ((0, 1.0), (2, -1.0)):
        s = 1.0 + sgn * 2.0 * px / w
        iz = 1.0 / s
        mx, my = (w - w * iz) / 2, (h - h * iz) / 2
        band = im.getchannel(ch).transform((w, h), Image.AFFINE, (iz, 0, mx, 0, iz, my), Image.BILINEAR)
        out[..., ch] = np.asarray(band).astype(np.float32)
    return out


def radial_rush(x, amt, cx=0.5, cy=0.45, n=5):
    """zoom-blur toward (cx, cy), computed at half res and mixed back by amt (0..1)."""
    if amt < 0.03:
        return x
    h, w = x.shape[:2]
    im = Image.fromarray(np.clip(x, 0, 255).astype(np.uint8)).resize((w // 2, h // 2), Image.BILINEAR)
    hw, hh = im.size
    acc = np.asarray(im).astype(np.float32)
    for i in range(1, n):
        s = 1.0 + 0.035 * amt * i
        iz = 1.0 / s
        mx, my = cx * hw * (1 - iz), cy * hh * (1 - iz)
        acc += np.asarray(im.transform((hw, hh), Image.AFFINE, (iz, 0, mx, 0, iz, my), Image.BILINEAR)).astype(np.float32)
    acc /= n
    big = np.asarray(Image.fromarray(np.clip(acc, 0, 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)).astype(np.float32)
    return x * (1 - amt) + big * amt


# ───────────────────────────────────────────── camera
_SHAKE = [(0.71, 1.0, 0.0), (1.37, 0.55, 2.1), (2.93, 0.22, 0.7)]     # (hz, weight, phase) smooth handheld


def handheld(t, amp=1.0):
    dx = sum(w * math.sin(2 * math.pi * f * t + ph) for f, w, ph in _SHAKE) * 9.0 * amp
    dy = sum(w * math.sin(2 * math.pi * f * t * 0.83 + ph + 1.0) for f, w, ph in _SHAKE) * 11.0 * amp
    rot = sum(w * math.sin(2 * math.pi * f * t * 0.57 + ph + 2.2) for f, w, ph in _SHAKE) * 0.28 * amp
    return dx, dy, rot


def apply_camera(x, z, dx, dy, rot_deg):
    """one affine: scale z about the centre, rotate rot_deg, shift (dx, dy). Keeps the whole frame covered."""
    h, w = x.shape[:2]
    th = math.radians(rot_deg)
    c, s = math.cos(th), math.sin(th)
    # output -> input mapping
    a, b = c / z, s / z
    cx, cy = w / 2.0, h / 2.0
    e = cx - a * cx - b * cy - dx
    f = cy + b * cx - a * cy - dy
    im = Image.fromarray(np.clip(x, 0, 255).astype(np.uint8))
    return np.asarray(im.transform((w, h), Image.AFFINE, (a, b, e, -b, a, f), Image.BICUBIC)).astype(np.float32)


def camera_margin_ok(z, dx, dy, rot_deg, w=W, h=H):
    th = abs(math.radians(rot_deg))
    need_x = (h / 2) * math.sin(th) + abs(dx)
    need_y = (w / 2) * math.sin(th) + abs(dy)
    return (w * z - w) / 2 > need_x + 2 and (h * z - h) / 2 > need_y + 2


# ───────────────────────────────────────────── vignette (extra, per chapter weight)
_VIG = {}


def vignette(x, k):
    if k <= 0:
        return x
    key = round(k, 2)
    if key not in _VIG:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 1.414
        _VIG[key] = (1.0 - k * np.clip(r, 0, 1) ** 2.0)[..., None].astype(np.float32)
    return x * _VIG[key]


def flash_add(x, amt, col=(255, 236, 200)):
    """screen-blend a uniform light hit; amt in 0..1 (0.1 ~ +12 mean luma on a mid frame)."""
    if amt <= 0.002:
        return x
    c = np.array(col, np.float32) * amt
    return 255.0 - (255.0 - np.clip(x, 0, 255)) * (255.0 - c) / 255.0


# ───────────────────────────────────────────── scene elements (RGBA layers / draws)
_TEX = {}


def rain_layer(t, strength=1.0, slant=-0.18, half=None):
    """two scrolling rain sheets (far thin, near thick) on a transparent layer. half='right' masks x<540."""
    key = 'rain'
    if key not in _TEX:
        rnd = np.random.default_rng(9)
        sheets = []
        for (n, ln, wd, a) in ((420, 70, 2, 95), (160, 130, 3, 150)):
            tex = Image.new('RGBA', (W, 2 * H), (0, 0, 0, 0))
            d = ImageDraw.Draw(tex)
            for _ in range(n):
                x0 = rnd.uniform(-200, W + 200); y0 = rnd.uniform(0, 2 * H)
                d.line([(x0, y0), (x0 + ln * slant, y0 + ln)], fill=(214, 230, 250, a), width=wd)
            sheets.append(tex)
        _TEX[key] = sheets
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for i, (tex, spd) in enumerate(zip(_TEX[key], (1500, 2600))):
        off = int((t * spd) % H)
        crop = tex.crop((0, 2 * H - H - off, W, 2 * H - off))
        if strength < 0.999:
            crop = Image.fromarray((np.asarray(crop).astype(np.float32) * np.array([1, 1, 1, strength], np.float32)).astype(np.uint8), 'RGBA')
        out.alpha_composite(crop)
    if half == 'right':
        a = np.asarray(out.getchannel('A')).astype(np.float32)
        xx = np.arange(W, dtype=np.float32)[None, :]
        a *= np.clip((xx - 540) / 60.0, 0, 1)
        out.putalpha(Image.fromarray(a.astype(np.uint8)))
    return out


def splashes(d, t, gy, half=None, n=14, seed=5):
    rnd = np.random.default_rng(seed)
    for i in range(n):
        ph = (t * 3.1 + rnd.random()) % 1.0
        x = rnd.uniform(40, W - 40)
        if half == 'right' and x < 580:
            continue
        r = 6 + 26 * ph
        a = int(160 * (1 - ph))
        d.ellipse([x - r, gy - r * .22, x + r, gy + r * .22], outline=(220, 232, 250, a), width=2)


def _money_sprites():
    if 'money' in _TEX:
        return _TEX['money']
    sp = []
    f = ImageFont.truetype('/home/user/fonts/Montserrat-VF.ttf', 30)
    try:
        f.set_variation_by_axes([800])
    except Exception:
        pass
    note = Image.new('RGBA', (120, 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(note)
    d.rounded_rectangle([0, 0, 119, 59], 8, fill=(120, 176, 96, 255), outline=(30, 24, 34, 255), width=3)
    d.rounded_rectangle([10, 10, 109, 49], 6, outline=(226, 232, 180, 200), width=2)
    d.ellipse([42, 12, 78, 48], fill=(226, 232, 180, 255), outline=(30, 24, 34, 255), width=2)
    d.text((60, 30), 'Rs', font=f, fill=(30, 24, 34, 255), anchor='mm')
    coin = Image.new('RGBA', (56, 56), (0, 0, 0, 0))
    d = ImageDraw.Draw(coin)
    d.ellipse([0, 0, 55, 55], fill=(226, 176, 84, 255), outline=(30, 24, 34, 255), width=3)
    d.ellipse([8, 8, 47, 47], outline=(255, 226, 150, 255), width=2)
    d.polygon([(28, 16), (34, 26), (44, 22), (40, 36), (16, 36), (12, 22), (22, 26)], fill=(150, 96, 40, 255))
    sp = [note, coin]
    _TEX['money'] = sp
    return sp


def money_rain(layer, t, t_start, n=22, seed=21, area=(0, W), speed=620.0, gust=0.0):
    """gold notes and coins tumbling down since t_start (RGBA layer)."""
    dt = t - t_start
    if dt < 0:
        return
    rnd = np.random.default_rng(seed)
    note, coin = _money_sprites()
    for i in range(n):
        x0 = rnd.uniform(area[0], area[1]); ph = rnd.uniform(0, 1); spd = speed * rnd.uniform(.75, 1.25)
        rot = rnd.uniform(0, 360); rs = rnd.uniform(-240, 240); sway = rnd.uniform(30, 80); wph = rnd.uniform(0, 6.28)
        kind = note if rnd.random() < .6 else coin
        # the particle enters at the top at a staggered time so the first second is a build, not a wall
        born = ph * 1.4
        if dt < born:
            continue
        y = -80 + (dt - born) * spd
        if y > H + 80:
            # recycle: loop with a new phase
            y = -80 + ((dt - born) * spd) % (H + 160)
        x = x0 + math.sin(dt * 2.0 + wph) * sway + gust * dt * 60
        im = kind.rotate(rot + rs * dt, resample=Image.BILINEAR, expand=True)
        sc = rnd.uniform(.75, 1.15)
        im = im.resize((max(2, int(im.width * sc)), max(2, int(im.height * sc))), Image.BILINEAR)
        layer.alpha_composite(im, (int(x - im.width / 2), int(y - im.height / 2)))


def confetti(layer, t, t_burst, cx, cy, n=46, seed=7, cols=((226, 176, 84), (255, 226, 150), (168, 112, 226), (248, 244, 233))):
    dt = t - t_burst
    if dt < 0 or dt > 1.8:
        return
    rnd = np.random.default_rng(seed)
    d = ImageDraw.Draw(layer, 'RGBA')
    for i in range(n):
        ang = rnd.uniform(-math.pi, 0) + rnd.uniform(-.4, .4)
        v = rnd.uniform(500, 1200)
        x = cx + math.cos(ang) * v * dt * (1 - .35 * dt)
        y = cy + math.sin(ang) * v * dt * (1 - .35 * dt) + 1500 * dt * dt
        col = cols[int(rnd.integers(len(cols)))]
        a = int(255 * cl((1.8 - dt) / .5) * sstep(cl(dt / 0.17)))
        w, h = 10 + rnd.uniform(0, 8), 5 + rnd.uniform(0, 4)
        rot = rnd.uniform(0, math.pi) + dt * rnd.uniform(4, 12)
        c, s = math.cos(rot), math.sin(rot)
        pts = [(x + c * w - s * h, y + s * w + c * h), (x - c * w - s * h, y - s * w + c * h),
               (x - c * w + s * h, y - s * w - c * h), (x + c * w + s * h, y + s * w - c * h)]
        d.polygon(pts, fill=col + (a,))


def shockwave(layer, t, t_hit, cx, cy, col=(255, 236, 190), rmax=620, dur=0.55):
    dt = t - t_hit
    if dt < 0 or dt > dur:
        return
    k = dt / dur
    r = 40 + rmax * (1 - (1 - k) ** 2.2)
    a = int(230 * (1 - k) ** 1.5 * sstep(cl(dt / 0.17)))   # 5-frame eased fade-in: no luma step on the hit frame
    wd = max(2, int(26 * (1 - k)))
    ring = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ring)
    d.ellipse([cx - r, cy - r * .45, cx + r, cy + r * .45], outline=col + (a,), width=wd)
    ring = ring.filter(ImageFilter.GaussianBlur(3 + 10 * k))
    layer.alpha_composite(ring)


def dust_puff(layer, t, t_hit, cx, cy, n=18, seed=3, col=(214, 200, 176)):
    dt = t - t_hit
    if dt < 0 or dt > 0.9:
        return
    rnd = np.random.default_rng(seed)
    puff = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(puff)
    for i in range(n):
        ang = rnd.uniform(-math.pi * .95, -math.pi * .05)
        v = rnd.uniform(200, 520)
        x = cx + math.cos(ang) * v * dt * (1 - .4 * dt) * 1.6
        y = cy + math.sin(ang) * v * dt * (1 - .4 * dt) * .5 + 160 * dt * dt
        r = 14 + 60 * dt
        a = int(130 * (1 - dt / .9) * sstep(cl(dt / 0.17)))
        d.ellipse([x - r, y - r * .6, x + r, y + r * .6], fill=col + (a,))
    layer.alpha_composite(puff.filter(ImageFilter.GaussianBlur(10)))


def speed_streaks(t, speed=2800.0, n=90, seed=13, alpha=120):
    """horizontal light streaks (night drive), scrolling right-to-left."""
    key = 'streak'
    if key not in _TEX:
        rnd = np.random.default_rng(seed)
        tex = Image.new('RGBA', (2 * W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(tex)
        for _ in range(n):
            x0 = rnd.uniform(0, 2 * W); y0 = rnd.uniform(380, 1250)
            ln = rnd.uniform(160, 520); wd = int(rnd.integers(2, 6))
            col = (255, 230, 170) if rnd.random() < .55 else (160, 210, 255)
            d.line([(x0, y0), (x0 + ln, y0)], fill=col + (int(rnd.integers(60, alpha)),), width=wd)
        _TEX[key] = tex.filter(ImageFilter.GaussianBlur(1.6))
    tex = _TEX[key]
    off = int((t * speed) % W)
    return tex.crop((off, 0, off + W, H))


def light_cone(layer, x0, y0, length=900, spread=230, col=(255, 240, 200), a=70):
    cone = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(cone)
    d.polygon([(x0, y0 - 10), (x0 + length, y0 - spread), (x0 + length, y0 + spread * .6), (x0, y0 + 12)], fill=col + (a,))
    layer.alpha_composite(cone.filter(ImageFilter.GaussianBlur(18)))


def god_rays(layer, t, cx, cy, col=(255, 226, 150), n=9, a=38, spin=0.08, length=2200):
    rays = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(rays)
    for i in range(n):
        ang = -math.pi / 2 + (i - n / 2) * 0.23 + math.sin(t * .7 + i) * .03 + t * spin
        wdt = 0.035 + 0.02 * math.sin(t * 1.3 + i * 2)
        d.polygon([(cx, cy), (cx + length * math.cos(ang - wdt), cy + length * math.sin(ang - wdt)),
                   (cx + length * math.cos(ang + wdt), cy + length * math.sin(ang + wdt))], fill=col + (a,))
    layer.alpha_composite(rays.filter(ImageFilter.GaussianBlur(14)))


def breath_fog(layer, t, x, y, seed=4):
    rnd = np.random.default_rng(seed)
    fog = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fog)
    for i in range(3):
        ph = (t * .55 + i / 3.0) % 1.0
        r = 18 + 70 * ph
        a = int(70 * math.sin(math.pi * ph))
        d.ellipse([x - 40 * ph - r, y - 30 * ph - r * .7, x - 40 * ph + r, y - 30 * ph + r * .7], fill=(220, 230, 240, a))
    layer.alpha_composite(fog.filter(ImageFilter.GaussianBlur(12)))


# ───────────────────────────────────────────── kinetic slam title (hook) and the end stamp
def _font(sz, wt=800):
    f = ImageFont.truetype('/home/user/fonts/Montserrat-VF.ttf', sz)
    try:
        f.set_variation_by_axes([wt])
    except Exception:
        pass
    return f


def _text_sprite(txt, sz, col, wt=800, extrude=10, shadow=True):
    f = _font(sz, wt)
    bb = f.getbbox(txt, anchor='ls')
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    pad = extrude + 24
    im = Image.new('RGBA', (tw + 2 * pad, th + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ox, oy = pad - bb[0], pad - bb[1]
    if shadow:
        d.text((ox + 6, oy + 14), txt, font=f, fill=(10, 6, 16, 150), anchor='ls')
    for k in range(extrude, 0, -1):
        sh = 0.45 + 0.4 * (1 - k / extrude)
        d.text((ox + k * .8, oy + k), txt, font=f, fill=tuple(int(c * sh * .5) for c in col) + (255,), anchor='ls')
    d.text((ox, oy), txt, font=f, fill=col + (255,), anchor='ls')
    d.text((ox - 1, oy - 2), txt, font=f, fill=(255, 255, 255, 70), anchor='ls')
    return im


def slam_words(layer, words, cols, t, t0, y, gap=0.16, sz=132, max_w=900):
    """each word slams from 2.2x to 1x (overshoot) with a 4-frame fade so the luma ramps, not steps."""
    f = _font(sz, 800)
    sp = f.getlength(' ')
    wid = [f.getlength(w) for w in words]
    tot = sum(wid) + sp * (len(words) - 1)
    if tot > max_w:                                   # fit the whole line inside the safe width
        sz = int(sz * max_w / tot)
        f = _font(sz, 800)
        sp = f.getlength(' ')
        wid = [f.getlength(w) for w in words]
        tot = sum(wid) + sp * (len(words) - 1)
    x = 540 - tot / 2
    for i, (w, ww) in enumerate(zip(words, wid)):
        d = t - (t0 + i * gap)
        if d >= 0:
            k = cl(d / .22)
            s = 2.2 - 1.2 * (1 - (1 - k) ** 3)
            over = 1 - .10 * math.sin(math.pi * cl((d - .22) / .20)) if d > .22 else 1.0
            s *= over
            a = cl(d / .13)
            spr = _text_sprite(w, sz, cols[i])
            if abs(s - 1) > 1e-3:
                spr = spr.resize((max(2, int(spr.width * s)), max(2, int(spr.height * s))), Image.BILINEAR)
            if a < 1:
                al = spr.getchannel('A').point(lambda v: int(v * a))
                spr.putalpha(al)
            cx = x + ww / 2
            layer.alpha_composite(spr, (int(cx - spr.width / 2), int(y - spr.height / 2)))
        x += ww + sp


def crown_icon(layer, cx, cy, s=1.0, col=(226, 176, 84)):
    d = ImageDraw.Draw(layer, 'RGBA')
    pts = [(-120, 40), (-120, -40), (-60, 10), (0, -80), (60, 10), (120, -40), (120, 40)]
    pts = [(cx + px * s, cy + py * s) for px, py in pts]
    d.polygon(pts, fill=col + (255,), outline=(30, 24, 34, 255))
    d.rectangle([cx - 120 * s, cy + 40 * s, cx + 120 * s, cy + 66 * s], fill=(255, 226, 150, 255), outline=(30, 24, 34, 255), width=3)
    for px in (-120, 0, 120):
        d.ellipse([cx + px * s - 14 * s, cy - 40 * s - 14 * s - (40 * s if px == 0 else 0), cx + px * s + 14 * s, cy - 40 * s + 14 * s - (40 * s if px == 0 else 0)], fill=(255, 240, 200, 255), outline=(30, 24, 34, 255), width=2)


def end_stamp(layer, t, t_hit, y=900):
    """final card: crown drops, 'AMEER KA KUTTA.' slams, 'insaan ya janwar?' fades under it."""
    d = t - t_hit
    if d < 0:
        return
    k = cl(d / .30)
    s = 1.9 - .9 * (1 - (1 - k) ** 3)
    s *= 1 - .08 * math.sin(math.pi * cl((d - .30) / .22)) if d > .30 else 1.0
    a = cl(d / .13)
    plate = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plate, 'RGBA')
    pd.rounded_rectangle([90, y - 150, W - 90, y + 150], 40, fill=(12, 8, 18, 215), outline=(226, 176, 84, 230), width=4)
    pd.rounded_rectangle([110, y - 130, W - 110, y + 130], 30, outline=(255, 255, 255, 40), width=2)
    sz = 108
    while _font(sz, 800).getlength('AMEER KA KUTTA.') > 800 and sz > 40:
        sz -= 4
    spr = _text_sprite('AMEER KA KUTTA.', sz, (248, 244, 233), extrude=12)
    plate.alpha_composite(spr, (int(540 - spr.width / 2), int(y - 30 - spr.height / 2)))
    crown_icon(plate, 540, y - 190, .55)
    f = _font(44, 600)
    k2 = cl((d - .45) / .3)
    if k2 > 0:
        pd.text((540, y + 82), 'insaan ya janwar?', font=f, fill=(226, 176, 84, int(255 * k2)), anchor='mm')
    if abs(s - 1) > 1e-3:
        plate = plate.resize((max(2, int(W * s)), max(2, int(H * s))), Image.BILINEAR)
    if a < 1:
        plate.putalpha(plate.getchannel('A').point(lambda v: int(v * a)))
    layer.alpha_composite(plate, (int((W - plate.width) / 2), int((H - plate.height) / 2)))
