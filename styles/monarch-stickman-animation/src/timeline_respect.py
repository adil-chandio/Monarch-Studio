"""Timeline for the 90 s "LOG AAPKI IZZAT KYUN NAHI KARTE" short — cut to the measured voice.

Same law as the POWER short: the voice stays at its recorded tempo (atempo 1.0), internal
pauses tightened to 0.30 s (src/vo_fit.py applied to assets/r{1..9}.mp3 -> r{i}_fit.wav),
the picture is cut to the result, and the remaining air is placed on purpose: a 1.2 s room
reveal before the first word, a 2.6 s slow-motion hold on the turn, and the end card.
"""
# measured lengths of assets/r{i}_fit.wav (build/vo_fit_respect.json)
VO = [6.338, 7.626, 4.044, 8.380, 7.458, 7.328, 7.590, 7.608, 11.468]
LEAD = [1.20, 0.25, 0.40, 0.25, 0.25, 0.25, 0.25, 0.25, 0.90]
TAIL = [1.50, 1.30, 2.60, 1.50, 1.50, 1.50, 1.60, 1.60, None]     # last tail absorbs the remainder
DUR_TOTAL = 90.0
ATEMPO = [1.0] * 9

_fixed = sum(VO) + sum(LEAD) + sum(t for t in TAIL if t is not None)
TAIL[8] = round(DUR_TOTAL - _fixed, 3)
assert 3.0 <= TAIL[8] <= 6.0, TAIL[8]

starts, t = [], 0.0
for i in range(9):
    starts.append(round(t, 3))
    t += LEAD[i] + VO[i] + TAIL[i]
SCENE_START = starts
SCENE_END = starts[1:] + [DUR_TOTAL]
VO_AT = [round(SCENE_START[i] + LEAD[i], 3) for i in range(9)]
ADELAY_MS = [int(round(v * 1000)) for v in VO_AT]
CUTS = SCENE_START[1:]
NAMES = ['HOOK', 'VILLAIN', 'TURN', 'KAM BOLO', 'WAQT', 'NA', 'KAMAR', 'LAFZ', 'PAYOFF']

# phrase starts inside each fitted clip (seconds from the clip start; src/vo_fit.silences on the fit)
PHRASES = [
    [0.00, 1.33, 2.88, 4.99, 5.77],                              # kamre | koi sar | izzat kyun | jawab | kadwa
    [0.00, 2.50, 3.99, 5.59, 6.64],                              # kyunki | har baat haan | har mazaak | jo sab ka | kisi ka nahi
    [0.00, 1.70, 2.63, 3.53],                                    # izzat maangi | kamai | paanch rules | aaj se
    [0.00, 1.00, 1.77, 3.41, 5.32, 6.16, 7.22],                  # rule ek | kam bolo | jo har waqt | sasti | ek jumla | sahi waqt | poora kamra
    [0.00, 0.94, 1.69, 2.52, 4.22, 5.84],                        # rule do | apna waqt | mehnga | jo available | zaroori nahi | marzi
    [0.00, 1.02, 2.31, 5.23, 6.45],                              # rule teen | na kehna | har haan ki keemat | ek saaf na | bina safai
    [0.00, 0.99, 2.01, 3.01, 3.95, 5.17, 6.69],                  # rule chaar | sambhalo | seedhi kamar | dheemi chaal | nazar | jism pehle | zubaan
    [0.00, 1.19, 2.65, 5.84, 6.87],                              # rule paanch | jo kaho | ek tooti | aapka lafz | aapki keemat
    [0.00, 1.25, 2.62, 4.13, 5.74, 6.77, 7.72, 8.36, 9.22, 10.26],  # ab wahi kamra | aap andar | sab sar | izzat shor | khamoshi | paanch | aaj se | follow | save | kal phir
]

if __name__ == '__main__':
    for i in range(9):
        print(f'S{i+1} {NAMES[i]:9s} {SCENE_START[i]:7.3f} -> {SCENE_END[i]:7.3f}  '
              f'dur {SCENE_END[i]-SCENE_START[i]:6.3f}  vo {VO[i]:.3f} at {VO_AT[i]:.3f}  lead {LEAD[i]} tail {TAIL[i]}')
    print('total', SCENE_END[-1], ' frames', int(round(DUR_TOTAL * 30)), ' adelay', ADELAY_MS)
