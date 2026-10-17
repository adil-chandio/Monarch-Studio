#!/usr/bin/env python3
"""Fit a *geometric* Monarch head from the user's locked face-sheet turnaround.

The still is input to a one-time photogrammetric fit and diffuse-texture bake;
it is NEVER a frame/plane in the animation. All animation moves the mesh as a
rigid head. Sensitive output belongs in .runtime (not Git).

Third-party topology: MediaPipe canonical_face_model.obj (468 vertices, 898
triangles), Apache-2.0, google-ai-edge/mediapipe commit at
https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/modules/face_geometry/data/canonical_face_model.obj
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import mediapipe as mp
import numpy as np
from PIL import Image

# Locked REAL v5 lossless character sheet. Hero shot is the largest near-frontal
# view; other turnaround panels are for visual comparison, not video plates.
HERO_CROP = (72, 414, 968, 1614)
EXPECTED_SHA = "0e666d1c4e75949d1639c2bcf347a38da4834164"  # Git blob SHA (model)


def parse_topology(path: Path) -> tuple[np.ndarray, list[tuple[int, int, int]]]:
    raw = path.read_bytes()
    blob_sha = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if blob_sha != EXPECTED_SHA:
        raise ValueError("MediaPipe canonical topology hash mismatch")
    vertices: list[list[float]] = []
    faces: list[tuple[int, int, int]] = []
    for line in raw.decode().splitlines():
        if line.startswith("v "):
            vertices.append([float(v) for v in line.split()[1:4]])
        elif line.startswith("f "):
            face = tuple(int(p.split("/")[0]) - 1 for p in line.split()[1:4])
            if len(face) != 3:
                raise ValueError("Canonical topology has a non-triangle")
            faces.append(face)
    if len(vertices) != 468 or len(faces) != 898:
        raise ValueError(f"Expected canonical 468/898 mesh; got {len(vertices)}/{len(faces)}")
    if any(i < 0 or i >= len(vertices) for face in faces for i in face):
        raise ValueError("Invalid face index")
    return np.asarray(vertices, dtype=np.float64), faces


def fit(canonical: np.ndarray, landmarks: np.ndarray, image_size: tuple[int, int]) -> tuple[np.ndarray, np.ndarray, float]:
    """Metric xyz, image UV, and scale (m/pixel); no per-frame morphing.

    Canonical geometry controls Z depth while measured v5 landmarks control X/Y
    silhouette. The coarse single-view z from MediaPipe is weighted only 25%;
    this prevents the rubber-mask effect from treating face-landmark noise as
    animated geometry. 33/263 are outer eye corners, 8.891718 cm in MediaPipe.
    Our world frame: X right, Y *away* from camera, Z up; nose projects to -Y.
    """
    if canonical.shape != (468, 3) or landmarks.shape != (468, 3):
        raise ValueError("Expected a 468-point face, with x/y/z per vertex")
    w, h = image_size
    eye_px = abs(landmarks[263, 0] - landmarks[33, 0]) * w
    if not 70 < eye_px < w * 0.65:
        raise ValueError(f"Implausible eye-corner distance: {eye_px:.1f}px")
    metres_per_px = (canonical[263, 0] - canonical[33, 0]) * 0.01 / eye_px
    eye_mid_x = (landmarks[33, 0] + landmarks[263, 0]) * 0.5
    xyz = np.empty((468, 3), dtype=np.float64)
    xyz[:, 0] = (landmarks[:, 0] - eye_mid_x) * w * metres_per_px
    xyz[:, 2] = (landmarks[168, 1] - landmarks[:, 1]) * h * metres_per_px
    canonical_depth = -(canonical[:, 2] - canonical[168, 2]) * 0.01
    measured_depth = (landmarks[:, 2] - landmarks[168, 2]) * w * metres_per_px
    xyz[:, 1] = 0.75 * canonical_depth + 0.25 * measured_depth
    uv = np.column_stack((landmarks[:, 0], 1.0 - landmarks[:, 1]))
    if not np.all(np.isfinite(xyz)) or not np.all(np.isfinite(uv)):
        raise ValueError("Face fit produced non-finite coordinates")
    return xyz, uv, metres_per_px


def fit_sheet(sheet: Path, topology: Path, output: Path, crop: tuple[int, int, int, int] = HERO_CROP) -> dict:
    original = Image.open(sheet).convert("RGB")
    if original.size != (2464, 2042):
        raise ValueError(f"Expected locked v5 full-res 2464×2042 sheet; got {original.size}")
    portrait = original.crop(crop)
    with mp.solutions.face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1,
                                          refine_landmarks=False, min_detection_confidence=0.65) as detector:
        result = detector.process(np.asarray(portrait))
    if not result.multi_face_landmarks or len(result.multi_face_landmarks) != 1:
        raise RuntimeError("Could not find exactly one face in the v5 hero portrait")
    landmarks = np.asarray([[v.x, v.y, v.z] for v in result.multi_face_landmarks[0].landmark])
    canonical, faces = parse_topology(topology)
    xyz, uv, scale = fit(canonical, landmarks, portrait.size)
    output.mkdir(parents=True, exist_ok=True)
    mesh_path = output / "monarch_face_v5.obj"
    texture_path = output / "monarch_face_v5_albedo.png"
    portrait.save(texture_path)
    with mesh_path.open("w") as fp:
        fp.write("# Monarch v5 3D face, fitted once from locked reference. Biometric asset: DO NOT COMMIT.\n")
        for x, y, z in xyz:
            fp.write(f"v {x:.8f} {y:.8f} {z:.8f}\n")
        for u, v in uv:
            fp.write(f"vt {u:.8f} {v:.8f}\n")
        for a, b, c in faces:
            fp.write(f"f {a+1}/{a+1} {b+1}/{b+1} {c+1}/{c+1}\n")
    stats = {
        "model": "CUSTOM_HERO_REAL_SHEET_v5 fitted 468-vertex surface",
        "source_sha256": hashlib.sha256(sheet.read_bytes()).hexdigest(),
        "mesh_sha256": hashlib.sha256(mesh_path.read_bytes()).hexdigest(),
        "texture_sha256": hashlib.sha256(texture_path.read_bytes()).hexdigest(),
        "source_crop": list(crop),
        "metric_metres_per_pixel": scale,
        "vertices": len(xyz), "triangles": len(faces),
        "mesh_file": mesh_path.name, "albedo_file": texture_path.name,
        "privacy": "Raw photo/texture/identity geometry remain in ignored .runtime; never commit or upload without approval.",
    }
    (output / "model_manifest.json").write_text(json.dumps(stats, indent=2) + "\n")
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet", type=Path, required=True)
    parser.add_argument("--canonical", type=Path, default=Path(__file__).with_name("canonical_face_model.obj"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(fit_sheet(args.sheet, args.canonical, args.output), indent=2))


if __name__ == "__main__":
    main()
