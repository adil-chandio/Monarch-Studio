#!/usr/bin/env python3
"""
film_window.py — WF-03 · Monarch Noir Film · film #2 "THE WINDOW" (topic COMPARISON) — NOIRGO MAX
Timeline + renderer (2026-10-10, turn 21). 1920×1080 · 24 fps · ≈155 s · full English VO (voice-03, 10 clips).

World  : illustrated real-life plates (plates/raw_*.png) through a crop camera (push / drift), per-window light control,
         rain, dust, practical glows.                                                   (world.py)
Hero   : the 3-D human stick figure, ray-cast per frame — face, five-finger hands, feet, props (phone, plate, sponge,
         ice pack, papers), IK on real objects, physically placed point lights.           (stick3d.py + human.py)
Grammar: holds carried by the voice + one light change or one gaze each, hard cuts on phrase starts, dips only around
         cards, a 6-cut flurry for "every night this year", red villain lines answered in white, DAY counter, 2 end cards.

CLI:  python3 film_window.py --events data/events_window.json            # write the timeline (cuts, text, light, VO)
      python3 film_window.py --still 83.9 out.jpg                        # one finished frame
      python3 film_window.py --sheet                                     # look sheet v2 (12 frames + metrics)
      python3 film_window.py --render seg.mp4 --shots 0-11               # render a shot range to an mp4 segment
      python3 film_window.py --bench                                     # per-shot frame cost
"""
import os, sys, math, json, time, argparse, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import world as Wd        # noqa: E402
import human as Hm        # noqa: E402
import stick3d as S       # noqa: E402

W, H, FPS = 1920, 1080, 24
BUILD = os.path.join(Wd.ROOT, 'build', 'wf03_window')
DATA = os.path.join(Wd.WF, 'data')
os.makedirs(BUILD, exist_ok=True)
os.makedirs(DATA, exist_ok=True)

# ─────────────────────────────────────────────── voice: clip start times (absolute, seconds)
VO = {'vo01': 1.2, 'vo02': 20.6, 'vo03': 38.4, 'vo04': 46.8, 'vo05': 51.8,
      'vo06': 59.1, 'vo07': 69.6, 'vo08': 89.6, 'vo09': 104.0, 'vo10': 124.2}

BLUE_L = (0.55, 0.72, 1.0)        # phone / TV light
COLD_L = (0.55, 0.70, 1.0)        # window light
AMBER_L = (1.0, 0.78, 0.50)       # the lamp
DAWN_L = (0.72, 0.76, 0.86)
EVENTS = dict(text=[], light=[], sfx=[], counter=[])
_recorded = set()


def rec(cat, t, **kw):
    """record a timeline event once (text reveals, light changes, sfx cues) for events.json / the audio build."""
    key = (cat, round(t, 3), kw.get('txt', ''), kw.get('what', ''))
    if key in _recorded:
        return
    _recorded.add(key)
    EVENTS[cat].append(dict(t=round(t, 3), **kw))


def ease(t):
    return Hm.ease(t)


def eq(t):
    return Hm.ease_q(t)


def clamp01(v):
    return min(1.0, max(0.0, v))


# ─────────────────────────────────────────────── camera (plate crop) with coordinate mapping
class Cam:
    """plate crop camera. Either (zoom, cx, cy, dx, dy) — clamped to the plate — or an explicit rect=(x0, y0, cw).
    Moves are built with cam_lerp(): both end cameras are clamped first, the RECT is interpolated, so a move can never
    hit the clamp mid-way (a clamp release/engage is a velocity step = a visible hitch)."""
    def __init__(self, zoom=1.0, cx=0.5, cy=0.5, dx=0.0, dy=0.0, rect=None):
        if rect is not None:
            x0, y0, cw = rect
            self.cw, self.ch = float(cw), float(cw) * H / W
            self.zoom = W / self.cw
            self.x0, self.y0 = float(x0), float(y0)
            self.cx, self.cy, self.dx, self.dy = (self.x0 + self.cw / 2) / W, (self.y0 + self.ch / 2) / H, 0.0, 0.0
            return
        self.zoom, self.cx, self.cy, self.dx, self.dy = zoom, cx, cy, dx, dy
        cw, ch = W / zoom, H / zoom
        self.cw, self.ch = cw, ch
        self.x0 = min(max(0.0, cx * W - cw / 2 + dx), W - cw)
        self.y0 = min(max(0.0, cy * H - ch / 2 + dy), H - ch)

    def shoot(self, arr):
        if self.zoom <= 1.0001 and abs(self.x0) < 0.01 and abs(self.y0) < 0.01:
            return arr
        im = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
        im = im.resize((W, H), Image.BICUBIC, box=(self.x0, self.y0, self.x0 + self.cw, self.y0 + self.ch))
        return np.asarray(im, np.float32)

    def map(self, px, py):
        return ((px - self.x0) * self.zoom, (py - self.y0) * self.zoom)

    def rect(self, r):
        a = self.map(r[0], r[1]); b = self.map(r[2], r[3])
        return (int(a[0]), int(a[1]), int(b[0]), int(b[1]))


def cam_lerp(c0, c1, u):
    """eased move between two (already clamped) cameras — interpolates the crop rect, C1-smooth, never clamps mid-move"""
    e = ease(u)
    return Cam(rect=(c0.x0 + (c1.x0 - c0.x0) * e, c0.y0 + (c1.y0 - c0.y0) * e, c0.cw + (c1.cw - c0.cw) * e))


def push(z0, z1, u):
    return z0 + (z1 - z0) * ease(u)


