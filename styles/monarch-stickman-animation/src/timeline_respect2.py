"""Timeline v2 for "LOG AAPKI IZZAT KYUN NAHI KARTE" — the voice flows, the picture cuts every 2-3 s.

User note (turn 10): the 90 s cut reached 90 s only through its pauses (1.55-2.85 s between
chapters); "voiceover flow barqarar hona chahiye, pauses na kam na zyada".  Measured: every
fitted clip already has <= 0.30 s inside (vo_fit), so only the chapter gaps change:

    sentence gap inside a clip     0.26-0.30 s   (unchanged)
    chapter gap                    0.55-0.70 s   (~2x a sentence gap = a paragraph breath)
    room reveal before word one    0.60 s
    end card after the last word   1.85 s

The same nine fitted clips (voice-01, atempo 1.0) -> 75.2 s = 2256 frames.
The chapter gap is split TAIL (after the last word, before the cut) + LEAD (cut -> next word)
so a chapter transition always lands inside the breath, never on a word.
"""
VO = [6.338, 7.626, 4.044, 8.380, 7.458, 7.328, 7.590, 7.608, 11.468]     # assets/r{i}_fit.wav
GAP = [0.60, 0.65, 0.70, 0.55, 0.55, 0.60, 0.55, 0.70]                     # breath between chapter i and i+1
LEAD = [0.60] + [round(g * 0.42, 3) for g in GAP]                           # cut -> first word
TAIL = [round(g - LEAD[i + 1], 3) for i, g in enumerate(GAP)] + [1.85]      # last word -> cut (last: end card)
DUR_TOTAL = round(sum(VO) + sum(LEAD) + sum(TAIL), 3)
ATEMPO = [1.0] * 9

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

# phrase starts inside each fitted clip (unchanged — the clips are the same files)
PHRASES = [
    [0.00, 1.33, 2.88, 4.99, 5.77],
    [0.00, 2.50, 3.99, 5.59, 6.64],
    [0.00, 1.70, 2.63, 3.53],
    [0.00, 1.00, 1.77, 3.41, 5.32, 6.16, 7.22],
    [0.00, 0.94, 1.69, 2.52, 4.22, 5.84],
    [0.00, 1.02, 2.31, 5.23, 6.45],
    [0.00, 0.99, 2.01, 3.01, 3.95, 5.17, 6.69],
    [0.00, 1.19, 2.65, 5.84, 6.87],
    [0.00, 1.25, 2.62, 4.13, 5.74, 6.77, 7.72, 8.36, 9.22, 10.26],
]

if __name__ == '__main__':
    for i in range(9):
        print(f'S{i+1} {NAMES[i]:9s} {SCENE_START[i]:7.3f} -> {SCENE_END[i]:7.3f}  '
              f'dur {SCENE_END[i]-SCENE_START[i]:6.3f}  vo {VO[i]:.3f} at {VO_AT[i]:.3f}  lead {LEAD[i]} tail {TAIL[i]}')
    print('total', DUR_TOTAL, ' frames', int(round(DUR_TOTAL * 30)), ' adelay', ADELAY_MS)
    print('voice share', round(sum(VO) / DUR_TOTAL * 100, 1), '%   air', round(DUR_TOTAL - sum(VO), 2), 's')
