#!/usr/bin/env python3
"""THE GRAVITY OF THE PHONE — WTF-30 #1 · world, props, timeline, hero choreography.

Everything that is TIME (the event ledger) lives here so render.py, audio.py and
gate.py read one source of truth.  World coordinates are the wide shot
(1080 x 1920 at zoom 1.0); the camera in render.py maps world -> screen.

Identity: WF-01 paper/ink · SHADE hero · the only colour is the phone's amber.
"""
import math, zlib, pathlib, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = pathlib.Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "styles").is_dir())
STYLE = ROOT / "styles" / "monarch-stickman-animation"
sys.path.insert(0, str(STYLE / "src"))
import toon as T      # noqa: E402
import shade as SH    # noqa: E402

W, H, FPS, DUR = 1080, 1920, 30, 20.0
NFRAMES = int(round(DUR * FPS))

# ── palette (WF-01) ───────────────────────────────────────────────────────────
PAPER, PAPER_D, INK, SOFT = (244, 238, 225), (231, 222, 204), (27, 25, 29), (103, 94, 84)
GOLD, AMBER, AMBER_HI = (184, 120, 8), (232, 160, 30), (255, 214, 120)
WOOD = (214, 200, 174)

# ── timeline (seconds) — THE event ledger ───────────────────────────────────
TL = dict(
    buzz_start=-0.50, pencil_start=-0.40, pencil_end=1.40,
    flip_up=1.45, flip_dur=0.32, glow_on=1.55, glow_full=2.05,
    cut_s2=2.00, walk_start=2.00, walk_end=3.60, pend_lean=2.60, page_lift=3.00,
    cut_s3=3.80, cut_s4=4.60,
    field_on=4.90, field_full=5.60,
    book_fly=5.25, book_fly_dur=0.42,
    brace_end=5.50, lunge=5.50, grab=5.90, flag_start=6.00, flag_full=7.40,
    ding1=5.60, ding2=7.20, ding3=8.80,
    slip1=9.00, slip2=9.42, look_lens=9.80, look_end=10.70,
    letgo=11.00, land=11.42, slap=11.58, flip_down=11.62, glow_off=12.00,
    drop=12.30, stand=13.00, cut_s5=14.60,
    line1=15.40, line2=16.66, hot=17.15, cut_s6=17.95,
    moral1=18.00, moral2=18.64, moral3=18.98, moral_out=19.50, end=20.00,   # 'Warna' · 'tum' · 'ulte.' (upside-down) · snap-out on the buzz
)
# music grid: 122.4 BPM → beat 0.4902 s; beat 10 = field_on (4.90), beat 35 = hot word (17.157); heartbeat = half-time
BPM = 122.4
BEAT = 60.0 / BPM


def beat_pulse(t, decay=0.11):
    """0..1 pulse that fires on every beat of the music grid while the field is on (glow + zoom lock)."""
    if not (TL["field_on"] <= t < TL["letgo"]):
        return 0.0
    ph = (t % BEAT)
    return math.exp(-ph / decay)

ROOM_FLOOR = 1500.0
DESK_TOP = 1295.0
PHONE = (885.0, DESK_TOP)          # the planet
LINTEL = (257.0, 931.0)            # door-frame top-right corner the hero grips
HERO_S = 480.0                     # total height px in world (274 px / m)


# ── small maths ──────────────────────────────────────────────────────────────
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, u):
    return a + (b - a) * u


