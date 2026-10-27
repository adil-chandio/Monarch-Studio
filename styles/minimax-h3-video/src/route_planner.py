#!/usr/bin/env python3
"""WF-06 · route planner — "kaun sa tool, kis paise me, kaise chalega".

Reads data/tool_registry.json and turns a production need into a concrete route:
which model, on which hardware, what it costs, what the steps are, and what will bite.

Usage
-----
    python3 styles/minimax-h3-video/src/route_planner.py list
    python3 styles/minimax-h3-video/src/route_planner.py plan --need talking_hero
    python3 styles/minimax-h3-video/src/route_planner.py plan --need broll_plate --free
    python3 styles/minimax-h3-video/src/route_planner.py plan --need reel_loop --duration 60 --budget 10
    python3 styles/minimax-h3-video/src/route_planner.py plan --need talking_hero --json

Exit codes: 0 ok · 2 bad input.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "tool_registry.json"

NEEDS = {
    "talking_hero": "Monarch face delivering dialogue on camera",
    "broll_plate": "cinematic B-roll / atmosphere / location plate",
    "reel_loop": "short vertical reel, product or hook shot",
    "film_scene": "multi-shot narrative scene for a film",
    "lipsync_only": "I already have a silent clip and my own voice track",
    "animate_still": "I have one photo/sheet frame and want believable motion",
}

SHOT_SECONDS = 5  # one H3 / Wan shot is 4-15 s; 5 s is the working unit


def load_registry(path: pathlib.Path = REGISTRY) -> dict:
    return json.loads(path.read_text())


def models_by_id(reg: dict) -> dict[str, dict]:
    return {m["id"]: m for m in reg["models"]}


def shots_needed(duration: float, per_shot: int = SHOT_SECONDS) -> int:
    return max(1, math.ceil(duration / per_shot))


def paid_cost(model: dict, resolution: str, seconds: float) -> float | None:
    rates = model.get("cost_usd_per_second") or {}
    if not isinstance(rates, dict):
        return None
    rate = rates.get(resolution)
    if rate is None:
        return None
    return round(rate * seconds, 2)


# --------------------------------------------------------------------------- plans
def plan_talking_hero(models: dict, *, free: bool, duration: float, quality: str) -> dict:
    shots = shots_needed(duration)
    if free:
        return {
            "route": "free talking chain (silent clip + own voice + lipsync)",
            "hardware": "free Colab T4 16 GB (or better)",
            "models": ["wan21-t2v-1.3b", "latentsync-15"],
            "cost_usd": 0.0,
            "time_estimate": f"{shots} clips x 8-25 min render + {shots} lipsync passes",
            "steps": [
                "1. Reference: Monarch face stills (front / 3-4 / profile) from characters/monarch",
                "2. Silent motion clip: Wan 1.3B (colab/MONARCH_T4_FREE_BRIDGE.ipynb) or LTX distilled i2v",
                "3. Voice: your own VO / TTS (Urdu OK — lipsync model imitates whatever audio you give it)",
                "4. Lipsync: LatentSync 1.5 (8 GB; T4 needs the sm_75 capability patch) on the clip + voice",
                "5. Finish: WF-05 edit, typography, music, 24->30 fps conform",
            ],
            "warnings": [
                "LatentSync 1.5 is 256px face region — good for close-ups, weak for wide shots",
                "A silent base clip must keep the head fairly still, otherwise lipsync smears",
                "Colab free TOS forbids server-style use; render per session, save to Drive",
                "Urdu lipsync quality depends on the audio you supply; test 5 s before a batch",
            ],
        }
    return {
        "route": "H3 Ref2VA hero shot (paid, native audio + 2K)",
        "hardware": "none (hosted API)",
        "models": ["minimax-h3-api"],
        "cost_usd": {
            "768P": paid_cost(models["minimax-h3-api"], "768P", duration),
            "2K": paid_cost(models["minimax-h3-api"], "2K", duration),
        },
        "time_estimate": f"{shots} shot(s), 30 s - 4 min each on the server",
        "steps": [
            "1. Reference pack: 4-5 Monarch stills + 1 voice reference (<=9 images, first 5 free)",
            "2. Prompt: Ref2VA six-section skeleton (knowledge/02_PROMPTING.md)",
            "3. estimate -> dry run -> run --yes (src/h3_client.py or the Colab notebook)",
            "4. QA gates: identity / audio / format / cost",
            "5. Hand visual + separated audio to WF-05",
        ],
        "warnings": [
            "Urdu/Hindi are not in H3's stable 11 languages — test one line first",
            f"Budget 1.5x for retries: ~${round((paid_cost(models['minimax-h3-api'], '2K', duration) or 0) * 1.5, 2)} at 2K",
            "Reference-image content and prompts are moderated",
        ],
    }


def plan_broll(models: dict, *, free: bool, duration: float) -> dict:
    shots = shots_needed(duration)
    if free:
        return {
            "route": "free plate (Wan 1.3B on T4)",
            "hardware": "free Colab T4 16 GB",
            "models": ["wan21-t2v-1.3b"],
            "cost_usd": 0.0,
            "time_estimate": f"{shots} clip(s) x 8-25 min",
            "steps": [
                "1. Write the H3-style prompt (style, subject, action, camera type+amplitude+speed)",
                "2. Render in colab/MONARCH_T4_FREE_BRIDGE.ipynb (480p, silent)",
                "3. Use as plate/draft; upscale or re-generate the hero angle on H3 if it ships",
            ],
            "warnings": ["480p only, 16 fps, no audio — fine as a draft, weak as a final 1080p master"],
        }
    return {
        "route": "720p free plate on a 24 GB card (Wan 2.2 TI2V-5B)",
        "hardware": "Colab Pro L4 / A100, or rented RTX 4090",
        "models": ["wan22-ti2v-5b"],
        "cost_usd": 0.0,
        "time_estimate": f"{shots} clip(s) x 2-9 min",
        "steps": [
            "1. Load Wan 2.2 TI2V-5B (fp8/offload) in ComfyUI or diffusers",
            "2. 720p, 24 fps, 5 s per shot; image-to-video when you have a plate still",
            "3. Silent output -> WF-05 music/SFX",
        ],
        "warnings": ["Apache-2.0 so commercial use is safe", "No native audio"],
    }


def plan_reel(models: dict, *, free: bool, duration: float) -> dict:
    if free:
        return plan_broll(models, free=True, duration=duration) | {
            "route": "free vertical reel (Wan 1.3B, 480x832)",
            "warnings": ["480x832 vertical is below Instagram's 720p floor — use as animatic, not final"],
        }
    h3 = models["minimax-h3-api"]
    shots = shots_needed(duration)
    return {
        "route": "H3 2K vertical reel (paid)",
        "hardware": "none (hosted API)",
        "models": ["minimax-h3-api"],
        "cost_usd": {"768P": paid_cost(h3, "768P", duration), "2K": paid_cost(h3, "2K", duration)},
        "time_estimate": f"{shots} shot(s); 9:16 ratio, native stereo audio",
        "steps": [
            "1. Shot list with ratio 9:16 and reserved empty space for typography",
            "2. estimate -> run --yes; keep receipts",
            "3. WF-05: captions (V5 clean policy), transitions, music bed",
        ],
        "warnings": ["2K is API-only", "Keep the lower third empty in the prompt so captions do not cover the face"],
    }


def plan_film(models: dict, *, free: bool, duration: float) -> dict:
    shots = shots_needed(duration)
    if free:
        return {
            "route": "free film draft (mixed free models)",
            "hardware": "free Colab T4 / Colab Pro",
            "models": ["wan21-t2v-1.3b", "ltx-video-distilled", "latentsync-15"],
            "cost_usd": 0.0,
            "time_estimate": f"{shots} clips — plan 2-4 sessions on free T4",
            "steps": [
                "1. Plates on Wan 1.3B / LTX; hero close-ups on HunyuanVideo 1.5 if a 24 GB card is available",
                "2. Silent by design; dialogue via own VO + LatentSync",
                "3. Assemble and finish in WF-05",
            ],
            "warnings": ["Free film = multi-session work; budget a day, not an hour"],
        }
    h3 = models["minimax-h3-api"]
    return {
        "route": "H3 768P draft -> 2K final (paid)",
        "hardware": "none (hosted API)",
        "models": ["minimax-h3-api"],
        "cost_usd": {
            "draft_768P": paid_cost(h3, "768P", duration),
            "final_2K": paid_cost(h3, "2K", duration),
        },
        "time_estimate": f"{shots} shots; 30 s - 4 min each",
        "steps": [
            "1. Draft every shot at 768P, lock edit in WF-05",
            "2. Re-run only the shots that survive the edit at 2K",
            "3. Receipts + gates + Drive delivery",
        ],
        "warnings": ["Do not render all 2K up front — the edit always drops shots"],
    }


def plan_lipsync(models: dict, *, free: bool) -> dict:
    model_id = "latentsync-15" if free else "latentsync-16"
    m = models[model_id]
    return {
        "route": f"lipsync with {m['name']} ({'free' if free else '24 GB card'})",
        "hardware": f"{m['vram_gb']} GB VRAM" + (" — free Colab T4 with the sm_75 patch" if free else ""),
        "models": [model_id],
        "cost_usd": 0.0,
        "time_estimate": m["speed_5s"],
        "steps": [
            "1. Silent clip (Wan/LTX/H3) + your voice track (WAV/MP3)",
            "2. Face must be visible and reasonably still; keep the head in frame",
            "3. Run LatentSync; review mouth sync at 100% zoom",
            "4. Finish in WF-05 with music so tiny artefacts are masked",
        ],
        "warnings": [
            "256px face region on 1.5 — close-ups only",
            "T4 runs fp32 by default (OOM); patch the compute-capability check to >= 7 for fp16",
        ] + ([] if free else ["1.6 needs 18 GB officially; 16 GB works with UNet CPU offload"]),
    }


def plan_animate_still(models: dict, *, free: bool) -> dict:
    if free:
        return {
            "route": "animate a Monarch still (LivePortrait)",
            "hardware": "free Colab T4 16 GB",
            "models": ["liveportrait"],
            "cost_usd": 0.0,
            "time_estimate": "seconds to minutes per clip",
            "steps": [
                "1. Use the locked hero still (front or 3/4) from characters/monarch",
                "2. Drive it with a performance video or a generated motion clip",
                "3. Optional: LatentSync on top for dialogue",
            ],
            "warnings": ["Motion range is limited; big head turns break the illusion"],
        }
    return {
        "route": "image-to-video with the locked still (H3 Ref2VA / Wan 2.2 I2V)",
        "hardware": "API, or a 24 GB card for Wan",
        "models": ["minimax-h3-api", "wan22-a14b"],
        "cost_usd": {"h3_768P_5s": paid_cost(models["minimax-h3-api"], "768P", 5),
                     "h3_2K_5s": paid_cost(models["minimax-h3-api"], "2K", 5)},
        "time_estimate": "30 s (API) / 4-8 min (local 24 GB)",
        "steps": [
            "1. Pick the still that matches the final framing",
            "2. H3 Ref2VA with that still + prompt skeleton, or Wan 2.2 I2V locally",
            "3. Gate identity against the master board",
        ],
        "warnings": ["More motion = more identity drift; keep camera moves small"],
    }


PLANNERS = {
    "talking_hero": plan_talking_hero,
    "broll_plate": plan_broll,
    "reel_loop": plan_reel,
    "film_scene": plan_film,
    "lipsync_only": plan_lipsync,
    "animate_still": plan_animate_still,
}


def build_plan(need: str, *, free: bool, duration: float, quality: str = "final",
               registry: dict | None = None) -> dict:
    reg = registry or load_registry()
    models = models_by_id(reg)
    if need not in PLANNERS:
        raise ValueError(f"unknown need '{need}' (choose from: {', '.join(PLANNERS)})")
    kwargs: dict[str, object] = {"free": free}
    if need in ("talking_hero", "broll_plate", "reel_loop", "film_scene"):
        kwargs["duration"] = duration
    if need == "talking_hero":
        kwargs["quality"] = quality
    plan = PLANNERS[need](models, **kwargs)
    plan.update({"need": need, "need_description": NEEDS[need], "free": free,
                 "duration_seconds": duration, "quality": quality})
    plan["licence_notes"] = {mid: models[mid]["licence"] for mid in plan["models"]}
    return plan


# --------------------------------------------------------------------------- cli
def render(plan: dict) -> str:
    out = [
        f"NEED      : {plan['need']} — {plan['need_description']}",
        f"ROUTE     : {plan['route']}",
        f"HARDWARE  : {plan['hardware']}",
        f"MODELS    : {', '.join(plan['models'])}",
        f"COST      : {'free' if plan['cost_usd'] == 0.0 else plan['cost_usd']}",
        f"TIME      : {plan['time_estimate']}",
        "",
        "STEPS",
    ]
    out += [f"  {s}" for s in plan["steps"]]
    if plan.get("warnings"):
        out += ["", "WATCH OUT"]
        out += [f"  ! {w}" for w in plan["warnings"]]
    if plan.get("licence_notes"):
        out += ["", "LICENCES"]
        out += [f"  {k}: {v}" for k, v in plan["licence_notes"].items()]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="WF-06 model/route planner")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="show needs and models")

    p = sub.add_parser("plan", help="build a route")
    p.add_argument("--need", required=True, choices=sorted(PLANNERS))
    p.add_argument("--free", action="store_true", help="zero-budget route")
    p.add_argument("--duration", type=float, default=5.0, help="total seconds (default 5)")
    p.add_argument("--quality", default="final", choices=["draft", "final"])
    p.add_argument("--json", action="store_true")

    args = ap.parse_args(argv)

    try:
        if args.cmd == "list":
            reg = load_registry()
            print(f"TIERS  ({reg['captured_at']})")
            for key, tier in reg["tiers"].items():
                print(f"  {key:<10} {tier['gpu']:<18} {str(tier['vram_gb']) + ' GB':<8} {tier['compute']}")
            print("\nNEEDS")
            for key, desc in NEEDS.items():
                print(f"  {key:<14} {desc}")
            print("\nMODELS")
            models = models_by_id(reg)
            for m in reg["models"]:
                audio = "audio" if m["native_audio"] else "silent"
                print(f"  {m['id']:<22} {m['tier']:<10} {str(m['vram_gb']) + ' GB':<8} {audio:<6} {m['licence'][:46]}")
            print(f"\n{len(models)} models · re-verify before quoting")
            return 0

        plan = build_plan(args.need, free=args.free, duration=args.duration, quality=args.quality)
        print(json.dumps(plan, indent=2) if args.json else render(plan))
        return 0
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
