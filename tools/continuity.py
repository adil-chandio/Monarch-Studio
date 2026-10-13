#!/usr/bin/env python3
"""Crash-safe active-work, checkpoint, transcript and sync-outbox controller."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "workflows" / "current"
STATE_PATH = CURRENT / "ACTIVE_TASK.json"
RESUME_PATH = CURRENT / "RESUME.md"
JOURNAL_PATH = CURRENT / "JOURNAL.jsonl"
CHAT_PATH = CURRENT / "CHAT_TRANSCRIPT.jsonl"
PAYLOAD = CURRENT / "payload"
START_HERE = ROOT / "START_HERE.md"
CONTINUITY = ROOT / "operations" / "continuity"
CHECKPOINTS = CONTINUITY / "checkpoints"
OUTBOX = CONTINUITY / "outbox"
HISTORY = ROOT / "operations" / "history"
TARGETS = CONTINUITY / "remote-targets.json"
LOCK_PATH = ROOT / ".continuity.lock"
RUNTIME = ROOT / ".continuity-runtime"

ACTIVE_STATUSES = {"active", "rendering", "syncing"}
VALID_STATUSES = ACTIVE_STATUSES | {"paused", "waiting_external", "blocked", "completed", "idle"}
EVENT_KINDS = {"user", "assistant", "decision", "action", "tool", "result", "error", "checkpoint", "sync", "process"}
PLATFORMS = {"github", "google_drive", "notion", "linear", "google_docs"}


class ContinuityError(RuntimeError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temp.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def atomic_json(path: Path, data: Any) -> None:
    atomic_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        if default is not None:
            return default
        raise ContinuityError(f"missing {path.relative_to(ROOT)}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContinuityError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc


@contextmanager
def locked() -> Iterator[None]:
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def state() -> dict[str, Any]:
    return load_json(STATE_PATH, {
        "schema_version": 1,
        "task_id": null_task_id(),
        "status": "idle",
        "title": "No active task",
        "style_id": None,
        "goal": "",
        "acceptance_criteria": [],
        "started_at": None,
        "updated_at": now(),
        "checkpoint_sequence": 0,
        "event_sequence": 0,
        "journal_head": None,
        "last_checkpoint": None,
        "next_action": "Start a task with continuity.py init.",
        "running_processes": [],
        "remote_sync": {platform: "not_configured" for platform in sorted(PLATFORMS)},
    })


def null_task_id() -> str:
    return "NONE"


def write_state(data: dict[str, Any]) -> None:
    data["updated_at"] = now()
    atomic_json(STATE_PATH, data)


def read_events() -> list[dict[str, Any]]:
    if not JOURNAL_PATH.exists():
        return []
    events = []
    for number, line in enumerate(JOURNAL_PATH.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ContinuityError(f"journal line {number} is invalid JSON: {exc}") from exc
    return events


def verify_journal() -> tuple[bool, str | None, int]:
    previous = None
    events = read_events()
    for expected_seq, event in enumerate(events, 1):
        if event.get("seq") != expected_seq:
            return False, f"sequence mismatch at event {expected_seq}", len(events)
        if event.get("prev_event_sha256") != previous:
            return False, f"chain mismatch at event {expected_seq}", len(events)
        claimed = event.get("event_sha256")
        body = dict(event)
        body.pop("event_sha256", None)
        actual = hashlib.sha256(canonical(body)).hexdigest()
        if claimed != actual:
            return False, f"hash mismatch at event {expected_seq}", len(events)
        previous = actual
    return True, previous, len(events)


def append_event(kind: str, actor: str, content: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    if kind not in EVENT_KINDS:
        raise ContinuityError(f"invalid event kind {kind}")
    data = state()
    ok, previous, count = verify_journal()
    if not ok:
        raise ContinuityError(f"refusing to append to damaged journal: {previous}")
    event = {
        "schema_version": 1,
        "task_id": data["task_id"],
        "seq": count + 1,
        "timestamp": now(),
        "kind": kind,
        "actor": actor,
        "content": content,
        "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "metadata": metadata or {},
        "prev_event_sha256": previous,
    }
    event["event_sha256"] = hashlib.sha256(canonical(event)).hexdigest()
    JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with JOURNAL_PATH.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    if kind in {"user", "assistant"}:
        transcript = {
            "schema_version": 1,
            "task_id": data["task_id"],
            "seq": event["seq"],
            "timestamp": event["timestamp"],
            "role": kind,
            "content": content,
            "content_sha256": event["content_sha256"],
            "journal_event_sha256": event["event_sha256"],
        }
        with CHAT_PATH.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(transcript, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
    data["event_sequence"] = event["seq"]
    data["journal_head"] = event["event_sha256"]
    write_state(data)
    return event


def run(command: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if check and proc.returncode:
        raise ContinuityError(f"command failed: {' '.join(command)}\n{proc.stderr or proc.stdout}")
    return proc


def git_snapshot() -> dict[str, Any]:
    if not (ROOT / ".git").exists():
        return {"initialized": False, "head": None, "branch": None, "status": ["Git is not initialized"]}
    head = run(["git", "rev-parse", "HEAD"]).stdout.strip()
    branch = run(["git", "branch", "--show-current"]).stdout.strip() or "DETACHED"
    status_lines = run(["git", "status", "--porcelain=v1", "--untracked-files=all"]).stdout.splitlines()
    remotes = run(["git", "remote", "-v"]).stdout.splitlines()
    submodules = run(["git", "submodule", "status"]).stdout.splitlines()
    return {
        "initialized": True,
        "head": head or None,
        "branch": branch,
        "status": status_lines,
        "remotes": remotes,
        "submodules": submodules,
    }


def payload_inventory() -> list[dict[str, Any]]:
    rows = []
    if not PAYLOAD.exists():
        return rows
    for path in sorted(PAYLOAD.rglob("*")):
        if not path.is_file():
            continue
        h = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                h.update(chunk)
        rows.append({"path": path.relative_to(ROOT).as_posix(), "size": path.stat().st_size, "sha256": h.hexdigest()})
    return rows


def render_resume(data: dict[str, Any], checkpoint_path: str | None = None) -> str:
    processes = data.get("running_processes", [])
    process_lines = "\n".join(f"- `{p['id']}` — {p['name']} — {p['state']}" for p in processes) or "- None recorded."
    criteria = "\n".join(f"- [ ] {item}" for item in data.get("acceptance_criteria", [])) or "- None recorded."
    return f"""# Resume capsule — {data['task_id']}

