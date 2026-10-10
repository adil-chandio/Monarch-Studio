#!/usr/bin/env python3
"""
verify.py — self-verification harness for the stickman_money_37s build.

Runs every acceptance gate from MASTER_PROMPT_V4.md §17 that can be checked
without re-rendering the whole film, and prints a PASS/FAIL table.

    python3 verify.py              # fast checks only (~15 s)
    python3 verify.py --frames     # + re-render 22 anchor frames and compare
                                   #   their sha256 against BUILD_MANIFEST.json
    python3 verify.py --audio      # + rebuild the soundtrack and count events

Exit code 0 = all gates passed, 1 = at least one failure.
"""
import sys, os, json, hashlib, subprocess, re

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, 'src'))
RESULTS = []


def chk(name, ok, detail=''):
    RESULTS.append((name, bool(ok), detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if detail else ''))
    return ok


def head(t):
    print(f"\n\033[1m{t}\033[0m" if sys.stdout.isatty() else f"\n{t}")


def ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def probe(path):
    ff = ffmpeg()
    if not ff or not os.path.exists(path):
        return ''
    return subprocess.run([ff, '-hide_banner', '-i', path],
                          capture_output=True, text=True).stderr


# ───────────────────────────────────────────── GATE 0: environment
def gate_env():
    head('GATE 0  environment')
    ok = True
    for m in ('numpy', 'PIL', 'scipy'):
        try:
            __import__(m); chk(f'import {m}', True)
        except Exception as e:
            ok &= chk(f'import {m}', False, str(e))
    ff = ffmpeg()
    ok &= chk('imageio-ffmpeg binary', bool(ff and os.path.exists(ff)), ff or 'missing')
    return ok


# ───────────────────────────────────────────── GATE 1: fonts
def gate_fonts():
    head('GATE 1  fonts')
    from PIL import ImageFont
    ok = True
    for f, size in [('PermanentMarker', 118), ('PatrickHand', 58),
                    ('Caveat-VF', 60), ('Montserrat-VF', 60)]:
        p = os.path.join(ROOT, 'fonts', f + '.ttf')
        if not os.path.exists(p):
            ok &= chk(f'{f}.ttf', False, 'missing'); continue
        try:
            bb = ImageFont.truetype(p, size).getbbox('JEEB KHALI? 123')
            good = (bb[2] - bb[0]) > 50 and (bb[3] - bb[1]) > 10
            ok &= chk(f'{f}.ttf', good, f'bbox={bb} size={os.path.getsize(p)}B')
        except Exception as e:
            ok &= chk(f'{f}.ttf', False, str(e))
    return ok


# ───────────────────────────────────────────── GATE 3: timeline
def gate_timeline(man):
    head('GATE 3  timeline oracle')
    import timeline as T
    ok = True
    ok &= chk('DUR_TOTAL == 37.0', T.DUR_TOTAL == 37.0, str(T.DUR_TOTAL))
    ok &= chk('SCENE_END[-1] == 37.0', T.SCENE_END[-1] == 37.0, str(T.SCENE_END[-1]))
    exp = man['timeline']['scene_start']
    ok &= chk('SCENE_START matches manifest',
              all(abs(a - b) < 1e-6 for a, b in zip(T.SCENE_START, exp)),
              str(T.SCENE_START))
    ok &= chk('VO_AT matches manifest',
              all(abs(a - b) < 1e-6 for a, b in zip(T.VO_AT, man['timeline']['vo_at'])),
              str(T.VO_AT))
    ok &= chk('frame count == 1110', int(30 * T.DUR_TOTAL) == 1110)
    ok &= chk('scenes are contiguous',
              all(abs(T.SCENE_END[i] - T.SCENE_START[i + 1]) < 1e-9 for i in range(5)))
    ok &= chk('all atempo in [0.5, 2.0]',
              all(0.5 <= a <= 2.0 for a in man['timeline']['atempo']),
              str(man['timeline']['atempo']))
    return ok


