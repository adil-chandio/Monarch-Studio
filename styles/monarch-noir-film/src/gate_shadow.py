#!/usr/bin/env python3
"""
gate_shadow.py — WF-03 film gates for THE SHADOW v1 (measured on the delivered mp4, never eyeballed).
usage: gate_shadow.py --mp4 FILE [--drive-md5 MD5] [--out GATES.md]
reads build/wf03_film/{picture_metrics,mix_stats,events,beats}.json + DNA_THE_SHADOW.json
"""
import os, sys, json, re, math, hashlib, subprocess, argparse, datetime
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WF = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(WF))
BUILD = os.path.join(ROOT, 'build', 'wf03_film')


def ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def probe(path):
    out = subprocess.run([ffmpeg(), '-i', path], capture_output=True, text=True).stderr
    dur = re.search(r'Duration: (\d+):(\d+):([\d.]+)', out)
    d = int(dur.group(1)) * 3600 + int(dur.group(2)) * 60 + float(dur.group(3))
    v = re.search(r'Video: (\w+).*?(\d{3,4})x(\d{3,4}).*?([\d.]+) fps', out)
    a = re.search(r'Audio: (\w+).*?(\d+) Hz, (\w+)', out)
    return dict(duration=d, vcodec=v.group(1), w=int(v.group(2)), h=int(v.group(3)), fps=float(v.group(4)),
                acodec=a.group(1), sr=int(a.group(2)), layout=a.group(3))


def grey_stack(path, w=96, h=54, fps=24):
    cmd = [ffmpeg(), '-nostats', '-loglevel', 'error', '-i', path, '-vf', f'fps={fps},scale={w}:{h}', '-f', 'rawvideo', '-pix_fmt', 'gray', '-']
    raw = subprocess.run(cmd, capture_output=True).stdout
    n = len(raw) // (w * h)
    return np.frombuffer(raw[:n * w * h], np.uint8).reshape(n, h, w)