# ─────────────────────────────────────────────── hero rendering helpers
def person_frame(layer, x, y, s, pose, lights, clip=None, SS=2, **kw):
    """Render the figure into a frame-scale RGBA layer through a frame-sized SS canvas (safe for big figures)."""
    can = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0))
    L = S._scale_lights(lights, 0, 0, SS)
    c = None if clip is None else tuple(v * SS for v in clip)
    J, ex = S.render(can, x * SS, y * SS, s * SS, pose, L, clip=c, **kw)
    bb = can.getbbox()
    if bb:
        x0, y0, x1, y1 = bb
        x0 -= x0 % SS; y0 -= y0 % SS; x1 += (-x1) % SS; y1 += (-y1) % SS
        x1 = min(x1, W * SS); y1 = min(y1, H * SS)
        crop = can.crop((x0, y0, x1, y1))
        if SS > 1:
            crop = crop.resize(((x1 - x0) // SS, (y1 - y0) // SS), Image.LANCZOS)
        layer.alpha_composite(crop, dest=(x0 // SS, y0 // SS))
    Jf = {k: (v[0] / SS, v[1] / SS) for k, v in J.items()}
    hc, hr = ex['head']
    ex['head'] = ((hc[0] / SS, hc[1] / SS), hr / SS)
    return Jf, ex


def hero(layer, cam, px, py, s, pose, lights, clip=None, **kw):
    """3-D hero anchored at plate-frame point (px, py) with plate-scale s, seen through `cam`."""
    x, y = cam.map(px, py)
    ss = s * cam.zoom
    SS = 2 if ss <= 1100 else 1
    return person_frame(layer, x, y, ss, pose, lights, clip=clip, SS=SS, **kw)


def silhouette(layer, x, y, s, pose, clip=None, **kw):
    """a dark 3-D person inside a window (frame px)."""
    L = S.light_rig()
    return S.person(layer, x, y, s, pose, L, clip=clip, silhouette=True, ink=0.0, ao=0.0, **kw)


def lights_from(cam, x, y, s, key_pt, key_col, key_int, **kw):
    """scene lights for a figure at frame (x, y, s) keyed by a practical at plate-frame point key_pt."""
    kp = cam.map(*key_pt) if cam is not None else key_pt
    return S.scene_lights(x, y, s, kp, key_col=key_col, key_int=key_int, **kw)


def face_closeup(bg, t, s, expr, look, blink_v, lights, head_t=0.0, head=0.0, focus_off=(0.0, 0.03), alpha=1.0, blur=0.0):
    """full-frame close-up of the hero's face (SS=1 — thin features are ≥ 8 px at this scale)."""
    can = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    pose = dict(Hm.p_stand(t), head_t=head_t, head=head)
    S.render_window(can, (0, 0, W, H), s, pose, lights, focus='hctr', focus_off=focus_off, expr=expr, look=look,
                    blink_v=blink_v, alpha=alpha)
    if blur > 0:
        can = can.filter(ImageFilter.GaussianBlur(blur))
    return Wd.composite(bg, can)


def phone_face_lights(s, fl, extra_rim=0.5):
    """phone-POV lighting: a blue point light where the phone is (in front of the face), faint cold rim from the window."""
    K3, _, _ = S.solve(0, 0, s, Hm.p_stand(0.0))
    hc = K3['hctr']
    pos = hc + np.array([0.02 * s, 0.03 * s, 0.33 * s])
    return S.light_rig(key_dir=(0.0, -0.4, 0.9), key_col=(0.4, 0.5, 0.8), key_int=0.10,
                       fill_dir=(0.6, -0.2, 0.75), fill_col=(0.3, 0.4, 0.6), fill_int=0.06,
                       rim_dir=(0.45, -0.5, -0.74), rim_col=(0.35, 0.45, 0.7), rim_int=extra_rim,
                       sky=(0.03, 0.04, 0.07), ground=(0.012, 0.012, 0.018),
                       points=[S.point_light(pos, BLUE_L, 1.7 * (0.75 + 0.25 * fl), 0.30 * s)])


def saccade(t, seed, base=(0.1, 0.18), amp=(0.22, 0.14), period=0.75):
    """gaze that jumps (reads a feed): a new fixation every ~period s, deterministic."""
    k = int(t / period)
    rng = np.random.default_rng(seed * 1000 + k)
    rng2 = np.random.default_rng(seed * 1000 + k - 1)
    a = (base[0] + (rng2.random() - 0.5) * amp[0] * 2, base[1] + (rng2.random() - 0.5) * amp[1] * 2)
    b = (base[0] + (rng.random() - 0.5) * amp[0] * 2, base[1] + (rng.random() - 0.5) * amp[1] * 2)
    u = clamp01((t - k * period) / 0.08)      # the jump itself takes 80 ms
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)


# ─────────────────────────────────────────────── text helpers
def readout(txt, t_on, layer, t, x=64, y=48, size=30, record=True):
    if t < t_on:
        return
    shown = Wd.typewriter(txt, t, t_on, cps=22.0)
    if shown:
        Wd.readout(layer, shown, x, y, size)
    if record:
        rec('text', t_on, kind='readout', txt=txt, cps=22.0)


def villain_line(txt, t_on, layer, t, x=110, y=930, size=44, col=None, record=True):
    if t < t_on:
        return
    shown = Wd.typewriter(txt, t, t_on, cps=16.0)
    if shown:
        Wd.villain(layer, shown, x, y, size, col=col or Wd.RED)
    if record:
        rec('text', t_on, kind='villain' if col is None else 'answer', txt=txt, cps=16.0)


def narration_fade(txt, t_on, layer, t, cy=960, size=46, italic=False, fade=0.6, t_off=None, record=True):
    if t < t_on:
        return
    a = ease((t - t_on) / fade)
    if t_off is not None and t > t_off - fade:
        a *= ease((t_off - t) / fade)
    if a <= 0:
        return
    Wd.narration(layer, txt, W / 2, cy, size, italic=italic, alpha=int(255 * a))
    if record:
        rec('text', t_on, kind='narration', txt=txt, cps=0)


def card(txt, t, t0, t1, size=64, italic=False, fade=0.5, caps_tracking=False, glyph=None):
    """serif card on black with fade in/out; glyph = ('blue'|'amber') draws the small window above the text."""
    f = np.zeros((H, W, 3), np.float32) + np.array([5, 5, 7], np.float32)
    a = ease((t - t0) / fade) * ease((t1 - t) / fade)
    if a <= 0:
        return f
    layer = Wd.text_layer()
    if glyph:
        col = (120, 170, 255) if glyph == 'blue' else (255, 196, 128)
        d = ImageDraw.Draw(layer)
        gx, gy, gw, gh = W / 2, 430, 30, 42
        d.rounded_rectangle([gx - gw / 2, gy - gh / 2, gx + gw / 2, gy + gh / 2], radius=3, fill=col + (int(255 * a),))
        d.line([(gx, gy - gh / 2), (gx, gy + gh / 2)], fill=(12, 12, 14, int(255 * a)), width=2)
        d.line([(gx - gw / 2, gy), (gx + gw / 2, gy)], fill=(12, 12, 14, int(255 * a)), width=2)
        f = Wd.glow(f, (gx, gy), 180, np.array(col, np.float32), power=0.22 * a, falloff=2.2)
    Wd.narration(layer, txt, W / 2, 560 if glyph else 540, size, italic=italic, alpha=int(255 * a))
    return Wd.composite(f, layer)


# ─────────────────────────────────────────────── world helpers
_wmask = {}


def windows_mask():
    if 'm' not in _wmask:
        m = np.zeros((H, W), np.float32)
        for w in Wd.windows():
            m = np.maximum(m, Wd._soft_rect_mask(w['rect'], 2))
        _wmask['m'] = m[..., None]
    return _wmask['m']


def facade(t, cam, rain_a=0.14, flick=True, dawn=0.0, emphasis=0.0, win_gain=1.0):
    f = Wd.plate('facade_night')
    if win_gain != 1.0 or emphasis > 0:
        M = windows_mask()
        f = f * (1 - M) * (1 - 0.3 * emphasis) + f * M * win_gain * (1 + 0.35 * emphasis)
    f = cam.shoot(f)
    if flick:
        for w in Wd.windows():
            if w['kind'] == 'blue':
                r = cam.rect(w['rect'])
                if r[2] > 0 and r[0] < W and r[3] > 0 and r[1] < H:
                    f = Wd.window_gain(f, r, Wd.flicker(t, 7 + hash(w['id']) % 5, rate=6, depth=0.3))
    if dawn > 0:
        f = Wd.grade(f, warm=0.3 * dawn, lift=0.07 * dawn, sat=0.92)
    if rain_a > 0:
        f = Wd.rain(f, t, density=170, alpha=rain_a)
    return f


def own_window(t, cam, state='blue', k=1.0, rain_a=0.15, dawn=0.0):
    """facade_hero with the hero's window blue (flicker) / dark / amber; k = transition 0..1 toward `state`."""
    base = Wd.plate('facade_hero') if state == 'blue' else Wd.facade_hero_dark()
    f = base.copy() if state != 'blue' else base
    x0, y0, x1, y1 = Wd.HERO_WIN
    c = ((x0 + x1) / 2, (y0 + y1) / 2)
    if state == 'blue':
        fl = Wd.flicker(t, 11, rate=7, depth=0.4) * k
        f = Wd.window_gain(f, Wd.HERO_WIN, 0.7 + 0.5 * fl)
        f = Wd.glow(f, c, 260, Wd.BLUE, power=0.22 * fl, falloff=2.5)
    elif state == 'amber':
        fl = Wd.lamp_flicker(t) * k
        m = Wd._soft_rect_mask((x0 + 6, y0 + 6, x1 - 6, y1 - 6), 3)[..., None]
        f = f * (1 - m) + (f * 0.3 + np.array([232, 178, 110], np.float32) * 0.85 * fl + f * 0.7 * (1 - k)) * m
        f = Wd.glow(f, c, 300, Wd.AMBER, power=0.26 * fl, falloff=2.4)
    f = cam.shoot(f)
    if dawn > 0:
        f = Wd.grade(f, warm=0.25 * dawn, lift=0.06 * dawn, sat=0.92)
    if rain_a > 0:
        f = Wd.rain(f, t, density=180, alpha=rain_a)
    return f


def window_people(layer, cam, t, specs):
    """small standing silhouettes inside facade windows. specs: list of (window id, t_on, seed)."""
    for wid, t_on, seed in specs:
        if t < t_on:
            continue
        w = Wd.win_by_id(wid)
        r = cam.rect(w['rect'])
        if r[2] < 0 or r[0] > W or r[3] < 0 or r[1] > H:
            continue
        h = r[3] - r[1]
        s = h * 1.4
        x = (r[0] + r[2]) / 2 + (seed % 3 - 1) * h * 0.1
        y = r[3] + h * 0.42
        pose = dict(Hm.p_stand(t + seed, 0.2 * (seed % 2 * 2 - 1)), yaw=(seed * 37) % 40 - 20)
        a = ease((t - t_on) / 0.4)
        if a < 1:
            pose['bob'] = 0.0
        silhouette(layer, x, y, s, pose, clip=r)


def bedroom_dark(cam, k=1.0):
    """the bedroom at night without the phone: plate × (0.55..1) with the window kept bright."""
    f = Wd.plate('bedroom_night')
    return cam.shoot(f) * (1.0 - 0.45 * k)


# ─────────────────────────────────────────────── bed (sit) composition — verified placement (turn 20)
def bed_sit(t, lift=0.0, phone_on=1.0, zoom=1.45, slump=0.75, look=(0.1, 0.7), expr='tired', blink_seed=11,
            head_drop=0.0, rd=None, tt=0.0):
    cam = Cam(zoom, 0.40, 0.62)
    f = cam.shoot(Wd.plate('bedroom_night')) * 0.55
    x, y, s = 930 * zoom / 1.45, 735 * zoom / 1.45, 700 * zoom / 1.45
    pose = dict(Hm.p_sit(t, slump - 0.3 * lift), yaw=-12, head=10 - 8 * lift + 12 * head_drop,
                head_t=6 - 10 * lift, ll=-5, lr=5, kl=98, kr=94, lz_l=72, lz_r=70)
    pose = S.reach(pose, 'r', (x + 5, y - 123 - 20 * lift), x, y, s, anchor='hip')
    pose = S.reach(pose, 'l', (x + 70, y), x, y, s, anchor='hip')
    pose['hw_r'] = 85
    K3, J, fr = S.solve(x, y, s, pose, anchor='hip')
    phone_pos = K3['har'] + np.array([0.0, -0.03 * s, 0.07 * s])
    fl = Wd.flicker(t, 3) * phone_on
    S.MATS['screen']['emit'] = 0.85 * phone_on
    L = S.scene_lights(x, y, s, cam.map(960, 330), key_col=COLD_L, key_int=0.30, key_z=-0.6,
                       fill_col=(0.2, 0.25, 0.35), fill_int=0.10, rim_dir=(0.0, -0.4, -0.9), rim_col=(0.45, 0.58, 0.85),
                       rim_int=0.55, sky=(0.05, 0.06, 0.10), ground=(0.02, 0.02, 0.03),
                       points=[S.point_light(phone_pos, BLUE_L, 2.2 * (0.8 + 0.2 * fl) * phone_on, 0.22 * s)])
    layer = Wd.text_layer()
    e = Hm.expr_mix(expr, 'doubt', lift) if isinstance(expr, str) else expr
    S.person(layer, x, y, s, pose, L, hands=('relax', 'phone'), props=[dict(kind='phone', hand='r')], expr=e,
             look=(look[0] - 0.3 * lift, look[1] - 0.6 * lift), anchor='hip', blink_v=Hm.blink(t, seed=blink_seed))
    S.MATS['screen']['emit'] = 0.85
    if phone_on > 0:
        f = Wd.glow(f, (J['har'][0], J['har'][1] - 20), 520, Wd.BLUE, power=0.55 * fl, falloff=2.2)
    f = Wd.composite(f, layer)
    return f, cam


# ─────────────────────────────────────────────── desk amber composition — verified placement (turn 20)
def desk_amber(t, lamp_on=1.0, head_turn=0.0, expr='calm', look=(0.5, 0.35), typing=1.0, dust_on=1.0):
    cam = Cam(1.5, 0.74, 0.60)
    fa = cam.shoot(Wd.plate('bedroom_amber'))
    if lamp_on < 1.0:
        fn = cam.shoot(Wd.plate('bedroom_night')) * 0.6
        f = fn * (1 - lamp_on) + fa * lamp_on
    else:
        f = fa
    lamp = (1430, 370)
    fl = Wd.lamp_flicker(t) * lamp_on
    if lamp_on > 0:
        f = Wd.glow(f, lamp, 520, Wd.AMBER, power=0.10 * fl, falloff=2.0)
    x, y, s = 1175, 868, 725
    wob = 0.012 * math.sin(t * 11.0) * typing
    pose = dict(Hm.p_sit(t, 0.1), yaw=84 - 30 * head_turn, lean=14 - 4 * head_turn, head=-4,
                head_t=-24 + 70 * head_turn, lz_l=84, lz_r=80, kl=92, kr=88)
    pose = S.reach(pose, 'l', (1395, 655 + 6 * math.sin(t * 9.0) * typing), x, y, s, anchor='hip')
    pose = S.reach(pose, 'r', (1415 + 8 * math.sin(t * 7.3) * typing, 668 - 5 * math.cos(t * 9.0) * typing), x, y, s, anchor='hip')
    pose['sh_up'] = wob
    L = S.scene_lights(x, y, s, lamp, key_col=AMBER_L, key_int=1.15 * fl + 0.02, key_z=0.3,
                       fill_col=(0.25, 0.3, 0.45), fill_int=0.12 + 0.1 * (1 - lamp_on), rim_dir=(-0.5, -0.4, -0.75),
                       rim_col=(0.5, 0.6, 0.9), rim_int=0.3 + 0.3 * (1 - lamp_on),
                       sky=(0.08, 0.08, 0.11), ground=(0.05, 0.035, 0.02))
    layer = Wd.text_layer()
    S.person(layer, x, y, s, pose, L, hands=('relax', 'grip'), expr=expr, look=look, anchor='hip',
             blink_v=Hm.blink(t, seed=21))
    f = Wd.composite(f, layer)
    if lamp_on > 0 and dust_on > 0:
        f = Wd.dust(f, t, lamp, 380, n=70, alpha=0.5 * lamp_on * dust_on)
    return f, cam


# ═══════════════════════════════════════════════ SHOTS  (fn(tl, t) → float32 frame before finish)
def s01_face(tl, t):
    s = 4700 + 140 * ease(tl / 3.4)
    fl = Wd.flicker(t, 3, rate=8, depth=0.3)
    if t > 4.6:
        fl *= 1.25
    cam = Cam(2.2, 0.22, 0.62)
    bg = cam.shoot(Wd.plate('bedroom_night'))
    bg = np.asarray(Image.fromarray(bg.astype(np.uint8)).filter(ImageFilter.GaussianBlur(4)), np.float32) * 0.35
    bg = Wd.glow(bg, (W / 2, H * 0.55), 900, Wd.BLUE, power=0.42 * fl, falloff=2.2)
    L = phone_face_lights(s, fl)
    look = saccade(t, 1)
    f = face_closeup(bg, t, s, 'tired', look, Hm.blink(t, 5), L, head_t=0.0, head=1.5 * math.sin(t * 0.6), focus_off=(0.0, 0.0))
    txt = Wd.text_layer()
    readout('11:48 PM', 1.4, txt, t)
    f = Wd.composite(f, txt)
    return Wd.grade(f, cold=0.5, sat=0.9)


def s02_bed_wide(tl, t):
    cam = cam_lerp(Cam(1.0, 0.42, 0.62), Cam(1.05, 0.42, 0.62), tl / 3.2)
    f = bedroom_dark(cam, 1.0)
    # the hero lying on the bed, phone above the face (side view: yaw 90 then rolled −90 about the hip)
    hx, hy, hs = 700, 688, 640
    pose = dict(Hm.p_phone_bed(t), yaw=90, az_l=118 + 3 * math.sin(t * 0.9), az_r=122 + 3 * math.sin(t * 0.9 + 1),
                head_t=-6)
    pose['hw_r'] = 70
    x, y = cam.map(hx, hy)
    s = hs * cam.zoom
    K3, J, fr = S.solve(x, y, s, pose, rot=-90, anchor='hip')
    phone_pos = 0.5 * (K3['har'] + K3['hctr']) + np.array([0.0, 0.0, 0.04 * s])
    fl = Wd.flicker(t, 3)
    L = S.scene_lights(x, y, s, cam.map(960, 330), key_col=COLD_L, key_int=0.25, key_z=-0.5,
                       fill_col=(0.2, 0.25, 0.35), fill_int=0.08, rim_dir=(0.0, -0.4, -0.9), rim_col=(0.45, 0.58, 0.85),
                       rim_int=0.5, sky=(0.05, 0.06, 0.10), ground=(0.02, 0.02, 0.03),
                       points=[S.point_light(phone_pos, BLUE_L, 2.4 * (0.8 + 0.2 * fl), 0.26 * s)])
    layer = Wd.text_layer()
    person_frame(layer, x, y, s, pose, L, SS=2, hands=('relax', 'phone'), props=[dict(kind='phone', hand='r')],
                 expr='tired', look=saccade(t, 2, base=(0.0, -0.1)), rot=-90, anchor='hip', blink_v=Hm.blink(t, 5))
    px = 0.5 * (J['har'][0] + J['hctr'][0]); py = 0.5 * (J['har'][1] + J['hctr'][1])
    f = Wd.glow(f, (px, py), 460, Wd.BLUE, power=0.5 * fl, falloff=2.2)
    f = Wd.glow(f, (px, py - 300), 700, Wd.BLUE, power=0.12 * fl, falloff=2.0)   # ceiling spill
    # the blanket covers his legs: re-composite the plate's blanket region over the figure with a soft mask
    bl = Wd._soft_rect_mask(cam.rect((600, 600, 1040, 790)), 14)[..., None]
    fig = Wd.composite(f, layer)
    f = fig * (1 - bl) + f * bl
    txt = Wd.text_layer()
    readout('11:48 PM', 1.4, txt, t)
    f = Wd.composite(f, txt)
    return Wd.grade(f, cold=0.5, sat=0.9)


def s03_facade_count(tl, t):
    cam = cam_lerp(Cam(1.04, 0.5, 0.48, dx=math.sin(t * 0.3) * 4), Cam(1.08, 0.5, 0.48, dx=math.sin(t * 0.3) * 4), tl / 3.1)
    f = facade(t, cam)
    txt = Wd.text_layer()
    readout('11:48 PM', 1.4, txt, t)
    n = int(round(31 * ease((t - 7.0) / 1.5)))
    if t >= 7.0:
        Wd.readout(txt, f"{n} WINDOWS LIT", 64, H - 92, size=28, alpha=190)
        rec('counter', 7.0, what='windows', n0=0, n1=31, dur=1.5)
    return Wd.grade(Wd.composite(f, txt), cold=0.35, sat=0.92)


def s04_facade_drift(tl, t):
    u = tl / 2.9
    cam = cam_lerp(Cam(1.28, 0.36, 0.47), Cam(1.28, 0.62, 0.47), u)
    f = facade(t, cam)
    layer = Wd.text_layer()
    window_people(layer, cam, t, [('C6', 0, 1), ('G5', 0, 2), ('E4', 0, 3), ('H3', 0, 4), ('I2', 0, 5)])
    f = Wd.composite(f, layer)
    txt = Wd.text_layer()
    readout('11:48 PM', 1.4, txt, t)
    return Wd.grade(Wd.composite(f, txt), cold=0.35, sat=0.92)


def s05_own_window(tl, t):
    u = clamp01((t - 14.6) / 1.8)
    x0, y0, x1, y1 = Wd.HERO_WIN
    cam = cam_lerp(Cam(1.0, (x0 + x1) / 2 / W, (y0 + y1) / 2 / H), Cam(1.7, (x0 + x1) / 2 / W, (y0 + y1) / 2 / H), u)
    f = own_window(t, cam, 'blue')
    txt = Wd.text_layer()
    readout('11:48 PM', 1.4, txt, t)
    return Wd.grade(Wd.composite(f, txt), cold=0.45, sat=0.9)


def s06_title(tl, t):
    rec('text', 16.9, kind='title', txt='THE WINDOW', cps=0)
    return card('THE WINDOW', t, 16.9, 20.0, size=96, glyph='blue')


def facade_push(tl, t, wid, dur, clock, t_clock):
    w = Wd.win_by_id(wid)
    r = w['rect']
    cam = cam_lerp(Cam(1.1, (r[0] + r[2]) / 2 / W, (r[1] + r[3]) / 2 / H), Cam(2.6, (r[0] + r[2]) / 2 / W, (r[1] + r[3]) / 2 / H), tl / dur)
    f = facade(t, cam)
    txt = Wd.text_layer()
    readout(clock, t_clock, txt, t)
    return Wd.grade(Wd.composite(f, txt), cold=0.35, sat=0.92)


def s07_push_b4(tl, t):
    return facade_push(tl, t, 'B4', 2.9, '11:52 PM', 20.3)


def s08_runner(tl, t):
    cam = cam_lerp(Cam(1.08, 0.5, 0.52), Cam(1.14, 0.5, 0.52), tl / 4.2)
    f = cam.shoot(Wd.plate('runner_window'))
    layer = Wd.text_layer()
    clip = cam.rect((350, 100, 1600, 1000))
    u = clamp01((t - 25.3) / 0.8)           # arms come down to the phone at "He's already posted the run."
    x, y = cam.map(930, 985)
    s = 560 * cam.zoom
    pose = dict(Hm.p_stand(t, 0.3), yaw=-25, lz_l=26, lz_r=-18, kl=38, kr=6, lean=5 + 6 * u,
                az_l=168 - 110 * u, az_r=172 - 118 * u, ef_l=8 + 90 * u, ef_r=6 + 92 * u, al=-10, ar=10,
                head=-6 + 18 * u, head_t=0)
    pose['sway'] = 0.01 * math.sin(t * 1.3)
    _, J, _ = S.solve(x, y, s, pose)
    silhouette(layer, x, y, s, pose, clip=clip)
    f = Wd.composite(f, layer)
    if u > 0:
        hx = 0.5 * (J['hal'][0] + J['har'][0]); hy = 0.5 * (J['hal'][1] + J['har'][1])
        f = Wd.glow(f, (hx, hy), 110, Wd.BLUE, power=0.6 * u * Wd.flicker(t, 4, rate=7, depth=0.3), falloff=1.6)
    f = Wd.rain(f, t, density=120, alpha=0.10)
    txt = Wd.text_layer()
    readout('11:52 PM', 20.3, txt, t)
    villain_line("he's ahead.", 25.6, txt, t)
    return Wd.grade(Wd.composite(f, txt), warm=0.15, sat=0.95)


def s09_push_i3(tl, t):
    return facade_push(tl, t, 'I3', 2.3, '11:53 PM', 27.4)


def couple_kitchen(t, cam, mode='cook', dim=1.0):
    """the couple as 3-D silhouettes inside the kitchen window. mode: cook | plates | silence."""
    layer = Wd.text_layer()
    clip = cam.rect((300, 190, 1620, 890))
    if mode in ('cook', 'plates', 'dawn'):
        stir = math.sin(t * 5.0)
        x, y = cam.map(560, 900)
        p1 = dict(Hm.p_stand(t, 0.3), yaw=55, az_l=35, az_r=48 + 8 * stir, ef_l=80, ef_r=70 + 10 * stir, lean=6)
        silhouette(layer, x, y, 520 * cam.zoom, p1, clip=clip)
        up = ease((t - 32.3) / 0.6) if mode == 'plates' else 0.0
        x, y = cam.map(1220, 905)
        p2 = dict(Hm.p_stand(t + 1.0, -0.4), yaw=-45, az_l=10 + 40 * up, az_r=12 + 36 * up, ef_l=70, ef_r=10 + 60 * up, lean=2)
        silhouette(layer, x, y, 500 * cam.zoom, p2, clip=clip)
    else:  # silence: her at the table head down, him at the sink with his back turned
        x, y = cam.map(1180, 770)
        s2 = 470 * cam.zoom
        p2 = dict(Hm.p_sit(t, 0.5), yaw=-8, head=28, head_t=4, lean=16)
        p2 = S.reach(p2, 'l', (x - 60 * cam.zoom, y + 20 * cam.zoom), x, y, s2, anchor='hip')
        p2 = S.reach(p2, 'r', (x + 70 * cam.zoom, y + 24 * cam.zoom), x, y, s2, anchor='hip')
        silhouette(layer, x, y, s2, p2, clip=clip, anchor='hip')
        x, y = cam.map(700, 905)
        p1 = dict(Hm.p_stand(t + 2.0, 0.2), yaw=180, az_l=20, az_r=22, ef_l=60, ef_r=62, lean=8, head=12)
        silhouette(layer, x, y, 520 * cam.zoom, p1, clip=clip)
    return layer


def s10_couple(tl, t):
    cam = cam_lerp(Cam(1.10, 0.5, 0.52), Cam(1.16, 0.5, 0.52), tl / 3.7)
    f = cam.shoot(Wd.plate('kitchen_window'))
    f = Wd.composite(f, couple_kitchen(t, cam, 'plates'))
    f = Wd.rain(f, t, density=120, alpha=0.10)
    txt = Wd.text_layer()
    readout('11:53 PM', 27.4, txt, t)
    villain_line("they're happy.", 31.5, txt, t)
    return Wd.grade(Wd.composite(f, txt), warm=0.25, sat=0.95)


def s11_push_d5(tl, t):
    return facade_push(tl, t, 'D5', 2.0, '11:55 PM', 33.4)


def deskman(t, cam, look_up=0.0, glow_k=1.0):
    """the man with two monitors, seated with his back to us, typing; look_up turns him toward the window (us)."""
    layer = Wd.text_layer()
    clip = cam.rect((190, 150, 1560, 900))
    x, y = cam.map(1150, 700)
    s = 500 * cam.zoom
    typ = math.sin(t * 9.0)
    pose = dict(Hm.p_sit(t, 0.15), yaw=180 - 40 * look_up, head_t=-70 * look_up, head=-6 + 4 * look_up,
                lean=10 - 6 * look_up, az_l=52 + 3 * typ, az_r=50 - 3 * typ, ef_l=78 + 4 * typ, ef_r=80 - 4 * typ,
                al=-12, ar=12)
    silhouette(layer, x, y, s, pose, clip=clip, anchor='hip')
    return layer


def s12_deskman_work(tl, t):
    cam = cam_lerp(Cam(1.08, 0.44, 0.5), Cam(1.14, 0.44, 0.5), tl / 2.8)
    f = cam.shoot(Wd.plate('desk_window'))
    mon = cam.map(1000, 470)
    f = Wd.glow(f, mon, 300, Wd.BLUE, power=0.18 * Wd.flicker(t, 9, rate=5, depth=0.25), falloff=2.0)
    f = Wd.composite(f, deskman(t, cam))
    f = Wd.rain(f, t, density=120, alpha=0.10)
    txt = Wd.text_layer()
    readout('11:55 PM', 33.4, txt, t)
    villain_line("you're late.", 36.3, txt, t, x=1180)
    return Wd.grade(Wd.composite(f, txt), cold=0.45, sat=0.9)


def s13_bed_lookup(tl, t):
    lift = ease((t - 40.3) / 0.9)
    f, cam = bed_sit(t, lift=lift, zoom=push(1.45, 1.52, tl / 4.3))
    txt = Wd.text_layer()
    readout('11:58 PM', 38.2, txt, t)
    return Wd.grade(Wd.composite(f, txt), cold=0.55, sat=0.9)


MONT = [(42.4, '11:58 PM', 1), (43.0, '1:12 AM', 2), (43.6, '2:40 AM', 3)]
FLURRY = [('win', 'MON  11:48 PM'), ('face', 'TUE  12:31 AM'), ('bed', 'WED  1:12 AM'),
          ('win', 'THU  2:40 AM'), ('face', 'FRI  11:52 PM'), ('win', 'SAT  3:05 AM')]


def s14_montage(tl, t):
    """three 0.6 s cuts of his window (same frame, three nights) then the 6-cut flurry: every night this year."""
    x0, y0, x1, y1 = Wd.HERO_WIN
    if t < 44.2:
        i = min(2, int((t - 42.4) / 0.6))
        t_on, clock, seed = MONT[i]
        cam = Cam(2.0 + 0.15 * i, (x0 + x1) / 2 / W, (y0 + y1) / 2 / H)
        f = own_window(t + seed * 3.1, cam, 'blue')
        txt = Wd.text_layer()
        Wd.readout(txt, clock, 64, 48, 30)
        rec('text', t_on, kind='readout', txt=clock, cps=99)
        return Wd.grade(Wd.composite(f, txt), cold=0.45, sat=0.9)
    i = min(5, int((t - 44.2) / 0.25))
    kind, clock = FLURRY[i]
    t_on = 44.2 + 0.25 * i
    rec('text', t_on, kind='readout', txt=clock, cps=99)
    if kind == 'win':
        cam = Cam(2.3 + 0.1 * i, (x0 + x1) / 2 / W, (y0 + y1) / 2 / H)
        f = own_window(t + i * 2.7, cam, 'blue')
        f = Wd.grade(f, cold=0.45, sat=0.9)
    elif kind == 'face':
        s = 4500
        fl = Wd.flicker(t + i, 3, rate=8, depth=0.3)
        cam = Cam(2.2, 0.22, 0.62)
        bg = cam.shoot(Wd.plate('bedroom_night'))
        bg = np.asarray(Image.fromarray(bg.astype(np.uint8)).filter(ImageFilter.GaussianBlur(4)), np.float32) * 0.35
        bg = Wd.glow(bg, (W / 2, H * 0.55), 900, Wd.BLUE, power=0.42 * fl, falloff=2.2)
        L = phone_face_lights(s, fl)
        f = face_closeup(bg, t, s, 'envy' if i == 1 else 'tired', saccade(t + i, 3), 0.0, L, head=-2.0 if i == 1 else 2.0)
        f = Wd.grade(f, cold=0.5, sat=0.9)
    else:
        f, _ = bed_sit(t + 5.0, lift=0.0, zoom=1.5)
        f = Wd.grade(f, cold=0.55, sat=0.9)
    txt = Wd.text_layer()
    Wd.readout(txt, clock, 64, 48, 30)
    return Wd.composite(f, txt)


def s15_red_card(tl, t):
    f = np.zeros((H, W, 3), np.float32) + np.array([5, 5, 7], np.float32)
    txt = Wd.text_layer()
    shown = Wd.typewriter('look at them.', t, 45.72, cps=26.0)
    if shown:
        d = ImageDraw.Draw(txt)
        fnt = Wd.font(Wd.F_TYPE, 72)
        tw = d.textlength('look at them.', font=fnt)
        Wd.villain(txt, shown, W / 2 - tw / 2, 505, 72)
    rec('text', 45.72, kind='villain', txt='look at them.', cps=26.0)
    return Wd.composite(f, txt)


def s16_lit_room(tl, t):
    cam = cam_lerp(Cam(1.0, 0.5, 0.48), Cam(1.07, 0.5, 0.48), tl / 5.1)
    k = ease((t - 49.3) / 1.0)
    f = facade(t, cam, emphasis=k)
    if k > 0:
        rec('light', 49.3, what='facade_emphasis')
    txt = Wd.text_layer()
    readout('11:58 PM', 38.2, txt, t)
    narration_fade('You only ever see the lit room.', 49.1, txt, t, italic=True)
    return Wd.grade(Wd.composite(f, txt), cold=0.35, sat=0.92)


def s17_runner_knee(tl, t):
    cam = cam_lerp(Cam(1.12, 0.46, 0.56), Cam(1.18, 0.46, 0.56), tl / 3.5)
    f = cam.shoot(Wd.plate('runner_window'))
    layer = Wd.text_layer()
    clip = cam.rect((350, 100, 1600, 1000))
    x, y = cam.map(640, 830)
    s = 540 * cam.zoom
    pose = dict(Hm.p_sit(t, 0.4), yaw=-22, lean=30, head=24, head_t=6, lz_l=82, lz_r=70, kl=88, kr=96)
    _, J0, _ = S.solve(x, y, s, pose, anchor='hip')
    kx, ky = J0['knl']
    pose = S.reach(pose, 'l', (kx - 10 * cam.zoom, ky - 6 * cam.zoom), x, y, s, anchor='hip')
    pose = S.reach(pose, 'r', (kx + 14 * cam.zoom, ky + 2 * cam.zoom), x, y, s, anchor='hip')
    pose['sh_up'] = 0.006 * math.sin(t * 1.6)
    silhouette(layer, x, y, s, pose, clip=clip, anchor='hip', hands=('cup', 'cup'))
    # the ice pack reads pale against the silhouette
    L = S.light_rig(key_int=0.5, fill_int=0.2, rim_int=0.2)
    can = Wd.text_layer()
    S.person(can, x, y, s, pose, L, clip=clip, anchor='hip', hands=('cup', 'cup'), props=[dict(kind='icepack', hand='r')],
             only='hand_r', ink=0.0, ao=0.0)
    layer.alpha_composite(can)
    f = Wd.composite(f, layer)
    f = Wd.rain(f, t, density=120, alpha=0.10)
    txt = Wd.text_layer()
    readout('12:06 AM', 51.7, txt, t)
    villain_line("he's hurting.", 53.6, txt, t, col=Wd.BONE)
    return Wd.grade(Wd.composite(f, txt), warm=0.1, sat=0.9)


def s18_couple_silence(tl, t):
    cam = cam_lerp(Cam(1.10, 0.5, 0.52), Cam(1.15, 0.5, 0.52), tl / 3.8)
    f = cam.shoot(Wd.plate('kitchen_window'))
    m = Wd._soft_rect_mask(cam.rect((300, 190, 1620, 890)), 8)[..., None]
    f = f * (1 - m) + f * m * 0.72
    f = Wd.composite(f, couple_kitchen(t, cam, 'silence'))
    f = Wd.rain(f, t, density=120, alpha=0.10)
    txt = Wd.text_layer()
    readout('12:11 AM', 55.2, txt, t)
    villain_line("they're quiet.", 57.6, txt, t, col=Wd.BONE)
    return Wd.grade(Wd.composite(f, txt), warm=0.1, sat=0.88)


def s19_deskman_glass(tl, t):
    cam = cam_lerp(Cam(1.08, 0.42, 0.5), Cam(1.2, 0.42, 0.5), tl / 5.0)
    f = cam.shoot(Wd.plate('desk_window'))
    layer = Wd.text_layer()
    clip = cam.rect((170, 200, 790, 880))
    x, y = cam.map(640, 870)
    s = 560 * cam.zoom
    p = dict(Hm.p_stand(t, 0.2), yaw=0, az_l=6, az_r=8, ef_l=12, ef_r=12, lean=3, head_t=2 * math.sin(t * 0.5))
    silhouette(layer, x, y, s, p, clip=clip)
    f = Wd.composite(f, layer)
    f = Wd.rain(f, t, density=120, alpha=0.10)
    txt = Wd.text_layer()
    readout('2:04 AM', 59.0, txt, t)
    villain_line("it's two a.m.", 61.0, txt, t, x=1180, col=Wd.BONE)
    return Wd.grade(Wd.composite(f, txt), cold=0.5, sat=0.9)


def s20_at_yours(tl, t):
    x0, y0, x1, y1 = Wd.HERO_WIN
    cam = cam_lerp(Cam(1.25, (x0 + x1) / 2 / W, (y0 + y1) / 2 / H), Cam(1.45, (x0 + x1) / 2 / W, (y0 + y1) / 2 / H), tl / 2.4)
    f = own_window(t, cam, 'blue')
    txt = Wd.text_layer()
    readout('2:04 AM', 59.0, txt, t)
    return Wd.grade(Wd.composite(f, txt), cold=0.45, sat=0.9)


def s21_face_calm(tl, t):
    s = 4400 + 120 * ease(tl / 3.0)
    fl = Wd.flicker(t, 6, rate=6, depth=0.25)
    cam = Cam(2.2, 0.22, 0.62)
    bg = cam.shoot(Wd.plate('bedroom_night'))
    bg = np.asarray(Image.fromarray(bg.astype(np.uint8)).filter(ImageFilter.GaussianBlur(4)), np.float32) * 0.35
    bg = Wd.glow(bg, (W / 2, H * 0.55), 900, Wd.BLUE, power=0.4 * fl, falloff=2.2)
    L = phone_face_lights(s, fl)
    e = Hm.expr_mix('tired', 'doubt', 0.5 + 0.5 * math.sin(t * 0.7))
    bl = max(Hm.blink(t, 8), ease((t - 67.6) / 0.35) * ease((68.5 - t) / 0.4))   # one long, slow blink
    f = face_closeup(bg, t, s, e, saccade(t, 4, period=1.3, amp=(0.1, 0.08)), bl, L, head=-2.0 + 1.5 * math.sin(t * 0.5))
    txt = Wd.text_layer()
    readout('2:04 AM', 59.0, txt, t)
    return Wd.grade(Wd.composite(f, txt), cold=0.5, sat=0.9)


def s22_phone_dies(tl, t):
    on = 1.0 - ease((t - 71.45) / 0.1)
    if on < 1.0:
        rec('light', 71.45, what='phone_off')
    drop = ease((t - 72.6) / 1.4)
    f, cam = bed_sit(t, lift=0.0, phone_on=on, zoom=1.45 + 0.02 * tl, head_drop=drop,
                     expr=Hm.expr_mix('tired', 'doubt', 0.4), look=(0.1, 0.7 - 0.5 * drop))
    txt = Wd.text_layer()
    readout('12:30 AM', 69.4, txt, t)
    return Wd.grade(Wd.composite(f, txt), cold=0.55, sat=0.9, lift=-0.01 * (1 - on))


def s23_window_off(tl, t):
    k = ease((t - 74.9) / 0.12)
    if k > 0:
        rec('light', 74.9, what='own_window_off')
    cam = cam_lerp(Cam(1.0, 0.5, 0.5), Cam(1.04, 0.5, 0.5), tl / 2.4)
    if k < 1.0:
        fb = own_window(t, cam, 'blue')
        fd = own_window(t, cam, 'dark')
        f = fb * (1 - k) + fd * k
    else:
        f = own_window(t, cam, 'dark')
    txt = Wd.text_layer()
    readout('12:30 AM', 69.4, txt, t)
    return Wd.grade(Wd.composite(f, txt), cold=0.45, sat=0.9)


def sit_to_stand(u):
    """pose blend sit (bed front edge, feet anchored) → stand with anticipation."""
    a = Hm.anticipate(u, back=0.10)
    a = max(0.0, a)
    lean_extra = 14 * math.sin(min(1.0, u / 0.35) * math.pi) if u < 0.5 else 0.0
    return dict(lz_l=78 * (1 - a), lz_r=74 * (1 - a), kl=96 * (1 - a) + 3 * a, kr=92 * (1 - a) + 3 * a,
                lean=20 * (1 - a) + 1.5 * a + lean_extra, head=8 * (1 - a), al=-8 - 8 * a, ar=8 + 8 * a,
                az_l=38 * (1 - a) + 2 * a, az_r=38 * (1 - a) - 2 * a, ef_l=62 * (1 - a) + 10 * a, ef_r=62 * (1 - a) + 10 * a,
                ll=-6, lr=6)


def s24_stand_walk(tl, t):
    cam = cam_lerp(Cam(1.0, 0.5, 0.56), Cam(1.06, 0.5, 0.56), tl / 5.0)
    f = bedroom_dark(cam, 1.0)
    layer = Wd.text_layer()
    # path: bed front (feet 760,1046 · s 483) → window (feet 1120, 950 · s 500)
    p0, p1 = (760.0, 1046.0), (1120.0, 950.0)
    if t < 78.3:
        px, py, s0 = p0[0], p0[1], 483.0
        pose = dict(sit_to_stand(0.0), yaw=-12, sh_up=0.004 * Hm.breathe(t))
        phase = 0.0
    elif t < 79.5:
        u = (t - 78.3) / 1.2
        px, py, s0 = p0[0], p0[1], 483.0
        pose = dict(sit_to_stand(u), yaw=-12 + 40 * ease(u), sh_up=0.004 * Hm.breathe(t))
        phase = 0.0
    elif t < 81.7:
        u = (t - 79.5) / 2.2
        uu = u * u * (3 - 2 * u) * 0.15 + u * 0.85
        px = p0[0] + (p1[0] - p0[0]) * uu
        py = p0[1] + (p1[1] - p0[1]) * uu
        s0 = 483 + 17 * uu
        phase = uu * 1.55
        pose = dict(Hm.walk_pose(phase % 1.0, stride=28, lean=5, arm=0.6), yaw=150 - 30 * ease((u - 0.8) / 0.2))
        pose['head'] = 6
    else:
        u = (t - 81.7) / 0.3
        px, py, s0 = p1[0], p1[1], 500.0
        pose = dict(Hm.p_stand(t, 0.2), yaw=180, head=4 - 4 * ease(u), sh_up=0.004 * Hm.breathe(t))
        phase = 0.0
    x, y = cam.map(px, py)
    s = s0 * cam.zoom
    if t >= 79.5:
        S.floor_shadow(layer, x, y, s, pose, direction=(0.0, 1.0), length=0.32, alpha=0.42, blur=8)
    L = S.scene_lights(x, y, s, cam.map(990, 330), key_col=COLD_L, key_int=0.85, key_z=-0.8,
                       fill_col=(0.25, 0.3, 0.42), fill_int=0.14, rim_dir=(0.0, -0.3, -0.95), rim_col=(0.6, 0.75, 1.0),
                       rim_int=1.0, sky=(0.06, 0.07, 0.11), ground=(0.02, 0.02, 0.03))
    J, _ = person_frame(layer, x, y, s, pose, L, SS=2, expr='tired', look=(0.0, 0.1), blink_v=Hm.blink(t, 12))
    if t >= 79.5:
        S.contact_shadows(layer, J, s, alpha=0.4)
    f = Wd.composite(f, layer)
    txt = Wd.text_layer()
    readout('12:31 AM', 77.1, txt, t)
    return Wd.grade(Wd.composite(f, txt), cold=0.5, sat=0.88)


def window_hero(t, cam, hands_up=1.0, expr='tired', dawn=0.0, lamp=0.0, x=960, y=1035, s=720, yaw=180, walk=None):
    """the hero at the glass seen from inside (back view). hands_up 0..1 raises the palms to the glass."""
    layer = Wd.text_layer()
    fx, fy = cam.map(x, y)
    fs = s * cam.zoom
    base = dict(Hm.p_window(t), yaw=yaw, lean=4 * hands_up + 1.0)
    if walk is not None:
        base = dict(Hm.walk_pose(walk % 1.0, stride=30, lean=4), yaw=yaw)
        pose = base
    elif hands_up <= 0:
        pose = dict(Hm.p_stand(t, 0.1), yaw=yaw, head=2)
    else:
        pose = S.reach(base, 'l', (fx + 125 * cam.zoom, fy - (515 - 200 * (1 - hands_up)) * cam.zoom), fx, fy, fs)
        pose = S.reach(pose, 'r', (fx - 125 * cam.zoom, fy - (515 - 200 * (1 - hands_up)) * cam.zoom), fx, fy, fs)
        if hands_up < 1.0:
            down = dict(Hm.p_stand(t, 0.1), yaw=yaw)
            for k in ('al', 'ar', 'az_l', 'az_r', 'ef_l', 'ef_r'):
                pose[k] = pose.get(k, 0) * hands_up + down.get(k, 0) * (1 - hands_up)
    S.floor_shadow(layer, fx, fy, fs, pose, direction=(0.0, 1.0), length=0.35, alpha=0.5 * (1 - 0.5 * dawn), blur=10)
    key_col = COLD_L if dawn < 0.5 else DAWN_L
    L = S.scene_lights(fx, fy, fs, cam.map(960, 330), key_col=key_col, key_int=1.0, key_z=-0.9,
                       fill_col=(0.3 + 0.3 * lamp, 0.36 + 0.2 * lamp, 0.5), fill_int=0.22 + 0.5 * lamp,
                       rim_dir=(0.0, -0.3, -0.95), rim_col=(0.6, 0.78, 1.0), rim_int=1.3 - 0.5 * dawn,
                       sky=(0.08, 0.10, 0.16), ground=(0.03, 0.03, 0.04))
    if lamp > 0:
        L['fill'] = (np.asarray(S._n((-0.3, -0.5, 0.8))), np.asarray(AMBER_L, float), 0.9 * lamp)
    hands = ('glass', 'glass') if hands_up > 0.5 else ('relax', 'relax')
    J, ex = person_frame(layer, fx, fy, fs, pose, L, SS=2, hands=hands, expr=expr, blink_v=Hm.blink(t, 13))
    return layer, J


def s25_at_glass(tl, t):
    cam = cam_lerp(Cam(1.12, 0.5, 0.47), Cam(1.16, 0.5, 0.47), tl / 1.6)
    f = cam.shoot(Wd.plate('window_inside'))
    up = ease((t - 82.2) / 1.0)
    layer, _ = window_hero(t, cam, hands_up=up)
    f = Wd.composite(f, layer)
    f = Wd.rain(f, t, density=170, alpha=0.14)
    txt = Wd.text_layer()
    readout('12:31 AM', 77.1, txt, t)
    return Wd.grade(Wd.composite(f, txt), cold=0.5, sat=0.9)


def s26_reflection(tl, t):
    """his reflection laid over the 31 windows — a GLASS GHOST: the face lit by the facade (warm) and the two cold
    screens (blue), the body as a faint bone haze (dark cloth reflects almost nothing, the glass gives it a soft halo)."""
    cam = cam_lerp(Cam(1.3, 0.5, 0.45), Cam(1.42, 0.5, 0.45), tl / 5.4)
    f = cam.shoot(Wd.plate('window_inside')) * 0.78
    s = 3000 + 80 * ease(tl / 5.4)
    meet = ease((t - 85.0) / 0.5)
    look = (0.0 + 0.12 * (1 - meet) * math.sin(t * 0.9), 0.18 * (1 - meet) + 0.0 * meet)
    e = Hm.expr_mix('doubt', 'neutral', 0.35 * meet)
    bl = max(Hm.blink(t, 6), ease((t - 86.3) / 0.12) * ease((86.62 - t) / 0.14))
    L = S.light_rig(key_dir=(0.0, -0.3, 0.95), key_col=(1.0, 0.82, 0.62), key_int=0.9,       # the lit windows, from the front
                    fill_dir=(0.7, -0.1, 0.7), fill_col=(0.45, 0.6, 1.0), fill_int=0.35,       # the two cold screens, right
                    rim_dir=(0.4, -0.5, -0.75), rim_col=(0.6, 0.78, 1.0), rim_int=0.25,
                    sky=(0.10, 0.09, 0.10), ground=(0.03, 0.03, 0.04))
    can = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    pose = dict(Hm.p_stand(t), head_t=4 * (1 - meet), head=-2.0 + 1.0 * math.sin(t * 0.4))
    S.render_window(can, (0, 0, W, H), s, pose, L, focus='hctr', focus_off=(0.0, 0.04), expr=e, look=look,
                    blink_v=bl, alpha=1.0, ink=0.12, ao=0.45)
    a = np.asarray(can, np.float32)
    al = a[..., 3] / 255.0
    # glass ghost: the silhouette as a soft bone haze (σ 9 px) so shoulders + hood read, not only the bright face
    haze = np.asarray(Image.fromarray((al * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(9)), np.float32) / 255.0
    # vertical falloff: strongest at the face, fading toward the sill (the room below the window is black glass)
    yy = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None]
    fall = 1.0 - 0.55 * np.clip((yy - 0.42) / 0.5, 0.0, 1.0)
    fig = Image.fromarray(np.dstack([a[..., :3], (al * 255)]).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.1))
    fig = np.asarray(fig, np.float32)
    rgb = fig[..., :3]; fa = fig[..., 3] / 255.0
    a_fig = fa * 0.27 * fall
    a_haze = haze * 0.10 * fall
    f = f * (1 - a_haze[..., None]) + np.array(Wd.BONE, np.float32) * a_haze[..., None]
    f = f * (1 - a_fig[..., None]) + rgb * a_fig[..., None]
    f = Wd.rain(f, t, density=170, alpha=0.13)
    txt = Wd.text_layer()
    readout('12:31 AM', 77.1, txt, t)
    villain_line('look at you.', 86.9, txt, t, col=Wd.BONE)
    return Wd.grade(Wd.composite(f, txt), cold=0.5, sat=0.85)


def s27_turn_away(tl, t):
    cam = Cam(1.12, 0.5, 0.47)
    f = cam.shoot(Wd.plate('window_inside'))
    if t < 90.4:
        up = 1.0 - ease((t - 89.4) / 0.8)
        layer, _ = window_hero(t, cam, hands_up=up)
    elif t < 91.3:
        u = ease((t - 90.4) / 0.9)
        layer = Wd.text_layer()
        fx, fy = cam.map(960, 1035); fs = 720 * cam.zoom
        pose = dict(Hm.p_stand(t, 0.1), yaw=180 + 90 * u, head_t=-30 * math.sin(u * math.pi), head=2)
        S.floor_shadow(layer, fx, fy, fs, pose, direction=(0.0, 1.0), length=0.35, alpha=0.5, blur=10)
        L = S.scene_lights(fx, fy, fs, cam.map(960, 330), key_col=COLD_L, key_int=1.0, key_z=-0.9,
                           fill_col=(0.3, 0.36, 0.5), fill_int=0.22, rim_dir=(0.0, -0.3, -0.95), rim_col=(0.6, 0.78, 1.0),
                           rim_int=1.3, sky=(0.08, 0.10, 0.16), ground=(0.03, 0.03, 0.04))
        person_frame(layer, fx, fy, fs, pose, L, SS=2, expr='tired', blink_v=Hm.blink(t, 13))
    else:
        u = (t - 91.3) / 1.6
        px = 960 - 560 * u
        layer = Wd.text_layer()
        fx, fy = cam.map(px, 1035); fs = 720 * cam.zoom
        pose = dict(Hm.walk_pose((u * 1.9) % 1.0, stride=30, lean=4), yaw=270)
        S.floor_shadow(layer, fx, fy, fs, pose, direction=(0.0, 1.0), length=0.35, alpha=0.5, blur=10)
        L = S.scene_lights(fx, fy, fs, cam.map(960, 330), key_col=COLD_L, key_int=1.0, key_z=-0.9,
                           fill_col=(0.3, 0.36, 0.5), fill_int=0.22, rim_dir=(0.0, -0.3, -0.95), rim_col=(0.6, 0.78, 1.0),
                           rim_int=1.3, sky=(0.08, 0.10, 0.16), ground=(0.03, 0.03, 0.04))
        J, _ = person_frame(layer, fx, fy, fs, pose, L, SS=2, expr='focus', blink_v=Hm.blink(t, 13))
        S.contact_shadows(layer, J, fs, alpha=0.4)
    f = Wd.composite(f, layer)
    f = Wd.rain(f, t, density=170, alpha=0.14)
    txt = Wd.text_layer()
    readout('12:33 AM', 89.1, txt, t)
    return Wd.grade(Wd.composite(f, txt), cold=0.5, sat=0.9)


def s28_boring_card(tl, t):
    rec('text', 93.1, kind='card', txt='The boring part.', cps=0)
    return card('The boring part.', t, 93.1, 94.15, size=52, italic=True, fade=0.3)


def s29_bed_making(tl, t):
    cam = Cam(1.45, 0.36, 0.62)
    f = cam.shoot(Wd.plate('bedroom_night')) * 0.75
    layer = Wd.text_layer()
    x, y, s = 1010, 980, 600
    u = (t - 94.2) / 2.9
    sweep = 0.5 - 0.5 * math.cos(u * math.pi * 2.0)          # two passes along the blanket edge
    tx = 900 - 200 * sweep
    base = dict(Hm.p_stand(t, 0.0), yaw=-62 - 8 * sweep, lean=38 + 4 * math.sin(u * math.pi * 2), head=10, kl=14, kr=10,
                lz_l=-6, lz_r=8)
    pose = S.reach(base, 'l', (tx - 120, 626 + 4 * math.sin(t * 6)), x, y, s)
    pose = S.reach(pose, 'r', (tx, 641 + 4 * math.cos(t * 6)), x, y, s)
    L = S.scene_lights(x, y, s, cam.map(980, 200), key_col=COLD_L, key_int=0.8, key_z=-0.5,
                       fill_col=(0.25, 0.3, 0.42), fill_int=0.16, rim_dir=(0.3, -0.4, -0.85), rim_col=(0.6, 0.75, 1.0),
                       rim_int=0.9, sky=(0.06, 0.07, 0.11), ground=(0.02, 0.02, 0.03))
    J, _ = person_frame(layer, x, y, s, pose, L, SS=2, hands=('flat', 'flat'), expr='focus', look=(-0.3, 0.5),
                        blink_v=Hm.blink(t, 14))
    S.contact_shadows(layer, J, s, alpha=0.4)
    f = Wd.composite(f, layer)
    txt = Wd.text_layer()
    readout('12:41 AM', 94.3, txt, t)
    return Wd.grade(Wd.composite(f, txt), cold=0.4, sat=0.9)


def s30_dishes(tl, t):
    cam = cam_lerp(Cam(1.0, 0.5, 0.6), Cam(1.07, 0.5, 0.6), tl / 2.5)
    f = cam.shoot(Wd.plate('kitchenette_night'))
    layer = Wd.text_layer()
    x, y = cam.map(790, 1105)
    s = 760 * cam.zoom
    ang = t * 2 * math.pi * 1.5
    pose = dict(Hm.p_stand(t, 0.1), yaw=152, lean=14, head=16, kl=6, kr=6)
    pose = S.reach(pose, 'l', cam.map(1000, 705), x, y, s)
    pose = S.reach(pose, 'r', cam.map(1050 + 22 * math.cos(ang), 690 + 12 * math.sin(ang)), x, y, s)
    pose['hw_l'] = -60
    pose['hw_r'] = 40
    L = S.scene_lights(x, y, s, cam.map(950, 300), key_col=(0.75, 0.86, 1.0), key_int=1.15, key_z=-0.2,
                       fill_col=(0.2, 0.24, 0.32), fill_int=0.14, rim_dir=(0.5, -0.6, -0.6), rim_col=(0.7, 0.8, 1.0),
                       rim_int=0.6, sky=(0.05, 0.06, 0.09), ground=(0.02, 0.02, 0.025))
    J, _ = person_frame(layer, x, y, s, pose, L, SS=2, hands=('flat', 'grip'), expr='focus', look=(0.4, 0.6),
                        props=[dict(kind='plate', hand='l'), dict(kind='sponge', hand='r')], blink_v=Hm.blink(t, 15))
    f = Wd.composite(f, layer)
    txt = Wd.text_layer()
    readout('12:52 AM', 97.2, txt, t)
    return Wd.grade(Wd.composite(f, txt), cold=0.35, sat=0.88)


def s31_desk_clear(tl, t):
    cam = cam_lerp(Cam(1.35, 0.72, 0.64), Cam(1.4, 0.72, 0.64), tl / 2.3)
    f = cam.shoot(Wd.plate('bedroom_night')) * 0.75
    layer = Wd.text_layer()
    x, y = cam.map(1430, 1040)
    s = 620 * cam.zoom
    u = (t - 99.6) / 2.3
    sw = 0.5 - 0.5 * math.cos(u * math.pi * 1.5)
    pose = dict(Hm.p_stand(t, -0.2), yaw=90, lean=12 + 4 * sw, head=8)
    pose = S.reach(pose, 'r', cam.map(1560 + 150 * sw, 772 + 10 * sw), x, y, s)
    pose = S.reach(pose, 'l', cam.map(1520, 700), x, y, s)
    pose['hw_r'] = 60
    L = S.scene_lights(x, y, s, cam.map(900, 300), key_col=COLD_L, key_int=0.8, key_z=-0.3,
                       fill_col=(0.25, 0.3, 0.42), fill_int=0.16, rim_dir=(0.6, -0.4, -0.7), rim_col=(0.6, 0.75, 1.0),
                       rim_int=0.8, sky=(0.06, 0.07, 0.11), ground=(0.02, 0.02, 0.03))
    J, _ = person_frame(layer, x, y, s, pose, L, SS=2, hands=('grip', 'flat'), expr='focus', look=(0.5, 0.5),
                        props=[dict(kind='papers', hand='l')], blink_v=Hm.blink(t, 16))
    S.contact_shadows(layer, J, s, alpha=0.4)
    f = Wd.composite(f, layer)
    txt = Wd.text_layer()
    readout('1:04 AM', 99.7, txt, t)
    return Wd.grade(Wd.composite(f, txt), cold=0.4, sat=0.9)


def s32_shoes(tl, t):
    cam = Cam(1.35, 0.64, 0.76)
    f = cam.shoot(Wd.plate('bedroom_night')) * 0.75
    layer = Wd.text_layer()
    x, y = cam.map(1150, 1058)
    s = 600 * cam.zoom
    u = (t - 101.9) / 1.7
    pose = dict(Hm.p_stand(t, 0.0), yaw=-40, lz_l=96, lz_r=92, kl=132, kr=128, lean=28, head=18, ll=-8, lr=8)
    pose = S.reach(pose, 'r', cam.map(1290 - 30 * ease(u), 992), x, y, s)
    pose = S.reach(pose, 'l', cam.map(1230, 1000), x, y, s)
    L = S.scene_lights(x, y, s, cam.map(900, 300), key_col=COLD_L, key_int=0.8, key_z=-0.3,
                       fill_col=(0.25, 0.3, 0.42), fill_int=0.16, rim_dir=(0.6, -0.4, -0.7), rim_col=(0.6, 0.75, 1.0),
                       rim_int=0.8, sky=(0.06, 0.07, 0.11), ground=(0.02, 0.02, 0.03))
    J, _ = person_frame(layer, x, y, s, pose, L, SS=2, hands=('grip', 'grip'), expr='focus', look=(-0.2, 0.7),
                        blink_v=Hm.blink(t, 17))
    f = Wd.composite(f, layer)
    txt = Wd.text_layer()
    readout('1:09 AM', 102.0, txt, t)
    return Wd.grade(Wd.composite(f, txt), cold=0.4, sat=0.9)


def s33_run_dawn(tl, t):
    cam = Cam(1.0, 0.5, 0.5)
    f = cam.shoot(Wd.plate('street_dawn'))
    layer = Wd.text_layer()
    u = (t - 103.6) / 4.8
    k = u ** 1.6
    px = 905 + (640 - 905) * k
    py = 870 + (1290 - 870) * k
    s = 230 + (900 - 230) * k
    phase = (t - 103.6) * 1.35
    pose = dict(Hm.run_pose(phase % 1.0, stride=46, lean=11), yaw=-22, head=14)
    pose['bob'] = 0.03 * abs(math.sin(2 * math.pi * phase))
    _, J, _ = S.solve(px, py, s, pose)
    S.contact_shadows(layer, J, s, alpha=0.5)
    L = S.light_rig(key_dir=(-0.3, -0.7, 0.55), key_col=(0.62, 0.68, 0.8), key_int=0.85,
                    fill_dir=(0.6, -0.2, 0.75), fill_col=(0.3, 0.33, 0.42), fill_int=0.18,
                    rim_dir=(0.2, -0.5, -0.84), rim_col=(0.75, 0.75, 0.85), rim_int=0.7,
                    sky=(0.14, 0.15, 0.2), ground=(0.04, 0.04, 0.045),
                    points=[S.point_light(np.array([(890 - px), (520 - py), 0.2 * s]), (1.0, 0.75, 0.45), 0.35, 0.9 * s)])
    person_frame(layer, px, py, s, pose, L, SS=2 if s <= 1100 else 1, expr='pain', look=(0.0, 0.4), blink_v=Hm.blink(t, 18))
    # wet-street reflection of the runner
    refl = layer.transpose(Image.FLIP_TOP_BOTTOM)
    a = np.asarray(refl.split()[3], np.float32) * 0.22
    refl.putalpha(Image.fromarray(a.astype(np.uint8)))
    refl = refl.filter(ImageFilter.GaussianBlur(3))
    off = int(2 * py - H)
    rl = Wd.text_layer()
    rl.alpha_composite(refl, dest=(0, max(0, off)), source=(0, max(0, -off)))
    f = Wd.composite(f, rl)
    f = Wd.composite(f, layer)
    txt = Wd.text_layer()
    readout('DAY 1  ·  5:10 AM', 103.8, txt, t, size=34)
    return Wd.grade(Wd.composite(f, txt), cold=0.25, warm=0.05, sat=0.9)


def s34_lamp_on(tl, t):
    on = ease((t - 109.9) / 0.08)
    if on > 0:
        rec('light', 109.9, what='lamp_on')
    f, cam = desk_amber(t, lamp_on=on, expr='focus', look=(0.5, 0.35), typing=1.0, dust_on=ease((t - 110.4) / 1.0))
    txt = Wd.text_layer()
    readout('DAY 9  ·  6:00 AM', 108.5, txt, t, size=34)
    return Wd.grade(Wd.composite(f, txt), warm=0.35 * on, cold=0.3 * (1 - on), sat=0.95)


def s35_run_past(tl, t):
    cam = cam_lerp(Cam(1.0, 0.5, 0.52), Cam(1.04, 0.5, 0.52), tl / 6.8)
    f = Wd.grade(cam.shoot(Wd.plate('kitchen_window')), warm=0.1, lift=0.05, sat=0.92)
    layer = couple_kitchen(t, cam, 'dawn')
    # the couple's heads turn toward the street when he passes (114.6–115.4)
    f = Wd.composite(f, layer)
    if 113.8 <= t <= 116.6:
        u = (t - 113.8) / 2.6
        px = -160 + 2240 * u
        py = 1190
        s = 400 * cam.zoom
        x, yy = cam.map(px, py)
        phase = (t - 113.8) * 2.1
        pose = dict(Hm.run_pose(phase % 1.0, stride=58, lean=12), yaw=90, head=4)
        hl = Wd.text_layer()
        L = S.light_rig(key_dir=(-0.2, -0.75, 0.55), key_col=(0.7, 0.72, 0.82), key_int=0.8,
                        fill_dir=(0.6, -0.2, 0.75), fill_col=(0.5, 0.4, 0.3), fill_int=0.25,
                        rim_dir=(0.1, -0.5, -0.86), rim_col=(1.0, 0.85, 0.6), rim_int=0.9,
                        sky=(0.14, 0.15, 0.2), ground=(0.04, 0.04, 0.045))
        J, _ = person_frame(hl, x, yy, s, pose, L, SS=2, expr='focus', blink_v=Hm.blink(t, 19))
        f = Wd.composite(f, hl)
    txt = Wd.text_layer()
    readout('DAY 23  ·  5:12 AM', 111.7, txt, t, size=34)
    return Wd.grade(Wd.composite(f, txt), warm=0.15, sat=0.95)


def s36_deskman_up(tl, t):
    cam = cam_lerp(Cam(1.08, 0.44, 0.5), Cam(1.16, 0.44, 0.5), tl / 2.5)
    f = Wd.grade(cam.shoot(Wd.plate('desk_window')), warm=0.08, lift=0.04, sat=0.92)
    up = ease((t - 119.5) / 0.9)
    mon = cam.map(1000, 470)
    f = Wd.glow(f, mon, 300, Wd.BLUE, power=0.16 * (1 - 0.6 * up), falloff=2.0)
    f = Wd.composite(f, deskman(t, cam, look_up=up))
    txt = Wd.text_layer()
    readout('DAY 40  ·  5:58 AM', 118.5, txt, t, size=34)
    return Wd.grade(Wd.composite(f, txt), cold=0.2, sat=0.92)


def s37_new_window(tl, t):
    k = ease((t - 121.3) / 0.25)
    if k > 0:
        rec('light', 121.3, what='own_window_amber')
    cam = cam_lerp(Cam(1.0, 0.5, 0.5), Cam(1.05, 0.5, 0.5), tl / 2.7)
    if k < 1.0:
        fd = own_window(t, cam, 'dark', rain_a=0.0, dawn=0.6)
        fa = own_window(t, cam, 'amber', rain_a=0.0, dawn=0.6)
        f = fd * (1 - k) + fa * k
    else:
        f = own_window(t, cam, 'amber', rain_a=0.0, dawn=0.6)
    txt = Wd.text_layer()
    readout('DAY 40  ·  5:58 AM', 118.5, txt, t, size=34)
    return Wd.grade(Wd.composite(f, txt), cold=0.1, sat=0.92)


def s38_facade_dawn(tl, t):
    cam = cam_lerp(Cam(1.0, 0.5, 0.48), Cam(1.05, 0.5, 0.48), tl / 3.4)
    f = facade(t, cam, rain_a=0.0, flick=False, dawn=0.8, win_gain=0.45)
    txt = Wd.text_layer()
    readout('DAY 40  ·  5:58 AM', 118.5, txt, t, size=34)
    return Wd.grade(Wd.composite(f, txt), sat=0.92)


PEOPLE = [('C6', 127.4, 1), ('A5', 127.7, 2), ('G5', 128.0, 3), ('B4', 128.3, 4), ('H4', 128.6, 5), ('E3', 128.9, 6),
          ('I2', 129.2, 7), ('K4', 129.5, 8)]


def s39_people(tl, t):
    cam = cam_lerp(Cam(1.05, 0.5, 0.48), Cam(1.12, 0.5, 0.48), tl / 4.0)
    f = facade(t, cam, rain_a=0.0, flick=False, dawn=0.8, win_gain=0.45)
    layer = Wd.text_layer()
    window_people(layer, cam, t, PEOPLE)
    f = Wd.composite(f, layer)
    txt = Wd.text_layer()
    narration_fade('Every window you have ever envied', 127.4, txt, t, cy=930, size=44, italic=True)
    narration_fade('has someone standing in it, looking at yours.', 127.9, txt, t, cy=990, size=44, italic=True)
    return Wd.grade(Wd.composite(f, txt), sat=0.92)


def s40_inside_dawn(tl, t):
    cam = cam_lerp(Cam(1.12, 0.5, 0.47), Cam(1.18, 0.5, 0.47), tl / 4.0)
    f = Wd.grade(cam.shoot(Wd.plate('window_inside')), warm=0.25, lift=0.06, sat=0.9)
    M = windows_mask()      # the opposite facade through the glass is dimmer at dawn (plate is a different crop — soft)
    layer, J = window_hero(t, cam, hands_up=0.0, expr='calm', dawn=1.0, lamp=0.8)
    f = Wd.composite(f, layer)
    txt = Wd.text_layer()
    readout('DAY 40  ·  6:01 AM', 131.1, txt, t, size=34)
    return Wd.grade(Wd.composite(f, txt), warm=0.1, sat=0.92)


def s41_light_it(tl, t):
    turn = ease((t - 136.1) / 0.9)
    f, cam = desk_amber(t, lamp_on=1.0, head_turn=turn, expr=Hm.expr_mix('focus', 'calm', turn),
                        look=(0.5 - 0.6 * turn, 0.35 - 0.3 * turn), typing=1.0 - turn)
    txt = Wd.text_layer()
    readout('DAY 40  ·  6:04 AM', 135.1, txt, t, size=34)
    return Wd.grade(Wd.composite(f, txt), warm=0.35, sat=0.95)


def s42_amber_wide(tl, t):
    cam = cam_lerp(Cam(1.06, 0.5, 0.5), Cam(1.0, 0.5, 0.5), tl / 3.2)
    f = own_window(t, cam, 'amber', rain_a=0.0, dawn=0.7)
    return Wd.grade(f, sat=0.92)


def s43_end1(tl, t):
    rec('text', 141.9, kind='card', txt='LIGHT YOUR OWN WINDOW.', cps=0)
    return card('LIGHT YOUR OWN WINDOW.', t, 141.9, 146.5, size=64, glyph='amber')


def s44_end2(tl, t):
    rec('text', 146.9, kind='card', txt='You only ever see the lit room.', cps=0)
    return card('You only ever see the lit room.', t, 146.9, 150.6, size=44, italic=True)


def s45_tail(tl, t):
    return np.zeros((H, W, 3), np.float32) + np.array([5, 5, 7], np.float32)


# ─────────────────────────────────────────────── the timeline
# (name, t0, fn, fade_in, fade_out, section)
SHOTS = [
    ('S01 face · phone POV',            0.0,   s01_face,         0.8, 0.0, 'HOOK'),
    ('S02 bed wide · lying, glowing',   3.4,   s02_bed_wide,     0.0, 0.0, 'HOOK'),
    ('S03 facade · 31 windows lit',     6.6,   s03_facade_count, 0.0, 0.0, 'HOOK'),
    ('S04 facade drift · people',       9.7,   s04_facade_drift, 0.0, 0.0, 'HOOK'),
    ('S05 his window · blue',           12.6,  s05_own_window,   0.0, 0.3, 'HOOK'),
    ('S06 title',                       16.4,  s06_title,        0.0, 0.0, 'TITLE'),
    ('S07 push → B4',                   20.2,  s07_push_b4,      0.0, 0.0, 'WINDOWS'),
    ('S08 the runner',                  23.1,  s08_runner,       0.0, 0.0, 'WINDOWS'),
    ('S09 push → I3',                   27.3,  s09_push_i3,      0.0, 0.0, 'WINDOWS'),
    ('S10 the couple · two plates',     29.6,  s10_couple,       0.0, 0.0, 'WINDOWS'),
    ('S11 push → D5',                   33.3,  s11_push_d5,      0.0, 0.0, 'WINDOWS'),
    ('S12 two monitors',                35.3,  s12_deskman_work, 0.0, 0.0, 'WINDOWS'),
    ('S13 bed · he looks up',           38.1,  s13_bed_lookup,   0.0, 0.0, 'WINDOWS'),
    ('S14 montage + flurry',            42.4,  s14_montage,      0.0, 0.0, 'WINDOWS'),
    ('S15 red card · look at them.',    45.7,  s15_red_card,     0.0, 0.0, 'WINDOWS'),
    ('S16 the lit room',                46.5,  s16_lit_room,     0.0, 0.0, 'SCORE'),
    ('S17 runner · the knee',           51.6,  s17_runner_knee,  0.0, 0.0, 'SCORE'),
    ('S18 couple · the silence',        55.1,  s18_couple_silence, 0.0, 0.0, 'SCORE'),
    ('S19 two monitors · at the glass', 58.9,  s19_deskman_glass, 0.0, 0.0, 'SCORE'),
    ('S20 at yours',                    63.9,  s20_at_yours,     0.0, 0.0, 'SCORE'),
    ('S21 face · so calm',              66.3,  s21_face_calm,    0.0, 0.0, 'SCORE'),
    ('S22 the phone dies',              69.3,  s22_phone_dies,   0.0, 0.0, 'TURN'),
    ('S23 his window goes dark',        74.6,  s23_window_off,   0.0, 0.0, 'TURN'),
    ('S24 he stands · the walk',        77.0,  s24_stand_walk,   0.0, 0.0, 'TURN'),
    ('S25 at the glass',                82.0,  s25_at_glass,     0.0, 0.0, 'TURN'),
    ('S26 the reflection',              83.6,  s26_reflection,   0.0, 0.0, 'TURN'),
    ('S27 he turns away',               89.0,  s27_turn_away,    0.0, 0.25, 'WORK'),
    ('S28 card · The boring part.',     92.9,  s28_boring_card,  0.0, 0.0, 'WORK'),
    ('S29 the bed',                     94.2,  s29_bed_making,   0.0, 0.0, 'WORK'),
    ('S30 the dishes',                  97.1,  s30_dishes,       0.0, 0.0, 'WORK'),
    ('S31 the desk',                    99.6,  s31_desk_clear,   0.0, 0.0, 'WORK'),
    ('S32 the shoes',                   101.9, s32_shoes,        0.0, 0.0, 'WORK'),
    ('S33 DAY 1 · the run',             103.6, s33_run_dawn,     0.0, 0.0, 'WORK'),
    ('S34 DAY 9 · the lamp',            108.4, s34_lamp_on,      0.0, 0.0, 'WORK'),
    ('S35 DAY 23 · running past',       111.6, s35_run_past,     0.0, 0.0, 'WORK'),
    ('S36 DAY 40 · he looks up',        118.4, s36_deskman_up,   0.0, 0.0, 'WORK'),
    ('S37 a new window',                120.9, s37_new_window,   0.0, 0.0, 'WORK'),
    ('S38 facade at dawn',              123.6, s38_facade_dawn,  0.0, 0.0, 'PAYOFF'),
    ('S39 someone standing in it',      127.0, s39_people,       0.0, 0.0, 'PAYOFF'),
    ('S40 from the inside',             131.0, s40_inside_dawn,  0.0, 0.0, 'PAYOFF'),
    ('S41 Light it.',                   135.0, s41_light_it,     0.0, 0.0, 'PAYOFF'),
    ('S42 his window · amber wide',     138.4, s42_amber_wide,   0.0, 0.4, 'PAYOFF'),
    ('S43 end card',                    141.6, s43_end1,         0.0, 0.0, 'END'),
    ('S44 end card 2',                  146.6, s44_end2,         0.0, 0.0, 'END'),
    ('S45 quiet',                       150.8, s45_tail,         0.0, 0.0, 'END'),
]
DUR = 155.0
NF = int(round(DUR * FPS))


def shot_at(t):
    i = 0
    for k, sh in enumerate(SHOTS):
        if t >= sh[1] - 1e-9:
            i = k
    return i


def shot_bounds(i):
    t0 = SHOTS[i][1]
    t1 = SHOTS[i + 1][1] if i + 1 < len(SHOTS) else DUR
    return t0, t1


def frame(t, i_frame=0):
    i = shot_at(t)
    name, t0, fn, fi, fo, sec = SHOTS[i]
    _, t1 = shot_bounds(i)
    tl = t - t0
    f = fn(tl, t)
    if fi > 0 and tl < fi:
        f = f * ease(tl / fi)
    if fo > 0 and t1 - t < fo:
        f = f * ease((t1 - t) / fo)
    # the next shot's fade-in also darkens nothing here; the previous shot's fade-out already did
    g = 1.2 if sec != 'END' else 0.6
    return Wd.finish(f, np.random.default_rng(1000 + i_frame), vignette=0.52, grain=g, halation=0.14)


def write_events(path):
    shots = []
    for i, sh in enumerate(SHOTS):
        t0, t1 = shot_bounds(i)
        shots.append(dict(i=i, name=sh[0], t0=t0, t1=round(t1, 3), fade_in=sh[3], fade_out=sh[4], section=sh[5]))
    # recorded events need the shots to have run once at their reveal times
    for i, sh in enumerate(SHOTS):
        t0, t1 = shot_bounds(i)
        for tt in np.arange(t0, t1, 0.25):
            try:
                _probe(sh, tt)
            except Exception as e:  # noqa
                pass
    ev = dict(fps=FPS, duration=DUR, frames=NF, vo=VO, shots=shots, text=sorted(EVENTS['text'], key=lambda d: d['t']),
              light=sorted(EVENTS['light'], key=lambda d: d['t']), counter=EVENTS['counter'],
              cuts=[s['t0'] for s in shots[1:]])
    json.dump(ev, open(path, 'w'), indent=1)
    print('events →', path, len(ev['text']), 'text ·', len(ev['light']), 'light ·', len(shots), 'shots')
    return ev


def _probe(sh, t):
    """cheap probe to collect text/light records without rendering the hero: run text-only helpers."""
    name, t0, fn, fi, fo, sec = sh
    probes = {
        's01_face': [('11:48 PM', 1.4)], 's03_facade_count': [('11:48 PM', 1.4)],
        's07_push_b4': [('11:52 PM', 20.3)], 's08_runner': [('11:52 PM', 20.3)],
        's09_push_i3': [('11:53 PM', 27.4)], 's11_push_d5': [('11:55 PM', 33.4)], 's13_bed_lookup': [('11:58 PM', 38.2)],
        's17_runner_knee': [('12:06 AM', 51.7)], 's18_couple_silence': [('12:11 AM', 55.2)], 's19_deskman_glass': [('2:04 AM', 59.0)],
        's22_phone_dies': [('12:30 AM', 69.4)], 's24_stand_walk': [('12:31 AM', 77.1)], 's27_turn_away': [('12:33 AM', 89.1)],
        's29_bed_making': [('12:41 AM', 94.3)], 's30_dishes': [('12:52 AM', 97.2)], 's31_desk_clear': [('1:04 AM', 99.7)],
        's32_shoes': [('1:09 AM', 102.0)], 's33_run_dawn': [('DAY 1  ·  5:10 AM', 103.8)], 's34_lamp_on': [('DAY 9  ·  6:00 AM', 108.5)],
        's35_run_past': [('DAY 23  ·  5:12 AM', 111.7)], 's36_deskman_up': [('DAY 40  ·  5:58 AM', 118.5)],
        's40_inside_dawn': [('DAY 40  ·  6:01 AM', 131.1)], 's41_light_it': [('DAY 40  ·  6:04 AM', 135.1)],
    }
    for txt, t_on in probes.get(fn.__name__, []):
        rec('text', t_on, kind='readout', txt=txt, cps=22.0)
    vill = {'s08_runner': ("he's ahead.", 25.6, 'villain'), 's10_couple': ("they're happy.", 31.5, 'villain'),
            's12_deskman_work': ("you're late.", 36.3, 'villain'), 's15_red_card': ('look at them.', 45.72, 'villain'),
            's17_runner_knee': ("he's hurting.", 53.6, 'answer'), 's18_couple_silence': ("they're quiet.", 57.6, 'answer'),
            's19_deskman_glass': ("it's two a.m.", 61.0, 'answer'), 's26_reflection': ('look at you.', 86.9, 'answer')}
    if fn.__name__ in vill:
        txt, t_on, kind = vill[fn.__name__]
        rec('text', t_on, kind=kind, txt=txt, cps=16.0 if kind != 'villain' or fn.__name__ != 's15_red_card' else 26.0)
    narr = {'s06_title': ('THE WINDOW', 16.9, 'title'), 's16_lit_room': ('You only ever see the lit room.', 49.1, 'narration'),
            's28_boring_card': ('The boring part.', 93.1, 'card'),
            's39_people': ('Every window you have ever envied / has someone standing in it, looking at yours.', 127.4, 'narration'),
            's43_end1': ('LIGHT YOUR OWN WINDOW.', 141.9, 'card'), 's44_end2': ('You only ever see the lit room.', 146.9, 'card')}
    if fn.__name__ in narr:
        txt, t_on, kind = narr[fn.__name__]
        rec('text', t_on, kind=kind, txt=txt, cps=0)
    for tt, what in ((7.0, 'counter'), (49.3, 'facade_emphasis'), (71.45, 'phone_off'), (74.9, 'own_window_off'),
                     (109.9, 'lamp_on'), (121.3, 'own_window_amber')):
        if what == 'counter':
            rec('counter', 7.0, what='windows', n0=0, n1=31, dur=1.5)
        else:
            rec('light', tt, what=what)
    mont = [(42.4, '11:58 PM'), (43.0, '1:12 AM'), (43.6, '2:40 AM')] + [(44.2 + 0.25 * i, FLURRY[i][1]) for i in range(6)]
    for t_on, clock in mont:
        rec('text', t_on, kind='readout', txt=clock, cps=99)


def render(out, i0, i1, log_every=24):
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    t0s, _ = shot_bounds(i0)
    _, t1s = shot_bounds(i1)
    f0, f1 = int(round(t0s * FPS)), int(round(t1s * FPS))
    cmd = [ff, '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14', '-pix_fmt', 'yuv420p', '-g', '48',
           '-threads', os.environ.get('FFTHREADS', '2'), '-x264-params', 'rc-lookahead=10:sync-lookahead=0', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t_start = time.time()
    metrics = []
    for k in range(f0, f1):
        t = k / FPS
        fr = frame(t, k)
        p.stdin.write(fr.tobytes())
        if k % log_every == 0:
            m = Wd.measure(fr)
            metrics.append(dict(f=k, t=round(t, 3), **m))
            el = time.time() - t_start
            done = k - f0 + 1
            print(f'frame {k}/{f1}  shot {shot_at(t)}  {el:.0f}s  {el / done:.2f}s/f  eta {(f1 - k) * el / done / 60:.1f}min  luma {m["luma"]}', flush=True)
    p.stdin.close()
    p.wait()
    json.dump(metrics, open(out + '.metrics.json', 'w'))
    print('saved', out, f'{time.time() - t_start:.0f}s', 'rc', p.returncode)


def sheet(path):
    picks = [0.9, 5.0, 8.4, 15.5, 25.9, 31.8, 41.6, 53.9, 62.0, 73.5, 80.4, 86.5, 95.8, 98.4, 101.0, 106.5, 110.8, 115.2,
             122.4, 129.5, 133.5, 137.4, 143.5]
    frames, metrics = [], {}
    for t in picks:
        img = frame(t, int(t * FPS))
        i = shot_at(t)
        nm = SHOTS[i][0]
        frames.append((f'{t:06.1f}s  {nm}', img))
        metrics[f'{t:.1f} {nm}'] = Wd.measure(img)
        print(t, nm, metrics[f'{t:.1f} {nm}'], flush=True)
        Image.fromarray(img).save(os.path.join(BUILD, f'v2_{t:06.1f}.jpg'), quality=88)
    cw, ch = 940, 529
    cols = 2
    rows = (len(frames) + 1) // cols
    sh = Image.new('RGB', (cols * cw + 40, 140 + rows * (ch + 50)), (9, 9, 11))
    d = ImageDraw.Draw(sh)
    ft = Wd.font(Wd.F_SANS, 40, 'SemiBold')
    fs = Wd.font(Wd.F_SANS, 21, 'Medium')
    d.text((24, 26), 'NOIRGO MAX — THE WINDOW · look sheet v2 (3-D human stick hero · real-life plates · full VO)', font=ft, fill=(236, 232, 222))
    d.text((24, 84), 'topic COMPARISON · 155 s · 45 shots · voice-03 · colour arc phone blue → own lamp amber → dawn', font=fs, fill=(170, 168, 160))
    for i, (name, img) in enumerate(frames):
        x = 20 + (i % cols) * cw
        y = 140 + (i // cols) * (ch + 50)
        sh.paste(Image.fromarray(img).resize((cw - 10, ch), Image.LANCZOS), (x, y))
        m = list(metrics.values())[i]
        d.text((x + 4, y + ch + 6), f"{name}  ·  luma {m['luma']} dark {int(m['dark'] * 100)}% chroma {m['chroma']}", font=fs, fill=(200, 196, 188))
    sh.save(path, quality=88)
    json.dump(metrics, open(path.replace('.jpg', '_metrics.json'), 'w'), indent=1)
    print('wrote', path, sh.size)


def bench():
    for i, shp in enumerate(SHOTS):
        t0, t1 = shot_bounds(i)
        t = t0 + (t1 - t0) * 0.5
        a = time.time()
        frame(t, int(t * FPS))
        b = time.time()
        print(f'{i:02d} {shp[0]:34s} {b - a:5.2f}s/frame  × {int((t1 - t0) * FPS):4d} frames = {(b - a) * (t1 - t0) * FPS / 60:5.1f} min', flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--events')
    ap.add_argument('--still', nargs=2, metavar=('T', 'OUT'))
    ap.add_argument('--stills', nargs='+', help='T [T ...] → build/wf03_window/still_T.jpg')
    ap.add_argument('--sheet', action='store_true')
    ap.add_argument('--render')
    ap.add_argument('--shots', default='0-%d' % (len(SHOTS) - 1))
    ap.add_argument('--bench', action='store_true')
    a = ap.parse_args()
    if a.events:
        write_events(a.events)
    if a.still:
        t = float(a.still[0])
        img = frame(t, int(t * FPS))
        Image.fromarray(img).save(a.still[1], quality=90)
        print(a.still[1], Wd.measure(img))
    if a.stills:
        for ts in a.stills:
            t = float(ts)
            a0 = time.time()
            img = frame(t, int(t * FPS))
            out = os.path.join(BUILD, f'still_{t:06.1f}.jpg')
            Image.fromarray(img).save(out, quality=88)
            print(out, SHOTS[shot_at(t)][0], Wd.measure(img), f'{time.time() - a0:.2f}s', flush=True)
    if a.sheet:
        sheet(os.path.join(Wd.WF, 'NOIRGO_LOOK_SHEET_v2_WINDOW.jpg'))
    if a.bench:
        bench()
    if a.render:
        i0, i1 = [int(v) for v in a.shots.split('-')]
        render(a.render, i0, i1)
