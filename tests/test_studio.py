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
        subprocess.run(CLI + ["clean", "all"], cwd=ROOT, text=True, capture_output=True)

    def run_cli(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        proc = subprocess.run(CLI + list(args), cwd=ROOT, text=True, capture_output=True)
        if check and proc.returncode:
            self.fail(f"CLI failed ({proc.returncode}): {' '.join(args)}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")
        return proc

    def test_registry_preserves_existing_and_registers_wf05(self) -> None:
        proc = self.run_cli("list", "--json")
        data = json.loads(proc.stdout)
        self.assertEqual([item["code"] for item in data["workflows"]], ["WF-01", "WF-03", "WF-05", "WF-06"])
        self.assertEqual(data["workflows"][0]["trigger"], "SHADEGO <topic>")
        self.assertEqual(data["workflows"][1]["state"], "ACTIVE_WITH_DRIFT")
        self.assertEqual(data["workflows"][3]["trigger"], "H3GO <topic or shot list>")
        self.assertEqual(data["workflows"][3]["state"], "PILOT_READY_NO_DELIVERY")

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

    def test_wf05_hydration_preserves_policy_and_history(self) -> None:
        source = ROOT / "styles/premium-motion-editing/data/approved-profile.json"
        before = digest(source)
        self.run_cli("hydrate", "wf5", "--force")
        home = ROOT / ".runtime/wf05/home/user"
        self.assertTrue((home / "src/wf05.py").exists())
        self.assertTrue((home / "projects/einstein-flow-state/versions/v6/QA.json").exists())
        result = self.run_cli("run", "wf05", "--", sys.executable, "src/wf05.py", "inspect")
        self.assertIn('"subtitle_mode": "off"', result.stdout)
        self.assertEqual(before, digest(source))

    def test_ignored_virtualenv_is_not_a_repo_manifest_input(self) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("studio_wf05_test", ROOT / "tools/studio.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        files = [p.relative_to(ROOT).as_posix() for p in module.eligible_repo_files()]
        self.assertFalse(any(x.startswith((".venv/", ".runtime/", "node_modules/")) for x in files))
        self.assertIn("styles/premium-motion-editing/data/approved-profile.json", files)

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