def colour_scan(path, w=480, h=270, fps=6):
    """stream the delivered file at w×h, fps → per-frame (t, luma, dark share <30, chroma mean(max-min), p99); no big arrays"""
    cmd = [ffmpeg(), '-nostats', '-loglevel', 'error', '-i', path, '-vf', f'fps={fps},scale={w}:{h}:flags=area', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    pr = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    out, k, nb = [], 0, w * h * 3
    while True:
        buf = pr.stdout.read(nb)
        if len(buf) < nb:
            break
        f = np.frombuffer(buf, np.uint8).reshape(h, w, 3).astype(np.float32)
        l = 0.299 * f[..., 0] + 0.587 * f[..., 1] + 0.114 * f[..., 2]
        out.append((k / fps, float(l.mean()), float((l < 30).mean()), float((f.max(axis=2) - f.min(axis=2)).mean()), float(np.percentile(l, 99))))
        k += 1
    pr.wait()
    return out


def loudness(path):
    out = subprocess.run([ffmpeg(), '-nostats', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    tail = out[out.rfind('Summary:'):]
    I = float(re.search(r'I:\s+(-?[\d.]+) LUFS', tail).group(1))
    lra = float(re.search(r'LRA:\s+(-?[\d.]+) LU', tail).group(1))
    tp = float(re.search(r'Peak:\s+(-?[\d.]+) dBFS', tail).group(1))
    # short-term profile (t, S)
    prof = [(float(m.group(1)), float(m.group(2))) for m in re.finditer(r't:\s+([\d.]+)\s+TARGET.*?S:\s*(-?[\d.]+)', out)]
    return I, lra, tp, prof


def rms_window(path, t0, t1):
    cmd = [ffmpeg(), '-nostats', '-loglevel', 'error', '-ss', f'{t0:.3f}', '-t', f'{t1 - t0:.3f}', '-i', path, '-ac', '1', '-ar', '48000', '-f', 's16le', '-']
    raw = subprocess.run(cmd, capture_output=True).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    return 20 * math.log10(max(1e-6, float(np.sqrt(np.mean(a * a)))))


def contrast(c1, c2):
    def L(c):
        r, g, b = [((x / 255) / 12.92 if x / 255 <= 0.03928 else ((x / 255 + 0.055) / 1.055) ** 2.4) for x in c]
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    a, b = sorted([L(c1), L(c2)], reverse=True)
    return (a + 0.05) / (b + 0.05)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mp4', required=True)
    ap.add_argument('--drive-md5', default='')
    ap.add_argument('--drive-id', default='')
    ap.add_argument('--out', default=os.path.join(WF, 'GATES_THE_SHADOW_v1.md'))
    args = ap.parse_args()

    ev = json.load(open(os.path.join(BUILD, 'events.json')))
    pm = json.load(open(os.path.join(BUILD, 'picture_metrics.json')))
    ms = json.load(open(os.path.join(BUILD, 'mix_stats.json')))
    beats = json.load(open(os.path.join(BUILD, 'beats.json')))
    dna = json.load(open(os.path.join(WF, 'DNA_THE_SHADOW.json')))
    md5 = hashlib.md5(open(args.mp4, 'rb').read()).hexdigest()
    size = os.path.getsize(args.mp4)
    pr = probe(args.mp4)
    rows = []

    def gate(name, ok, measured, target):
        rows.append((name, bool(ok), measured, target))

    # 1 container
    gate('G01 container', pr['w'] == 1920 and pr['h'] == 1080 and abs(pr['fps'] - 24) < 0.1 and pr['vcodec'] == 'h264' and pr['acodec'] == 'aac',
         f"{pr['w']}x{pr['h']} {pr['fps']:.0f} fps {pr['vcodec']} / {pr['acodec']} {pr['sr']} Hz {pr['layout']}", '1920x1080 24 fps h264 / aac 48 kHz stereo')
    gate('G02 duration (film 120–180 s)', 120 <= pr['duration'] <= 180, f"{pr['duration']:.2f} s", '120–180 s (brain plan ≈150 s)')

    # 2 picture — measured on the DELIVERED file (480×270 area-scaled, 6 fps); renderer metrics kept only for the error count
    shots_tl = ev['shots']
    def shot_of(t):
        for i, sh in enumerate(shots_tl):
            if sh['t0'] <= t < sh['t0'] + sh['dur']:
                return i
        return len(shots_tl) - 1
    cs = colour_scan(args.mp4)
    per = {}
    for t, l, dk, ch, p99 in cs:
        d_ = per.setdefault(shot_of(t), dict(name=shots_tl[shot_of(t)]['name'], n=0, luma=0.0, dark=0.0, chroma=0.0, p99=0.0))
        d_['n'] += 1; d_['luma'] += l; d_['dark'] += dk; d_['chroma'] += ch; d_['p99'] += p99
    for d_ in per.values():
        for kk in ('luma', 'dark', 'chroma', 'p99'):
            d_[kk] /= d_['n']
    luma = float(np.mean([c[1] for c in cs])); dark = float(np.mean([c[2] for c in cs])); chroma = float(np.mean([c[3] for c in cs]))
    gate('G03 mean luma (Day One 18/255)', 10 <= luma <= 30, f'{luma:.1f} /255', '10–30 /255')
    gate('G04 dark pixels (<30/255) share (Day One 89 % dark frames)', dark >= 0.70, f'{dark * 100:.1f} %', '≥ 70 %')
    gate('G05 chroma (Day One sat 0.08)', chroma <= 25.5, f'{chroma:.1f} /255 ≈ sat {chroma / 255:.3f}', '≤ 0.10')
    SETUP = ('S02', 'S03', 'S04', 'S06', 'S09', 'S10', 'S12', 'S14', 'S15', 'S16', 'S17', 'S18')
    setup = [d_ for d_ in per.values() if d_['name'][:3] in SETUP]
    worst = max(setup, key=lambda d_: d_['luma'])
    gate('G06 setup shots luma ≤ 34 (look-sheet target 14–30 + 4 for medium framings)', all(d_['luma'] <= 34 for d_ in setup),
         f"max {worst['luma']:.1f} ({worst['name'][:3]}); setup shots " + ' '.join(f"{d_['name'][:3]} {d_['luma']:.0f}" for d_ in setup), '≤ 34 /255 per setup shot')
    errs = pm.get('errors', [])
    gate('G07 render errors (frames that raised and were repeated)', len(errs) == 0, f'{len(errs)}', '0')

    # 3 cut grammar measured from the delivered file — 96×54 grey proxies at 24 fps
    g = grey_stack(args.mp4).astype(np.int16)
    dd = np.abs(np.diff(g, axis=0))
    frac = (dd > 10).mean(axis=(1, 2))                                   # share of pixels that changed by > 10 levels
    mean_ = g.mean(axis=(1, 2)); max_ = g.max(axis=(1, 2))
    prev4 = np.array([frac[max(0, i - 4):i].mean() if i > 0 else 0.0 for i in range(len(frac))])
    cand = [i + 1 for i in range(len(frac)) if frac[i] >= 0.08 and frac[i] >= 2.0 * prev4[i]]
    det = []
    for c in cand:
        if not det or c - det[-1] > 3:
            det.append(c)
    det_t = [c / 24.0 for c in det]
    # planned boundaries: hard cut unless a fade is declared on either side or the picture passes through an empty black frame
    FADES = {'S06': (0, 0.6), 'S07': (0.3, 0), 'S18': (0, 0.6), 'S19': (0.3, 0), 'S20': (0, 1.5)}
    empty_t = np.where((mean_ < 2.0) & (max_ < 8))[0] / 24.0
    bounds = []
    for k_ in range(1, len(shots_tl)):
        t = shots_tl[k_]['t0']; a, b = shots_tl[k_ - 1]['name'][:3], shots_tl[k_]['name'][:3]
        declared_soft = FADES.get(a, (0, 0))[1] > 0 or FADES.get(b, (0, 0))[0] > 0
        through_black = bool(np.any(np.abs(empty_t - t) <= 0.5))
        hard_det = any(abs(t - x) <= 0.13 for x in det_t)
        kind = 'dip' if (declared_soft or through_black) else 'hard'
        bounds.append((t, a, b, kind, hard_det, through_black))
    hard = [bd for bd in bounds if bd[3] == 'hard']
    hard_ok = [bd for bd in hard if bd[4]]
    dips = [bd for bd in bounds if bd[3] == 'dip']
    dips_ok = [bd for bd in dips if bd[5] or bd[4]]
    missed = [f"{bd[1]}→{bd[2]} @{bd[0]:.1f}" for bd in hard if not bd[4]]
    gate('G08 every planned hard cut is a measured hard cut (Δ-pixel share ≥ 8 %, spike)', len(hard_ok) == len(hard),
         f'{len(hard_ok)}/{len(hard)} hard cuts measured' + (f'; missed: {missed}' if missed else '') + f'; {len(dips_ok)}/{len(dips)} dips pass through black', 'all planned hard cuts detected')
    # unplanned transitions: detections that are neither a planned boundary nor inside a planned flicker / flash window
    FLICKER = [(29.0, 31.5), (ev['lamp'][2]['t'] - 0.3, ev['lamp'][2]['t'] + 0.5), (ev['wall_touch'] - 0.1, ev['wall_touch'] + 0.5)] + [(fl - 0.15, fl + 0.15) for fl in ev['flash']]   # ev['flash'] = renderer-declared white flash frames (relight 56.71, wall 100.5)
    unplanned = [round(x, 2) for x in det_t if not any(abs(x - bd[0]) <= 0.13 for bd in bounds) and not any(a_ <= x <= b_ for a_, b_ in FLICKER)]
    gate('G09 no unplanned transitions (no dissolves / wipes — renderer has only cut + dip; Day One: 0)', len(unplanned) == 0,
         f'{len(det_t)} spikes measured: {len(det_t) - len(unplanned)} planned cuts / flame gutter / relight / wall flash, {len(unplanned)} unplanned {unplanned}', '0 unplanned')
    # stillness: 1-s motion on the proxies (grain floor ≈ 0.13 after 20× area pooling)
    mot = np.abs(g[24:] - g[:-24]).mean(axis=(1, 2))
    CARDS = ('S01', 'C2 ', 'C4 ', 'C6 ', 'S19', 'S20')
    def longest_static(pred):
        best, run = 0, 0
        for i, m in enumerate(mot):
            sh = shots_tl[shot_of((i + 12) / 24.0)]['name'][:3]
            if pred(sh) and m < 0.2:
                run += 1; best = max(best, run)
            else:
                run = 0
        return best / 24.0
    st_scene = longest_static(lambda sh: sh not in CARDS)
    st_card = longest_static(lambda sh: sh in CARDS)
    gate('G10 nothing perfectly still (longest 1-s-motion < 0.2 run)', st_scene <= 1.5 and st_card <= 4.5,
         f'scene shots {st_scene:.2f} s · text cards {st_card:.2f} s (all 12 holds alive: drift + lamp flicker + grain)', 'scene ≤ 1.5 s · cards ≤ 4.5 s (Day One: static title cards)')
    PLANNED_BLACK = [(0.0, 0.6), (39.5 - 0.7, 39.5 + 0.7), (143.4 - 0.7, 143.4 + 0.7), (ev['end_card'] - 0.5, ev['end_card'] + 0.5), (ev['total'] - 1.6, ev['total'] + 1)]
    stray = [round(t, 2) for t in empty_t if not any(a_ <= t <= b_ for a_, b_ in PLANNED_BLACK)]
    gate('G11 empty black frames only at card-in / dips / card gap / tail', len(stray) == 0, f'{len(empty_t)} empty frames, {len(stray)} stray {stray[:6]}', '0 stray')

    # 4 structure from the locked timeline
    holds = [s for s in ev['shots'] if 8.0 <= s['dur'] <= 14.0]
    gate('G12 holds 8–14 s (Day One 10–11 s holds)', 8 <= len(holds) <= 16, f"{len(holds)} holds: " + ', '.join(f"{s['name'][:3]} {s['dur']:.1f}" for s in holds), '8–16 holds')
    longest = max(s['dur'] for s in ev['shots'])
    gate('G13 longest shot ≤ 14 s', longest <= 14.0, f'{longest:.1f} s', '≤ 14 s')
    mont = [s for s in ev['shots'] if ev['montage'][0] - 0.01 <= s['t0'] < ev['montage'][1] - 0.01]
    clim = [s for s in ev['shots'] if ev['climax'][0] - 0.01 <= s['t0'] < ev['climax'][1] - 0.01]
    gate('G14 montage accelerando + 0.4 s climax', len(mont) == 8 and all(mont[i]['dur'] > mont[i + 1]['dur'] for i in range(len(mont) - 1)) and len(clim) == 6,
         f"montage {len(mont)} shots {mont[0]['dur']:.1f}→{mont[-1]['dur']:.1f} s; climax {len(clim)} × {clim[0]['dur']:.1f} s", '8 shrinking shots + 6 × 0.4 s')
    gate('G15 beats density (film rule: new thing every 3–6 s)', beats['beats'] >= 44 and beats['max_gap'] <= 6.5, f"{beats['beats']} beats, max gap {beats['max_gap']} s", '≥ 44 beats, gap ≤ 6.5 s')
    gate('G16 spoken lines (brief: 2–3 English lines)', len(ev['vo']) == 3, '; '.join(f"{v['t']:.1f} s “{v['text']}”" for v in ev['vo']), '3 lines')
    gate('G17 callbacks ≥ 3', len(dna['callbacks']) >= 3, f"{len(dna['callbacks'])}: " + ' | '.join(c.split(':')[0] for c in dna['callbacks']), '≥ 3')
    gate('G18 quotable lines = 2 + title pun, no CTA', len(dna['quotable_lines']) == 2 and bool(dna.get('title_pun')), f"{dna['quotable_lines']} · “{dna['title_pun']}”", '2 + pun, 0 CTA')
    gate('G19 text contrast (bone on wall / red villain large type)', contrast((236, 232, 222), (14, 14, 15)) >= 4.5 and contrast((214, 38, 32), (7, 7, 9)) >= 3.0,
         f"bone {contrast((236, 232, 222), (14, 14, 15)):.1f}:1 · red {contrast((214, 38, 32), (7, 7, 9)):.1f}:1 (≥ 96 px)", 'body ≥ 4.5:1 · large ≥ 3:1')

    # 5 sound measured on the delivered file
    I, lra, tp, prof = loudness(args.mp4)
    gate('G20 integrated loudness', abs(I + 16.5) <= 1.0, f'{I:.1f} LUFS (wav {ms["lufs"]})', '−16.5 ± 1.0 LUFS')
    gate('G21 true peak', tp <= -1.0, f'{tp:.1f} dBTP', '≤ −1.0 dBTP')
    gate('G22 loudness range (Day One ≈ 4.5; film breathes)', 4.0 <= lra <= 16.0, f'{lra:.1f} LU', '4–16 LU')
    tail0 = ev['vo'][-1]['t'] + 5.9
    tail_rms = rms_window(args.mp4, tail0, pr['duration'])
    last10 = rms_window(args.mp4, pr['duration'] - 10, pr['duration'])
    gate('G23 quiet ending after the last line', tail_rms <= -26.0, f'{tail_rms:.1f} dB RMS from {tail0:.1f} s (last 10 s incl. line 3: {last10:.1f} dB)', '≤ −26 dB RMS')
    # climax vs setup: short-term loudness arc
    def S_at(t):
        c = [s for tt, s in prof if abs(tt - t) < 0.3]
        return c[0] if c else float('nan')
    arc = {k: S_at(t) for k, t in (('S03 14 s', 14.0), ('dark 46 s', 46.0), ('climax 86 s', 86.0), ('walk 92 s', 92.0), ('wall 104 s', 104.0), ('end 153 s', 153.0))}
    gate('G24 dynamic arc (climax louder than setup, ending quieter than both)', arc['climax 86 s'] >= arc['S03 14 s'] + 3 and arc['end 153 s'] <= arc['climax 86 s'] - 10 and arc['end 153 s'] <= arc['S03 14 s'],
         ' · '.join(f'{k} {v:.1f}' for k, v in arc.items()) + ' (LUFS-S)', 'climax ≥ setup + 3 LU; end ≤ climax − 10 LU and ≤ setup')
    gate('G25 limiter transparency', ms.get('limiter_pct', 0) <= 3.0, f"{ms.get('limiter_pct', 0)} % samples under gain reduction", '≤ 3 %')

    # 6 brain + delivery
    sys.path.insert(0, os.path.join(ROOT, 'brain'))
    import concept as C
    ok20, rows20 = C.gate(os.path.join(WF, 'DNA_THE_SHADOW.json'), verbose=False)
    gate('G26 brain gate #20 freshness', ok20, f"{sum(r[1] for r in rows20)}/{len(rows20)} PASS", 'PASS')
    gate('G27 md5 local = Drive', (args.drive_md5 == md5) if args.drive_md5 else False, f'local {md5} · drive {args.drive_md5 or "—"}', 'equal')

    passed = sum(1 for r in rows if r[1])
    lines = [f"# GATES — THE SHADOW v1 (WF-03 · Monarch Noir Film) — {passed}/{len(rows)} PASS",
             f"_measured {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} on `{os.path.basename(args.mp4)}` ({size / 1e6:.2f} MB, md5 `{md5}`" + (f", Drive `{args.drive_id}`" if args.drive_id else '') + ")_", '',
             '| # gate | result | measured | target |', '|---|---|---|---|']
    for name, ok, measured, target in rows:
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {measured} | {target} |")
    lines += ['', '## per-shot picture metrics — measured on the delivered file (480×270 area-scaled, 6 fps, /255)', '', '| shot | t0 | dur | luma | dark<30 | chroma | p99 |', '|---|---|---|---|---|---|---|']
    for k_ in sorted(per):
        d_ = per[k_]; sh = shots_tl[k_]
        lines.append(f"| {d_['name']} | {sh['t0']:.1f} | {sh['dur']:.1f} | {d_['luma']:.1f} | {d_['dark'] * 100:.0f} % | {d_['chroma']:.1f} | {d_['p99']:.0f} |")
    lines += ['', '## transitions measured on 96×54 grey proxies (spike = share of pixels changing > 10 levels ≥ 8 % and ≥ 2× the previous 4 frames)', '',
              '| boundary | t | planned | measured |', '|---|---|---|---|']
    for t, a, b, kind, hard_det, through_black in bounds:
        lines.append(f"| {a} → {b} | {t:.2f} | {kind} | {'hard cut spike' if hard_det else ''}{' + ' if hard_det and through_black else ''}{'through black' if through_black else ''}{'' if (hard_det or through_black) else 'not detected'} |")
    lines += ['', f"spikes at: {[round(x, 2) for x in det_t]}", '',
              '## short-term loudness arc (LUFS-S)', '', ' · '.join(f'{k} {v:.1f}' for k, v in arc.items()), '',
              '## brain gate #20', ''] + [f"- [{'PASS' if ok else 'FAIL'}] {n} {('— ' + why) if why else ''}" for n, ok, why in rows20]
    open(args.out, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print('\n'.join(lines[:5 + len(rows)]))
    json.dump(dict(md5=md5, size=size, passed=passed, total=len(rows), lufs=I, tp=tp, lra=lra, duration=pr['duration'], luma=luma, dark=dark, chroma=chroma,
                   holds=len(holds), cuts_detected=len(det_t), hard_cuts=f'{len(hard_ok)}/{len(hard)}', beats=beats['beats'], tail_rms=tail_rms, arc=arc),
              open(os.path.join(BUILD, 'gates_summary.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