# ───────────────────────────────────────────── GATE 4: drawing language
def gate_draw(man):
    head('GATE 4  drawing language')
    import numpy as np
    from PIL import ImageDraw
    import stickbase as SB
    ok = True
    pal = man['palette']
    ok &= chk('palette matches manifest',
              all(tuple(pal[k]) == getattr(SB, k) for k in
                  ('CHALK', 'GOLD', 'CYAN', 'MINT', 'RED', 'PINK')))
    ok &= chk('canvas 1080x1920 @30', (SB.W, SB.H, SB.FPS) == (1080, 1920, 30))
    ok &= chk('TQ == 2 (15 Hz boil)', SB.TQ == 2)
    a = np.asarray(SB.BOARD).astype(float)
    ok &= chk('BOARD is textured, not flat',
              a.std() > 3 and 10 < a.mean() < 45, f'mean={a.mean():.2f} std={a.std():.2f}')
    ok &= chk('VIGN centre lift ~1.06',
              abs(float(SB.VIGN[SB.H // 2, SB.W // 2, 0]) - 1.06) < 0.01)
    ok &= chk('hsh() is deterministic', SB.hsh(1.234) == SB.hsh(1.234))
    ok &= chk('hsh() in [0,1)', all(0 <= SB.hsh(i * 0.37) < 1 for i in range(500)))
    # _cut must truncate by arc length
    pts = [(0, 0), (100, 0), (100, 100)]
    half = SB._cut(pts, 0.5)
    ok &= chk('_cut truncates by arc length',
              abs(half[-1][0] - 100) < 1e-6 and abs(half[-1][1] - 0) < 1e-6, str(half[-1]))
    # rig returns attachment points
    im = SB.BOARD.convert('RGBA'); d = ImageDraw.Draw(im)
    j = SB.stick(d, 540, 1500, 600, SB.pose_dance(1.0), SB.CHALK, 10, 31, 0, 1, 'happy')
    ok &= chk('stick() returns joint dict',
              set(j) >= {'head', 'hand_l', 'hand_r', 'hip', 'neck', 'hr'}, str(sorted(j)))
    # knee clamp
    ok &= chk('pose_walk knees never hyperextend',
              all(SB.pose_walk(t / 50.)['kl'] >= 0 and SB.pose_walk(t / 50.)['kr'] >= 0
                  for t in range(500)))
    return ok


# ───────────────────────────────────────────── GATE 5: render determinism
def gate_frames(man, do_render):
    head('GATE 5  frame rendering')
    if not do_render:
        print('  (skipped — pass --frames to enable)')
        return True
    import numpy as np
    from stick2 import render, NF
    ok = chk('NF == 1110', NF == 1110, str(NF))
    bad = []
    for k, want in sorted(man['anchor_frame_hashes'].items(), key=lambda x: int(x[0])):
        i = int(k)
        fr = render(i)
        got = hashlib.sha256(fr.tobytes()).hexdigest()[:16]
        if got != want:
            bad.append((i, want, got))
    ok &= chk(f'{len(man["anchor_frame_hashes"])} anchor frames bit-identical',
              not bad, '' if not bad else f'{len(bad)} mismatched: {bad[:3]}')
    f0 = render(0)
    ok &= chk('frame 0 is not black (R8)', float(f0.mean()) > 15,
              f'mean={f0.mean():.2f}')
    ok &= chk('render(i) is pure / repeatable',
              hashlib.sha256(render(400).tobytes()).digest() ==
              hashlib.sha256(render(400).tobytes()).digest())
    return ok


# ───────────────────────────────────────────── GATE 7: soundtrack
def gate_audio(man, do_audio):
    head('GATE 7  soundtrack')
    if not do_audio:
        print('  (skipped — pass --audio to enable)')
        return True
    src = open(os.path.join(ROOT, 'src', 'make_audio4.py')).read()
    log = []
    OLD = "def add(x, at, pan=.5, g=1.0):"
    NEW = OLD + "\n    LOG.append(at)"
    s2 = src.replace(OLD, NEW, 1).replace(
        "with wave.open('/home/user/build/music4.wav', 'wb') as w:",
        "if 0:\n  with open(os.devnull,'wb') as w:")
    g = {'LOG': log, '__name__': '__main__', 'os': os}
    exec(compile(s2, 'audio_verify', 'exec'), g)
    n = man['audio']['events_total']
    ok = chk(f'event count == {n}', len(log) == n, str(len(log)))
    ok &= chk('N samples == 48000*37', g['N'] == 48000 * 37, str(g['N']))
    ok &= chk('BPM == 112', g['BPM'] == 112.0)
    ok &= chk('chords match manifest',
              [[r, list(t)] for r, t in g['CHORDS']] == man['music']['chords'])
    peak = float(abs(g['mix']).max())
    ok &= chk('master peak ~0.93', abs(peak - 0.93) < 0.02, f'{peak:.4f}')
    return ok


# ───────────────────────────────────────────── GATE 11: deliverable
def gate_deliverable(man):
    head('GATE 11  delivered file')
    p = os.path.join(ROOT, 'stickman_money_37s_v2.mp4')
    if not os.path.exists(p):
        return chk('deliverable present', False, 'stickman_money_37s_v2.mp4 missing')
    ok = chk('deliverable present', True)
    size = os.path.getsize(p)
    ok &= chk('size <= 15 MB', size <= man['video']['target_bytes'],
              f'{size/1e6:.2f} MB')
    s = probe(p)
    m = re.search(r'Duration: (\d+):(\d+):([\d.]+)', s)
    if m:
        dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
        ok &= chk('duration == 37.00 +/- 0.02', abs(dur - 37.0) <= 0.02, f'{dur:.2f}s')
    ok &= chk('1080x1920', '1080x1920' in s)
    ok &= chk('30 fps', '30 fps' in s)
    ok &= chk('yuv420p', 'yuv420p' in s)
    ok &= chk('h264 High', 'h264 (High)' in s)
    ok &= chk('aac 48000 Hz stereo', 'aac' in s and '48000 Hz' in s and 'stereo' in s)
    return ok


# ───────────────────────────────────────────── GATE S: source integrity
def gate_source(man):
    head('GATE S  source integrity')
    ok = True
    for f, want in man['source_hashes'].items():
        p = os.path.join(ROOT, f)
        if not os.path.exists(p):
            ok &= chk(f, False, 'missing'); continue
        got = hashlib.sha256(open(p, 'rb').read()).hexdigest()
        ok &= chk(f, got == want, 'MODIFIED' if got != want else f'{got[:16]}')
    return ok


def main():
    do_frames = '--frames' in sys.argv
    do_audio = '--audio' in sys.argv
    mp = os.path.join(ROOT, 'BUILD_MANIFEST.json')
    if not os.path.exists(mp):
        print('BUILD_MANIFEST.json not found — cannot verify.'); return 1
    man = json.load(open(mp))

    print('=' * 68)
    print(f"  VERIFY  {man['project']}   spec {man['spec_version']}")
    print('=' * 68)

    gate_env(); gate_fonts(); gate_source(man)
    gate_timeline(man); gate_draw(man)
    gate_frames(man, do_frames); gate_audio(man, do_audio)
    gate_deliverable(man)

    n = len(RESULTS); p = sum(1 for _, o, _ in RESULTS if o)
    print('\n' + '=' * 68)
    print(f'  {p}/{n} checks passed')
    if p < n:
        print('  FAILURES:')
        for name, o, d in RESULTS:
            if not o:
                print(f'    - {name}  {d}')
    print('=' * 68)
    return 0 if p == n else 1


if __name__ == '__main__':
    sys.exit(main())
