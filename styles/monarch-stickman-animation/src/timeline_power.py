"""Timeline for the 42 s "POWERFUL MAN" short — cut to the measured voice.

The 37 s build stretched every line 1.35–1.53x to hit a frozen target. Here the
voice is left at its recorded tempo (atempo 1.0): the pauses inside each clip
were tightened to 0.30 s (src/vo_fit.py), the picture is cut to the result, and
the remaining air is distributed as scene tails so the film ends at 42.000 s.
"""
# measured lengths of assets/p{i}_fit.wav (src/vo_fit.py output)
VO = [5.626, 5.516, 6.516, 6.250, 6.546, 8.122]
LEAD = [0.30, 0.05, 0.05, 0.05, 0.05, 0.05]
TAIL = [0.45, 0.42, 0.42, 0.42, 0.42, None]      # last tail absorbs the remainder
DUR_TOTAL = 42.0
ATEMPO = [1.0] * 6

_fixed = sum(VO) + sum(LEAD) + sum(t for t in TAIL if t is not None)
TAIL[5] = round(DUR_TOTAL - _fixed, 3)
assert TAIL[5] >= 0.30, TAIL[5]

starts, t = [], 0.0
for i in range(6):
    starts.append(round(t, 3))
    t += LEAD[i] + VO[i] + TAIL[i]
SCENE_START = starts
SCENE_END = starts[1:] + [DUR_TOTAL]
VO_AT = [round(SCENE_START[i] + LEAD[i], 3) for i in range(6)]
ADELAY_MS = [int(round(v * 1000)) for v in VO_AT]
CUTS = SCENE_START[1:]
NAMES = ['HOOK', 'JISM', 'DIMAGH', 'CONTROL', 'VALUE', 'GO']

if __name__ == '__main__':
    for i in range(6):
        print(f'S{i+1} {NAMES[i]:8s} {SCENE_START[i]:7.3f} -> {SCENE_END[i]:7.3f}  '
              f'dur {SCENE_END[i]-SCENE_START[i]:6.3f}  vo {VO[i]:.3f} at {VO_AT[i]:.3f}  tail {TAIL[i]}')
    print('total', SCENE_END[-1], ' adelay', ADELAY_MS)