- **Status:** `{data['status']}`
- **Title:** {data['title']}
- **Style:** `{data.get('style_id') or 'studio-operation'}`
- **Checkpoint sequence:** {data.get('checkpoint_sequence', 0)}
- **Last checkpoint:** {data.get('last_checkpoint') or 'none'}

## Goal

{data.get('goal') or 'No goal recorded.'}

## Acceptance criteria

{criteria}

## Exact next action

{data.get('next_action') or 'No next action recorded.'}

## Running processes

{process_lines}

## Recovery command

```bash
python3 tools/continuity.py resume
```

## Durable evidence

- Active state: `workflows/current/ACTIVE_TASK.json`
- Hash-chained action journal: `workflows/current/JOURNAL.jsonl`
- Visible user/assistant transcript: `workflows/current/CHAT_TRANSCRIPT.jsonl`
- Active payload only: `workflows/current/payload/`
- Latest checkpoint package: `{checkpoint_path or data.get('last_checkpoint_path') or 'none'}`

Never restart this task from the beginning when these records exist. Verify the journal, inspect the latest checkpoint, then execute **Exact next action**.
"""


def write_resume_files(data: dict[str, Any], checkpoint_path: str | None = None) -> None:
    text = render_resume(data, checkpoint_path)
    atomic_text(RESUME_PATH, text)
    start = f"""# START HERE

