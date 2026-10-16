#!/usr/bin/env python3
"""Editing Monarch Studio registry, validation and compatibility-runtime CLI."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import py_compile
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "studio" / "registry.json"
RUNTIME_ROOT = ROOT / ".runtime"
MANIFEST_PATH = ROOT / ".studio-manifest.json"

SKIP_PARTS = {
    ".git",
    ".runtime",
    ".continuity-runtime",
    ".venv",
    "venv",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "vendor",
    "__pycache__",
    "node_modules",
    "build",
    "dist",
    "coverage",
}
TEXT_EXTENSIONS = {
    ".py", ".sh", ".md", ".json", ".txt", ".csv", ".tsv", ".toml",
    ".yaml", ".yml", ".ini", ".cfg", ".html", ".css", ".js", ".svg",
}
AUTHORITY_MD5 = {
    "styles/monarch-stickman-animation/RESUME_STATE.md": "6034f114c84ca4079424f6734755dde5",
    "styles/monarch-stickman-animation/SHADEGO.md": "f65d4c0b36e316643007221ef6c0840b",
    "styles/monarch-noir-film/RESUME_STATE.md": "de32cd2b9488315675b5fede2758e902",
    "styles/monarch-noir-film/HUB.md": "cd7c21a4de0da9e9ce983d6f81f4b101",
    "styles/monarch-noir-film/films/04am/GATES_NOIRGO_4AM_v2.md": "0f096b1e57dc3ab6458d6d0efd9ee4be",
    "characters/monarch/CUSTOM_HERO_CHARACTER_BIBLE_v2.pdf": "24a5d5c3d1a1aa234d4420a34bf6b4ad",
    "characters/monarch/CUSTOM_HERO_MASTER_BOARD_v2.png": "8977b5ee07e381894cffa4470b017759",
}


class StudioError(RuntimeError):
    """A user-facing studio operation error."""


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise StudioError(f"missing JSON file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise StudioError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc


def registry() -> dict[str, Any]:
    data = load_json(REGISTRY_PATH)
    if not isinstance(data, dict) or not isinstance(data.get("workflows"), list):
        raise StudioError("studio/registry.json has no workflows array")
    return data


def workflow_entry(selector: str) -> dict[str, Any]:
    needle = selector.lower().replace("_", "-")
    for item in registry()["workflows"]:
        aliases = {
            str(item.get("code", "")).lower(),
            str(item.get("code", "")).lower().replace("-", ""),
            str(item.get("slug", "")).lower(),
            Path(str(item.get("path", ""))).name.lower(),
        }
        if needle in aliases or needle.replace("-", "") in aliases:
            return item
    choices = ", ".join(w["slug"] for w in registry()["workflows"])
    raise StudioError(f"unknown workflow {selector!r}; choose {choices}")


def workflow_source(entry: dict[str, Any]) -> Path:
    path = (ROOT / entry["path"]).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError as exc:
        raise StudioError(f"workflow path escapes repository: {path}") from exc
    return path


def runtime_home(entry: dict[str, Any]) -> Path:
    return RUNTIME_ROOT / entry["slug"] / "home" / "user"


def hash_file(path: Path, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def eligible_repo_files() -> Iterable[Path]:
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path == MANIFEST_PATH:
            continue
        rel = path.relative_to(ROOT)
        if any(part in SKIP_PARTS for part in rel.parts):
            continue
        if path.suffix in {".pyc", ".pyo"} or path.name in {".DS_Store", ".continuity.lock"}:
            continue
        yield path


def sparse_checkout_enabled() -> bool:
    if not (ROOT / ".git").exists():
        return False
    proc = subprocess.run(
        ["git", "config", "--bool", "core.sparseCheckout"],
        cwd=ROOT, text=True, capture_output=True,
    )
    return proc.returncode == 0 and proc.stdout.strip().lower() == "true"


def git_tracked_paths() -> set[str]:
    if not (ROOT / ".git").exists():
        return set()
    proc = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True)
    if proc.returncode:
        return set()
    return {item.decode("utf-8") for item in proc.stdout.split(b"\0") if item}


def git_sparse_omitted_paths() -> set[str]:
    if not sparse_checkout_enabled():
        return set()
    proc = subprocess.run(["git", "ls-files", "-v", "-z"], cwd=ROOT, capture_output=True)
    if proc.returncode:
        return set()
    return {
        item[2:].decode("utf-8")
        for item in proc.stdout.split(b"\0")
        if item.startswith(b"S ")
    }


def make_manifest() -> dict[str, Any]:
    files: dict[str, Any] = {}
    # Sparse Arena checkouts omit archived binaries from the working tree. Preserve
    # only paths explicitly marked skip-worktree; do not preserve materialized paths
    # that were deleted or moved before the next git add.
    if sparse_checkout_enabled() and MANIFEST_PATH.exists():
        previous = load_json(MANIFEST_PATH).get("files", {})
        omitted = git_sparse_omitted_paths()
        files.update({rel: record for rel, record in previous.items() if rel in omitted})
    for path in eligible_repo_files():
        rel = path.relative_to(ROOT).as_posix()
        files[rel] = {"sha256": hash_file(path), "size": path.stat().st_size}
    return {
        "schema_version": 1,
        "algorithm": "sha256",
        "generated_at": now_iso(),
        "sparse_checkout_aware": True,
        "excludes": [".git", ".runtime", ".continuity-runtime", "vendor", "build/cache/output directories"],
        "files": dict(sorted(files.items())),
    }


def command_manifest(args: argparse.Namespace) -> int:
    data = make_manifest()
    if args.write:
        MANIFEST_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {MANIFEST_PATH.relative_to(ROOT)} with {len(data['files'])} files")
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


def command_list(args: argparse.Namespace) -> int:
    data = registry()
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0
    rows = []
    for item in data["workflows"]:
        delivery = item.get("current_delivery") or item.get("current_fully_sourced_delivery") or {}
        rows.append((
            item["code"], item["slug"], item["state"], item["trigger"],
            delivery.get("title", "—"), item["path"],
        ))
    headers = ("CODE", "ALIAS", "STATE", "TRIGGER", "CURRENT R1 DELIVERY", "PATH")
    widths = [max(len(str(row[i])) for row in [headers, *rows]) for i in range(len(headers))]
    print("  ".join(headers[i].ljust(widths[i]) for i in range(len(headers))))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(str(row[i]).ljust(widths[i]) for i in range(len(row))))
    return 0


def module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def command_doctor(args: argparse.Namespace) -> int:
    required_commands = ["bash", "git"]
    optional_commands = ["ffmpeg", "ffprobe"]
    required_modules = ["numpy", "PIL", "scipy", "imageio_ffmpeg", "reportlab", "fitz"]
    failures = []

    print(f"repository : {ROOT}")
    print(f"python     : {sys.version.split()[0]} ({sys.executable})")
    if sys.version_info < (3, 10):
        failures.append("Python >= 3.10")

    print("\nCommands")
    for name in required_commands:
        found = shutil.which(name)
        print(f"  {'OK' if found else 'MISSING':7} {name:16} {found or ''}")
        if not found:
            failures.append(name)
    for name in optional_commands:
        found = shutil.which(name)
        print(f"  {'OK' if found else 'OPTIONAL':7} {name:16} {found or 'imageio-ffmpeg may supply a binary'}")

    print("\nPython render modules")
    for name in required_modules:
        ok = module_available(name)
        print(f"  {'OK' if ok else 'MISSING':7} {name}")
        if not ok:
            failures.append(name)

    katex = [
        Path("/usr/share/R/doc/html/katex/fonts/KaTeX_Main-Regular.ttf"),
        Path("/usr/share/R/doc/html/katex/fonts/KaTeX_Main-Italic.ttf"),
        Path("/usr/share/R/doc/html/katex/fonts/KaTeX_Typewriter-Regular.ttf"),
    ]
    print("\nSystem font compatibility")
    for path in katex:
        print(f"  {'OK' if path.exists() else 'MISSING':7} {path}")
    if not all(path.exists() for path in katex):
        print("  note: WF-03 historical code references these exact paths; install KaTeX fonts or port font lookup before a full render")

    usage = shutil.disk_usage(ROOT)
    print(f"\nfree disk  : {usage.free / (1024 ** 3):.2f} GiB")
    print(f"runtime dir: {RUNTIME_ROOT.relative_to(ROOT)}")

    if failures:
        print("\nDoctor failed required checks: " + ", ".join(failures))
        print("Install requirements/render.txt before rendering.")
        return 1
    print("\nDoctor: required command/module checks passed.")
    return 0


class Validation:
    def __init__(self, quiet: bool = False) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.passes: list[str] = []
        self.quiet = quiet

    def ok(self, message: str) -> None:
        self.passes.append(message)
        if not self.quiet:
            print(f"PASS  {message}")

    def warn(self, message: str) -> None:
        self.warnings.append(message)
        if not self.quiet:
            print(f"WARN  {message}")

    def fail(self, message: str) -> None:
        self.errors.append(message)
        if not self.quiet:
            print(f"FAIL  {message}")


def validate_registry(v: Validation) -> None:
    try:
        data = registry()
    except StudioError as exc:
        v.fail(str(exc))
        return
    codes = [str(item.get("code")) for item in data["workflows"]]
    slugs = [str(item.get("slug")) for item in data["workflows"]]
    if len(codes) != len(set(codes)) or len(slugs) != len(set(slugs)):
        v.fail("workflow codes/slugs are not unique")
    else:
        v.ok(f"registry has {len(codes)} unique workflows")

    for item in data["workflows"]:
        source = workflow_source(item)
        if not source.is_dir():
            v.fail(f"{item['code']} path missing: {item['path']}")
            continue
        manifest_path = source / "workflow.json"
        try:
            wf = load_json(manifest_path)
        except StudioError as exc:
            v.fail(str(exc))
            continue
        if wf.get("code") != item.get("code") or wf.get("slug") != item.get("slug"):
            v.fail(f"{item['code']} registry/workflow.json identity mismatch")
        else:
            v.ok(f"{item['code']} identity and path")
        missing = [rel for rel in wf.get("required_paths", []) if not (source / rel).exists()]
        if missing:
            v.fail(f"{item['code']} missing required paths: {', '.join(missing)}")
        else:
            v.ok(f"{item['code']} required paths ({len(wf.get('required_paths', []))})")

    wf03 = next((item for item in data["workflows"] if item.get("code") == "WF-03"), None)
    if not wf03 or wf03.get("state") != "ACTIVE_WITH_DRIFT" or len(wf03.get("drift", [])) < 3:
        v.fail("WF-03 known cross-source drift is not explicitly declared")
    elif not (ROOT / "docs" / "RECONCILIATION.md").exists():
        v.fail("WF-03 drift is declared but docs/RECONCILIATION.md is missing")
    else:
        v.ok("WF-03 drift is explicit and linked to reconciliation policy")

    for character in data.get("characters", []):
        char_root = ROOT / character["path"]
        try:
            char = load_json(ROOT / character["registry"])
        except StudioError as exc:
            v.fail(str(exc))
            continue
        missing = []
        consolidated = char.get("consolidated_authority", {})
        for value in consolidated.values():
            if not (char_root / value["path"]).exists():
                missing.append(value["path"])
        for variant in char.get("variants", {}).values():
            for value in (variant.get("face"), variant.get("body")):
                if value and not (char_root / value["preview"]).exists():
                    missing.append(value["preview"])
        if missing:
            v.fail(f"character authority paths missing: {', '.join(missing)}")
        else:
            v.ok(f"character {char.get('character')} authority and previews")


def validate_style_library(v: Validation) -> None:
    try:
        data = load_json(ROOT / "styles" / "registry.json")
    except StudioError as exc:
        v.fail(str(exc))
        return
    rows = data.get("styles", [])
    ids = [row.get("style_id") for row in rows]
    if not rows or len(ids) != len(set(ids)):
        v.fail("style registry is empty or contains duplicate IDs")
        return
    failures = 0
    for row in rows:
        base = ROOT / row["path"]
        try:
            style = load_json(base / "style.json")
        except StudioError as exc:
            failures += 1
            v.fail(str(exc))
            continue
        if style.get("style_id") != row.get("style_id") or style.get("path") != row.get("path"):
            failures += 1
            v.fail(f"style registry mismatch: {row.get('style_id')}")
        for rel in ("README.md", "workflow.json", style.get("knowledge_index", "knowledge/INDEX.md")):
            if not (base / rel).exists():
                failures += 1
                v.fail(f"style {row.get('style_id')} missing {rel}")
    if not failures:
        v.ok(f"permanent style library ({len(rows)} named styles)")


def validate_continuity(v: Validation) -> None:
    required = [
        ROOT / "workflows" / "current" / "ACTIVE_TASK.json",
        ROOT / "workflows" / "current" / "RESUME.md",
        ROOT / "workflows" / "current" / "JOURNAL.jsonl",
        ROOT / "workflows" / "current" / "CHAT_TRANSCRIPT.jsonl",
        ROOT / "START_HERE.md",
    ]
    missing = [path.relative_to(ROOT).as_posix() for path in required if not path.exists()]
    if missing:
        v.fail("continuity files missing: " + ", ".join(missing))
        return
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "continuity.py"), "status", "--json"],
        cwd=ROOT, text=True, capture_output=True,
    )
    if proc.returncode:
        v.fail("continuity status failed: " + (proc.stderr or proc.stdout).strip())
        return
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        v.fail(f"continuity status returned invalid JSON: {exc}")
        return
    if not report.get("journal_valid"):
        v.fail("continuity journal hash chain is invalid")
    elif report.get("active_task", {}).get("task_id") in {None, ""}:
        v.fail("continuity active-task identity is missing")
    else:
        v.ok(f"continuity journal ({report.get('journal_events', 0)} hash-chained events)")


def validate_json(v: Validation) -> None:
    count = 0
    for path in eligible_repo_files():
        if path.suffix.lower() != ".json":
            continue
        count += 1
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # report exact imported-file issue
            v.fail(f"JSON {path.relative_to(ROOT)}: {exc}")
    if not any(error.startswith("JSON ") for error in v.errors):
        v.ok(f"JSON syntax ({count} files)")


def validate_python(v: Validation) -> None:
    count = 0
    failures = 0
    for path in eligible_repo_files():
        if path.suffix.lower() != ".py":
            continue
        count += 1
        try:
            source = path.read_text(encoding="utf-8")
            compile(source, str(path), "exec")
        except Exception as exc:
            failures += 1
            v.fail(f"Python {path.relative_to(ROOT)}: {exc}")
    if not failures:
        v.ok(f"Python syntax ({count} files)")


def validate_shell(v: Validation) -> None:
    bash = shutil.which("bash")
    scripts = [path for path in eligible_repo_files() if path.suffix.lower() == ".sh"]
    if not bash:
        v.fail("bash unavailable; cannot syntax-check shell scripts")
        return
    failures = 0
    for path in scripts:
        proc = subprocess.run([bash, "-n", str(path)], text=True, capture_output=True)
        if proc.returncode:
            failures += 1
            detail = (proc.stderr or proc.stdout).strip().splitlines()[-1]
            v.fail(f"shell {path.relative_to(ROOT)}: {detail}")
    if not failures:
        v.ok(f"shell syntax ({len(scripts)} files)")


def validate_authority_hashes(v: Validation) -> None:
    failures = 0
    for rel, expected in AUTHORITY_MD5.items():
        path = ROOT / rel
        if not path.exists():
            failures += 1
            v.fail(f"authority missing: {rel}")
            continue
        actual = hash_file(path, "md5")
        if actual != expected:
            failures += 1
            v.fail(f"authority MD5 mismatch: {rel} expected {expected}, got {actual}")
    if not failures:
        v.ok(f"authority MD5s ({len(AUTHORITY_MD5)} files)")


def validate_repo_manifest(v: Validation) -> None:
    if not MANIFEST_PATH.exists():
        v.fail(".studio-manifest.json missing; run: python3 tools/studio.py manifest --write")
        return
    try:
        data = load_json(MANIFEST_PATH)
    except StudioError as exc:
        v.fail(str(exc))
        return
    expected = data.get("files", {})
    if not isinstance(expected, dict):
        v.fail(".studio-manifest.json files field is invalid")
        return
    current = {path.relative_to(ROOT).as_posix(): path for path in eligible_repo_files()}
    missing = sorted(set(expected) - set(current))
    extra = sorted(set(current) - set(expected))
    sparse_omitted: list[str] = []
    if missing and sparse_checkout_enabled():
        omitted = git_sparse_omitted_paths()
        sparse_omitted = [rel for rel in missing if rel in omitted]
        missing = [rel for rel in missing if rel not in omitted]
        if sparse_omitted:
            v.warn(f"manifest verification deferred for {len(sparse_omitted)} sparse-omitted tracked files")
    if missing:
        v.fail("manifest paths missing: " + ", ".join(missing[:10]) + (" …" if len(missing) > 10 else ""))
    if extra:
        v.fail("manifest lacks current paths: " + ", ".join(extra[:10]) + (" …" if len(extra) > 10 else ""))
    mismatches = []
    for rel in sorted(set(expected) & set(current)):
        record = expected[rel]
        path = current[rel]
        if record.get("size") != path.stat().st_size or record.get("sha256") != hash_file(path):
            mismatches.append(rel)
    if mismatches:
        v.fail("manifest content mismatch: " + ", ".join(mismatches[:10]) + (" …" if len(mismatches) > 10 else ""))
    if not missing and not extra and not mismatches:
        v.ok(f"repository SHA-256 manifest ({len(current)} files)")


def validate_sizes_and_secrets(v: Validation) -> None:
    huge = []
    large = []
    suspicious = []
    secret_names = {".env", "id_rsa", "id_ed25519", ".netrc", ".git-credentials"}
    for path in eligible_repo_files():
        size = path.stat().st_size
        rel = path.relative_to(ROOT).as_posix()
        if size >= 100 * 1024 * 1024:
            huge.append(rel)
        elif size >= 50 * 1024 * 1024:
            large.append(rel)
        if path.name in secret_names or path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
            suspicious.append(rel)
    if huge:
        v.fail("files at/over 100 MiB: " + ", ".join(huge))
    else:
        v.ok("no Git blob reaches 100 MiB")
    if large:
        v.warn("large Git blobs (50–100 MiB): " + ", ".join(large))
    if suspicious:
        v.fail("possible credential files: " + ", ".join(suspicious))
    else:
        v.ok("no obvious credential filenames")


def validate_submodules(v: Validation) -> None:
    data = registry()
    gitmodules = ROOT / ".gitmodules"
    if not gitmodules.exists():
        v.fail(".gitmodules missing for registered vendor repositories")
        return
    text = gitmodules.read_text(encoding="utf-8", errors="replace")
    for item in data.get("vendor", []):
        rel = item["path"]
        path = ROOT / rel
        if f"path = {rel}" not in text:
            v.fail(f"vendor path absent from .gitmodules: {rel}")
            continue
        expected = item["commit"]
        actual = None
        if path.exists() and (path / ".git").exists():
            proc = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], text=True, capture_output=True)
            if not proc.returncode:
                actual = proc.stdout.strip()
        elif (ROOT / ".git").exists():
            # A clean sparse/uninitialized checkout still has an authoritative gitlink.
            proc = subprocess.run(["git", "ls-files", "--stage", "--", rel], cwd=ROOT, text=True, capture_output=True)
            fields = proc.stdout.strip().split()
            if len(fields) >= 2 and fields[0] == "160000":
                actual = fields[1]
        if actual is None:
            v.fail(f"vendor pin unavailable (neither initialized submodule nor gitlink): {rel}")
        elif actual != expected:
            v.fail(f"vendor commit mismatch {rel}: expected {expected}, got {actual}")
        else:
            v.ok(f"vendor pin {rel} @ {actual[:12]} (working tree optional)")


def validate_portability(v: Validation) -> None:
    if not (ROOT / ".gitignore").exists():
        v.fail(".gitignore missing")
        return
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8", errors="replace")
    if ".runtime/" not in ignored:
        v.fail(".runtime/ is not Git-ignored")
    else:
        v.ok("generated compatibility runtime is Git-ignored")

    count = 0
    files = 0
    for entry in registry()["workflows"]:
        for path in workflow_source(entry).rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            hits = text.count("/home/user")
            if hits:
                files += 1
                count += hits
    if count:
        v.warn(f"preserved historical absolute paths: {count} references in {files} files; use hydrate/run")
    else:
        v.ok("no historical /home/user paths detected")


def command_validate(args: argparse.Namespace) -> int:
    v = Validation(quiet=args.quiet)
    validate_registry(v)
    validate_style_library(v)
    validate_continuity(v)
    validate_json(v)
    validate_python(v)
    validate_shell(v)
    validate_authority_hashes(v)
    validate_sizes_and_secrets(v)
    validate_portability(v)
    validate_submodules(v)
    validate_repo_manifest(v)

    summary = {
        "passed": len(v.passes),
        "warnings": len(v.warnings),
        "errors": len(v.errors),
        "warning_messages": v.warnings,
        "error_messages": v.errors,
    }
    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"\nValidation summary: {len(v.passes)} passed, {len(v.warnings)} warnings, {len(v.errors)} errors")
    return 1 if v.errors else 0


def generated_copy(src: Path, dst: Path, replacements: dict[str, str], stats: dict[str, int]) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    mode = src.stat().st_mode
    text: str | None = None
    if src.suffix.lower() in TEXT_EXTENSIONS or src.stat().st_size < 1024 * 1024:
        try:
            text = src.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            text = None
    if text is not None:
        original = text
        for old, new in replacements.items():
            text = text.replace(old, new)
        dst.write_text(text, encoding="utf-8")
        shutil.copymode(src, dst)
        stats["copied_text"] += 1
        if text != original:
            stats["rewritten_text"] += 1
        return
    try:
        os.link(src, dst)
        stats["hardlinked_binary"] += 1
    except OSError:
        shutil.copy2(src, dst)
        stats["copied_binary"] += 1
    os.chmod(dst, stat.S_IMODE(mode))


def mirror_tree(src: Path, dst: Path, replacements: dict[str, str], stats: dict[str, int]) -> None:
    for path in sorted(src.rglob("*")):
        rel = path.relative_to(src)
        if any(part in {".git", ".runtime", "__pycache__", "build", "node_modules", ".venv", "venv"} for part in rel.parts):
            continue
        target = dst / rel
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            generated_copy(path, target, replacements, stats)


def hydrate(entry: dict[str, Any], force: bool = False) -> Path:
    src = workflow_source(entry)
    base = RUNTIME_ROOT / entry["slug"]
    home = runtime_home(entry)
    if base.exists():
        if not force:
            raise StudioError(f"runtime already exists: {base.relative_to(ROOT)}; pass --force to recreate")
        shutil.rmtree(base)
    home.mkdir(parents=True, exist_ok=True)
    (home / "build").mkdir(parents=True, exist_ok=True)
    replacements = {"/home/user": str(home)}
    stats = {"copied_text": 0, "rewritten_text": 0, "hardlinked_binary": 0, "copied_binary": 0}

    if entry["slug"] == "wf01":
        mirror_tree(src, home, replacements, stats)
    elif entry["slug"] == "wf02":
        # Current 3D projects are already relative-path portable. Preserve their
        # source bytes rather than applying the older workflows' path rewrite.
        mirror_tree(src, home, {}, stats)
    elif entry["slug"] == "wf03":
        legacy = home / "workflows" / "wf03_monarch_noir_film"
        mirror_tree(src, legacy, replacements, stats)

        shared_src = ROOT / "styles" / "monarch-stickman-animation" / "src"
        for name in ("toon.py", "shade.py"):
            generated_copy(shared_src / name, home / "src" / name, replacements, stats)
        mirror_tree(ROOT / "styles" / "monarch-stickman-animation" / "fonts", home / "fonts", replacements, stats)
        mirror_tree(ROOT / "studio" / "editor-brain" / "brain", home / "brain", replacements, stats)
        generated_copy(
            ROOT / "studio" / "editor-brain" / "MONARCH_EDITOR_BRAIN.md",
            home / "MONARCH_EDITOR_BRAIN.md",
            replacements,
            stats,
        )
    else:
        raise StudioError(f"no hydration adapter for {entry['slug']}")

    metadata = {
        "schema_version": 1,
        "generated_at": now_iso(),
        "workflow": entry["code"],
        "source": str(src),
        "runtime_home": str(home),
        "policy": "Generated compatibility copy; authoritative repository source was not modified.",
        "stats": stats,
    }
    (base / "hydration.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return home


def command_hydrate(args: argparse.Namespace) -> int:
    entry = workflow_entry(args.workflow)
    home = hydrate(entry, force=args.force)
    data = load_json(home.parents[1] / "hydration.json")
    print(f"hydrated {entry['code']} -> {home.relative_to(ROOT)}")
    print("stats: " + ", ".join(f"{key}={value}" for key, value in data["stats"].items()))
    return 0


def command_run(args: argparse.Namespace) -> int:
    entry = workflow_entry(args.workflow)
    home = runtime_home(entry)
    if args.rehydrate:
        home = hydrate(entry, force=True)
    elif not home.exists():
        print(f"runtime missing; hydrating {entry['code']} first", file=sys.stderr)
        home = hydrate(entry, force=False)

    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise StudioError("run requires a command after --")

    env = os.environ.copy()
    env["MONARCH_STUDIO_ROOT"] = str(ROOT)
    env["MONARCH_RUNTIME_HOME"] = str(home)
    python_paths = [str(home / "src")]
    if entry["slug"] == "wf03":
        python_paths.insert(0, str(home / "workflows" / "wf03_monarch_noir_film" / "src"))
    if env.get("PYTHONPATH"):
        python_paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(python_paths)

    print(f"[{entry['code']}] cwd={home}")
    print("+ " + " ".join(command))
    try:
        proc = subprocess.run(command, cwd=home, env=env)
    except FileNotFoundError as exc:
        raise StudioError(f"command not found: {command[0]}") from exc
    return proc.returncode


def command_clean(args: argparse.Namespace) -> int:
    if args.workflow == "all":
        target = RUNTIME_ROOT
    else:
        entry = workflow_entry(args.workflow)
        target = RUNTIME_ROOT / entry["slug"]
    if target.exists():
        shutil.rmtree(target)
        print(f"removed {target.relative_to(ROOT)}")
    else:
        print(f"already clean: {target.relative_to(ROOT)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="studio.py",
        description="Editing Monarch Studio registry, validator and compatibility runtime",
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    p_list = sub.add_parser("list", help="list registered workflows")
    p_list.add_argument("--json", action="store_true", help="emit normalized registry JSON")
    p_list.set_defaults(func=command_list)

    p_doctor = sub.add_parser("doctor", help="check local render dependencies")
    p_doctor.set_defaults(func=command_doctor)

    p_validate = sub.add_parser("validate", help="validate repository structure and integrity")
    p_validate.add_argument("--quiet", action="store_true", help="only print the summary")
    p_validate.add_argument("--json", action="store_true", help="emit the summary as JSON")
    p_validate.set_defaults(func=command_validate)

    p_hydrate = sub.add_parser("hydrate", help="create a generated legacy-compatible runtime")
    p_hydrate.add_argument("workflow", help="workflow alias/code (wf01, wf02, wf03 or WF-01, WF-02, WF-03)")
    p_hydrate.add_argument("--force", action="store_true", help="replace an existing runtime")
    p_hydrate.set_defaults(func=command_hydrate)

    p_run = sub.add_parser("run", help="run a command in a hydrated compatibility runtime")
    p_run.add_argument("workflow", help="workflow alias/code")
    p_run.add_argument("--rehydrate", action="store_true", help="recreate the runtime before running")
    p_run.add_argument("command", nargs=argparse.REMAINDER, help="command after --")
    p_run.set_defaults(func=command_run)

    p_clean = sub.add_parser("clean", help="remove generated compatibility runtime(s)")
    p_clean.add_argument("workflow", nargs="?", default="all", help="wf01, wf02, wf03 or all")
    p_clean.set_defaults(func=command_clean)

    p_manifest = sub.add_parser("manifest", help="create the repository SHA-256 manifest")
    p_manifest.add_argument("--write", action="store_true", help="write .studio-manifest.json")
    p_manifest.set_defaults(func=command_manifest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except StudioError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
