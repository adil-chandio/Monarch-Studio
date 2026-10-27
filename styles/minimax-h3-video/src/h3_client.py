#!/usr/bin/env python3
"""WF-06 · MiniMax-H3 API client for Monarch Studio (dependency-free, stdlib only).

Same logic as styles/minimax-h3-video/colab/MONARCH_H3_COLAB.ipynb, but runnable from a
terminal / CI / this sandbox so the shot list can live in git instead of a notebook.

Usage
-----
    export MINIMAX_API_KEY=...
    python3 styles/minimax-h3-video/src/h3_client.py estimate data/shotlist.example.json
    python3 styles/minimax-h3-video/src/h3_client.py run data/shotlist.example.json --out /tmp/h3 --yes
    python3 styles/minimax-h3-video/src/h3_client.py query 424010985738629

Exit codes: 0 ok · 2 usage/config/validation error · 3 API/task error.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import mimetypes
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

API_BASE = os.environ.get("MINIMAX_API_BASE", "https://api.minimax.io")
CREATE_PATH = "/v2/video_generation"
QUERY_PATH = "/v2/query/video_generation/{task_id}"

# Official list prices, USD per output second. Verify before quoting.
RATES = {
    "MiniMax-H3": {"768P": 0.08, "2K": 0.13},
    "MiniMax-H3-Highspeed": {"768P": 0.06},
    "MiniMax-H3-Lite": {"480P": 0.04, "768P": 0.04},
    "MiniMax-H3-Max": {"480P": 0.05, "768P": 0.08},
}
IMAGE_RATE_EXTRA = 0.04  # per reference image beyond the first five
FREE_IMAGES = 5
REGEN_2K_RATE = 0.05

RETRY_BUFFER = 1.5


class ConfigError(RuntimeError):
    pass


class TaskError(RuntimeError):
    pass


# --------------------------------------------------------------------------- helpers
def md5(path: str | pathlib.Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def data_url(path: str | pathlib.Path) -> str:
    p = pathlib.Path(path)
    if not p.is_file():
        raise ConfigError(f"reference file not found: {p}")
    mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode("ascii")


def as_url(value: str) -> str:
    return value if str(value).startswith(("http://", "https://", "data:")) else data_url(value)


def _request(method: str, url: str, key: str, payload: dict | None = None, timeout: int = 120) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as exc:  # surface the API error body, not just the status
        body = exc.read().decode(errors="replace")
        raise TaskError(f"{method} {url} -> {exc.code}: {body[:600]}") from None
    except urllib.error.URLError as exc:
        raise TaskError(f"{method} {url} network error: {exc.reason}") from None


# --------------------------------------------------------------------------- API
def build_payload(spec: dict, resolve_files: bool = True) -> dict:
    """Shot spec -> POST /v2/video_generation body.

    resolve_files=False validates structure only (so a shot list can be priced before the
    reference images exist); True inlines local files and fails fast on a missing path.
    """
    if not spec.get("prompt", "").strip():
        raise ConfigError(f"{spec.get('id')}: prompt is empty")
    content: list[dict] = [{"type": "text", "text": spec["prompt"]}]

    has_keyframe = bool(spec.get("first_frame") or spec.get("last_frame"))
    refs = list(spec.get("references") or [])
    has_reference = bool(refs or spec.get("reference_videos") or spec.get("reference_audio"))
    if has_keyframe and has_reference:
        raise ConfigError(
            f"{spec.get('id')}: image-to-video and reference-to-video are mutually exclusive")

    def resolve(value: str) -> str:
        return as_url(value) if resolve_files else str(value)

    if spec.get("first_frame"):
        content.append({"type": "image_url", "image_url": {"url": resolve(spec["first_frame"])},
                        "role": "first_frame"})
    if spec.get("last_frame"):
        content.append({"type": "image_url", "image_url": {"url": resolve(spec["last_frame"])},
                        "role": "last_frame"})
    for ref in refs:
        content.append({"type": "image_url", "image_url": {"url": resolve(ref)}, "role": "reference_image"})
    for vid in spec.get("reference_videos") or []:
        content.append({"type": "video_url", "video_url": {"url": resolve(vid)}, "role": "reference_video"})
    for aud in spec.get("reference_audio") or []:
        content.append({"type": "audio_url", "audio_url": {"url": resolve(aud)}, "role": "reference_audio"})

    if len(refs) > 9:
        raise ConfigError(f"{spec.get('id')}: at most 9 reference images allowed")

    duration = int(spec["duration"])
    if not 4 <= duration <= 15:
        raise ConfigError(f"{spec.get('id')}: duration must be 4-15 s (got {duration})")

    model = spec.get("model", "MiniMax-H3")
    resolution = spec.get("resolution", "768P")
    if resolution not in RATES.get(model, {}):
        raise ConfigError(f"{spec.get('id')}: {model} does not offer {resolution}")

    payload = {"model": model, "content": content, "resolution": resolution, "duration": duration}

    ratio = spec.get("ratio")
    if has_keyframe:
        payload["ratio"] = "adaptive"          # ignored by the API, kept explicit for receipts
    elif ratio == "adaptive":
        if not has_reference:
            raise ConfigError(
                f"{spec.get('id')}: text-to-video requires an explicit ratio, not adaptive")
        payload["ratio"] = "adaptive"
    elif ratio:
        payload["ratio"] = ratio
    elif not has_reference:
        raise ConfigError(f"{spec.get('id')}: text-to-video requires an explicit ratio")
    return payload


def create_task(payload: dict, key: str) -> str:
    data = _request("POST", f"{API_BASE}{CREATE_PATH}", key, payload)
    task_id = data.get("task_id")
    if not task_id:
        raise TaskError(f"no task_id in response: {json.dumps(data)[:400]}")
    return str(task_id)


def query_task(task_id: str, key: str) -> dict:
    return _request("GET", f"{API_BASE}{QUERY_PATH.format(task_id=task_id)}", key).get("task", {})


def poll(task_id: str, key: str, timeout: int = 1800, interval: int = 15, verbose: bool = True) -> dict:
    started = time.time()
    while time.time() - started < timeout:
        task = query_task(task_id, key)
        status = task.get("status")
        if verbose:
            print(f"  [{int(time.time() - started):4d}s] {status}", flush=True)
        if status == "succeeded":
            return task
        if status in ("failed", "cancelled"):
            raise TaskError(f"task {task_id} {status}: {json.dumps(task)[:600]}")
        time.sleep(interval)
    raise TaskError(f"task {task_id} still running after {timeout}s (already billed — keep the task_id)")


def download(url: str, dest: pathlib.Path) -> pathlib.Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=300) as resp, open(dest, "wb") as fh:
        for chunk in iter(lambda: resp.read(1 << 20), b""):
            fh.write(chunk)
    return dest


# --------------------------------------------------------------------------- cost
def shot_cost(spec: dict) -> float | None:
    model = spec.get("model", "MiniMax-H3")
    resolution = spec.get("resolution", "768P")
    rate = RATES.get(model, {}).get(resolution)
    if rate is None:
        return None
    extra_images = max(0, len(spec.get("references") or []) - FREE_IMAGES)
    ref_video_seconds = float(spec.get("reference_video_seconds", 0) or 0)
    return int(spec["duration"]) * rate + extra_images * IMAGE_RATE_EXTRA + ref_video_seconds * rate


def estimate(shots: list[dict]) -> float:
    total = 0.0
    print(f"{'shot':<32}{'model':<24}{'res':<6}{'sec':>5}  cost")
    for spec in shots:
        cost = shot_cost(spec)
        if cost is None:
            print(f"{spec.get('id', '?'):<32}{spec.get('model', '?'):<24}{spec.get('resolution', '?'):<6}"
                  f"{spec.get('duration', '?'):>5}  ?")
            continue
        total += cost
        print(f"{spec.get('id', '?'):<32}{spec.get('model', '?'):<24}{spec.get('resolution', '?'):<6}"
              f"{spec['duration']:>5}  ${cost:.2f}")
    print(f"\nESTIMATE ${total:.2f}  ·  with {RETRY_BUFFER}x retry buffer ${total * RETRY_BUFFER:.2f}")
    return total


# --------------------------------------------------------------------------- run
def run_shot(spec: dict, key: str, out_dir: pathlib.Path, timeout: int = 1800) -> dict:
    payload = build_payload(spec)
    print(f"\n> {spec['id']} · {payload['model']} · {payload['resolution']} · {payload['duration']}s")
    task_id = create_task(payload, key)
    print("  task_id:", task_id)
    task = poll(task_id, key, timeout=timeout)

    url = task.get("content", {}).get("url")
    receipt = {
        "id": spec["id"],
        "task_id": task_id,
        "model": payload["model"],
        "resolution": payload["resolution"],
        "duration": payload["duration"],
        "ratio": task.get("ratio", payload.get("ratio")),
        "usage": task.get("usage", {}),
        "url": url,
        "created_at": int(time.time()),
    }
    if url:
        dest = download(url, out_dir / f"{spec['id']}.mp4")
        receipt.update({"local_path": str(dest), "md5": md5(dest), "bytes": dest.stat().st_size})
        print(f"  ok {dest} ({receipt['bytes'] / 1e6:.1f} MB, md5 {receipt['md5'][:10]})")
    return receipt


def load_shots(path: str) -> list[dict]:
    data = json.loads(pathlib.Path(path).read_text())
    shots = data["shots"] if isinstance(data, dict) else data
    if not isinstance(shots, list) or not shots:
        raise ConfigError(f"{path}: expected a non-empty 'shots' list")
    ids = [s.get("id") for s in shots]
    if len(set(ids)) != len(ids) or not all(ids):
        raise ConfigError(f"{path}: every shot needs a unique id")
    return shots


def require_key() -> str:
    key = os.environ.get("MINIMAX_API_KEY", "").strip()
    if not key:
        raise ConfigError("MINIMAX_API_KEY is not set")
    return key


# --------------------------------------------------------------------------- cli
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="MiniMax-H3 shot runner (WF-06)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_est = sub.add_parser("estimate", help="price a shot list, spend nothing")
    p_est.add_argument("shotlist")

    p_run = sub.add_parser("run", help="submit + poll + download")
    p_run.add_argument("shotlist")
    p_run.add_argument("--out", default="h3_runs", help="output directory")
    p_run.add_argument("--yes", action="store_true", help="confirm real spend")
    p_run.add_argument("--timeout", type=int, default=1800)
    p_run.add_argument("--only", nargs="*", help="subset of shot ids")

    p_q = sub.add_parser("query", help="status of an existing task (free)")
    p_q.add_argument("task_id")

    args = ap.parse_args(argv)

    try:
        if args.cmd == "estimate":
            estimate(load_shots(args.shotlist))
            return 0

        if args.cmd == "query":
            print(json.dumps(query_task(args.task_id, require_key()), indent=2))
            return 0

        shots = load_shots(args.shotlist)
        if args.only:
            shots = [s for s in shots if s["id"] in set(args.only)]
            if not shots:
                raise ConfigError("--only matched no shot ids")
        for spec in shots:                     # structure only: priceable without the media present
            build_payload(spec, resolve_files=False)
        estimate(shots)
        if not args.yes:
            print("\nDry run only. Add --yes to actually submit (this spends money).")
            return 0

        key = require_key()
        for spec in shots:                     # preflight: every local reference must exist
            build_payload(spec, resolve_files=True)

        out_dir = pathlib.Path(args.out) / time.strftime("h3-%Y%m%d-%H%M%S")
        out_dir.mkdir(parents=True, exist_ok=True)
        receipts = []
        for spec in shots:
            try:
                receipts.append(run_shot(spec, key, out_dir, timeout=args.timeout))
            except TaskError as exc:
                print(f"  FAILED {spec['id']}: {exc}")
                receipts.append({"id": spec["id"], "error": str(exc)})
            (out_dir / "receipts.json").write_text(json.dumps(receipts, indent=2))
        print(f"\nreceipts: {out_dir / 'receipts.json'}")
        return 0 if all("error" not in r for r in receipts) else 3

    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    except TaskError as exc:
        print(f"api error: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