def smooth(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


def ease_in(u, p=2.2):
    return clamp(u) ** p


def ease_out(u, p=2.2):
    return 1 - (1 - clamp(u)) ** p


def seg(t, a, b):
    """0..1 progress of t through [a, b]."""
    if b <= a:
        return 1.0 if t >= b else 0.0
    return clamp((t - a) / (b - a))


def rot_pt(x, y, deg):
    """Rotate about the origin; positive = clockwise on screen (y down)."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return (x * c - y * s, x * s + y * c)


def blend_pose(a, b, u):
    o = dict(a)
    for k, v in b.items():
        av = a.get(k)
        if isinstance(v, (int, float)) and isinstance(av, (int, float)):
            o[k] = av * (1 - u) + v * u
        elif isinstance(v, (int, float)) and av is None:
            o[k] = v * u
        else:
            o[k] = v if u >= 0.5 else (av if av is not None else v)
    return o


def hash01(*keys):
    """Deterministic 0..1 hash (CRC32 — Python's str hash is randomised per process, which would
    make particles jump between render halves)."""
    h = 0
    for k in keys:
        h = (h * 1000003 + zlib.crc32(str(k).encode())) & 0xFFFFFFFF
    return (h % 10007) / 10007.0


# ── field strength k(t): 0 = normal gravity, 1 = the phone is the planet ─────
def field(t):
    if t < TL["field_on"]:
        return 0.0
    if t < TL["drop"]:
        return smooth(seg(t, TL["field_on"], TL["field_full"]))
    return 0.0


def field_vis(t):
    """Field strength for the eye (floor warp, vignette): the physics switch is instant at the drop,
    the picture relaxes over ~0.2 s so the restore reads as a release, not a cut."""
    if t >= TL["drop"]:
        u = t - TL["drop"]
        return math.exp(-u / 0.07) * (1 + 0.25 * math.sin(2 * math.pi * u / 0.28) * math.exp(-u / 0.12))
    return field(t)


def world_time(t):
    """S6 is S1 evaluated at loop time: tau = t - DUR (negative) after the last cut."""
    return t - DUR if t >= TL["cut_s6"] else t


def glow(t):
    """Phone glow 0..1 (amber), with the three notification dings as pulses.  t = world time."""
    if t < TL["glow_on"]:
        return 0.0
    g = smooth(seg(t, TL["glow_on"], TL["glow_full"]))
    if t >= TL["glow_off"]:
        g *= 1 - ease_out(seg(t, TL["glow_off"], TL["glow_off"] + 0.16), 1.6)
    for d in (TL["ding1"], TL["ding2"], TL["ding3"]):
        if d <= t < d + 0.26:
            g += 0.35 * (1 - (t - d) / 0.26)
    return g


def phone_state(t):
    """face: 0 = face-down, 1 = face-up; flip progress p in 0..1 (card flip).  t = world time."""
    tau = t
    buzz = (TL["buzz_start"] <= tau < TL["flip_up"])
    if tau < TL["flip_up"]:
        return dict(face=0.0, p=0.0, buzz=buzz, lift=0.0, tau=tau)
    if tau < TL["flip_up"] + TL["flip_dur"]:
        p = seg(tau, TL["flip_up"], TL["flip_up"] + TL["flip_dur"])
        return dict(face=1.0 if p >= 0.5 else 0.0, p=p, buzz=False, lift=math.sin(math.pi * p) * 26, tau=tau)
    if tau < TL["flip_down"]:
        return dict(face=1.0, p=0.0, buzz=False, lift=0.0, tau=tau)
    if tau < TL["flip_down"] + TL["flip_dur"]:
        p = seg(tau, TL["flip_down"], TL["flip_down"] + TL["flip_dur"])
        return dict(face=0.0 if p >= 0.5 else 1.0, p=p, buzz=False, lift=math.sin(math.pi * p) * 14, tau=tau)
    return dict(face=0.0, p=0.0, buzz=False, lift=0.0, tau=tau)


def pencil_x(t):
    u = seg(t, TL["pencil_start"], TL["pencil_end"])
    return 700 + 77 * ease_in(u, 2.2)


# ── props ────────────────────────────────────────────────────────────────────
# home / pile / down are (x, y, rot_deg_clockwise).  Flights: t0, dur, mode, arc.
PROPS = {
    "cup":    dict(home=(1000, DESK_TOP, 0), pile=(976, DESK_TOP, -9), down=(978, DESK_TOP, 0),
                   t0=4.95, dur=0.42, mode="slide", arc=0, fall=0.22, bounce=4, z=11),
    "page0":  dict(home=(758, DESK_TOP, 0), pile=(796, DESK_TOP, 16), down=(766, DESK_TOP, 0),
                   t0=5.00, dur=0.55, mode="fly", arc=28, fall=0.55, bounce=0, z=7),
    "page1":  dict(home=(784, DESK_TOP, 0), pile=(806, DESK_TOP, 26), down=(790, DESK_TOP, 0),
                   t0=5.08, dur=0.52, mode="fly", arc=36, fall=0.62, bounce=0, z=8),
    "page2":  dict(home=(810, DESK_TOP, 0), pile=(816, DESK_TOP, 38), down=(812, DESK_TOP, 0),
                   t0=5.16, dur=0.48, mode="fly", arc=40, fall=0.70, bounce=0, z=9),
    "sbook0": dict(home=(775, 960, 0), pile=(735, DESK_TOP, 90), down=(735, DESK_TOP, 90),
                   t0=5.30, dur=0.50, mode="fly", arc=-40, fall=0.18, bounce=5, z=4),
    "sbook1": dict(home=(803, 960, 0), pile=(756, DESK_TOP, 72), down=(752, DESK_TOP, 88),
                   t0=5.40, dur=0.50, mode="fly", arc=-30, fall=0.22, bounce=6, z=5),
    "sbook2": dict(home=(831, 960, 0), pile=(774, DESK_TOP, 54), down=(770, DESK_TOP, 86),
                   t0=5.50, dur=0.48, mode="fly", arc=-24, fall=0.26, bounce=7, z=6),
    "hbook":  dict(home=None, pile=(742, DESK_TOP - 26, 90), down=(742, DESK_TOP - 26, 90),
                   t0=TL["book_fly"], dur=TL["book_fly_dur"], mode="fly", arc=-60, fall=0.2, bounce=3, z=10),
    "clock":  dict(home=(430, 760, 0), pile=(652, 1428, 62), down=(588, 1494, -82),
                   t0=5.60, dur=0.72, mode="fly", arc=-90, fall=0.34, bounce=10, z=3),
    "chair":  dict(home=(545, ROOM_FLOOR, 0), pile=(628, ROOM_FLOOR - 38, 34), down=(652, ROOM_FLOOR, 0),
                   t0=5.90, dur=0.90, mode="slide", arc=0, fall=0.30, bounce=12, z=2),
    "fbook0": dict(home=(420, ROOM_FLOOR, 0), pile=(538, ROOM_FLOOR, 0), down=(534, ROOM_FLOOR, 0),
                   t0=6.40, dur=0.80, mode="slide", arc=0, fall=0.2, bounce=2, z=1),
    "fbook1": dict(home=(420, ROOM_FLOOR - 28, 0), pile=(556, ROOM_FLOOR - 28, 6), down=(540, ROOM_FLOOR - 28, 3),
                   t0=6.44, dur=0.80, mode="slide", arc=0, fall=0.22, bounce=3, z=1),
    "fbook2": dict(home=(420, ROOM_FLOOR - 56, 0), pile=(576, ROOM_FLOOR - 56, 15), down=(522, ROOM_FLOOR - 56, -5),
                   t0=6.48, dur=0.80, mode="slide", arc=0, fall=0.30, bounce=6, z=1),
    "plant":  dict(home=(316, ROOM_FLOOR, 0), pile=(478, ROOM_FLOOR, 36), down=(462, ROOM_FLOOR, -88),
                   t0=6.80, dur=0.85, mode="slide", arc=0, fall=0.40, bounce=8, z=0),
}
PROP_ORDER = sorted(PROPS, key=lambda n: PROPS[n]["z"])


def prop_state(name, t):
    """(x, y, rot, phase, k_jitter) for a prop at time t.  phase in home/fly/pile/fall/down."""
    P = PROPS[name]
    k = field(t)
    home = P["home"]
    if home is None:  # the hero's book: lives in his hand until it flies
        home = P["pile"]
    if t < P["t0"]:
        x, y, r = home
        # crack pre-lean (S2) : things lean a few degrees toward the phone before the field
        if name.startswith("page") and t >= TL["page_lift"]:
            r += 7 * smooth(seg(t, TL["page_lift"], TL["page_lift"] + 0.5)) * (1 if name == "page2" else 0.3)
        return x, y, r, "home", 0.0, 0.0
    if t < P["t0"] + P["dur"]:
        u = seg(t, P["t0"], P["t0"] + P["dur"])
        f = ease_in(u, 2.0 if P["mode"] == "fly" else 1.7)
        x = lerp(home[0], P["pile"][0], f)
        y = lerp(home[1], P["pile"][1], f)
        r = lerp(home[2], P["pile"][2], smooth(u))
        if P["mode"] == "fly":
            y += P["arc"] * math.sin(math.pi * u)
        return x, y, r, "fly", 0.0, u
    if t < TL["drop"]:
        x, y, r = P["pile"]
        # arrival settle (tiny rebound) + strain jitter
        dt = t - (P["t0"] + P["dur"])
        if dt < 0.18:
            s = math.sin(math.pi * dt / 0.18) * 3
            x -= s * (1 if P["pile"][0] > home[0] else -1)
        return x, y, r, "pile", 0.9 * k, 1.0
    # the drop
    delay = 0.02 * (PROPS[name]["z"] % 4)
    u = (t - TL["drop"] - delay) / P["fall"]
    if u < 0:
        x, y, r = P["pile"]
        return x, y, r, "pile", 0.0, 1.0
    f = min(1.0, u * u)
    x = lerp(P["pile"][0], P["down"][0], f)
    y = lerp(P["pile"][1], P["down"][1], f)
    r = lerp(P["pile"][2], P["down"][2], min(1.0, u ** 1.5))
    if 1.0 <= u < 1.5 and P["bounce"]:
        y -= P["bounce"] * math.sin(math.pi * (u - 1.0) / 0.5)
    phase = "fall" if u < 1.0 else "down"
    return x, y, r, phase, 0.0, min(1.0, u)


def prop_vel(name, t):
    x0, y0, *_ = prop_state(name, t - 1 / FPS)
    x1, y1, *_ = prop_state(name, t)
    return x1 - x0, y1 - y0


# ── procedural sprite tiles (2x, RGBA) with anchors ──────────────────────────
S2 = 2  # sprite oversampling


def _tile(w, h):
    im = Image.new("RGBA", (int(w * S2), int(h * S2)), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im, "RGBA")


def _poly(d, pts, fill=None, outline=INK, width=3):
    d.polygon(pts, fill=fill, outline=outline, width=width * S2 // 2 if width else 0)


def sprite_cup():
    im, d = _tile(80, 64)
    X = lambda x: (x + 40) * S2; Y = lambda y: (y + 60) * S2
    body = [(X(-22), Y(-50)), (X(22), Y(-50)), (X(18), Y(0)), (X(-18), Y(0))]
    d.polygon(body, fill=PAPER, outline=INK, width=4)
    d.ellipse([X(-22), Y(-56), X(22), Y(-44)], fill=PAPER_D, outline=INK, width=4)
    d.ellipse([X(-16), Y(-54), X(16), Y(-46)], fill=(70, 50, 36, 255))
    d.arc([X(18), Y(-44), X(40), Y(-14)], 270, 90, fill=INK, width=5)
    d.arc([X(20), Y(-41), X(37), Y(-17)], 270, 90, fill=INK, width=2)
    return im, (40 * S2, 60 * S2)


def sprite_book(w, h, tone=0.0, spine_left=True):
    im, d = _tile(w + 8, h + 8)
    X = lambda x: (x + (w + 8) / 2) * S2; Y = lambda y: (y + h + 4) * S2
    col = tuple(int(c * (1 - 0.18 * tone)) for c in PAPER_D)
    d.rectangle([X(-w / 2), Y(-h), X(w / 2), Y(0)], fill=col, outline=INK, width=4)
    sx = -w / 2 + 6 if spine_left else w / 2 - 6
    d.line([(X(sx), Y(-h)), (X(sx), Y(0))], fill=INK, width=3)
    for yy in np.linspace(-h * 0.8, -h * 0.2, 3):
        d.line([(X(-w / 2 + 10), Y(yy)), (X(w / 2 - 4), Y(yy))], fill=SOFT + (120,), width=2)
    return im, ((w + 8) / 2 * S2, (h + 4) * S2)


def sprite_flatbook(w=120, h=28, tone=0.0):
    im, d = _tile(w + 8, h + 8)
    X = lambda x: (x + (w + 8) / 2) * S2; Y = lambda y: (y + h + 4) * S2
    col = tuple(int(c * (1 - 0.15 * tone)) for c in PAPER_D)
    d.rectangle([X(-w / 2), Y(-h), X(w / 2), Y(0)], fill=col, outline=INK, width=4)
    d.rectangle([X(-w / 2), Y(-h), X(w / 2), Y(-h + 7)], fill=PAPER, outline=INK, width=3)
    d.line([(X(-w / 2 + 12), Y(-h / 2)), (X(w / 2 - 12), Y(-h / 2))], fill=SOFT + (110,), width=2)
    return im, ((w + 8) / 2 * S2, (h + 4) * S2)


def sprite_clock(r=72):
    im, d = _tile(r * 2 + 12, r * 2 + 12)
    c = (r + 6) * S2
    d.ellipse([c - r * S2, c - r * S2, c + r * S2, c + r * S2], fill=PAPER, outline=INK, width=6)
    d.ellipse([c - (r - 9) * S2, c - (r - 9) * S2, c + (r - 9) * S2, c + (r - 9) * S2], outline=SOFT + (150,), width=2)
    for i in range(12):
        a = math.radians(i * 30)
        l = 12 if i % 3 == 0 else 6
        d.line([(c + (r - 14) * S2 * math.sin(a), c - (r - 14) * S2 * math.cos(a)),
                (c + (r - 14 - l) * S2 * math.sin(a), c - (r - 14 - l) * S2 * math.cos(a))], fill=INK, width=4)
    d.line([(c, c), (c + 0.52 * r * S2 * math.sin(math.radians(300)), c - 0.52 * r * S2 * math.cos(math.radians(300)))], fill=INK, width=8)
    d.line([(c, c), (c + 0.78 * r * S2 * math.sin(math.radians(60)), c - 0.78 * r * S2 * math.cos(math.radians(60)))], fill=INK, width=6)
    d.ellipse([c - 7, c - 7, c + 7, c + 7], fill=INK)
    return im, (c, c)


def sprite_chair():
    im, d = _tile(160, 270)
    X = lambda x: (x + 80) * S2; Y = lambda y: (y + 262) * S2
    lw = 9 * S2
    # back post + rails
    d.line([(X(-52), Y(0)), (X(-58), Y(-250))], fill=INK, width=lw)
    d.line([(X(-58), Y(-250)), (X(-14), Y(-246))], fill=INK, width=lw)
    d.line([(X(-56), Y(-205)), (X(-16), Y(-202))], fill=INK, width=lw - 3)
    d.line([(X(-55), Y(-165)), (X(-17), Y(-163))], fill=INK, width=lw - 3)
    # seat
    d.polygon([(X(-60), Y(-128)), (X(58), Y(-124)), (X(62), Y(-108)), (X(-62), Y(-112))], fill=PAPER_D, outline=INK, width=4)
    # legs
    d.line([(X(50), Y(-110)), (X(56), Y(0))], fill=INK, width=lw)
    d.line([(X(-50), Y(-112)), (X(-52), Y(0))], fill=INK, width=lw)
    d.line([(X(-50), Y(-50)), (X(54), Y(-48))], fill=INK, width=lw - 4)
    return im, (80 * S2, 262 * S2)


def sprite_plant():
    im, d = _tile(150, 190)
    X = lambda x: (x + 75) * S2; Y = lambda y: (y + 184) * S2
    # leaves
    for ang, L, wdt in ((-70, 120, 26), (-35, 110, 24), (0, 128, 28), (32, 104, 22), (66, 118, 26), (-18, 80, 18), (16, 86, 18)):
        pts = []
        for u in np.linspace(0, 1, 18):
            px = (wdt * math.sin(math.pi * u)) * (1 if u < 1 else 0)
            py = -L * u
            pts.append(rot_pt(px, py, ang))
        for u in np.linspace(1, 0, 18):
            px = -(wdt * math.sin(math.pi * u))
            py = -L * u
            pts.append(rot_pt(px, py, ang))
        d.polygon([(X(px), Y(py - 58)) for px, py in pts], fill=(214, 206, 186, 255), outline=INK, width=4)
        tip = rot_pt(0, -L, ang)
        d.line([(X(0), Y(-58)), (X(tip[0] * 0.92), Y(tip[1] * 0.92 - 58))], fill=INK + (110,), width=2)
    # pot
    d.polygon([(X(-34), Y(-62)), (X(34), Y(-62)), (X(26), Y(0)), (X(-26), Y(0))], fill=PAPER_D, outline=INK, width=4)
    d.rectangle([X(-38), Y(-74), X(38), Y(-60)], fill=PAPER, outline=INK, width=4)
    d.ellipse([X(-30), Y(-70), X(30), Y(-64)], fill=(60, 48, 40, 255))
    return im, (75 * S2, 184 * S2)


def sprite_phone(face_up):
    """Foreshortened slab 128 x 52; anchor = bottom centre."""
    w, h, th = 128, 44, 10
    im, d = _tile(w + 20, h + th + 20)
    X = lambda x: (x + (w + 20) / 2) * S2; Y = lambda y: (y + h + th + 10) * S2
    # side (thickness)
    d.rounded_rectangle([X(-w / 2), Y(-h - th + th), X(w / 2), Y(0)], radius=10 * S2, fill=(40, 38, 42, 255), outline=INK, width=4)
    if face_up:
        d.rounded_rectangle([X(-w / 2), Y(-h - th), X(w / 2), Y(-th)], radius=10 * S2, fill=(22, 20, 24, 255), outline=INK, width=4)
        d.rounded_rectangle([X(-w / 2 + 7), Y(-h - th + 6), X(w / 2 - 7), Y(-th - 6)], radius=6 * S2, fill=AMBER + (255,))
        d.rounded_rectangle([X(-w / 2 + 7), Y(-h - th + 6), X(w / 2 - 7), Y(-h - th + 16)], radius=4 * S2, fill=AMBER_HI + (255,))
        d.rounded_rectangle([X(-30), Y(-h / 2 - th - 6), X(30), Y(-h / 2 - th + 6)], radius=6 * S2, fill=(255, 240, 200, 255))
        d.ellipse([X(-w / 2 + 12), Y(-h - th + 18), X(-w / 2 + 20), Y(-h - th + 26)], fill=(255, 255, 255, 230))
    else:
        d.rounded_rectangle([X(-w / 2), Y(-h - th), X(w / 2), Y(-th)], radius=10 * S2, fill=PAPER_D, outline=INK, width=4)
        d.rounded_rectangle([X(-w / 2 + 8), Y(-h - th + 7), X(-w / 2 + 30), Y(-h - th + 25)], radius=5 * S2, fill=(50, 46, 48, 255), outline=INK, width=2)
        d.ellipse([X(-w / 2 + 12), Y(-h - th + 10), X(-w / 2 + 19), Y(-h - th + 17)], fill=(20, 18, 20, 255))
        d.ellipse([X(-w / 2 + 20), Y(-h - th + 11), X(-w / 2 + 26), Y(-h - th + 17)], fill=(20, 18, 20, 255))
    return im, ((w + 20) / 2 * S2, (h + th + 10) * S2)


_SPRITES = {}


def sprites():
    if _SPRITES:
        return _SPRITES
    _SPRITES["cup"] = sprite_cup()
    _SPRITES["sbook0"] = sprite_book(26, 110, 0.0)
    _SPRITES["sbook1"] = sprite_book(30, 96, 0.5)
    _SPRITES["sbook2"] = sprite_book(24, 104, 0.25)
    _SPRITES["hbook"] = sprite_book(56, 80, 0.4)
    _SPRITES["fbook0"] = sprite_flatbook(124, 28, 0.3)
    _SPRITES["fbook1"] = sprite_flatbook(112, 26, 0.0)
    _SPRITES["fbook2"] = sprite_flatbook(100, 24, 0.5)
    _SPRITES["clock"] = sprite_clock(72)
    _SPRITES["chair"] = sprite_chair()
    _SPRITES["plant"] = sprite_plant()
    _SPRITES["phone_up"] = sprite_phone(True)
    _SPRITES["phone_down"] = sprite_phone(False)
    return _SPRITES


# ── hero choreography ────────────────────────────────────────────────────────
def P_grip(t, strain=1.0):
    a = math.sin(t * 9.0)
    return dict(yaw=0, lean=0, twist=0, head=4 + 3 * a * strain, head_t=0, sh_up=0.02 * strain,
                al=-166, az_l=4, el=0, ef_l=10 + 10 * strain, ar=166, az_r=4, er=0, ef_r=10 + 10 * strain,
                ll=-3, lz_l=0, kl=6, lr=3, lz_r=0, kr=6, hl='fist', hr='fist', _br=0)


def P_brace(t):
    b = math.sin(t * 7.0)
    return dict(yaw=0, lean=-16 - 2 * b, head=-8, head_t=10, al=-78, az_l=12, el=0, ef_l=22, ar=82, az_r=12, er=0, ef_r=22,
                ll=-27, lz_l=10, kl=24, lr=24, lz_r=10, kr=24, hl='open', hr='open', _br=0)


def P_crouch(t, deep=1.0):
    return dict(yaw=4, lean=4 * deep, head=6, head_t=12, al=-60 * deep - 14, az_l=18 * deep, el=0, ef_l=30 * deep + 8,
                ar=60 * deep + 14, az_r=18 * deep, er=0, ef_r=30 * deep + 8,
                ll=-20 * deep - 4, lz_l=34 * deep, kl=58 * deep + 2, lr=20 * deep + 4, lz_r=34 * deep, kr=58 * deep + 2,
                hl='open', hr='open', _br=0)


def P_squat_reach(t):
    """Deep squat on the desk, right hand down on the phone."""
    return dict(yaw=6, lean=22, head=16, head_t=18, al=-70, az_l=22, el=0, ef_l=40,
                ar=0, az_r=0, er=-20, ef_r=0,
                ll=-26, lz_l=85, kl=130, lr=26, lz_r=81, kr=124, hl='open', hr='open', _br=0)


def P_stand_look(t):
    p = T.p_idle(t)
    p.update(dict(head_t=22, head=8, yaw=8))
    return p


def hero_state(t):
    """Returns None when the hero is not in the shot, else a dict:
    feet (x, y) world · pose · expr · look · blink · flip · rot (deg, PIL CCW) · pivot (joint name or None)
    · pivot_world (x, y) when rotated · smear (dx, dy) · book (bool: holds the book) · s"""
    if t < TL["walk_start"]:
        return None
    st = dict(s=HERO_S, expr="sly", look=(0.0, 0.0), blink=0.0, flip=False, rot=0.0, pivot=None,
              pivot_world=None, smear=(0, 0), book=False, shadow=True, surface=ROOM_FLOOR)
    bl = 0.0
    for tb in (2.9, 4.3, 8.2, 10.25, 12.9, 14.1, 16.2, 17.7):
        if tb <= t < tb + 0.14:
            bl = 1.0 if t < tb + 0.08 else 1 - (t - tb - 0.08) / 0.06
    st["blink"] = bl

    if t < TL["walk_end"]:
        u = seg(t, TL["walk_start"], TL["walk_end"])
        x = lerp(-70, 400, u)
        p = T.p_walk(t)
        p["yaw"] = 55
        # left hand carries the book against the chest
        p.update(dict(al=-24, az_l=58, el=-18, ef_l=86, hl='fist'))
        st.update(feet=(x, ROOM_FLOOR), pose=p, expr="sly", look=(0.45, 0.05), book=True)
        if t > 3.25:  # notices: head turns to the desk
            w = smooth(seg(t, 3.25, 3.6))
            p["head_t"] = 30 * w
            st["expr"] = "think" if w > 0.5 else "sly"
            st["look"] = (0.45 + 0.4 * w, 0.05 + 0.25 * w)
        return st

    if t < TL["field_on"]:
        p = T.p_idle(t)
        p.update(dict(yaw=10, head_t=34, head=6, al=-24, az_l=58, el=-18, ef_l=86, hl='fist'))
        st.update(feet=(400, ROOM_FLOOR), pose=p, expr="shock" if t > 4.3 else "think", look=(0.85, 0.35), book=True)
        return st

    if t < TL["brace_end"]:
        k = field(t)
        u = seg(t, TL["field_on"], TL["brace_end"])
        x = 400 + 48 * ease_in(u, 2.0)
        base = T.p_idle(t)
        base.update(dict(yaw=10, head_t=30, al=-24, az_l=58, el=-18, ef_l=86, hl='fist'))
        p = blend_pose(base, P_brace(t), smooth(seg(t, TL["field_on"], TL["field_on"] + 0.3)))
        if t >= TL["book_fly"]:
            p["hl"] = "open"
        st.update(feet=(x, ROOM_FLOOR), pose=p, expr="angry" if k > 0.5 else "shock", look=(0.8, 0.4),
                  book=t < TL["book_fly"], smear=(-6 * k, 0))
        return st

    if t < TL["grab"]:
        u = seg(t, TL["lunge"], TL["grab"])
        x = lerp(448, GRAB_FEET_X, smooth(u))
        y = ROOM_FLOOR - 70 * math.sin(math.pi * u)
        p = blend_pose(P_brace(t), P_grip(t, 0.4), smooth(u))
        p["lean"] = lerp(-18, 0, u)
        st.update(feet=(x, y), pose=p, expr="angry", look=(-0.6, -0.5), shadow=u < 0.15 or u > 0.85)
        return st

    if t < TL["letgo"]:
        # hanging from the lintel: rotate the whole figure about the hands
        u = smooth(seg(t, TL["flag_start"], TL["flag_full"]))
        ang = 62 * u + 5 * math.sin(2 * math.pi * 0.6 * (t - 6.0)) * u + 3 * math.sin(2 * math.pi * 2.3 * t) * u
        if TL["flag_full"] <= t < TL["flag_full"] + 0.5:   # overshoot settle
            ang += 6 * math.sin(math.pi * (t - TL["flag_full"]) / 0.5)
        px, py = LINTEL
        for ts in (TL["slip1"], TL["slip2"]):
            if t >= ts:
                px += 6 * ease_out(seg(t, ts, ts + 0.08), 2)
                py += 2 * ease_out(seg(t, ts, ts + 0.08), 2)
                if t < ts + 0.3:
                    ang += 7 * math.sin(math.pi * seg(t, ts, ts + 0.3))
        strain = 0.4 + 0.6 * u
        p = P_grip(t, strain)
        kick = math.sin(2 * math.pi * 1.9 * t)
        p["kl"] = 14 + 22 * max(0.0, kick) * u
        p["kr"] = 14 + 22 * max(0.0, -kick) * u
        p["lz_l"] = 6 * kick * u
        p["lz_r"] = -6 * kick * u
        expr, look = ("determined", (0.0, 0.9))
        if t >= 7.6:
            expr = "angry"
        if TL["look_lens"] <= t < TL["look_end"]:
            w = smooth(seg(t, TL["look_lens"], TL["look_lens"] + 0.18))
            expr = "sly" if w > 0.5 else "angry"
            look = (0.0, 0.9 * (1 - w))
            p["head"] = 4 - 8 * w
        elif t >= TL["look_end"]:
            expr = "determined"
            look = (0.0, 0.9 * smooth(seg(t, TL["look_end"], TL["look_end"] + 0.2)))
        st.update(feet=(px, py), pose=p, expr=expr, look=look, rot=ang, pivot="hands", pivot_world=(px, py),
                  shadow=False)
        return st

    if t < TL["land"]:
        u = seg(t, TL["letgo"], TL["land"])
        f = ease_in(u, 1.6)
        hx = lerp(HIP_LETGO[0], HIP_LAND[0], f)
        hy = lerp(HIP_LETGO[1], HIP_LAND[1], f) - 40 * math.sin(math.pi * u)
        ang = lerp(62, 0, smooth(u))
        p = blend_pose(P_grip(t, 1.0), P_crouch(t, 1.0), smooth(seg(u, 0.35, 1.0)))
        st.update(feet=(hx, hy), pose=p, expr="shock", look=(0.3, 0.8), rot=ang, pivot="hip", pivot_world=(hx, hy),
                  shadow=False, smear=(-(1 - u) * 26, -(1 - u) * 8), surface=DESK_TOP)
        return st

    if t < TL["drop"]:
        u = seg(t, TL["land"], TL["slap"])
        p = blend_pose(P_crouch(t, 1.0), P_squat_reach(t), smooth(u))
        if t >= TL["slap"]:
            p = P_squat_reach(t)
            p["ar"] = 0 + 4 * math.sin(2 * math.pi * 3 * t)
        expr = "focus" if t < TL["slap"] else "determined"
        if t >= TL["glow_off"]:
            expr = "neutral"
        st.update(feet=(LAND_FEET_X, DESK_TOP), pose=p, expr=expr, look=(0.25, 0.85), surface=DESK_TOP)
        return st

    # after the drop: knee buckle, then stands up on the desk
    u = seg(t, TL["drop"], TL["drop"] + 0.18)
    buck = math.sin(math.pi * u) * 0.35
    w = smooth(seg(t, TL["stand"] - 0.4, TL["stand"] + 0.6))
    base = blend_pose(P_squat_reach(t), P_crouch(t, 0.9 + buck), 0.5 + 0.5 * buck)
    p = blend_pose(base, P_stand_look(t), w)
    expr = "neutral"
    look = (0.25, 0.8 * (1 - w) + 0.25 * w)
    if 13.5 <= t < 14.3:   # looks left at the fallen room
        v = math.sin(math.pi * seg(t, 13.5, 14.3))
        p["head_t"] = lerp(p.get("head_t", 0), -36, v)
        look = (-0.6 * v, 0.2)
    if t >= 16.55:   # meaning shot: turns to the lens, proud
        v = smooth(seg(t, 16.55, 16.95))
        p["head_t"] = lerp(p.get("head_t", 0), 0, v)
        p["head"] = lerp(p.get("head", 0), -3, v)
        look = (0.25 * (1 - v), 0.25 * (1 - v))
        expr = "proud" if v > 0.5 else "neutral"
    st.update(feet=(LAND_FEET_X, DESK_TOP), pose=p, expr=expr, look=look, surface=DESK_TOP)
    return st


# geometry constants solved from the rig (hands midpoint for the grip pose etc.)
def solve(pose, s=HERO_S, flip=False):
    """Joint dict (hand_l/hand_r/hip/head ...) in world coords for feet at (0, 0)."""
    K, J, KS, sgn = SH._solve(0, 0, s, pose, flip)
    return dict(hand_l=J["hal"], hand_r=J["har"], hip=J["hipc"], head=J["hctr"], foot_l=J["ftl"], foot_r=J["ftr"])


def _hands_mid(J):
    return ((J["hand_l"][0] + J["hand_r"][0]) / 2, (J["hand_l"][1] + J["hand_r"][1]) / 2)


_J0 = solve(P_grip(0, 0.4))
_HM = _hands_mid(_J0)
GRAB_FEET_X = LINTEL[0] - _HM[0]
GRIP_HANDS_UP = -_HM[1]                       # hands above the feet when standing with arms up
_Jc = solve(P_crouch(0, 1.0))
HIP_ABOVE_FEET_CROUCH = -_Jc["hip"][1]
LAND_FEET_X = 806.0
HIP_LAND = (LAND_FEET_X + _Jc["hip"][0], DESK_TOP - HIP_ABOVE_FEET_CROUCH)
_Jg = solve(P_grip(0, 1.0))
_d_hands_hip = ((_Jg["hip"][0] - _hands_mid(_Jg)[0]) ** 2 + (_Jg["hip"][1] - _hands_mid(_Jg)[1]) ** 2) ** 0.5


def _hip_at_letgo():
    px, py = LINTEL[0] + 12, LINTEL[1] + 4
    ang = math.radians(62)
    return (px + _d_hands_hip * math.sin(ang), py + _d_hands_hip * math.cos(ang))


HIP_LETGO = _hip_at_letgo()


# ── lamp (procedural, bends with the field) ─────────────────────────────────
def lamp_geometry(t):
    k = field(t)
    base = (728.0, DESK_TOP)
    # normal pose
    elbow0, head0, hang0 = (752.0, 1158.0), (822.0, 1192.0), 0.0
    elbow1, head1, hang1 = (790.0, 1196.0), (838.0, 1228.0), 10.0
    w = k
    if t >= TL["drop"]:
        dt = t - TL["drop"]
        w = 0.42 * math.exp(-dt * 1.8) * math.cos(2 * math.pi * 1.6 * dt) + 0.08
    e = (lerp(elbow0[0], elbow1[0], w), lerp(elbow0[1], elbow1[1], w))
    h = (lerp(head0[0], head1[0], w), lerp(head0[1], head1[1], w))
    return base, e, h, lerp(hang0, hang1, w)


# ── pendulum angle (clockwise +, hangs from the clock's bottom) ──────────────
def pendulum_angle(t):
    tau = t
    if t < TL["pend_lean"]:
        return 11 * math.sin(2 * math.pi * 0.5 * tau)
    if t < TL["pend_lean"] + 0.6:
        u = smooth(seg(t, TL["pend_lean"], TL["pend_lean"] + 0.6))
        return lerp(11 * math.sin(2 * math.pi * 0.5 * TL["pend_lean"]), 30, u) + 2 * math.sin(2 * math.pi * 9 * t) * u
    if t < PROPS["clock"]["t0"]:
        return 30 + 1.5 * math.sin(2 * math.pi * 9 * t)
    return 30


# ── rug (slides and bunches toward the desk) ────────────────────────────────
def rug_state(t):
    k = field(t)
    u = ease_in(seg(t, 5.4, 6.4), 1.8) if t >= 5.4 else 0.0
    if t >= TL["drop"]:
        u = 1.0
    x0 = lerp(360, 500, u)
    x1 = lerp(660, 690, u)
    return x0, x1, u


def dust_events():
    """(t, x, y, size, strength) — puffs the renderer draws for 0.6 s."""
    ev = [(PROPS["clock"]["t0"], 430, 700, 60, 0.5),
          (TL["land"], LAND_FEET_X, DESK_TOP, 90, 0.7),
          (TL["drop"] + 0.30, 652, ROOM_FLOOR, 120, 1.0),
          (TL["drop"] + 0.34, 588, ROOM_FLOOR, 90, 0.8),
          (TL["drop"] + 0.40, 440, ROOM_FLOOR, 90, 0.7),
          (TL["drop"] + 0.30, 530, ROOM_FLOOR, 60, 0.5),
          (TL["drop"] + 0.20, 752, DESK_TOP, 50, 0.4)]
    return ev


# ── field flow: ink specks streaming toward the phone (the pull made visible in every frame) ──
N_FLOW = 64


def flow_particles(t):
    """[(x, y, vx, vy, alpha)] in world px while the field is on; after the drop they fall for 0.45 s."""
    out = []
    k = field(t)
    falling = TL["drop"] <= t < TL["drop"] + 0.45
    if k <= 0.02 and not falling:
        return out
    px, py = PHONE[0], PHONE[1] - 20
    for i in range(N_FLOW):
        h1, h2, h3, h4 = hash01(i, 11), hash01(i, 12), hash01(i, 13), hash01(i, 14)
        ang = math.pi * (0.55 + 1.9 * h1)              # mostly from the left / above (the room side)
        R0 = 420 + 980 * h2
        T = 1.1 + 1.5 * h3
        tt_ = (t if not falling else TL["drop"]) - TL["field_on"]
        p = ((tt_ / T) + h4) % 1.0
        pe = p ** 1.7                                  # accelerate toward the phone
        r = R0 * (1 - pe)
        x = px + math.cos(ang) * r
        y = py + math.sin(ang) * r * 0.62
        if y > ROOM_FLOOR - 6:
            y = ROOM_FLOOR - 6 - (y - (ROOM_FLOOR - 6)) * 0.2
        if x < -40 or x > 1120 or y < -60:
            continue
        dr = R0 * 1.7 * p ** 0.7 / T                   # radial speed px/s
        vx = -math.cos(ang) * dr * k
        vy = -math.sin(ang) * dr * 0.62 * k
        a = min(1.0, p / 0.12) * min(1.0, (1 - p) / 0.08) * k
        if falling:
            dt = t - TL["drop"]
            y += 2600 * dt * dt
            vx, vy = 0.0, 2600 * 2 * dt
            a = min(1.0, p / 0.12) * max(0.0, 1 - dt / 0.45)
            if y > ROOM_FLOOR - 4:
                continue
        if a > 0.02:
            out.append((x, y, vx, vy, a * (0.45 + 0.55 * h3)))
    return out


def sweat_drops(t):
    """[(t0, x0, y0)] spawn events for strain drops during the flag; each lives 0.5 s flying toward the phone."""
    ev = []
    t0 = 6.9
    j = 0
    while t0 < TL["letgo"] - 0.1:
        ev.append((t0, j))
        t0 += 0.30 + 0.22 * hash01(j, 21)
        j += 1
    return ev


def land_squash(t):
    """(sx, sy) squash & stretch around the feet on the desk landing and on the stand-up."""
    for t0, amt in ((TL["land"], 0.16), (TL["stand"] + 0.42, 0.05)):
        if t0 <= t < t0 + 0.2:
            u = (t - t0) / 0.2
            d = amt * math.sin(math.pi * u) * math.exp(-u * 1.5) * (1 if u < 0.5 else -0.45)
            return 1 + d * 0.8, 1 - d
    return 1.0, 1.0


if __name__ == "__main__":
    print("GRAB_FEET_X", GRAB_FEET_X, "hands up", GRIP_HANDS_UP, "HIP_LAND", HIP_LAND, "HIP_LETGO", HIP_LETGO)
    for t in (0, 1.0, 3.0, 5.2, 6.5, 9.9, 11.2, 11.7, 12.5, 15.0):
        h = hero_state(t)
        print(t, field(t), round(glow(t), 2), phone_state(t)["face"], h and (h["feet"], h["expr"], h["rot"]))