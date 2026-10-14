"""Small deterministic kinematics, independent of the render backend.

All distances are meters. Foot targets are world-space positions: no camera
movement, optical flow, or image deformation is used to imply a step.
"""
import math
import numpy as np


def ease(t):
    t = float(np.clip(t, 0.0, 1.0))
    return t * t * (3.0 - 2.0 * t)


def pulse(t, start, rise, hold, fall):
    if t < start:
        return 0.0
    if t < start + rise:
        return ease((t - start) / rise)
    if t < start + rise + hold:
        return 1.0
    return 1.0 - ease((t - start - rise - hold) / fall)


def two_bone(base, target, length_a, length_b, pole):
    """Analytic, length-preserving two-link inverse kinematics.

    Returns joint, reachable tip, and target residual. The solver never scales
    a bone. A zero-length aim or collinear pole is handled explicitly.
    """
    a, t, p = (np.asarray(v, dtype=float) for v in (base, target, pole))
    delta = t - a
    distance = float(np.linalg.norm(delta))
    axis = delta / distance if distance > 1e-10 else np.array([0., 0., -1.])
    d = float(np.clip(distance, abs(length_a - length_b) + 1e-6,
                      length_a + length_b - 1e-6))
    tip = a + axis * d
    pole_plane = (p - a) - axis * np.dot(p - a, axis)
    if np.linalg.norm(pole_plane) < 1e-9:
        fallback = np.array([1., 0., 0.])
        if abs(np.dot(fallback, axis)) > .9:
            fallback = np.array([0., 1., 0.])
        pole_plane = fallback - axis * np.dot(fallback, axis)
    pole_plane /= np.linalg.norm(pole_plane)
    along = (length_a ** 2 - length_b ** 2 + d ** 2) / (2 * d)
    height = math.sqrt(max(0., length_a ** 2 - along ** 2))
    joint = a + axis * along + pole_plane * height
    return joint, tip, float(np.linalg.norm(tip - t))


def targets(t):
    """One measured step, planted recovery, and a deliberate cuff adjustment."""
    advance = ease((t - .85) / 1.70)
    step = ease((t - 1.0) / .90)
    lift = .055 * math.sin(math.pi * step)
    root = np.array([-.018 * math.sin(math.pi * advance), -.115 * advance,
                     -.025 - .005 * math.sin(math.pi * advance)])
    feet = {
        'L': np.array([-.105, -.25 * step, .095 + lift]),
        'R': np.array([.105, 0., .095]),
    }
    adjust = pulse(t, .95, 1.0, 1.15, 1.3)
    hands = {
        'L': np.array([-.270, -.035, .946]) * (1-adjust)
             + np.array([-.09, -.250, 1.185]) * adjust + root,
        'R': np.array([.270, -.035, .946]) * (1-adjust)
             + np.array([-.025, -.306, 1.218]) * adjust + root,
    }
    yaw = -.24 * pulse(t, 1.85, .75, .90, 1.15)
    return {'root': root, 'feet': feet, 'hands': hands,
            'adjust': adjust, 'head_yaw': yaw, 'left_step': step}
