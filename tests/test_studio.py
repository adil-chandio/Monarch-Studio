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

    def test_registry_lists_current_workflows(self) -> None:
        proc = self.run_cli("list", "--json")
        data = json.loads(proc.stdout)
        self.assertEqual([item["code"] for item in data["workflows"]], ["WF-01", "WF-03", "WF-04"])
        self.assertEqual(data["workflows"][0]["trigger"], "SHADEGO <topic>")
        self.assertEqual(data["workflows"][1]["state"], "ACTIVE_WITH_DRIFT")
        self.assertEqual(data["workflows"][2]["trigger"], "CHAOSGO <reference_or_topic>")

    def test_wf04_receipt_matches_registry_and_quality_gates(self) -> None:
        registry = json.loads((ROOT / "studio" / "registry.json").read_text())
        wf04 = next(item for item in registry["workflows"] if item["code"] == "WF-04")
        style = ROOT / wf04["path"]
        receipt = json.loads((style / "records" / "DELIVERY_RECEIPT.json").read_text())
        gates = json.loads((style / "records" / "GATE_REPORT.json").read_text())
        workflow = json.loads((style / "workflow.json").read_text())
        master = receipt["master_delivery"]

        self.assertEqual(gates["gates_passed"], "21/21")
        self.assertEqual(len(gates["gates"]), 21)
        self.assertTrue(all(gate["passed"] for gate in gates["gates"]))
        self.assertEqual(master["md5"], gates["master_md5"])
        self.assertEqual(master["size_bytes"], gates["master_size_bytes"])
        self.assertEqual(master["md5"], wf04["current_delivery"]["md5"])
        self.assertEqual(master["drive_id_chaos_folder"], wf04["current_delivery"]["drive_id"])
        self.assertEqual(master["md5"], workflow["deliveries"][-1]["md5"])
        self.assertEqual(
            [item["version"] for item in receipt["superseded_v2_deliveries"]],
            ["v2_pre_motion_boost", "v2_pre_flash_fix"],
        )

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
