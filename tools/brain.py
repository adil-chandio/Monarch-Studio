#!/usr/bin/env python3
"""Video brain: durable, append-only memory for every Monarch editing/animation style.

Every style keeps its brain in  styles/<style-id>/brain/video-brain/:
  MINDSET.md       identity, quality bar, rules, what premium means for this style (edited by hand, versioned in git)
  TOOLCHAIN.md     tools, versions, exact commands, access and blockers (edited by hand)
  PIPELINE.md      the production recipe for this style, current version (edited by hand)
  NEXT_LEVEL.md    prioritised upgrade backlog (edited by hand)
  SESSION_LOG.md   append-only: every working turn (request, action, result)
  PROBLEMS.md      append-only: symptom, cause, fix, verified-by, status (P-###)
  SKILLS.md        append-only: reusable skills with evidence (K-###)
  STRATEGIES.md    append-only: approach decisions, alternatives rejected, measured outcome (ST-###)
  VIDEO_LOG.md     append-only: every video or lookdev version, settings, timing, review, Drive ID (V-###)

Rules: the CLI only appends. Changing an old entry means a new reconciliation entry, never an edit.

Usage:
  python3 tools/brain.py list
  python3 tools/brain.py init <style-id> --code WF-02 --name "..."
  python3 tools/brain.py resume <style-id>
  python3 tools/brain.py session <style-id> --request "..." --action "..." --result "..." [--files a,b]
  python3 tools/brain.py problem <style-id> --symptom "..." --cause "..." --fix "..." --verified-by "..." --status open|fixed
  python3 tools/brain.py resolve <style-id> P-001 --fix "..." --verified-by "..."
  python3 tools/brain.py skill <style-id> --name "..." --when "..." --how "..." --evidence "..."
  python3 tools/brain.py strategy <style-id> --decision "..." --alternatives "..." --outcome "..."
  python3 tools/brain.py video <style-id> --version "..." --file "..." --drive-id "..." --settings "..." --timing "..." --review "..." --status draft|reviewed|accepted|rejected
  python3 tools/brain.py check
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
STYLES = ROOT / "styles"
TZ = ZoneInfo("Asia/Karachi")

LEDGERS = {
    "SESSION_LOG.md": ("Session log", "S"),
    "PROBLEMS.md": ("Problems and fixes", "P"),
    "SKILLS.md": ("Skills", "K"),
    "STRATEGIES.md": ("Strategies and decisions", "ST"),
    "VIDEO_LOG.md": ("Video and lookdev log", "V"),
}
HAND_FILES = ["MINDSET.md", "TOOLCHAIN.md", "PIPELINE.md", "NEXT_LEVEL.md"]
BRAIN_REL = Path("brain") / "video-brain"


def now() -> str:
    return dt.datetime.now(TZ).strftime("%Y-%m-%d %H:%M %Z")


def today() -> str:
    return dt.datetime.now(TZ).strftime("%Y-%m-%d")


def brain_dir(style_id: str) -> Path:
    return STYLES / style_id / BRAIN_REL


def registry_styles() -> list[dict]:
    data = json.loads((STYLES / "registry.json").read_text(encoding="utf-8"))
    return data.get("styles", [])


def next_id(path: Path, prefix: str) -> str:
    if not path.exists():
        return f"{prefix}-001"
    nums = [int(m) for m in re.findall(rf"^## {re.escape(prefix)}-(\d+)\b", path.read_text(encoding="utf-8"), re.M)]
    return f"{prefix}-{(max(nums) + 1 if nums else 1):03d}"


def append(path: Path, text: str) -> None:
    if not path.exists():
        raise SystemExit(f"missing ledger {path}. Run: tools/brain.py init <style-id>")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(text.rstrip() + "\n\n")


def require_style(style_id: str) -> Path:
    d = brain_dir(style_id)
    if not d.exists():
        raise SystemExit(f"no brain for style '{style_id}'. Run: tools/brain.py init {style_id} --code WF-0X --name '...'")
    return d


# ----------------------------------------------------------------- init
def cmd_init(a: argparse.Namespace) -> int:
    style_dir = STYLES / a.style_id
    d = style_dir / BRAIN_REL
    if d.exists() and any(d.iterdir()):
        raise SystemExit(f"brain already exists for {a.style_id}; add entries with the other subcommands")
    d.mkdir(parents=True, exist_ok=True)
    (style_dir / "knowledge").mkdir(parents=True, exist_ok=True)
    head = f"# {a.name or a.style_id} · video brain\n\nStyle `{a.style_id}`{' · workflow ' + a.code if a.code else ''}. Created {now()}.\n\n"
    for fname in HAND_FILES:
        p = d / fname
        if not p.exists():
            title = fname.replace(".md", "").replace("_", " ").title()
            p.write_text(head + f"## {title}\n\n_To be filled by hand. Versioned in git._\n", encoding="utf-8")
    for fname, (title, _) in LEDGERS.items():
        p = d / fname
        if not p.exists():
            p.write_text(head + f"## {title} (append-only)\n\nUse `tools/brain.py` to add entries. Do not edit old entries.\n", encoding="utf-8")
    index = style_dir / "knowledge" / "INDEX.md"
    if not index.exists():
        index.write_text(
            f"# {a.name or a.style_id} · knowledge index\n\n"
            "Start here before any work on this style:\n\n"
            "1. `brain/video-brain/MINDSET.md`\n2. `brain/video-brain/NEXT_LEVEL.md`\n"
            "3. `brain/video-brain/TOOLCHAIN.md`\n4. `brain/video-brain/PIPELINE.md`\n"
            "5. `python3 tools/brain.py resume " + a.style_id + "`\n\n"
            "Append-only ledgers: `SESSION_LOG.md`, `PROBLEMS.md`, `SKILLS.md`, `STRATEGIES.md`, `VIDEO_LOG.md`.\n",
            encoding="utf-8",
        )
    print(f"initialised brain: {d.relative_to(ROOT)}")
    return 0


# ----------------------------------------------------------------- appenders
def cmd_session(a: argparse.Namespace) -> int:
    d = require_style(a.style_id)
    p = d / "SESSION_LOG.md"
    sid = next_id(p, "S")
    files = ", ".join(f"`{f.strip()}`" for f in a.files.split(",")) if a.files else "none"
    append(p, f"## {sid} · {now()}\n\n- **Request:** {a.request}\n- **Action:** {a.action}\n- **Result:** {a.result}\n- **Files:** {files}\n")
    print(sid)
    return 0


def cmd_problem(a: argparse.Namespace) -> int:
    d = require_style(a.style_id)
    p = d / "PROBLEMS.md"
    pid = next_id(p, "P")
    append(p, f"## {pid} · {today()} · status: {a.status}\n\n- **Symptom:** {a.symptom}\n- **Cause:** {a.cause}\n- **Fix:** {a.fix or 'open'}\n- **Verified by:** {a.verified_by or 'not yet'}\n")
    print(pid)
    return 0


def cmd_resolve(a: argparse.Namespace) -> int:
    d = require_style(a.style_id)
    p = d / "PROBLEMS.md"
    if not re.search(rf"^## {re.escape(a.problem_id)} ·", p.read_text(encoding="utf-8"), re.M):
        raise SystemExit(f"{a.problem_id} not found in {p}")
    append(p, f"## {a.problem_id} update · {today()} · status: fixed\n\n- **Fix:** {a.fix}\n- **Verified by:** {a.verified_by}\n")
    print(f"{a.problem_id} resolved (reconciliation entry added)")
    return 0


def cmd_skill(a: argparse.Namespace) -> int:
    d = require_style(a.style_id)
    p = d / "SKILLS.md"
    kid = next_id(p, "K")
    append(p, f"## {kid} · {today()} · {a.name}\n\n- **When to use:** {a.when}\n- **How:** {a.how}\n- **Evidence:** {a.evidence}\n")
    print(kid)
    return 0


def cmd_strategy(a: argparse.Namespace) -> int:
    d = require_style(a.style_id)
    p = d / "STRATEGIES.md"
    stid = next_id(p, "ST")
    append(p, f"## {stid} · {today()}\n\n- **Decision:** {a.decision}\n- **Alternatives rejected:** {a.alternatives or 'none recorded'}\n- **Outcome:** {a.outcome or 'pending'}\n")
    print(stid)
    return 0


def cmd_video(a: argparse.Namespace) -> int:
    d = require_style(a.style_id)
    p = d / "VIDEO_LOG.md"
    vid = next_id(p, "V")
    append(p, (f"## {vid} · {today()} · {a.version} · status: {a.status}\n\n"
               f"- **File:** {a.file or 'none (still only)'}\n- **Drive ID:** {a.drive_id or 'not uploaded'}\n"
               f"- **Settings:** {a.settings or 'n/a'}\n- **Timing:** {a.timing or 'n/a'}\n- **Review:** {a.review or 'not reviewed'}\n"))
    print(vid)
    return 0


# ----------------------------------------------------------------- resume / list / check
def _tail_entries(path: Path, n: int) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"(?m)^(?=## )", text)
    entries = [p.strip() for p in parts if p.startswith("## ")]
    return entries[-n:]


def _open_problems(path: Path) -> list[str]:
    """Problems whose latest status is open. A later 'update' entry (resolve) marks it fixed."""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    entries = [p.strip() for p in re.split(r"(?m)^(?=## )", text) if p.startswith("## ")]
    latest: dict[str, tuple[str, str]] = {}  # id -> (status, entry)
    for e in entries:
        m = re.match(r"## (P-\d+)( update)? ", e)
        if not m:
            continue
        pid = m.group(1)
        if m.group(2):
            latest[pid] = ("fixed", e)
        else:
            status = "open" if "status: open" in e.splitlines()[0] else "fixed"
            latest[pid] = (status, e)
    return [entry for status, entry in latest.values() if status == "open"]


def cmd_resume(a: argparse.Namespace) -> int:
    d = require_style(a.style_id)
    print(f"# RESUME · {a.style_id} · {now()}\n")
    for fname in ["MINDSET.md", "NEXT_LEVEL.md", "TOOLCHAIN.md", "PIPELINE.md"]:
        p = d / fname
        if p.exists():
            print(p.read_text(encoding="utf-8").strip() + "\n")
    open_p = _open_problems(d / "PROBLEMS.md")
    print("## Open problems\n" + ("\n\n".join(open_p) if open_p else "none") + "\n")
    print("## Last 5 skills\n" + ("\n\n".join(_tail_entries(d / "SKILLS.md", 5)) or "none") + "\n")
    print("## Last 3 strategies\n" + ("\n\n".join(_tail_entries(d / "STRATEGIES.md", 3)) or "none") + "\n")
    print("## Last video\n" + ("\n\n".join(_tail_entries(d / "VIDEO_LOG.md", 1)) or "none") + "\n")
    print("## Last 3 sessions\n" + ("\n\n".join(_tail_entries(d / "SESSION_LOG.md", 3)) or "none") + "\n")
    return 0


def cmd_list(_: argparse.Namespace) -> int:
    for s in registry_styles():
        d = brain_dir(s["style_id"])
        status = "brain" if d.exists() else "NO BRAIN"
        print(f"{s.get('workflow_code', '?'):7} {s['style_id']:34} {status}")
    return 0


def cmd_check(_: argparse.Namespace) -> int:
    problems = []
    for s in registry_styles():
        sid = s["style_id"]
        d = brain_dir(sid)
        if not d.exists():
            problems.append(f"{sid}: no brain directory")
            continue
        for fname in HAND_FILES + list(LEDGERS):
            if not (d / fname).exists():
                problems.append(f"{sid}: missing {fname}")
        for fname, (_, prefix) in LEDGERS.items():
            p = d / fname
            if not p.exists() or fname == "SESSION_LOG.md":
                continue
            ids = re.findall(rf"^## ({re.escape(prefix)}-\d+)\b", p.read_text(encoding="utf-8"), re.M)
            if len(ids) != len(set(ids)):
                problems.append(f"{sid}: duplicate ids in {fname}")
        if not (STYLES / sid / "knowledge" / "INDEX.md").exists():
            problems.append(f"{sid}: missing knowledge/INDEX.md")
    if problems:
        print("\n".join("FAIL  " + p for p in problems))
        return 1
    print("PASS  every registered style has a complete video brain")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Monarch video brain (append-only style memory)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init"); p.add_argument("style_id"); p.add_argument("--code", default=""); p.add_argument("--name", default="")
    p.set_defaults(fn=cmd_init)
    p = sub.add_parser("resume"); p.add_argument("style_id"); p.set_defaults(fn=cmd_resume)
    p = sub.add_parser("list"); p.set_defaults(fn=cmd_list)
    p = sub.add_parser("check"); p.set_defaults(fn=cmd_check)

    p = sub.add_parser("session"); p.add_argument("style_id"); p.add_argument("--request", required=True)
    p.add_argument("--action", required=True); p.add_argument("--result", required=True); p.add_argument("--files", default="")
    p.set_defaults(fn=cmd_session)

    p = sub.add_parser("problem"); p.add_argument("style_id"); p.add_argument("--symptom", required=True)
    p.add_argument("--cause", required=True); p.add_argument("--fix", default=""); p.add_argument("--verified-by", default="")
    p.add_argument("--status", choices=["open", "fixed"], default="open"); p.set_defaults(fn=cmd_problem)

    p = sub.add_parser("resolve"); p.add_argument("style_id"); p.add_argument("problem_id")
    p.add_argument("--fix", required=True); p.add_argument("--verified-by", required=True); p.set_defaults(fn=cmd_resolve)

    p = sub.add_parser("skill"); p.add_argument("style_id"); p.add_argument("--name", required=True)
    p.add_argument("--when", required=True); p.add_argument("--how", required=True); p.add_argument("--evidence", required=True)
    p.set_defaults(fn=cmd_skill)

    p = sub.add_parser("strategy"); p.add_argument("style_id"); p.add_argument("--decision", required=True)
    p.add_argument("--alternatives", default=""); p.add_argument("--outcome", default=""); p.set_defaults(fn=cmd_strategy)

    p = sub.add_parser("video"); p.add_argument("style_id"); p.add_argument("--version", required=True)
    p.add_argument("--file", default=""); p.add_argument("--drive-id", default=""); p.add_argument("--settings", default="")
    p.add_argument("--timing", default=""); p.add_argument("--review", default="")
    p.add_argument("--status", choices=["draft", "reviewed", "accepted", "rejected"], default="draft")
    p.set_defaults(fn=cmd_video)

    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
