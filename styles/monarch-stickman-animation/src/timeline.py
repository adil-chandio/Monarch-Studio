"""Shared timeline for the 37s stickman version (derived from measured VO clip lengths)."""
TEMPO = 1.45
RAW = [7.13, 10.15, 9.31, 6.40, 9.02, 8.33]
VO = [round(r / TEMPO, 3) for r in RAW]
LEAD = 0.30
TAIL = [0.35, 0.30, 0.30, 0.30, 0.30, 0.45]

DUR_TOTAL = 37.0
starts, t = [], 0.0
for i in range(6):
    starts.append(round(t, 3))
    t += (LEAD if i == 0 else 0.0) + VO[i] + TAIL[i]
SCENE_START = starts
SCENE_END = starts[1:] + [DUR_TOTAL]
VO_AT = [round(SCENE_START[i] + (LEAD if i == 0 else 0.05), 3) for i in range(6)]

if __name__ == '__main__':
    for i in range(6):
        print(f'S{i+1}: {SCENE_START[i]:6.2f} -> {SCENE_END[i]:6.2f}  (vo {VO[i]:.2f} at {VO_AT[i]:.2f})')
    print('total', SCENE_END[-1])
