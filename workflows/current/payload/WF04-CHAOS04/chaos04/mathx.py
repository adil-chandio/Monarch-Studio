"""Pure-python maths: no Blender, so the timing and direction layers stay testable."""
from __future__ import annotations

import math
import random

TAU = math.pi * 2


def smoothstep(a, b, x):
    if b == a:
        return 0.0
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def ease_io(t):
    t = min(1.0, max(0.0, t))
    return t * t * t * (t * (t * 6 - 15) + 10)


def wobble(seed, t, amps=((0.31, 1.0), (0.77, 0.55), (1.9, 0.28), (4.3, 0.12)), freq=1.0):
    rnd = random.Random(seed)
    total = 0.0
    for f, a in amps:
        total += a * math.sin(TAU * f * freq * t + rnd.uniform(0, TAU))
    return total


def lerp(a, b, t):
    return a + (b - a) * t


def vlerp(a, b, t):
    from mathutils import Vector
    return Vector(a).lerp(Vector(b), min(1.0, max(0.0, t)))
