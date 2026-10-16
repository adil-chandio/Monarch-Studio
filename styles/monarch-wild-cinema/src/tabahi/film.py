"""TABAHI FILM — the compositor. One frame pipeline, declarative shot plan.

Pipeline order (fixed, each stage justified):

  1. STAGE   2.5D parallax plate        -- the world moves in depth
  2. GRADE   cinematic look             -- before type, so type stays crisp
  3. AIR     rays / haze / motes        -- volumetric life
  4. ACTION  streaks / impact / shake   -- physical event
  5. TYPE    extruded kinetic layers    -- the idea, readable
  6. CUT     transition blend           -- motivated hand-off
  7. WRITE   raw frames into ffmpeg     -- streaming, no PNG scratch

An episode is DATA: a shot plan (JSON) plus plates. That is what makes the
engine agent-authorable — A03 writes the plan, A05 runs the renderer, and
neither needs to touch Python.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image

from . import core as C
from . import depth as D
from . import films as F
from . import grade as G
from . import kinetic as K
from . import score as S
from . import transitions as T


# ─────────────────────────────────────────────────────────────────────────────
# WRITER  (raw frames straight into ffmpeg; no PNG scratch, no wasted disk)
# ─────────────────────────────────────────────────────────────────────────────

class Writer:
    def __init__(self, path, size=(C.W, C.H), fps: int = C.FPS, crf: int = 19,
                 preset: str = "medium", pix_fmt: str = "yuv420p"):
        self.path = pathlib.Path(path)
        self.size = size
        cmd = [C.ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{size[0]}x{size[1]}", "-r", str(fps), "-i", "-",
               "-an", "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
               "-pix_fmt", pix_fmt, "-movflags", "+faststart", str(self.path)]
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        self.frames = 0

    def write(self, frame: np.ndarray):
        if frame.dtype != np.uint8:
            frame = np.clip(frame, 0, 255).astype(np.uint8)
        self.p.stdin.write(frame.tobytes())
        self.frames += 1

    def close(self):
        self.p.stdin.close()
        err = self.p.stderr.read().decode()[-2000:]
        rc = self.p.wait()
        if rc != 0:
            print(f"  !! encoder exit {rc}\n{err}", file=sys.stderr)
            raise SystemExit(1)
        return self.path


# ─────────────────────────────────────────────────────────────────────────────
# TYPE LAYER CACHE  (build once per spec, animate per frame)
# ─────────────────────────────────────────────────────────────────────────────

_LAYER_CACHE: dict[str, dict | None] = {}


def _key(spec: dict) -> str:
    """Cache key. The CANVAS is part of the identity: a headline laid out for
    1920x1080 is not the same layer as one laid out for 1080x1920, and sharing
    the cache between the two would put a landscape layer on a portrait frame."""
    return hashlib.sha1(f"{C.W}x{C.H}|{json.dumps(spec, sort_keys=True)}".encode()).hexdigest()[:16]


def _add_scrim(lay, amount: float = 0.42, pad: int = 48, feather: int = 34, pos=(0, 0)):
    """Composite a soft dark panel behind the ink.

    MEASURED NEED: G05 measured 2.25:1 on shot 07's headline against a lit
    plate (the gate wants 4.5:1). The fix is not a darker grade for the whole
    shot — it is a scrim under the type, which is what broadcast lower-thirds
    do and what WF-05's legibility chapter requires.
    """
    import numpy as np
    from PIL import Image, ImageFilter
    ax = np.array(lay)
    ink = ax[..., 3] > 24
    if ink.sum() < 200:
        return lay
    ys, xs = np.where(ink)
    # MEASURED BUG: the panel was placed with the layer's on-screen position
    # subtracted, which is only correct for full-frame canvases. Card layers
    # (species, rule, lower, gauge, source, callout) return a small image that
    # is positioned afterwards, so subtracting `pos` pushed the panel off the
    # card — shot 05's species card measured 1.88:1 with a scrim that had
    # landed 620 px above the text. The panel is built in LAYER coordinates.
    lw, lh = lay.size
    y0 = max(int(ys.min()) - pad, 0)
    y1 = min(int(ys.max()) + pad, lh)
    x0 = max(int(xs.min()) - pad, 0)
    x1 = min(int(xs.max()) + pad, lw)
    if y1 - y0 < 4 or x1 - x0 < 4:
        return lay
    panel = Image.new("L", (x1 - x0, y1 - y0), int(255 * amount))
    panel = panel.filter(ImageFilter.GaussianBlur(feather))
    dark = Image.new("RGBA", (x1 - x0, y1 - y0), (6, 8, 14, 255))
    out = Image.new("RGBA", lay.size, (0, 0, 0, 0))
    out.paste(dark, (x0, y0), panel)
    return Image.alpha_composite(out, lay)


def _build_pil(spec: dict):
    """Build the type layer, then apply the scrim every legible layer needs.

    MEASURED (PROOF-01, delivered frames, WCAG ink-vs-surroundings): headline
    1.61, stat 2.07, mark 1.21-1.33, gauge 1.17, lower 2.48 — the gate wants
    4.5:1. Type over a lit wildlife plate does not reach that without a
    backdrop, so the scrim is applied centrally, for all kinds, from the spec.
    """
    _raw, lay, pos = _build_pil_pair(spec)
    return lay, pos


def _build_pil_pair(spec: dict):
    """(raw ink layer, scrimmed layer, fitted position).

    One place computes the position, so a gate can never sample a box that the
    renderer did not use. MEASURED: G05 briefly measured 1.00 because it asked
    the builder for the pre-fit position while the delivered frame used the
    fitted one — it compared the glyphs with themselves.
    """
    raw, pos = _build_pil_raw(spec)
    pos = _fit_safe(raw, pos)
    # No scrim on the brand mark: MEASURED in the delivered frame — a scrim sized
    # to a small corner mark paints a hard-cornered black rectangle over the plate
    # (the ~1500 opaque pixels give `_add_scrim` a tiny panel and the 34 px feather
    # has nothing to fade into). The mark is bone + amber over a graded plate and
    # measures 6.5:1 unaided.
    amt = spec.get("scrim")
    if amt and spec.get("kind") != "mark":
        lay = _add_scrim(raw, float(amt), pos=pos)
    else:
        lay = raw
    return raw, lay, pos


def _fit_safe(lay, pos, margin: int = 24):
    """Translate a positioned layer until its INK sits inside the safe band.

    MEASURED (9:16 attempt #2, measured on the built layers): nominal placement
    is not enough. `pos` is a layer anchor, but what the viewer reads is the ink,
    and the ink extends past `anchor + size` by the extrusion depth (13 steps),
    the glow and the underline. A portrait headline placed by its nominal bottom
    landed at y 1402-1665 against a safe band that ends at 1620 — i.e. inside the
    platform's action bar. This measures the RAW alpha-ink bbox and translates.
    The scrim panel is deliberately excluded: it is a soft gradient and may bleed
    past the band, the letters may not.

    Horizontal: the ink is centred inside the band as well, which also fixes
    landscape `xy` values that were written for a 1920-wide frame.
    """
    bb = lay.getchannel("A").getbbox()
    if bb is None:
        return pos
    x, y = int(pos[0]), int(pos[1])
    y0, y1 = y + bb[1], y + bb[3]
    x0, x1 = x + bb[0], x + bb[2]
    safe0, safe1 = C.SAFE

    if y1 - y0 <= (safe1 - safe0):
        if y0 < safe0:
            y += safe0 - y0
        elif y1 > safe1:
            y -= y1 - safe1
    else:                       # taller than the band: align to its top
        y += safe0 - y0
    if x1 - x0 <= (C.W - 2 * margin):
        if x0 < margin:
            x += margin - x0
        elif x1 > C.W - margin:
            x -= x1 - (C.W - margin)
    return (x, y)


def _build_pil_raw(spec: dict):
    """Build the RGBA type layer in PIL, once per unique spec."""
    kind = spec.get("kind", "headline")
    accent = spec.get("accent", "amber")
    if kind == "headline":
        return K.headline(spec["text"], spec.get("size", 132), spec.get("accent_word"),
                          align=spec.get("align", "center"), accent=accent,
                          pos=spec.get("pos", "lower")), (0, 0)
    if kind == "stat":
        return K.stat_slam(spec["value"], spec.get("unit", ""), spec.get("note", ""),
                           accent=accent, pos=spec.get("pos", "center"),
                           big=spec.get("big", 260)), (0, 0)
    if kind == "rule":
        lay = K.rule_card(int(spec["number"]), spec["text"], accent)
        if lay.size[0] > C.W - 96:
            lay = lay.resize((C.W - 96, max(int(lay.size[1] * (C.W - 96) / lay.size[0]), 1)),
                             Image.LANCZOS)
        return lay, spec.get("xy", (int((C.W - lay.size[0]) / 2),
                                    C.H - 520 + int(spec["number"]) * 170))
    if kind == "species":
        lay = K.species_card(spec["name"], spec["answer"], accent,
                             min(int(spec.get("width", 1180)), C.W - 96))
        if "xy" in spec:
            return lay, spec["xy"]
        bottom = (C.SAFE[1] - lay.size[1] - 20) if C.PORTRAIT else (C.H - lay.size[1] - 150)
        return lay, (int((C.W - lay.size[0]) / 2), bottom)
    if kind == "lower":
        lay = K.lower_third(spec["kicker"], spec["main"], accent,
                            min(int(spec.get("width", 1080)), C.W - 96))
        return lay, spec.get("xy", (112, (C.SAFE[1] - lay.size[1] - 20) if C.PORTRAIT
                                    else (C.H - 360)))
    from . import viz as V
    if kind == "chart":
        lay = V.bar_chart([tuple(r) for r in spec["rows"]], spec.get("title", ""),
                          spec.get("unit", ""), accent, spec.get("reveal", 1.0),
                          min(int(spec.get("width", 1180)), C.W - 96))
        return lay, spec.get("xy", (112, C.H - lay.size[1] - 130))
    if kind == "range":
        lay = V.range_chart(spec["rows"], spec.get("title", ""), spec.get("note", ""),
                            spec.get("reveal", 1.0))
        return lay, spec.get("xy", (112, C.H - lay.size[1] - 130))
    if kind == "gauge":
        # portrait: a 520 px gauge in a 1080 px frame leaves no margin for the
        # source stamp or the headline, so the default size drops with the canvas
        gsize = int(spec.get("size", 520 if not C.PORTRAIT else 430))
        lay = V.gauge(spec["value"], spec["label"], spec.get("sub", ""), accent, gsize)
        if "xy" in spec:
            return lay, spec["xy"]
        dx = 130 if not C.PORTRAIT else 90
        dy = (130 if not C.PORTRAIT else 40)
        return lay, (C.W - lay.size[0] - dx, (C.SAFE[0] + 30) if C.PORTRAIT
                     else (C.H - lay.size[1] - dy))
    if kind == "source":
        lay = V.source_stamp(spec["cites"], width=min(1180, C.W - 96))
        return lay, spec.get("xy", (112, C.H - lay.size[1] - 150))
    if kind == "callout":
        lay = V.callout(spec["text"], accent)
        return lay, spec.get("xy", (112, 240))
    if kind == "mark":
        return K.corner_mark(spec.get("series", "MONARCH"), spec.get("sub", "FILES"),
                             spec.get("ep", "")), (0, 0)
    raise ValueError(f"unknown type kind: {kind}")


def build_layer(spec: dict) -> dict | None:
    """Return a CROPPED layer record: {rgb, alpha, x, y}.

    Cropping is the whole performance story of the type pass. A full-frame
    RGBA round-trip through PIL cost 82 ms per composite; a cropped numpy ROI
    blend costs ~6 ms and produces the same frame.
    """
    k = _key(spec)
    if k in _LAYER_CACHE:
        return _LAYER_CACHE[k]
    layer, (ox, oy) = _build_pil(spec)
    arr = np.asarray(layer)
    a = arr[..., 3]
    ys, xs = np.where(a > 2)
    rec = None
    if len(ys):
        y0, y1, x0, x1 = int(ys.min()), int(ys.max()) + 1, int(xs.min()), int(xs.max()) + 1
        rec = {"rgb": np.ascontiguousarray(arr[y0:y1, x0:x1, :3]),
               "alpha": np.ascontiguousarray(arr[y0:y1, x0:x1, 3].astype(np.float32) / 255.0),
               "x": ox + x0, "y": oy + y0,
               "w": x1 - x0, "h": y1 - y0}
    _LAYER_CACHE[k] = rec
    return rec


def animate_np(rec: dict, t_in: float, mode: str = "extrude_tilt", entry: float = K.ENTRY,
               overshoot: float = 1.12, direction: int = 1):
    """Animate a cropped layer. Returns (rgb, alpha, x, y). After entry: no cost."""
    u = C.clamp(t_in / max(entry, 1e-3))
    if u >= 0.999 or mode in (None, "none"):
        return rec["rgb"], rec["alpha"], rec["x"], rec["y"]

    rgb, alpha, x, y = rec["rgb"], rec["alpha"], rec["x"], rec["y"]
    w, h = rec["w"], rec["h"]

    if mode in ("rise", "slide"):
        dx = int(direction * 140 * (1 - C.e_back(u, overshoot))) if mode == "slide" else 0
        dy = int(64 * (1 - C.e_back(u, overshoot))) if mode == "rise" else 0
        return rgb, alpha, x + dx, y + dy

    if mode == "wipe":
        cut = int(w * C.e_io(u) * 1.06)
        a = alpha.copy()
        a[:, cut:] = 0.0
        return rgb, a, x, y

    # pop / extrude_tilt need a real warp: build one 4-channel buffer
    buf = np.dstack([rgb, (alpha * 255.0).astype(np.uint8)])
    if mode == "pop":
        sc = 1.0 - 0.10 * (1 - C.e_back(u, overshoot))
        m = cv2.getRotationMatrix2D((w / 2, h / 2), 0, max(sc, 0.55))
        out = cv2.warpAffine(buf, m, (w, h), flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    else:                                   # extrude_tilt
        p = C.e_io(u)
        a = 1.0 - p
        src = np.float32([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]])
        xp, ysh = w * 0.055 * a, h * 0.085 * a
        if direction > 0:
            dst = np.float32([[xp, ysh], [w - 1 - xp, 0], [w - 1, h - 1], [0, h - 1 - ysh]])
        else:
            dst = np.float32([[xp, 0], [w - 1 - xp, ysh], [w - 1, h - 1 - ysh], [0, h - 1]])
        m = cv2.getPerspectiveTransform(src, dst)
        out = cv2.warpPerspective(buf, m, (w, h), flags=cv2.INTER_LINEAR,
                                  borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        out[..., 3] = (out[..., 3].astype(np.float32) * (0.25 + 0.75 * p)).astype(np.uint8)
    return out[..., :3], out[..., 3].astype(np.float32) / 255.0, x, y


def composite(frame: np.ndarray, rgb: np.ndarray, alpha: np.ndarray, x: int, y: int,
              opacity: float = 1.0) -> np.ndarray:
    """Alpha blend a cropped layer into the frame inside its own ROI."""
    if opacity <= 0.004:
        return frame
    fh, fw = frame.shape[:2]
    lh, lw = alpha.shape[:2]
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + lw, fw), min(y + lh, fh)
    if x0 >= x1 or y0 >= y1:
        return frame
    sx0, sy0 = x0 - x, y0 - y
    sub_a = alpha[sy0:sy0 + (y1 - y0), sx0:sx0 + (x1 - x0)]
    if opacity < 0.999:
        sub_a = sub_a * opacity
    sub_rgb = rgb[sy0:sy0 + (y1 - y0), sx0:sx0 + (x1 - x0)].astype(np.float32)
    roi = frame[y0:y1, x0:x1].astype(np.float32)
    a3 = sub_a[..., None]
    frame[y0:y1, x0:x1] = np.clip(roi * (1.0 - a3) + sub_rgb * a3, 0, 255).astype(np.uint8)
    return frame


def layer_visible(spec: dict, local_t: float) -> bool:
    return spec.get("in", 0.0) <= local_t <= spec.get("out", 1e9)


def draw_type(frame: np.ndarray, specs: list[dict], local_t: float, shot_dur: float) -> np.ndarray:
    live = [s for s in specs if layer_visible(s, local_t)]
    if not live:
        return frame
    for i, spec in enumerate(live):
        rec = build_layer(spec)
        if rec is None:
            continue
        t_in = local_t - spec.get("in", 0.0)
        rgb, a, x, y = animate_np(rec, t_in, spec.get("anim", "extrude_tilt"),
                                  spec.get("entry", K.ENTRY), spec.get("overshoot", 1.12),
                                  spec.get("direction", 1))
        dur = max(spec.get("out", shot_dur) - spec.get("in", 0.0), 0.4)
        op = spec.get("opacity", 1.0) * K.hold_fade(t_in, dur, spec.get("fade_out", 0.26))
        frame = composite(frame, rgb, a, x, y, op)
    return frame


# ─────────────────────────────────────────────────────────────────────────────
# EFFECTS
# ─────────────────────────────────────────────────────────────────────────────

def apply_fx(frame: np.ndarray, fx: dict, local_t: float, frame_idx: int,
             depth_alpha: np.ndarray | None = None) -> np.ndarray:
    if not fx:
        return frame
    if fx.get("rays"):
        frame = F.god_rays(frame, local_t, fx["rays"], fx.get("rays_angle", 68.0))
    if fx.get("haze"):
        frame = F.haze(frame, local_t, fx["haze"], fx.get("haze_seed", 3))
    if fx.get("motes"):
        frame = F.motes(frame, local_t, int(fx["motes"]), fx.get("motes_strength", 0.55),
                        depth_alpha, fx.get("motes_seed", 5))
    if fx.get("streaks") and fx.get("streaks_from", 0.0) <= local_t:
        k = fx["streaks"] * C.clamp((local_t - fx.get("streaks_from", 0.0)) / max(fx.get("streaks_ramp", 0.6), 1e-3))
        frame = F.speed_streaks(frame, local_t - fx.get("streaks_from", 0.0), k, fx.get("streaks_angle", 12.0))
    for at in fx.get("impact", []) or []:
        if 0 <= local_t - at <= 0.6:
            frame = F.impact(frame, local_t - at, fx.get("impact_x", 0.5), fx.get("impact_y", 0.5),
                             fx.get("impact_strength", 1.0))
    for at in fx.get("flash", []) or []:
        if 0 <= local_t - at <= 0.4:
            frame = F.flash(frame, local_t - at, fx.get("flash_strength", 0.34))
    if fx.get("chroma"):
        frame = F.chroma(frame, fx["chroma"])
    return frame


def apply_shake(frame: np.ndarray, fx: dict, local_t: float) -> np.ndarray:
    amps = fx.get("shake", []) if isinstance(fx.get("shake"), list) else (
        [0.0] if fx.get("shake") else [])
    if not amps:
        return frame
    amp = fx.get("shake", 0) if not isinstance(fx.get("shake"), list) else max(fx["shake"], default=0)
    if amp <= 0.1:
        return frame
    return F.apply_shake(frame, F.shake_matrix(local_t, amp=float(amp), seed=fx.get("shake_seed", 0.0)))


# ─────────────────────────────────────────────────────────────────────────────
# THE FILM
# ─────────────────────────────────────────────────────────────────────────────

class Film:
    """Render a declarative shot plan into a silent picture master."""

    def __init__(self, plan: dict, out_dir, plate_dir=None, size=(C.W, C.H),
                 log_every: int = 60, verbose: bool = True):
        self.plan = plan
        self.out_dir = pathlib.Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.shots = plan["shots"]
        self.plates = pathlib.Path(plate_dir or plan.get("plates", C.PLATES))
        self.size = size
        self.log_every = log_every
        self.verbose = verbose
        self.timeline = []

    def total_duration(self) -> float:
        return float(sum(s["dur"] for s in self.shots))

    def render(self, out_path=None, crf: int = 19, preset: str = "medium") -> pathlib.Path:
        out_path = pathlib.Path(out_path or (self.out_dir / "picture.mp4"))
        w = Writer(out_path, self.size, crf=crf, preset=preset)
        stages: dict[str, D.Stage] = {}
        grades: dict[str, G.Grade] = {}
        prev_frame = None
        prev_kind = None
        global_idx = 0
        t_cursor = 0.0

        for si, shot in enumerate(self.shots):
            plate_p = self.plates / shot["plate"]
            key = f"{shot['plate']}|{json.dumps(shot.get('depth', {}), sort_keys=True)}"
            if key not in stages:
                stages[key] = D.stage_from_file(plate_p, shot.get("depth", {}))
            stage = stages[key]
            look = shot.get("look", self.plan.get("look", "nocturne"))
            if look not in grades:
                grades[look] = G.Grade(look)
            gr = grades[look]

            n = max(int(round(shot["dur"] * C.FPS)), 1)
            cam = shot.get("cam", {})
            fx = shot.get("fx", {}) or {}
            types = shot.get("type", []) or []
            direction = shot.get("direction", 1)
            trans_kind = shot.get("transition_in", "hard")
            k_frames = T.frames_for(trans_kind)
            d_alpha = None
            if fx.get("motes") and stage._d_alpha is not None:
                d_alpha = stage._d_alpha

            for i in range(n):
                p = i / (n - 1) if n > 1 else 1.0
                local_t = i / C.FPS
                frame = stage.frame(p, cam, direction)
                frame = gr.apply(frame, global_idx)
                frame = apply_fx(frame, fx, local_t, global_idx, d_alpha)
                raw = frame
                frame = draw_type(frame, types, local_t, shot["dur"])
                if i < k_frames and prev_frame is not None:
                    frame = T.apply(trans_kind, prev_frame, frame, i / max(k_frames - 1, 1),
                                    direction, **shot.get("transition_args", {}))
                frame = apply_shake(frame, fx, local_t)
                if frame.shape[1] != self.size[0] or frame.shape[0] != self.size[1]:
                    frame = C.resize(frame, self.size[0], self.size[1])
                w.write(frame)
                prev_frame = frame.copy()
                global_idx += 1
                if self.verbose and global_idx % self.log_every == 0:
                    C.say(f"    frame {global_idx:5d}  shot {shot['id']}  t={t_cursor + local_t:6.2f}s")

            self.timeline.append({"id": shot["id"], "start": round(t_cursor, 3),
                                  "dur": shot["dur"], "plate": shot["plate"],
                                  "transition_in": trans_kind, "look": look,
                                  "types": [t.get("kind") for t in types]})
            t_cursor += shot["dur"]
            if self.verbose:
                C.say(f"  shot {shot['id']:>3}  {shot['dur']:5.1f}s  {shot['plate']:<24} "
                      f"in={trans_kind:<8} frames={n}")
            prev_kind = trans_kind

        w.close()
        C.write_json(self.out_dir / "TIMELINE.json",
                     {"fps": C.FPS, "size": list(self.size), "total_s": self.total_duration(),
                      "shots": self.timeline})
        return out_path


# ─────────────────────────────────────────────────────────────────────────────
# MASTER ASSEMBLY
# ─────────────────────────────────────────────────────────────────────────────

def mux(picture, audio, out, size=None, crf: int = 19, preset: str = "medium",
        audio_bitrate: str = "192k") -> pathlib.Path:
    """Encode the delivery master: H.264 high profile, AAC 48 kHz stereo.

    The container's dimensions come from the PICTURE, never from a parameter
    (`size` is accepted and ignored for call compatibility): the vertical master
    is muxed by this same function, and a hard-coded 1920x1080 default here would
    silently letterbox it. G18 reads the dimensions back out of the delivered
    file precisely because that class of mistake is invisible in the log.
    """
    out = pathlib.Path(out)
    C.run([C.ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
           "-i", str(picture), "-i", str(audio),
           "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.2",
           "-x264-params", "keyint=60:min-keyint=30:scenecut=0",
           "-c:a", "aac", "-b:a", audio_bitrate, "-ar", "48000", "-ac", "2",
           "-movflags", "+faststart", "-shortest", str(out)], "mux")
    return out


def verify(master, expect_seconds: float | None = None) -> dict:
    import json
    st = subprocess.run([C.ffmpeg(), "-hide_banner", "-i", str(master)],
                        capture_output=True, text=True).stderr
    info = {"path": str(master),
            "size_bytes": pathlib.Path(master).stat().st_size}
    for line in st.splitlines():
        if "Duration:" in line:
            hms = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = hms.split(":")
            info["duration_s"] = round(int(h) * 3600 + int(m) * 60 + float(s), 3)
        if "Stream #" in line and "Video:" in line:
            info["video"] = line.split("Video:")[1].strip()[:120]
        if "Stream #" in line and "Audio:" in line:
            info["audio"] = line.split("Audio:")[1].strip()[:120]
    if expect_seconds:
        info["av_duration_delta_s"] = round(abs(info.get("duration_s", 0) - expect_seconds), 3)
    return info


def render_vertical(plan: dict, out_path, fps: int = C.FPS, plate_dir=None,
                    crf: int = 12, preset: str = "ultrafast") -> pathlib.Path:
    """Render the 9:16 cut: tracked crop, then TYPE laid out for the portrait frame.

    MEASURED GAP this closes: `vertical_path` cropped camera + grade into 1080x1920
    and left the type behind, because every type builder reads `core.W/H` at call
    time and the canvas was fixed at 1920x1080. The result was a real Shorts master
    with no reason for a viewer to watch it — a landscape composition letterboxed
    into a phone. Here the type pass runs inside `core.canvas(VW, VH)`, so the same
    layer grammar (headline, stat, species card, lower third, mark) lays itself out
    for the portrait frame, and a shot may declare `vertical_type` to compose the
    Short differently from the long-form cut.

    Placement is TRACKED, not centred: the crop window follows each shot's declared
    subject rect and is damped across shot boundaries, so the animal stays framed.

    Vertical-safe geometry (brand law, `knowledge/04`): the type lives between
    y 420 and y 1620 of 1920, because the platform's UI covers the top ~13 % and
    the bottom ~25 % of a Short.
    """
    out_path = pathlib.Path(out_path)
    w = Writer(out_path, (C.VW, C.VH), fps=fps, crf=crf, preset=preset)
    stages: dict[str, D.Stage] = {}
    grades: dict[str, G.Grade] = {}
    prev_frame = None
    prev_cx = 0.5
    global_idx = 0
    root = pathlib.Path(plate_dir or plan.get("plates", C.PLATES))
    t_cursor = 0.0
    for shot in plan["shots"]:
        plate_p = root / shot["plate"]
        key = f"{shot['plate']}|{json.dumps(shot.get('depth', {}), sort_keys=True)}"
        if key not in stages:
            stages[key] = D.stage_from_file(plate_p, shot.get("depth", {}))
        stage = stages[key]
        look = shot.get("look", plan.get("look", "nocturne"))
        if look not in grades:
            grades[look] = G.Grade(look)
        gr = grades[look]
        cam = shot.get("cam", {})
        fx = shot.get("fx", {}) or {}
        types = shot.get("vertical_type", shot.get("type", [])) or []
        direction = shot.get("direction", 1)
        k_frames = T.frames_for(shot.get("transition_in", "hard"))
        d_alpha = stage._d_alpha if fx.get("motes") else None
        rect = shot.get("depth", {}).get("rect", (0.2, 0.12, 0.8, 0.98))
        target_cx = (rect[0] + rect[2]) / 2.0
        n = max(int(round(shot["dur"] * fps)), 1)
        cw = int(C.H * 9 / 16)
        for i in range(n):
            p = i / (n - 1) if n > 1 else 1.0
            local_t = i / fps
            frame = stage.frame(p, cam, direction)
            frame = gr.apply(frame, global_idx)
            frame = apply_fx(frame, fx, local_t, global_idx, d_alpha)
            cx = prev_cx + (target_cx - prev_cx) * C.e_io(C.clamp(i / (0.5 * fps)))
            x0 = int(C.clamp(cx * C.W - cw / 2, 0, C.W - cw))
            fv = C.resize(frame[:, x0:x0 + cw], C.VW, C.VH)
            if types:
                with C.canvas(C.VW, C.VH):
                    fv = draw_type(fv, types, local_t, shot["dur"])
            if i < k_frames and prev_frame is not None:
                pass          # a cross-shot vertical transition would need the
                              # previous VERTICAL frame; kept out until designed
            fv = apply_shake(fv, fx, local_t)
            w.write(fv)
            prev_frame = fv.copy()
            prev_cx = cx
            global_idx += 1
            if global_idx % 240 == 0:
                C.say(f"    v-frame {global_idx:5d}  shot {shot['id']}  t={t_cursor + local_t:6.2f}s")
        t_cursor += shot["dur"]
        if True:
            C.say(f"  v-shot {shot['id']:>3}  {shot['dur']:5.1f}s  {shot['plate']:<24} "
                  f"types={len(types)} frames={n}")
    w.close()
    return out_path


def vertical_path(plan: dict, out_path, fps: int = C.FPS, plate_dir=None) -> pathlib.Path:
    """Render a 9:16 Shorts cut from the same plan, camera following the subject.

    The crop window is driven by each shot's declared subject rect, damped
    across shot boundaries, so the animal stays framed instead of the frame
    being blindly centred.
    """
    w = Writer(out_path, (C.VW, C.VH), fps=fps)
    stages: dict[str, D.Stage] = {}
    prev_cx = 0.5
    root = pathlib.Path(plate_dir or plan.get("plates", C.PLATES))
    for shot in plan["shots"]:
        plate_p = root / shot["plate"]
        key = f"{shot['plate']}|{json.dumps(shot.get('depth', {}), sort_keys=True)}"
        if key not in stages:
            stages[key] = D.stage_from_file(plate_p, shot.get("depth", {}))
        stage = stages[key]
        gr = G.Grade(shot.get("look", plan.get("look", "nocturne")))
        rect = shot.get("depth", {}).get("rect", (0.2, 0.12, 0.8, 0.98))
        target_cx = (rect[0] + rect[2]) / 2.0
        n = max(int(round(shot["dur"] * fps)), 1)
        for i in range(n):
            p = i / (n - 1) if n > 1 else 1.0
            frame = stage.frame(p, shot.get("cam", {}), shot.get("direction", 1))
            frame = gr.apply(frame, i)
            cx = prev_cx + (target_cx - prev_cx) * C.e_io(C.clamp(i / (0.5 * fps)))
            cw = int(C.H * 9 / 16)
            x0 = int(C.clamp(cx * C.W - cw / 2, 0, C.W - cw))
            crop = frame[:, x0:x0 + cw]
            w.write(C.resize(crop, C.VW, C.VH))
            prev_cx = cx
    w.close()
    return pathlib.Path(out_path)


# ─────────────────────────────────────────────────────────────────────────────
# PROOF TOOLS
# ─────────────────────────────────────────────────────────────────────────────

def contact_sheet(frames: list[np.ndarray], cols: int, path, tile=(480, 270)) -> pathlib.Path:
    rows = math.ceil(len(frames) / cols)
    sheet = Image.new("RGB", (cols * tile[0], rows * tile[1]), (8, 8, 10))
    for i, f in enumerate(frames):
        im = Image.fromarray(f).resize(tile, Image.LANCZOS)
        sheet.paste(im, ((i % cols) * tile[0], (i // cols) * tile[1]))
    sheet.save(path, quality=92)
    return pathlib.Path(path)
