from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = [sys.executable, str(ROOT / "tools" / "studio.py")]
MATERIALIZE = [sys.executable, str(ROOT / "tools" / "materialize.py")]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class StudioCliTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def tearDownClass(cls) -> None:
        # Never erase unrelated in-progress film renders / delivery masters in
        # .runtime/. Only remove compatibility copies these tests can create.
        for workflow in ("wf01", "wf02", "wf03"):
            subprocess.run(CLI + ["clean", workflow], cwd=ROOT, text=True, capture_output=True)

    def run_cli(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        proc = subprocess.run(CLI + list(args), cwd=ROOT, text=True, capture_output=True)
        if check and proc.returncode:
            self.fail(f"CLI failed ({proc.returncode}): {' '.join(args)}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")
        return proc

    def test_registry_lists_live_workflows_preserving_existing_authority(self) -> None:
        proc = self.run_cli("list", "--json")
        data = json.loads(proc.stdout)
        self.assertEqual([item["code"] for item in data["workflows"]], ["WF-01", "WF-02", "WF-03"])
        by_code = {item["code"]: item for item in data["workflows"]}
        self.assertEqual(by_code["WF-01"]["trigger"], "SHADEGO <topic>")
        self.assertEqual(by_code["WF-02"]["style_id"], "monarch-zackd-3d")
        self.assertEqual(by_code["WF-03"]["state"], "ACTIVE_WITH_DRIFT")

    def test_registered_required_paths_exist(self) -> None:
        registry = json.loads((ROOT / "studio" / "registry.json").read_text())
        for item in registry["workflows"]:
            base = ROOT / item["path"]
            manifest = json.loads((base / "workflow.json").read_text())
            for rel in manifest["required_paths"]:
                self.assertTrue((base / rel).exists(), f"{item['code']} missing {rel}")

    def test_wf01_hydration_rewrites_generated_copy_without_source_drift(self) -> None:
        source = ROOT / "styles" / "monarch-stickman-animation" / "src" / "respect2.py"
        before = digest(source)
        self.run_cli("hydrate", "wf01", "--force")
        home = ROOT / ".runtime" / "wf01" / "home" / "user"
        generated = home / "src" / "respect2.py"
        self.assertTrue(generated.exists())
        self.assertIn(str(home / "shade_respect_v2.mp4"), generated.read_text())
        self.assertEqual(before, digest(source), "hydration modified authoritative source")
        status = self.run_cli("run", "wf01", "--", sys.executable, "brain/concept.py", "status")
        brain_registry = json.loads(
            (ROOT / "styles" / "monarch-stickman-animation" / "brain" / "registry.json").read_text()
        )
        expected_count = len(brain_registry["videos"])
        expected_latest = brain_registry["videos"][-1]["key"]
        self.assertIn(f"{expected_count} delivered videos", status.stdout.lower())
        self.assertIn(expected_latest.lower(), status.stdout.lower())

    def test_wf02_hydration_preserves_portable_project_source(self) -> None:
        data = json.loads(self.run_cli("list", "--json").stdout)
        entry = next(item for item in data["workflows"] if item["code"] == "WF-02")
        source = ROOT / entry["path"]
        project = Path(entry["current_delivery"]["project_path"])
        before = digest(source / project / "src" / "film.js")
        self.run_cli("hydrate", "wf02", "--force")
        home = ROOT / ".runtime" / "wf02" / "home" / "user"
        self.assertEqual(before, digest(home / project / "src" / "film.js"))
        self.assertEqual(before, digest(source / project / "src" / "film.js"))
        self.assertTrue((home / project / "assets" / "models" / "cutaway.glb").exists())

    def test_wf03_hydration_recreates_legacy_layout_and_shared_dependencies(self) -> None:
        source = ROOT / "styles" / "monarch-noir-film" / "src" / "encode_window.sh"
        before = digest(source)
        self.run_cli("hydrate", "wf03", "--force")
        home = ROOT / ".runtime" / "wf03" / "home" / "user"
        legacy = home / "workflows" / "wf03_monarch_noir_film"
        self.assertTrue((legacy / "src" / "film_window.py").exists())
        self.assertTrue((home / "src" / "toon.py").exists())
        self.assertTrue((home / "src" / "shade.py").exists())
        self.assertTrue((home / "fonts" / "Montserrat-VF.ttf").exists())
        self.assertTrue((home / "brain" / "concept.py").exists())
        self.assertIn(str(home / "build" / "wf03_window"), (legacy / "src" / "encode_window.sh").read_text())
        self.assertEqual(before, digest(source), "hydration modified authoritative source")
        help_result = self.run_cli(
            "run", "wf03", "--", sys.executable,
            "workflows/wf03_monarch_noir_film/src/film_window.py", "--help",
        )
        self.assertIn("--render", help_result.stdout)

    def test_materialization_status_is_read_only(self) -> None:
        proc = subprocess.run(MATERIALIZE + ["status"], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("tracked=", proc.stdout)
        self.assertIn("sparse_omitted=", proc.stdout)

    def test_integrity_manifest_excludes_generated_and_vendor_contents(self) -> None:
        data = json.loads((ROOT / ".studio-manifest.json").read_text())
        paths = set(data["files"])
        self.assertIn("README.md", paths)
        self.assertNotIn(".studio-manifest.json", paths)
        self.assertFalse(any(path.startswith(".runtime/") for path in paths))
        self.assertFalse(any(path.startswith(".venv/") for path in paths))
        self.assertFalse(any(path.startswith("venv/") for path in paths))
        self.assertFalse(any(path.startswith("vendor/effectcraft/") for path in paths))

    def test_missing_manifest_paths_are_genuine_sparse_omissions(self) -> None:
        data = json.loads((ROOT / ".studio-manifest.json").read_text())
        missing = [rel for rel in data["files"] if not (ROOT / rel).exists()]
        for rel in missing:
            proc = subprocess.run(
                ["git", "ls-files", "-v", "--", rel],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertTrue(
                proc.stdout.startswith("S "),
                f"manifest retained a missing path not marked skip-worktree: {rel}",
            )


if __name__ == "__main__":
    unittest.main()