The repository uses one active workflow slot. Do not guess or restart an existing task.

- **Task:** `{data['task_id']}`
- **Status:** `{data['status']}`
- **Title:** {data['title']}
- **Next action:** {data.get('next_action') or 'none'}
- **Resume capsule:** [`workflows/current/RESUME.md`](workflows/current/RESUME.md)

Run:

```bash
python3 tools/continuity.py resume
python3 tools/studio.py validate
```

Permanent style knowledge is under [`styles/`](styles/). Only currently running work belongs under `workflows/current/`.
"""
    atomic_text(START_HERE, start)


def ensure_active(data: dict[str, Any]) -> None:
    if data.get("status") in {"idle", "completed"} or data.get("task_id") == null_task_id():
        raise ContinuityError("no active task")


def command_init(args: argparse.Namespace) -> int:
    with locked():
        old = state()
        if old.get("status") not in {"idle", "completed"} and not args.force:
            raise ContinuityError(f"task {old['task_id']} is still {old['status']}; complete/pause it or pass --force")
        if args.force and CURRENT.exists() and old.get("task_id") != null_task_id():
            emergency = HISTORY / f"{old['task_id']}-forced-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
            emergency.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(CURRENT, emergency, dirs_exist_ok=True)
        if CURRENT.exists():
            shutil.rmtree(CURRENT)
        PAYLOAD.mkdir(parents=True, exist_ok=True)
        data = {
            "schema_version": 1,
            "task_id": args.task_id,
            "status": "active",
            "title": args.title,
            "style_id": args.style,
            "goal": args.goal,
            "acceptance_criteria": args.acceptance or [],
            "started_at": now(),
            "updated_at": now(),
            "checkpoint_sequence": 0,
            "event_sequence": 0,
            "journal_head": None,
            "last_checkpoint": None,
            "last_checkpoint_path": None,
            "next_action": args.next_action or "Record the user request verbatim, then begin the first implementation step.",
            "running_processes": [],
            "remote_sync": {platform: "pending" for platform in sorted(PLATFORMS)},
        }
        write_state(data)
        JOURNAL_PATH.touch()
        CHAT_PATH.touch()
        append_event("action", "continuity", "Active task initialized.", {"title": args.title, "style_id": args.style})
        data = state()
        write_resume_files(data)
        print(f"initialized {args.task_id}: {args.title}")
    return 0


def get_content(args: argparse.Namespace) -> str:
    if getattr(args, "file", None):
        return Path(args.file).read_text(encoding="utf-8")
    if getattr(args, "message", None) is not None:
        return args.message
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise ContinuityError("provide --message, --file, or stdin")


def command_log(args: argparse.Namespace) -> int:
    with locked():
        data = state()
        ensure_active(data)
        content = get_content(args)
        event = append_event(args.kind, args.actor, content, {"source": args.source} if args.source else {})
        print(f"logged event {event['seq']} {event['event_sha256'][:12]} ({args.kind})")
    return 0


def command_process(args: argparse.Namespace) -> int:
    with locked():
        data = state()
        ensure_active(data)
        rows = data.setdefault("running_processes", [])
        if args.operation == "add":
            rows = [p for p in rows if p["id"] != args.id]
            rows.append({"id": args.id, "name": args.name, "state": args.state, "started_at": now(), "resume_instruction": args.resume_instruction})
            data["running_processes"] = rows
            write_state(data)
            append_event("process", "continuity", f"Process {args.id} recorded as {args.state}.", rows[-1])
        elif args.operation == "remove":
            found = next((p for p in rows if p["id"] == args.id), None)
            data["running_processes"] = [p for p in rows if p["id"] != args.id]
            write_state(data)
            append_event("process", "continuity", f"Process {args.id} removed from active ledger.", {"previous": found})
        else:
            print(json.dumps(rows, indent=2, ensure_ascii=False))
            return 0
        write_resume_files(state())
    return 0


def create_checkpoint(summary: str, next_action: str, status: str | None = None) -> tuple[dict[str, Any], Path]:
    data = state()
    ensure_active(data)
    if status:
        if status not in VALID_STATUSES:
            raise ContinuityError(f"invalid status {status}")
        data["status"] = status
    data["checkpoint_sequence"] = int(data.get("checkpoint_sequence", 0)) + 1
    data["last_checkpoint"] = now()
    data["next_action"] = next_action
    write_state(data)
    event = append_event("checkpoint", "continuity", summary, {"sequence": data["checkpoint_sequence"], "next_action": next_action, "status": data["status"]})
    data = state()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    checkpoint_id = f"{data['checkpoint_sequence']:04d}-{stamp}"
    cp_dir = CHECKPOINTS / data["task_id"] / checkpoint_id
    cp_dir.mkdir(parents=True, exist_ok=False)
    snapshot = {
        "schema_version": 1,
        "checkpoint_id": checkpoint_id,
        "created_at": data["last_checkpoint"],
        "summary": summary,
        "next_action": next_action,
        "active_state": data,
        "journal_event": event,
        "journal_head": data.get("journal_head"),
        "git": git_snapshot(),
        "payload_inventory": payload_inventory(),
    }
    atomic_json(cp_dir / "checkpoint.json", snapshot)
    handoff = render_resume(data, cp_dir.relative_to(ROOT).as_posix())
    atomic_text(cp_dir / "HANDOFF.md", handoff)
    data["last_checkpoint_path"] = cp_dir.relative_to(ROOT).as_posix()
    write_state(data)
    write_resume_files(data, data["last_checkpoint_path"])

    out_dir = OUTBOX / data["task_id"] / checkpoint_id
    out_dir.mkdir(parents=True, exist_ok=False)
    atomic_json(out_dir / "checkpoint.json", snapshot)
    targets = load_json(TARGETS, {"targets": {}})
    sync = {
        "schema_version": 1,
        "checkpoint_id": checkpoint_id,
        "task_id": data["task_id"],
        "created_at": data["last_checkpoint"],
        "targets": {
            platform: {
                "status": "pending",
                "target": targets.get("targets", {}).get(platform),
                "remote_id": None,
                "synced_at": None,
                "note": None,
            }
            for platform in sorted(PLATFORMS)
        },
    }
    atomic_json(out_dir / "SYNC.json", sync)
    status_text = f"""# Checkpoint {checkpoint_id}

