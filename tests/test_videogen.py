from __future__ import annotations
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import videogen as vg  # noqa: E402


def make_project(tmp: pathlib.Path, *, route: str = "free", aspect: str = "9:16",
                 template: str = "reel", key: str | None = None) -> pathlib.Path:
    path = vg.new_project("p1", "Project one", aspect, tmp, template=template)
    data = json.loads(path.read_text())
    data["route"] = route
    for shot in data["shots"]:
        shot["prompt"] = "a cinematic shot of something specific, slow push in"
    path.write_text(json.dumps(data, indent=2))
    if key is not None:
        import os
        os.environ["MINIMAX_API_KEY"] = key
    return path


class ProjectTests(unittest.TestCase):
    def test_new_project_creates_layout(self):
        with tempfile.TemporaryDirectory() as td:
            path = vg.new_project("reel-01", "Reel 01", "9:16", pathlib.Path(td), template="reel")
            self.assertTrue(path.exists())
            data = json.loads(path.read_text())
            self.assertEqual(data["project_id"], "reel-01")
            self.assertEqual(data["aspect"], "9:16")
            self.assertEqual(data["schema_version"], vg.SCHEMA_VERSION)
            self.assertEqual(len(data["shots"]), 3)
            for sub in ("shots", "queue", "lipsync", "delivery"):
                self.assertTrue((path.parent / sub).is_dir())

    def test_new_project_rejects_bad_aspect_and_duplicates(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(vg.EngineError):
                vg.new_project("x", "X", "3:2", pathlib.Path(td))
            vg.new_project("dup", "Dup", "9:16", pathlib.Path(td))
            with self.assertRaises(vg.EngineError):
                vg.new_project("dup", "Dup again", "9:16", pathlib.Path(td))

    def test_templates_have_valid_shots(self):
        for template in ("reel", "film", "hero-test"):
            with self.subTest(template=template), tempfile.TemporaryDirectory() as td:
                path = vg.new_project("t", "T", "16:9", pathlib.Path(td), template=template)
                data = json.loads(path.read_text())
                self.assertEqual(vg.validate_project(data, path), [])

    def test_validation_catches_real_mistakes(self):
        with tempfile.TemporaryDirectory() as td:
            path = vg.new_project("p", "P", "9:16", pathlib.Path(td), template="hero-test")
            data = json.loads(path.read_text())
            base = data["shots"][0]

            broken = dict(data, shots=[dict(base, seconds=30)])
            self.assertTrue(any("4-15" in p for p in vg.validate_project(broken, path)))

            broken = dict(data, shots=[dict(base), dict(base)])
            self.assertTrue(any("duplicate" in p for p in vg.validate_project(broken, path)))

            broken = dict(data, shots=[dict(base, ratio="7:3")])
            self.assertTrue(any("ratio" in p for p in vg.validate_project(broken, path)))

            broken = dict(data, shots=[dict(base, prompt="   ")])
            self.assertTrue(any("prompt" in p for p in vg.validate_project(broken, path)))

            broken = dict(data, shots=[{"id": "l1", "kind": "lipsync", "seconds": 5}])
            problems = vg.validate_project(broken, path)
            self.assertTrue(any("source" in p for p in problems))
            self.assertTrue(any("audio" in p for p in problems))

            self.assertTrue(any("route" in p for p in vg.validate_project(dict(data, route="cheap"), path)))
            self.assertTrue(any("budget_usd" in p for p in vg.validate_project(dict(data, budget_usd=-1), path)))
            self.assertTrue(any("schema_version" in p for p in vg.validate_project(dict(data, schema_version=9), path)))

    def test_shot_ids_cannot_escape_the_folder(self):
        with tempfile.TemporaryDirectory() as td:
            path = vg.new_project("p", "P", "9:16", pathlib.Path(td), template="hero-test")
            data = json.loads(path.read_text())
            data["shots"][0]["id"] = "../evil"
            self.assertTrue(any("plain filename" in p for p in vg.validate_project(data, path)))


class PlanTests(unittest.TestCase):
    def test_free_route_is_zero_cost_and_adds_lipsync_for_hero(self):
        with tempfile.TemporaryDirectory() as td:
            plan = vg.build_plan(json.loads(make_project(pathlib.Path(td), route="free").read_text()),
                                 has_key=False)
            self.assertEqual(plan["estimate_usd"], 0.0)
            hero = next(e for e in plan["shots"] if e["kind"] == "hero")
            self.assertEqual([s["engine"] for s in hero["steps"]], ["wan", "latentsync"])
            plate = next(e for e in plan["shots"] if e["kind"] == "plate")
            self.assertEqual([s["engine"] for s in plate["steps"]], ["wan"])

    def test_paid_route_prices_h3_per_shot_kind(self):
        with tempfile.TemporaryDirectory() as td:
            plan = vg.build_plan(json.loads(make_project(pathlib.Path(td), route="paid").read_text()),
                                 has_key=True)
            hero = next(e for e in plan["shots"] if e["kind"] == "hero")
            plate = next(e for e in plan["shots"] if e["kind"] == "plate")
            self.assertEqual(hero["steps"][0]["resolution"], "2K")
            self.assertAlmostEqual(hero["total_cost"], 0.65)
            self.assertEqual(plate["steps"][0]["resolution"], "768P")
            self.assertAlmostEqual(plate["total_cost"], 0.40)
            self.assertEqual(plan["paid_step_count"], 3)

    def test_auto_route_falls_back_to_free_without_a_key(self):
        with tempfile.TemporaryDirectory() as td:
            project = json.loads(make_project(pathlib.Path(td), route="auto").read_text())
            with_key = vg.build_plan(project, has_key=True)
            without = vg.build_plan(project, has_key=False)
            self.assertGreater(with_key["estimate_usd"], 0.0)
            self.assertEqual(without["estimate_usd"], 0.0)
            self.assertIn("free", without["shots"][0]["engine_label"])

    def test_budget_flag_uses_the_retry_buffer(self):
        with tempfile.TemporaryDirectory() as td:
            project = json.loads(make_project(pathlib.Path(td), route="paid").read_text())
            project["budget_usd"] = 1.5            # estimate 1.45 but 2.17 with retries
            plan = vg.build_plan(project, has_key=True)
            self.assertFalse(plan["within_budget"])
            project["budget_usd"] = 5.0
            self.assertTrue(vg.build_plan(project, has_key=True)["within_budget"])

    def test_plan_warns_about_missing_voice_and_references(self):
        with tempfile.TemporaryDirectory() as free_td, tempfile.TemporaryDirectory() as paid_td:
            free_plan = vg.build_plan(
                json.loads(make_project(pathlib.Path(free_td), route="free").read_text()), has_key=False)
            self.assertTrue(any("voice_ref" in w for w in free_plan["warnings"]))
            paid_plan = vg.build_plan(
                json.loads(make_project(pathlib.Path(paid_td), route="paid").read_text()), has_key=True)
            self.assertTrue(any("reference images" in w for w in paid_plan["warnings"]))

    def test_cost_helper_matches_published_rates(self):
        self.assertAlmostEqual(vg.h3_cost(10, "768P"), 0.8)
        self.assertAlmostEqual(vg.h3_cost(10, "2K"), 1.3)
        self.assertAlmostEqual(vg.h3_cost(15, "2K"), 1.95)


class FakeH3:
    """Stand-in for styles/minimax-h3-video/src/h3_client.py (no network in tests)."""

    calls: list[dict] = []

    @staticmethod
    def build_payload(spec, resolve_files=True):
        return {"model": spec["model"], "resolution": spec["resolution"], "duration": spec["duration"],
                "ratio": spec.get("ratio"), "content": [{"type": "text", "text": spec["prompt"]}]}

    @staticmethod
    def run_shot(spec, key, out_dir):
        FakeH3.calls.append({"spec": spec, "key": key, "out_dir": str(out_dir)})
        out_dir.mkdir(parents=True, exist_ok=True)
        dest = out_dir / f"{spec['id']}.mp4"
        dest.write_bytes(b"fake-mp4")
        return {"status": "succeeded", "engine": "h3", "task_id": "1234",
                "local_path": str(dest), "md5": vg.md5(dest), "bytes": dest.stat().st_size,
                "usage": {"output_seconds": spec["duration"]}}


class RenderTests(unittest.TestCase):
    def setUp(self):
        FakeH3.calls = []

    def test_paid_render_needs_yes_before_spending(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="paid", key="sk-test")
            with mock.patch.object(vg, "_h3_engine", lambda: FakeH3):
                self.assertEqual(vg.render(path, confirm=False), 0)
            self.assertEqual(FakeH3.calls, [], "dry run must not submit anything")

    def test_paid_render_with_yes_calls_the_api(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="paid", key="sk-test")
            with mock.patch.object(vg, "_h3_engine", lambda: FakeH3):
                self.assertEqual(vg.render(path, confirm=True), 0)
            self.assertEqual(len(FakeH3.calls), 3)
            receipts = json.loads((path.parent / "receipts.json").read_text())
            self.assertEqual(receipts["shots"]["s01-hook"]["task_id"], "1234")

    def test_budget_guard_blocks_confirm(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="paid", key="sk-test")
            data = json.loads(path.read_text())
            data["budget_usd"] = 0.5
            path.write_text(json.dumps(data, indent=2))
            with mock.patch.object(vg, "_h3_engine", lambda: FakeH3):
                with self.assertRaises(vg.EngineError):
                    vg.render(path, confirm=True)
                self.assertEqual(vg.render(path, confirm=True, allow_over_budget=True), 0)

    def test_missing_key_is_reported_not_crashed(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="paid")
            import os
            with mock.patch.dict(os.environ, {}, clear=True), \
                 mock.patch.object(vg, "_h3_engine", lambda: FakeH3):
                self.assertEqual(vg.render(path, confirm=True), 0)
            self.assertEqual(FakeH3.calls, [])

    def test_free_render_emits_a_valid_queue_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free", aspect="9:16")
            self.assertEqual(vg.render(path, confirm=True), 0)
            queue_files = list((path.parent / "queue").glob("free_jobs-*.json"))
            self.assertEqual(len(queue_files), 1)
            payload = json.loads(queue_files[0].read_text())
            self.assertEqual(payload["model"], "Wan-AI/Wan2.1-T2V-1.3B-Diffusers")
            self.assertEqual(len(payload["jobs"]), 3)
            for job in payload["jobs"]:
                self.assertEqual((job["frames"] - 1) % 4, 0)
                self.assertLessEqual(job["height"], 832)
                self.assertGreaterEqual(job["frames"], 17)

    def test_free_hero_gets_a_lipsync_script_with_talk_output(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free", template="hero-test")
            vg.render(path, confirm=True)
            script = path.parent / "lipsync" / "s01-hero.sh"
            self.assertTrue(script.exists())
            text = script.read_text()
            self.assertIn("s01-hero-talk.mp4", text)
            self.assertIn("LatentSync", text)
            self.assertIn("capability", text)          # the sm_75 patch note is preserved
            self.assertTrue(script.stat().st_mode & 0o100)

    def test_only_subset_limits_work(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            vg.render(path, confirm=True, only=["s02-plate"])
            payload = json.loads(next((path.parent / "queue").glob("*.json")).read_text())
            self.assertEqual([j["id"] for j in payload["jobs"]], ["s02-plate"])


class VerifyAssembleTests(unittest.TestCase):
    def test_verify_reports_missing_media(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            self.assertEqual(vg.verify(path), 3)

    def test_verify_passes_and_records_md5_without_ffprobe(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            data = json.loads(path.read_text())
            for shot in data["shots"]:
                (path.parent / "shots" / f"{shot['id']}.mp4").write_bytes(b"media")
            with mock.patch.object(vg, "which", lambda binary: None):
                self.assertEqual(vg.verify(path), 0)
            receipts = json.loads((path.parent / "receipts.json").read_text())
            self.assertEqual(receipts["shots"]["s01-hook"]["md5"], vg.md5(path.parent / "shots/s01-hook.mp4"))
            self.assertFalse(receipts["shots"]["s01-hook"]["probe"]["available"])

    def test_verify_prefers_the_talk_version(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free", template="hero-test")
            (path.parent / "shots" / "s01-hero.mp4").write_bytes(b"silent")
            (path.parent / "shots" / "s01-hero-talk.mp4").write_bytes(b"talking")
            with mock.patch.object(vg, "which", lambda binary: None):
                self.assertEqual(vg.verify(path), 0)
            receipts = json.loads((path.parent / "receipts.json").read_text())
            self.assertEqual(receipts["shots"]["s01-hero"]["md5"], vg.md5(path.parent / "shots/s01-hero-talk.mp4"))

    def test_verify_warns_on_bad_duration_when_ffprobe_exists(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free", template="hero-test")
            data = json.loads(path.read_text())
            data["shots"][0]["seconds"] = 10
            path.write_text(json.dumps(data, indent=2))
            (path.parent / "shots" / "s01-hero.mp4").write_bytes(b"media")
            with mock.patch.object(vg, "which", lambda binary: "/usr/bin/" + binary), \
                 mock.patch.object(vg, "probe", lambda p: {"available": True, "width": 1080, "height": 1920,
                                                           "fps": 24.0, "duration": 3.0,
                                                           "video_codec": "h264", "audio_codec": None}):
                self.assertEqual(vg.verify(path), 3)

    def test_assemble_without_ffmpeg_is_an_honest_error(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free", template="hero-test")
            (path.parent / "shots" / "s01-hero.mp4").write_bytes(b"media")
            with mock.patch.object(vg, "which", lambda binary: None):
                with self.assertRaises(vg.EngineError) as ctx:
                    vg.assemble(path)
            self.assertIn("ffmpeg not found", str(ctx.exception))

    def test_assemble_refuses_when_a_shot_is_missing(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            with mock.patch.object(vg, "which", lambda binary: "/usr/bin/" + binary):
                with self.assertRaises(vg.EngineError):
                    vg.assemble(path)

    def test_assemble_writes_master_and_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free", template="hero-test")
            (path.parent / "shots" / "s01-hero.mp4").write_bytes(b"media")

            def fake_run(cmd, **kwargs):
                pathlib.Path(cmd[-1]).write_bytes(b"master-bytes")
                return mock.Mock(returncode=0, stderr="", stdout="")

            with mock.patch.object(vg, "which", lambda binary: "/usr/bin/" + binary), \
                 mock.patch.object(vg, "subprocess") as sp, \
                 mock.patch.object(vg, "probe", lambda p: {"available": False}):
                sp.run.side_effect = fake_run
                self.assertEqual(vg.assemble(path), 0)
            master = path.parent / "delivery" / "p1_MASTER.mp4"
            self.assertTrue(master.exists())
            receipts = json.loads((path.parent / "receipts.json").read_text())
            self.assertEqual(receipts["master"]["md5"], vg.md5(master))


class CliTests(unittest.TestCase):
    def test_plan_status_and_doctor_exit_zero(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            self.assertEqual(vg.main(["plan", str(path)]), 0)
            self.assertEqual(vg.main(["status", str(path)]), 0)
            self.assertEqual(vg.main(["doctor"]), 0)

    def test_missing_project_is_a_clean_error(self):
        self.assertEqual(vg.main(["plan", "/tmp/definitely-not-here.json"]), 2)

    def test_new_via_cli(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(vg.main(["new", "--id", "cli-1", "--title", "CLI one", "--out", td]), 0)
            self.assertTrue((pathlib.Path(td) / "cli-1" / "project.json").exists())


if __name__ == "__main__":
    unittest.main()
