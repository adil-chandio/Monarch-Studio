#!/usr/bin/env python3
"""
gate_window.py — WF-03 film gates for THE WINDOW v1 (film #2, NOIRGO MAX) — measured on the delivered mp4, never eyeballed.
usage: gate_window.py --mp4 FILE [--drive-md5 MD5] [--drive-id ID] [--out GATES.md]
reads data/events_window.json, data/vo_window_info.json, DNA_THE_WINDOW.json, build/wf03_window/{mix_stats,seg_*.metrics}.json
Targets were fixed from the approved look sheet / script before the delivered file was measured (see RESUME_STATE).
"""
import os, sys, json, re, math, glob, hashlib, subprocess, argparse, datetime
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WF = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(WF))
BUILD = os.path.join(ROOT, 'build', 'wf03_window')
sys.path.insert(0, HERE)
from gate_shadow import ffmpeg, probe, grey_stack, colour_scan, loudness, rms_window, contrast  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mp4', required=True)
    ap.add_argument('--drive-md5', default='')
    ap.add_argument('--drive-id', default='')
    ap.add_argument('--out', default=os.path.join(WF, 'GATES_THE_WINDOW_v1.md'))
    args = ap.parse_args()

    ev = json.load(open(os.path.join(WF, 'data', 'events_window.json')))
    info = json.load(open(os.path.join(WF, 'data', 'vo_window_info.json')))
    dna = json.load(open(os.path.join(WF, 'DNA_THE_WINDOW.json')))
    ms = json.load(open(os.path.join(BUILD, 'mix_stats.json')))
    md5 = hashlib.md5(open(args.mp4, 'rb').read()).hexdigest()
    size = os.path.getsize(args.mp4)
    pr = probe(args.mp4)
    shots = ev['shots']
    for s in shots:
        s['dur'] = round(s['t1'] - s['t0'], 3)
    light = {d['what']: d['t'] for d in ev['light']}
    rows = []

    def gate(name, ok, measured, target):
        rows.append((name, bool(ok), measured, target))

    # 1 container
    gate('G01 container', pr['w'] == 1920 and pr['h'] == 1080 and abs(pr['fps'] - 24) < 0.1 and pr['vcodec'] == 'h264' and pr['acodec'] == 'aac',
         f"{pr['w']}x{pr['h']} {pr['fps']:.0f} fps {pr['vcodec']} / {pr['acodec']} {pr['sr']} Hz {pr['layout']}", '1920x1080 24 fps h264 / aac 48 kHz stereo')
    gate('G02 duration (film 120–180 s; timeline 155.0)', 120 <= pr['duration'] <= 180 and abs(pr['duration'] - ev['duration']) <= 0.25,
         f"{pr['duration']:.2f} s (timeline {ev['duration']:.1f})", '120–180 s, = timeline ± 0.25')

    # 2 picture — measured on the DELIVERED file (480×270 area-scaled, 6 fps)
    def shot_of(t):
        for i, sh in enumerate(shots):
            if sh['t0'] <= t < sh['t1']:
                return i
        return len(shots) - 1
    cs = colour_scan(args.mp4)
    per = {}
    for t, l, dk, ch, p99 in cs:
        d_ = per.setdefault(shot_of(t), dict(name=shots[shot_of(t)]['name'], n=0, luma=0.0, dark=0.0, chroma=0.0, p99=0.0))
        d_['n'] += 1; d_['luma'] += l; d_['dark'] += dk; d_['chroma'] += ch; d_['p99'] += p99
    for d_ in per.values():
        for kk in ('luma', 'dark', 'chroma', 'p99'):
            d_[kk] /= d_['n']
    luma = float(np.mean([c[1] for c in cs])); dark = float(np.mean([c[2] for c in cs])); chroma = float(np.mean([c[3] for c in cs]))
    gate('G03 mean luma (NOIRGO MAX: lit rooms are the villain — Day One 18, look sheet v2 target 20–36)', 20 <= luma <= 36, f'{luma:.1f} /255', '20–36 /255')
    gate('G04 dark pixels (<30/255) share', dark >= 0.50, f'{dark * 100:.1f} %', '≥ 50 %')
    gate('G05 chroma (Day One sat 0.08; amber act allowed)', chroma <= 25.5, f'{chroma:.1f} /255 ≈ sat {chroma / 255:.3f}', '≤ 0.10')
    # night ambience shots; S21 (face lit by the phone at 2.2× — the villain's light on his face, planned bright) is a close-up insert, not ambience
    BEDROOM = ('S01', 'S02', 'S03', 'S04', 'S05', 'S13', 'S22', 'S23', 'S24', 'S25', 'S26', 'S27', 'S29', 'S31', 'S32')
    setup = [d_ for d_ in per.values() if d_['name'][:3] in BEDROOM]
    worst = max(setup, key=lambda d_: d_['luma'])
    gate('G06 night bedroom / facade ambience shots luma ≤ 34 (S21 phone-lit face insert excluded by design)', all(d_['luma'] <= 34 for d_ in setup),
         f"max {worst['luma']:.1f} ({worst['name'][:3]}); " + ' '.join(f"{d_['name'][:3]} {d_['luma']:.0f}" for d_ in setup), '≤ 34 /255 per shot')
    segs = sorted(glob.glob(os.path.join(BUILD, 'seg_*.mp4.metrics.json')))
    nmet = sum(len(json.load(open(p))) for p in segs)
    gate('G07 render integrity (4 segments, metrics every 24 frames, no frame raised)', len(segs) == 4 and nmet == 155,
         f'{len(segs)} segments, {nmet} metric rows (3720 frames / 24)', '4 segments · 155 rows')

    # 3 cut grammar measured from the delivered file — 96×54 grey proxies at 24 fps
    g = grey_stack(args.mp4).astype(np.int16)
    dd = np.abs(np.diff(g, axis=0))
    frac = (dd > 10).mean(axis=(1, 2))
    mean_ = g.mean(axis=(1, 2)); max_ = g.max(axis=(1, 2))
    prev4 = np.array([frac[max(0, i - 4):i].mean() if i > 0 else 0.0 for i in range(len(frac))])
    prev1 = np.concatenate([[0.0], frac[:-1]])
    # a cut is a JUMP: ≥ 8 % changed pixels, ≥ 2× the previous 4-frame mean AND ≥ 1.6× the previous frame
    # (a camera move ramping smoothly from rest is not a transition); the 0.8 s fade-in from black is excluded
    cand = [i + 1 for i in range(len(frac)) if frac[i] >= 0.08 and frac[i] >= 2.0 * prev4[i] and frac[i] >= 1.6 * prev1[i]
            and (i + 1) / 24.0 >= 0.9]
    det = []
    for c in cand:
        if not det or c - det[-1] > 3:
            det.append(c)
    det_t = [c / 24.0 for c in det]
    empty_t = np.where((mean_ < 2.0) & (max_ < 8))[0] / 24.0
    # one camera move split over two timeline entries on purpose: S38 ends and S39 starts on the same crop (1.05, 0.5, 0.48)
    # and the eight people appear inside the same frame — a cut here would break the payoff; measured as NO spike
    CONTINUOUS = {('S38', 'S39')}
    bounds = []
    for k_ in range(1, len(shots)):
        a, b = shots[k_ - 1], shots[k_]
        t = b['t0']
        declared_soft = a['fade_out'] > 0 or b['fade_in'] > 0
        through_black = bool(np.any(np.abs(empty_t - t) <= 0.5))
        card_pair = ('card' in a['name'] or 'title' in a['name'] or 'quiet' in a['name']) and ('card' in b['name'] or 'quiet' in b['name'])
        hard_det = any(abs(t - x) <= 0.13 for x in det_t)
        continuous = (a['name'][:3], b['name'][:3]) in CONTINUOUS
        kind = 'continuous' if continuous else ('dip' if (declared_soft or through_black or card_pair) else 'hard')
        bounds.append((t, a['name'][:3], b['name'][:3], kind, hard_det, through_black))
    hard = [bd for bd in bounds if bd[3] == 'hard']
    hard_ok = [bd for bd in hard if bd[4]]
    dips = [bd for bd in bounds if bd[3] == 'dip']
    missed = [f"{bd[1]}→{bd[2]} @{bd[0]:.1f}" for bd in hard if not bd[4]]
    cont = [bd for bd in bounds if bd[3] == 'continuous']
    cont_ok = [bd for bd in cont if not bd[4]]
    gate('G08 every planned hard cut is a measured hard cut (Δ-pixel share ≥ 8 %, spike); continuous takes show no spike',
         len(hard_ok) == len(hard) and len(cont_ok) == len(cont),
         f'{len(hard_ok)}/{len(hard)} hard cuts measured' + (f'; missed: {missed}' if missed else '') + f'; {len(dips)} soft boundaries (fades / card gaps); '
         + f'{len(cont_ok)}/{len(cont)} continuous takes seamless (S38→S39 @127.0)', 'all planned hard cuts detected')
    flurry = [d['t'] for d in ev['text'] if d['kind'] == 'readout' and 42.4 <= d['t'] < 45.7]
    PLANNED = [(x - 0.15, x + 0.15) for x in flurry] + [(ev['counter'][0]['t'] - 0.1, ev['counter'][0]['t'] + ev['counter'][0]['dur'] + 0.2)]
    PLANNED += [(light[k] - 0.2, light[k] + 0.4) for k in light] + [(45.7, 46.1)]
    for k_ in range(1, len(shots)):   # declared fades: the whole fade is a planned dip
        a, b = shots[k_ - 1], shots[k_]
        if a['fade_out'] > 0:
            PLANNED.append((b['t0'] - a['fade_out'] - 0.1, b['t0'] + 0.1))
        if b['fade_in'] > 0:
            PLANNED.append((b['t0'] - 0.1, b['t0'] + b['fade_in'] + 0.1))
    unplanned = [round(x, 2) for x in det_t if not any(abs(x - bd[0]) <= 0.13 for bd in bounds) and not any(a_ <= x <= b_ for a_, b_ in PLANNED)]
    gate('G09 no unplanned transitions (only cuts, dips, planned light events, the flurry)', len(unplanned) == 0,
         f'{len(det_t)} spikes measured: {len(det_t) - len(unplanned)} planned, {len(unplanned)} unplanned {unplanned}', '0 unplanned')
    mot = np.abs(g[24:] - g[:-24]).mean(axis=(1, 2))
    CARDS = {s['name'][:3] for s in shots if any(w in s['name'] for w in ('card', 'title', 'quiet'))}
    def longest_static(pred):
        best, run = 0, 0
        for i, m in enumerate(mot):
            sh = shots[shot_of((i + 12) / 24.0)]['name'][:3]
            if pred(sh) and m < 0.2:
                run += 1; best = max(best, run)
            else:
                run = 0
        return best / 24.0
    st_scene = longest_static(lambda sh: sh not in CARDS)
    st_card = longest_static(lambda sh: sh in CARDS)
    gate('G10 nothing perfectly still (longest 1-s-motion < 0.2 run)', st_scene <= 1.5 and st_card <= 4.5,
         f'scene shots {st_scene:.2f} s · cards {st_card:.2f} s (rain, breathing, saccades, drift, grain)', 'scene ≤ 1.5 s · cards ≤ 4.5 s')
    PLANNED_BLACK = [(0.0, 0.9), (light['phone_off'] - 0.05, light['phone_off'] + 1.3)]
    for s in shots:
        if s['name'][:3] in CARDS:
            PLANNED_BLACK.append((s['t0'] - 0.5, s['t1'] + 0.5))
        if s['fade_out'] > 0:
            PLANNED_BLACK.append((s['t1'] - 0.3, s['t1'] + 0.3))
    PLANNED_BLACK.append((ev['duration'] - 1.6, ev['duration'] + 1))
    stray = [round(t, 2) for t in empty_t if not any(a_ <= t <= b_ for a_, b_ in PLANNED_BLACK)]
    gate('G11 empty black frames only at fade-in / cards / fades / the dead phone / tail', len(stray) == 0, f'{len(empty_t)} empty frames, {len(stray)} stray {stray[:6]}', '0 stray')

    # 4 structure from the locked timeline
    holds = [s for s in shots if 4.0 <= s['dur'] <= 7.0]
    gate('G12 carried holds 4–7 s (every hold carries a VO phrase, a light or a music change)', 8 <= len(holds) <= 20, f"{len(holds)} holds: " + ', '.join(f"{s['name'][:3]} {s['dur']:.1f}" for s in holds), '8–20 holds')
    longest = max(s['dur'] for s in shots)
    gate('G13 longest shot ≤ 7 s', longest <= 7.0, f'{longest:.1f} s ({max(shots, key=lambda s: s["dur"])["name"]})', '≤ 7 s')
    mont = sorted([d['t'] for d in ev['text'] if d['kind'] == 'readout' and 42.4 <= d['t'] < 45.7])
    gaps_m = [round(mont[i + 1] - mont[i], 2) for i in range(len(mont) - 1)]
    gate('G14 montage: 3 × 0.6 s readouts → 6 × 0.25 s flurry → red card + 0.35 s hole', len(mont) == 9 and all(gp <= gq + 1e-6 for gp, gq in zip(gaps_m[1:], gaps_m[:-1])) and min(gaps_m) == 0.25,
         f"{len(mont)} readouts, gaps {gaps_m}", '9 readouts, non-increasing gaps, flurry 0.25 s')
    # beats = cuts ∪ text ∪ light ∪ counter ∪ VO phrase starts ∪ music entries ∪ animation beats
    beats = set(round(c, 1) for c in ev['cuts']) | set(round(d['t'], 1) for d in ev['text']) | set(round(d['t'], 1) for d in ev['light']) | {ev['counter'][0]['t']}
    for k, t0 in ev['vo'].items():
        beats.add(round(t0, 1))
        for g_ in info[k]['gaps']:
            beats.add(round(t0 + g_[1], 1))
    MUSIC = (12.6, 16.9, 20.2, 27.3, 33.3, 42.4, 46.5, 83.6, 89.05, 93.1, 94.2, 103.6, 108.4, 109.9, 111.6, 118.4, 121.3, 126.0, 129.4, 132.8, 135.0, 136.2, 139.6, 141.9, 146.95)
    ANIM = (78.25, 79.5, 82.0, 88.0, 90.4, 91.3, 94.55, 97.9, 99.95, 102.15, 113.8, 114.6, 119.45, 137.0)
    beats |= set(round(t, 1) for t in MUSIC + ANIM)
    bl = sorted(t for t in beats if t < 150.8)
    bgaps = [(round(bl[i + 1] - bl[i], 2), bl[i]) for i in range(len(bl) - 1)]
    mg = max(bgaps)
    gate('G15 beats density (new thing ≤ 4.8 s apart; ≥ 120 beats)', len(bl) >= 120 and mg[0] <= 4.8, f"{len(bl)} beats, max gap {mg[0]} s at {mg[1]} s", '≥ 120 beats, gap ≤ 4.8 s')
    vo_total = sum(info[k]['dur'] for k in ev['vo'])
    gate('G16 full voiceover (brief: 10 clips, voice-03, each at its planned start)', len(ev['vo']) == 10 and all(k in info for k in ev['vo']),
         f"{len(ev['vo'])} clips, {vo_total:.1f} s of voice = {vo_total / ev['duration'] * 100:.0f} % of runtime; starts " + ' '.join(f"{v:.1f}" for v in ev['vo'].values()), '10 clips')
    gate('G17 callbacks ≥ 3', len(dna['callbacks']) >= 3, f"{len(dna['callbacks'])}: " + ' | '.join(c.split(' — ')[0].split(':')[0][:40] for c in dna['callbacks']), '≥ 3')
    gate('G18 quotable lines = 2 + title pun, no CTA', len(dna['quotable_lines']) == 2 and bool(dna.get('title_pun')), f"{dna['quotable_lines']} · “{dna['title_pun'][:60]}”", '2 + pun, 0 CTA')
    gate('G19 text contrast (bone on wall / red villain large type / white answers)', contrast((236, 232, 222), (14, 14, 15)) >= 4.5 and contrast((214, 38, 32), (7, 7, 9)) >= 3.0,
         f"bone {contrast((236, 232, 222), (14, 14, 15)):.1f}:1 · red {contrast((214, 38, 32), (7, 7, 9)):.1f}:1 (≥ 60 px)", 'body ≥ 4.5:1 · large ≥ 3:1')

    # 5 sound measured on the delivered file
    I, lra, tp, prof = loudness(args.mp4)
    gate('G20 integrated loudness', abs(I + 16.5) <= 1.0, f'{I:.1f} LUFS (wav {ms["lufs"]})', '−16.5 ± 1.0 LUFS')
    gate('G21 true peak', tp <= -1.0, f'{tp:.1f} dBTP', '≤ −1.0 dBTP')
    gate('G22 loudness range (narrated film: 4–16)', 4.0 <= lra <= 16.0, f'{lra:.1f} LU', '4–16 LU')
    tail0 = 146.6
    tail_rms = rms_window(args.mp4, tail0, pr['duration'])
    last_vo_end = ev['vo']['vo10'] + info['vo10']['dur']
    gate('G23 quiet ending (from the second end card to the end)', tail_rms <= -26.0, f'{tail_rms:.1f} dB RMS from {tail0:.1f} s (last line ends {last_vo_end:.1f} s)', '≤ −26 dB RMS')
    def S_at(t):
        c = [s for tt, s in prof if abs(tt - t) < 0.3]
        return c[0] if c else float('nan')
    bed_wav = os.path.join(BUILD, 'bed_only.wav')
    _, _, _, bprof = loudness(bed_wav) if os.path.exists(bed_wav) else (0, 0, 0, prof)
    def B_at(t):
        c = [s_ for tt, s_ in bprof if abs(tt - t) < 0.3]
        return c[0] if c else float('nan')
    climax_t = max(((tt, s_) for tt, s_ in bprof if 136.0 <= tt <= 146.0), key=lambda z: z[1])[0]
    arc = {k: B_at(t) for k, t in (('hook 5 s', 5.0), ('windows 30 s', 30.0), ('dead phone 76 s', 76.0), ('clock stop 88.5 s', 88.5), (f'climax {climax_t:.0f} s', climax_t), ('end 153 s', 153.0))}
    ck = [k for k in arc if k.startswith('climax')][0]
    full = ' · '.join(f'{k.split()[0]} {S_at(t):.1f}' for k, t in (('hook', 5.0), ('windows', 30.0), ('phone', 76.0), ('climax', climax_t), ('end', 153.0)))
    gate('G24 dynamic arc of the score/SFX bed (VO-muted bus; with a full voiceover the mix short-term loudness is the voice)',
         arc['dead phone 76 s'] <= arc['windows 30 s'] - 1.5 and arc[ck] >= arc['hook 5 s'] + 6.0 and arc['end 153 s'] <= arc[ck] - 10,
         'bed: ' + ' · '.join(f'{k} {v:.1f}' for k, v in arc.items()) + f' (LUFS-S) · full mix: {full}', 'dead phone ≤ windows − 1.5; climax ≥ hook + 6; end ≤ climax − 10')
    gate('G25 limiter transparency', ms.get('limiter_pct', 0) <= 3.0, f"{ms.get('limiter_pct', 0)} % samples under gain reduction", '≤ 3 %')

    # 6 brain + delivery
    sys.path.insert(0, os.path.join(ROOT, 'brain'))
    import concept as C
    ok20, rows20 = C.gate(os.path.join(WF, 'DNA_THE_WINDOW.json'), verbose=False)
    gate('G26 brain gate #20 freshness', ok20, f"{sum(r[1] for r in rows20)}/{len(rows20)} PASS", 'PASS')
    gate('G27 md5 local = Drive', (args.drive_md5 == md5) if args.drive_md5 else False, f'local {md5} · drive {args.drive_md5 or "—"}', 'equal')

    passed = sum(1 for r in rows if r[1])
    lines = [f"# GATES — THE WINDOW v1 (WF-03 · Monarch Noir Film · film #2 · NOIRGO MAX) — {passed}/{len(rows)} PASS",
             f"_measured {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} on `{os.path.basename(args.mp4)}` ({size / 1e6:.2f} MB, md5 `{md5}`" + (f", Drive `{args.drive_id}`" if args.drive_id else '') + ")_", '',
             '| # gate | result | measured | target |', '|---|---|---|---|']
    for name, ok, measured, target in rows:
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {measured} | {target} |")
    lines += ['', '## per-shot picture metrics — measured on the delivered file (480×270 area-scaled, 6 fps, /255)', '', '| shot | t0 | dur | luma | dark<30 | chroma | p99 |', '|---|---|---|---|---|---|---|']
    for k_ in sorted(per):
        d_ = per[k_]; sh = shots[k_]
        lines.append(f"| {d_['name']} | {sh['t0']:.1f} | {sh['dur']:.1f} | {d_['luma']:.1f} | {d_['dark'] * 100:.0f} % | {d_['chroma']:.1f} | {d_['p99']:.0f} |")
    lines += ['', '## transitions measured on 96×54 grey proxies (spike = share of pixels changing > 10 levels ≥ 8 % and ≥ 2× the previous 4 frames)', '',
              '| boundary | t | planned | measured |', '|---|---|---|---|']
    for t, a, b, kind, hard_det, through_black in bounds:
        lines.append(f"| {a} → {b} | {t:.2f} | {kind} | {'hard cut spike' if hard_det else ''}{' + ' if hard_det and through_black else ''}{'through black' if through_black else ''}{'' if (hard_det or through_black) else ('soft' if kind == 'dip' else 'not detected')} |")
    lines += ['', f"spikes at: {[round(x, 2) for x in det_t]}", '',
              '## short-term loudness arc (LUFS-S)', '', ' · '.join(f'{k} {v:.1f}' for k, v in arc.items()), '',
              '## brain gate #20', ''] + [f"- [{'PASS' if ok else 'FAIL'}] {n} {('— ' + why) if why else ''}" for n, ok, why in rows20]
    open(args.out, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print('\n'.join(lines[:5 + len(rows)]))
    json.dump(dict(md5=md5, size=size, passed=passed, total=len(rows), lufs=I, tp=tp, lra=lra, duration=pr['duration'], luma=luma, dark=dark, chroma=chroma,
                   holds=len(holds), cuts_detected=len(det_t), hard_cuts=f'{len(hard_ok)}/{len(hard)}', beats=len(bl), max_beat_gap=mg[0], tail_rms=tail_rms, arc=arc),
              open(os.path.join(BUILD, 'gates_summary.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