- Task: `{data['task_id']}`
- Status: `{data['status']}`
- Title: {data['title']}
- Style: `{data.get('style_id') or 'studio-operation'}`
- Time: {data['last_checkpoint']}
- Journal head: `{data.get('journal_head')}`

## Completed since prior checkpoint

{summary}

## Exact next action

{next_action}

## Cross-platform rule

The same factual status must be applied to GitHub, Google Drive, Notion, Linear and Google Docs. Remote IDs/results are recorded in `SYNC.json`; no platform is silently skipped.
"""
    atomic_text(out_dir / "STATUS.md", status_text)
    return snapshot, cp_dir


def commit_checkpoint(task_id: str, sequence: int, push: bool) -> dict[str, Any]:
    if not (ROOT / ".git").exists():
        return {"committed": False, "pushed": False, "reason": "git_not_initialized"}
    studio = ROOT / "tools" / "studio.py"
    if studio.exists():
        proc = run([sys.executable, str(studio), "manifest", "--write"])
        if proc.returncode:
            raise ContinuityError(proc.stderr or proc.stdout)
    run(["git", "add", "-A"], check=True)
    diff = run(["git", "diff", "--cached", "--quiet"])
    committed = diff.returncode != 0
    commit = None
    if committed:
        run(["git", "commit", "-m", f"checkpoint({task_id}): {sequence:04d}"], check=True)
        commit = run(["git", "rev-parse", "HEAD"], check=True).stdout.strip()
    pushed = False
    reason = None
    if push:
        remotes = run(["git", "remote"]).stdout.split()
        if "origin" not in remotes:
            reason = "origin_remote_missing"
        else:
            branch = run(["git", "branch", "--show-current"]).stdout.strip() or "HEAD"
            proc = run(["git", "push", "-u", "origin", branch])
            pushed = proc.returncode == 0
            if not pushed:
                reason = (proc.stderr or proc.stdout).strip()
    return {"committed": committed, "commit": commit, "pushed": pushed, "reason": reason}


def command_checkpoint(args: argparse.Namespace) -> int:
    with locked():
        snapshot, cp_dir = create_checkpoint(args.summary, args.next_action, args.status)
        result = commit_checkpoint(snapshot["active_state"]["task_id"], snapshot["active_state"]["checkpoint_sequence"], args.push) if args.commit else {"committed": False, "pushed": False, "reason": "commit_not_requested"}
        RUNTIME.mkdir(parents=True, exist_ok=True)
        atomic_json(RUNTIME / "last-checkpoint-result.json", {"checkpoint": cp_dir.relative_to(ROOT).as_posix(), "git_result": result, "finished_at": now()})
        print(f"checkpoint {snapshot['checkpoint_id']} created")
        print(json.dumps(result, ensure_ascii=False))
    return 0


def command_status(args: argparse.Namespace) -> int:
    data = state()
    ok, head, count = verify_journal()
    report = {
        "active_task": data,
        "journal_valid": ok,
        "journal_events": count,
        "journal_head_verified": head,
        "git": git_snapshot(),
        "payload_files": len(payload_inventory()),
    }
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"task      : {data['task_id']}")
        print(f"status    : {data['status']}")
        print(f"title     : {data['title']}")
        print(f"checkpoint: {data.get('checkpoint_sequence', 0)} @ {data.get('last_checkpoint') or 'none'}")
        print(f"journal   : {'VALID' if ok else 'INVALID'} ({count} events, head {str(head)[:12]})")
        print(f"next      : {data.get('next_action')}")
        git = report["git"]
        print(f"git       : {git.get('head') or 'not initialized'}; dirty entries={len(git.get('status', []))}")
    return 0 if ok else 1


def command_resume(args: argparse.Namespace) -> int:
    data = state()
    ok, head, count = verify_journal()
    if not ok:
        raise ContinuityError(f"journal verification failed: {head}")
    write_resume_files(data)
    if args.json:
        print(json.dumps({"state": data, "journal_events": count, "journal_head": head, "git": git_snapshot()}, indent=2, ensure_ascii=False))
    else:
        print(RESUME_PATH.read_text(encoding="utf-8"))
        git = git_snapshot()
        if git.get("status"):
            print("## Current Git/worktree delta")
            for line in git["status"][:50]:
                print(f"- `{line}`")
    return 0


def command_set_status(args: argparse.Namespace) -> int:
    if args.status not in VALID_STATUSES:
        raise ContinuityError(f"invalid status {args.status}")
    with locked():
        data = state()
        ensure_active(data)
        previous = data["status"]
        data["status"] = args.status
        if args.next_action:
            data["next_action"] = args.next_action
        write_state(data)
        append_event("action", "continuity", f"Task status changed {previous} → {args.status}.", {"next_action": data["next_action"]})
        write_resume_files(state())
    return 0


def command_sync_mark(args: argparse.Namespace) -> int:
    if args.platform not in PLATFORMS:
        raise ContinuityError(f"invalid platform {args.platform}")
    with locked():
        path = OUTBOX / args.task_id / args.checkpoint / "SYNC.json"
        data = load_json(path)
        row = data["targets"][args.platform]
        row.update({"status": args.status, "remote_id": args.remote_id, "url": args.url, "synced_at": now(), "note": args.note})
        atomic_json(path, data)
        current = state()
        if current.get("task_id") == args.task_id:
            current.setdefault("remote_sync", {})[args.platform] = args.status
            write_state(current)
            append_event("sync", "continuity", f"{args.platform} checkpoint {args.checkpoint}: {args.status}", {"remote_id": args.remote_id, "url": args.url, "note": args.note})
            write_resume_files(state())
        print(f"marked {args.platform}={args.status}")
    return 0


def command_export(args: argparse.Namespace) -> int:
    data = state()
    ensure_active(data)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive = RUNTIME / f"{data['task_id']}-{stamp}-continuity.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(CURRENT, arcname="workflows/current")
        task_cp = CHECKPOINTS / data["task_id"]
        if task_cp.exists():
            tar.add(task_cp, arcname=f"operations/continuity/checkpoints/{data['task_id']}")
        task_out = OUTBOX / data["task_id"]
        if task_out.exists():
            tar.add(task_out, arcname=f"operations/continuity/outbox/{data['task_id']}")
    bundle = None
    if args.git_bundle and (ROOT / ".git").exists():
        bundle = RUNTIME / f"{data['task_id']}-{stamp}.bundle"
        run(["git", "bundle", "create", str(bundle), "--all"], check=True)
    print(json.dumps({"continuity_archive": str(archive), "git_bundle": str(bundle) if bundle else None}, indent=2))
    return 0


def command_complete(args: argparse.Namespace) -> int:
    with locked():
        data = state()
        ensure_active(data)
        snapshot, _ = create_checkpoint(args.summary, "Task complete; consult permanent archive.", "completed")
        task_id = data["task_id"]
        archive = HISTORY / task_id
        if archive.exists():
            raise ContinuityError(f"history destination already exists: {archive.relative_to(ROOT)}")
        archive.mkdir(parents=True)
        for path in [STATE_PATH, RESUME_PATH, JOURNAL_PATH, CHAT_PATH]:
            if path.exists():
                shutil.copy2(path, archive / path.name)
        if PAYLOAD.exists() and any(PAYLOAD.iterdir()):
            if args.destination:
                destination = (ROOT / args.destination).resolve()
                try:
                    destination.relative_to(ROOT)
                except ValueError as exc:
                    raise ContinuityError("destination escapes repository") from exc
                destination.mkdir(parents=True, exist_ok=True)
                shutil.copytree(PAYLOAD, destination / task_id, dirs_exist_ok=False)
            else:
                shutil.copytree(PAYLOAD, archive / "payload")
        shutil.rmtree(CURRENT)
        CURRENT.mkdir(parents=True)
        idle = {
            "schema_version": 1, "task_id": null_task_id(), "status": "idle", "title": "No active task",
            "style_id": None, "goal": "", "acceptance_criteria": [], "started_at": None, "updated_at": now(),
            "checkpoint_sequence": 0, "event_sequence": 0, "journal_head": None, "last_checkpoint": None,
            "last_checkpoint_path": None, "next_action": "Start the next task with continuity.py init.",
            "running_processes": [], "remote_sync": {platform: "not_configured" for platform in sorted(PLATFORMS)},
            "completed_task": task_id, "completion_checkpoint": snapshot["checkpoint_id"],
        }
        write_state(idle)
        JOURNAL_PATH.touch()
        CHAT_PATH.touch()
        write_resume_files(idle)
        print(f"completed {task_id}; archived at {archive.relative_to(ROOT)}")
    return 0


def command_audit(args: argparse.Namespace) -> int:
    data = state()
    ok, reason, _ = verify_journal()
    if not ok:
        print(f"FAIL journal: {reason}")
        return 1
    if data.get("status") in ACTIVE_STATUSES:
        last = data.get("last_checkpoint")
        if not last:
            print("FAIL active task has no checkpoint")
            return 1
        age = (datetime.now(timezone.utc) - parse_time(last)).total_seconds() / 60
        if age > args.max_age_minutes:
            print(f"FAIL active checkpoint is {age:.1f} minutes old; limit {args.max_age_minutes}")
            return 1
        print(f"PASS active checkpoint age {age:.1f} minutes")
    else:
        print(f"PASS status {data.get('status')} is exempt from hourly freshness")
    return 0


def command_watch(args: argparse.Namespace) -> int:
    print(f"continuity watch started; interval={args.interval_seconds}s", flush=True)
    while True:
        time.sleep(args.interval_seconds)
        with locked():
            data = state()
            if data.get("status") not in ACTIVE_STATUSES:
                print(f"{now()} skip status={data.get('status')}", flush=True)
                continue
            last = data.get("last_checkpoint")
            if last and (datetime.now(timezone.utc) - parse_time(last)).total_seconds() < args.interval_seconds * 0.9:
                continue
            summary = "Automatic heartbeat checkpoint; no unrecorded conclusion inferred."
            next_action = data.get("next_action") or "Resume from the active task record."
            snapshot, _ = create_checkpoint(summary, next_action)
            result = commit_checkpoint(data["task_id"], snapshot["active_state"]["checkpoint_sequence"], args.push) if args.commit else {}
            print(f"{now()} checkpoint={snapshot['checkpoint_id']} result={json.dumps(result)}", flush=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Editing Monarch continuity and recovery controller")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="open the single active task slot")
    p.add_argument("--task-id", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--style")
    p.add_argument("--goal", required=True)
    p.add_argument("--acceptance", action="append")
    p.add_argument("--next-action")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=command_init)

    p = sub.add_parser("log", help="append a hash-chained event and visible chat when applicable")
    p.add_argument("--kind", choices=sorted(EVENT_KINDS), required=True)
    p.add_argument("--actor", default="arena-agent")
    p.add_argument("--message")
    p.add_argument("--file")
    p.add_argument("--source")
    p.set_defaults(func=command_log)

    p = sub.add_parser("process", help="maintain long-running process ledger")
    p.add_argument("operation", choices=["add", "remove", "list"])
    p.add_argument("--id")
    p.add_argument("--name", default="unnamed")
    p.add_argument("--state", default="running")
    p.add_argument("--resume-instruction", default="Use the process tool with this ID; do not restart blindly.")
    p.set_defaults(func=command_process)

    p = sub.add_parser("checkpoint", help="write durable resume/checkpoint/outbox records")
    p.add_argument("--summary", required=True)
    p.add_argument("--next-action", required=True)
    p.add_argument("--status", choices=sorted(VALID_STATUSES))
    p.add_argument("--commit", action="store_true")
    p.add_argument("--push", action="store_true")
    p.set_defaults(func=command_checkpoint)

    p = sub.add_parser("status")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_status)

    p = sub.add_parser("resume")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_resume)

    p = sub.add_parser("set-status")
    p.add_argument("status", choices=sorted(VALID_STATUSES))
    p.add_argument("--next-action")
    p.set_defaults(func=command_set_status)

    p = sub.add_parser("sync-mark")
    p.add_argument("--task-id", required=True)
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--platform", choices=sorted(PLATFORMS), required=True)
    p.add_argument("--status", required=True)
    p.add_argument("--remote-id")
    p.add_argument("--url")
    p.add_argument("--note")
    p.set_defaults(func=command_sync_mark)

    p = sub.add_parser("export")
    p.add_argument("--git-bundle", action="store_true")
    p.set_defaults(func=command_export)

    p = sub.add_parser("complete")
    p.add_argument("--summary", required=True)
    p.add_argument("--destination", help="style-relative destination such as styles/<id>/projects")
    p.set_defaults(func=command_complete)

    p = sub.add_parser("audit")
    p.add_argument("--max-age-minutes", type=float, default=70.0)
    p.set_defaults(func=command_audit)

    p = sub.add_parser("watch", help="long-running hourly checkpoint watcher")
    p.add_argument("--interval-seconds", type=int, default=3300)
    p.add_argument("--commit", action="store_true")
    p.add_argument("--push", action="store_true")
    p.set_defaults(func=command_watch)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except ContinuityError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
