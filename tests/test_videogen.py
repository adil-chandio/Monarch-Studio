from __future__ import annotations
import json
import os
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


class AllowPaidMixin:
    """Tests that deliberately exercise the paid route must unlock it explicitly."""

    def setUp(self):
        self._paid_env = os.environ.get("MONARCH_ALLOW_PAID")
        os.environ["MONARCH_ALLOW_PAID"] = "1"

    def tearDown(self):
        if self._paid_env is None:
            os.environ.pop("MONARCH_ALLOW_PAID", None)
        else:
            os.environ["MONARCH_ALLOW_PAID"] = self._paid_env


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


class PlanTests(AllowPaidMixin, unittest.TestCase):
    def test_free_route_is_zero_cost_and_adds_lipsync_for_hero(self):
        with tempfile.TemporaryDirectory() as td:
            plan = vg.build_plan(json.loads(make_project(pathlib.Path(td), route="free").read_text()),
                                 has_key=False)
            self.assertEqual(plan["estimate_usd"], 0.0)
            hero = next(e for e in plan["shots"] if e["kind"] == "hero")
            self.assertEqual([s["engine"] for s in hero["steps"]],
                             ["wan", "latentsync", "mmaudio", "upscale"])
            plate = next(e for e in plan["shots"] if e["kind"] == "plate")
            self.assertEqual([s["engine"] for s in plate["steps"]], ["wan", "mmaudio", "upscale"])
            self.assertEqual(plan["delivery"]["out_height"], 1664)

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


class RenderTests(AllowPaidMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
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

    def test_verify_rejects_empty_files(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            data = json.loads(path.read_text())
            for shot in data["shots"]:
                (path.parent / "shots" / f"{shot['id']}.mp4").write_bytes(b"")
            with mock.patch.object(vg, "which", lambda binary: None):
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


class MobileTests(unittest.TestCase):
    """The owner is on a phone: one notebook, one Run all, prompts baked in."""

    def _notebook(self, path):
        return json.loads((path.parent / "mobile" / "MOBILE_p1.ipynb").read_text())

    def test_mobile_writes_one_notebook(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            with mock.patch("builtins.print"):
                self.assertEqual(vg.mobile(path), 0)
            notebooks = list((path.parent / "mobile").glob("*.ipynb"))
            self.assertEqual(len(notebooks), 1)
            nb = self._notebook(path)
            self.assertEqual(nb["nbformat"], 4)
            self.assertEqual(sum(1 for c in nb["cells"] if c["cell_type"] == "code"), 7)

    def test_notebook_quantises_the_text_encoder(self):
        """22.7 GB UMT5 crashes Colab's 12.7 GB RAM: it must be loaded 4-bit."""
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            with mock.patch("builtins.print"):
                vg.mobile(path)
            source = "".join(self._notebook(path)["cells"][2]["source"])
            self.assertIn("load_in_4bit=True", source)
            self.assertIn("nf4", source)
            self.assertIn("HF_HUB_DISABLE_XET", source)
            self.assertIn("malloc_trim", source)
            self.assertIn("low_cpu_mem_usage=True", source)
            self.assertIn("UniPCMultistepScheduler", source)
            self.assertIn("flow_shift=3.0", source)

    def test_clips_release_the_pipeline_before_upscale(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            with mock.patch("builtins.print"):
                vg.mobile(path)
            clips = "".join(self._notebook(path)["cells"][3]["source"])
            self.assertIn("del pipe", clips)
            self.assertIn("free_mem", clips)

    def test_upscale_has_an_ffmpeg_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            with mock.patch("builtins.print"):
                vg.mobile(path)
            upscale = "".join(self._notebook(path)["cells"][-2]["source"])
            self.assertIn("flags=lanczos", upscale)
            self.assertIn("enhancer is None", upscale)

    def test_max_frames_caps_every_shot(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            for shot in json.loads(path.read_text())["shots"]:
                shot["seconds"] = 5
            data = json.loads(path.read_text())
            for shot in data["shots"]:
                shot["seconds"] = 5
            path.write_text(json.dumps(data, indent=2))
            with mock.patch("builtins.print"):
                vg.mobile(path, max_frames=33)
            source = "".join(self._notebook(path)["cells"][1]["source"])   # JOBS live in the config cell
            frames = [int(line.split(":")[1].strip().rstrip(","))
                      for line in source.splitlines() if '"frames"' in line]
            self.assertTrue(frames and all(f <= 33 for f in frames), frames)
            self.assertTrue(all((f - 1) % 4 == 0 for f in frames), frames)

    def test_one_cell_mode_is_a_single_play_button(self):
        """A phone shows one play button per cell: collapse everything into one."""
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            with mock.patch("builtins.print"):
                vg.mobile(path, one_cell=True)
            nb = self._notebook(path)
            code = [c for c in nb["cells"] if c["cell_type"] == "code"]
            self.assertEqual(len(code), 1)
            source = "".join(code[0]["source"])
            for stage in ("RUN_CLIPS", "JOBS", "Wan2.1-T2V-1.3B-Diffusers", "_outputs.zip", "DONE"):
                self.assertIn(stage, source)

    def test_one_cell_keeps_the_markdown_intro(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            with mock.patch("builtins.print"):
                vg.mobile(path, one_cell=True)
            nb = self._notebook(path)
            self.assertEqual(nb["cells"][0]["cell_type"], "markdown")

    def test_notebook_survives_a_failed_drive_mount(self):
        """Drive auth fails on phones routinely: the notebook must fall back, not crash."""
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            with mock.patch("builtins.print"):
                vg.mobile(path)
            nb = self._notebook(path)
            config = "".join(nb["cells"][1]["source"])
            self.assertIn("LOCAL_BASE", config)
            self.assertIn("except Exception", config)
            self.assertIn("BASE = DRIVE_BASE if DRIVE_OK else LOCAL_BASE", config)
            summary = "".join(nb["cells"][-1]["source"])
            self.assertIn("_outputs.zip", summary)
            self.assertIn("colab_files.download", summary)
            self.assertIn("DONE", summary)

    def test_notebook_code_cells_compile(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            with mock.patch("builtins.print"):
                vg.mobile(path)
            for index, cell in enumerate(self._notebook(path)["cells"]):
                if cell["cell_type"] != "code":
                    continue
                lines = []
                for line in "".join(cell["source"]).splitlines():
                    if line.lstrip().startswith(("!", "%")):
                        indent = line[:len(line) - len(line.lstrip())]
                        lines.append(f"{indent}pass  # {line.strip()[1:]}")
                    else:
                        lines.append(line)
                compile("\n".join(lines), f"<cell{index}>", "exec")   # raises on syntax error

    def test_jobs_and_text_are_baked_in(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            data = json.loads(path.read_text())
            data["shots"][0]["vo_text"] = "hook line"
            data["shots"][1]["foley_prompt"] = "wind over concrete"
            path.write_text(json.dumps(data, indent=2))
            with mock.patch("builtins.print"):
                vg.mobile(path)
            text = "\n".join("".join(c["source"]) for c in self._notebook(path)["cells"])
            self.assertIn('"s01-hook"', text)
            self.assertIn("hook line", text)
            self.assertIn("wind over concrete", text)
            self.assertIn("05 · Projects/{PROJECT}", text)
            self.assertIn("DONE ✅", text)
            self.assertIn("RUN_CLIPS", text)
            self.assertNotIn("TODO: put your job list", text)

    def test_jobs_use_the_free_frame_size_and_4k_plus_1(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            with mock.patch("builtins.print"):
                vg.mobile(path)
            cfg = "".join(self._notebook(path)["cells"][1]["source"])
            start = cfg.index("JOBS = [")
            jobs = json.loads(cfg[start + len("JOBS = "):cfg.index("\n]", start) + 2])
            self.assertEqual(len(jobs), 3)
            for job in jobs:
                self.assertEqual((job["width"], job["height"]), (480, 832))
                self.assertEqual((job["frames"] - 1) % 4, 0)
                self.assertGreaterEqual(job["frames"], 17)

    def test_receipts_record_the_mobile_run(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            with mock.patch("builtins.print"):
                vg.mobile(path)
            receipts = json.loads((path.parent / "receipts.json").read_text())
            self.assertEqual(receipts["mobile"]["mode"], "phone_run_all")
            self.assertEqual(receipts["mobile"]["shots"], 3)

    def test_mobile_cli_exit_zero(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            with mock.patch("builtins.print"):
                self.assertEqual(vg.main(["mobile", str(path)]), 0)


class ProbeFallbackTests(unittest.TestCase):
    """No ffprobe on this box: probe() must parse `ffmpeg -i` instead of giving up."""

    def test_which_finds_static_ffmpeg_or_none(self):
        resolved = vg.which("ffmpeg")
        self.assertTrue(resolved is None or pathlib.Path(resolved).exists())

    def test_probe_parses_ffmpeg_output(self):
        stderr = (
            "Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'clip.mp4':\n"
            "  Duration: 00:00:05.00, start: 0.000000, bitrate: 128 kb/s\n"
            "  Stream #0:0[0x1](und): Video: h264 (High), yuv420p, 480x832 [SAR 1:1 DAR 15:26], "
            "24 fps, 24 tbr, 12288 tbn\n"
            "  Stream #0:1[0x2](und): Audio: aac (LC), 44100 Hz, stereo, fltp\n"
        )
        with mock.patch.object(vg, "which", lambda b: None if b == "ffprobe" else "/usr/bin/ffmpeg"), \
             mock.patch.object(vg.subprocess, "run",
                               lambda *a, **k: mock.Mock(returncode=1, stdout="", stderr=stderr)):
            info = vg.probe(pathlib.Path("/tmp/clip.mp4"))
        self.assertTrue(info["available"])
        self.assertEqual((info["width"], info["height"]), (480, 832))
        self.assertEqual(info["fps"], 24.0)
        self.assertEqual(info["duration"], 5.0)
        self.assertEqual(info["video_codec"], "h264")
        self.assertEqual(info["audio_codec"], "aac")
        self.assertEqual(info["probe"], "ffmpeg -i")

    def test_probe_reports_no_binary_at_all(self):
        with mock.patch.object(vg, "which", lambda b: None):
            self.assertEqual(vg.probe(pathlib.Path("/tmp/x.mp4")), {"available": False})


class FreeOnlyTests(unittest.TestCase):
    """Zero-spend mode: the tool must be incapable of billing by accident."""

    def setUp(self):
        self._env = {k: os.environ.get(k) for k in ("MONARCH_FREE_ONLY", "MONARCH_ALLOW_PAID")}
        for key in self._env:
            os.environ.pop(key, None)

    def tearDown(self):
        for key, value in self._env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_default_is_free_only(self):
        self.assertTrue(vg.free_only())
        os.environ["MONARCH_FREE_ONLY"] = "0"
        self.assertFalse(vg.free_only())
        os.environ.pop("MONARCH_FREE_ONLY")
        os.environ["MONARCH_ALLOW_PAID"] = "1"
        self.assertFalse(vg.free_only())

    def test_paid_project_is_rewritten_to_the_free_chain(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="paid")
            data = json.loads(path.read_text())
            plan = vg.build_plan(data, has_key=True)
            self.assertTrue(plan["free_only"])
            self.assertEqual(plan["estimate_usd"], 0.0)
            self.assertEqual(plan["paid_step_count"], 0)
            self.assertGreater(plan["blocked_paid"], 0)
            self.assertTrue(any("free-only mode" in w for w in plan["warnings"]))
            engines = {s["engine"] for e in plan["shots"] for s in e["steps"]}
            self.assertNotIn("h3", engines)
            self.assertIn("wan", engines)

    def test_allow_paid_restores_h3(self):
        os.environ["MONARCH_ALLOW_PAID"] = "1"
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="paid")
            plan = vg.build_plan(json.loads(path.read_text()), has_key=True)
            self.assertFalse(plan["free_only"])
            self.assertGreater(plan["estimate_usd"], 0)

    def test_render_never_spends_in_free_mode(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="paid")
            with mock.patch("builtins.print") as printed, \
                 mock.patch.object(vg, "render_h3") as h3:
                vg.render(path, confirm=True)
            self.assertFalse(h3.called)
            out = " ".join(str(c.args[0]) for c in printed.call_args_list if c.args)
            self.assertIn("FREE-ONLY MODE", out)

    def test_compute_menu_lists_card_free_providers_only(self):
        menu = vg.free_compute()
        self.assertTrue(menu["providers"])
        self.assertTrue(all(p["card_required"] is False for p in menu["providers"]))
        excluded = {row["id"] for row in menu["excluded_on_purpose"]}
        self.assertIn("modal", excluded)
        self.assertIn("minimax_h3_api", excluded)

    def test_kaggle_limit_is_read_from_the_menu(self):
        self.assertEqual(vg.quota_limits().get("kaggle"), 30.0)
        self.assertNotIn("colab_free", vg.quota_limits())

    def test_quota_use_and_report(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = pathlib.Path(td) / "free_quota.json"
            with mock.patch.object(vg, "FREE_QUOTA", ledger):
                state = vg.quota_use("kaggle", 1.5, "reel-01 batch")
                self.assertEqual(state["used"]["kaggle"], 1.5)
                vg.quota_use("kaggle", 2)
                rows = {r["id"]: r for r in vg.quota_report()}
                self.assertEqual(rows["kaggle"]["used"], 3.5)
                self.assertEqual(rows["kaggle"]["left"], 26.5)
                self.assertIsNone(rows["colab_free"]["limit"])
                self.assertEqual(state["week"], vg._iso_week())

    def test_quota_rejects_unknown_provider_and_bad_hours(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = pathlib.Path(td) / "free_quota.json"
            with mock.patch.object(vg, "FREE_QUOTA", ledger):
                with self.assertRaises(vg.EngineError):
                    vg.quota_use("some_gpu_shop", 1)
                with self.assertRaises(vg.EngineError):
                    vg.quota_use("kaggle", 0)

    def test_quota_rolls_over_to_a_new_week(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = pathlib.Path(td) / "free_quota.json"
            ledger.write_text(json.dumps({"week": "1999-W01", "used": {"kaggle": 30.0}, "log": []}))
            with mock.patch.object(vg, "FREE_QUOTA", ledger):
                state = vg.quota_state()
                self.assertEqual(state["week"], vg._iso_week())
                self.assertEqual(state["used"], {})

    def test_doctor_prints_free_mode_and_quota(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = pathlib.Path(td) / "free_quota.json"
            with mock.patch.object(vg, "FREE_QUOTA", ledger), mock.patch("builtins.print") as printed:
                self.assertEqual(vg.doctor(), 0)
            out = "".join(str(c.args[0]) for c in printed.call_args_list if c.args)
            self.assertIn("free-only mode", out)
            self.assertIn("free compute menu", out)
            self.assertIn("kaggle quota", out)


class AudioTests(unittest.TestCase):
    """Free audio stack: voice + foley + bed, and the honest licence lines."""

    def _project(self, td, **audio):
        path = make_project(pathlib.Path(td), route="free")
        data = json.loads(path.read_text())
        data["audio"] = {**(data.get("audio") or {}), **audio}
        path.write_text(json.dumps(data, indent=2))
        return path, json.loads(path.read_text())

    def test_defaults_are_the_free_stack(self):
        with tempfile.TemporaryDirectory() as td:
            _, project = self._project(td)
            cfg = vg.audio_config(project)
            self.assertEqual((cfg["vo_engine"], cfg["foley_engine"], cfg["bed_engine"]),
                             ("kokoro", "mmaudio", "musicgen"))
            self.assertTrue(cfg["mix"])

    def test_bad_engine_is_a_user_error(self):
        with tempfile.TemporaryDirectory() as td:
            _, project = self._project(td, vo_engine="elevenlabs")
            with self.assertRaises(vg.EngineError):
                vg.audio_config(project)

    def test_stems_follow_text_and_engines(self):
        with tempfile.TemporaryDirectory() as td:
            _, project = self._project(td, foley_engine="off")
            shot = project["shots"][0]
            shot["vo_text"] = "line one"
            stems = vg.audio_stems(project, shot)
            self.assertEqual(list(stems), ["vo"])
            self.assertEqual(stems["vo"]["file"], "audio/vo/s01-hook.wav")
            self.assertEqual(stems["vo"]["engine"], "kokoro")

    def test_dialogue_list_supplies_text(self):
        with tempfile.TemporaryDirectory() as td:
            _, project = self._project(td, dialogue=[{"shot": "s02-plate", "text": "plate line"}])
            self.assertEqual(vg.shot_vo_text(project, project["shots"][1]), "plate line")
            self.assertEqual(vg.shot_vo_text(project, project["shots"][0]), "")

    def test_non_commercial_weights_are_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            _, project = self._project(td)
            warns = " ".join(vg.audio_licence_warnings(project))
            self.assertIn("NON-COMMERCIAL", warns)
            self.assertIn("mmaudio", warns)
            with tempfile.TemporaryDirectory() as td2:
                _, apache = self._project(td2, foley_engine="thinksound", bed_engine="off")
                self.assertFalse(any("foley" in w for w in vg.audio_licence_warnings(apache)))

    def test_audio_notebook_has_voice_foley_and_bed(self):
        with tempfile.TemporaryDirectory() as td:
            path, _ = self._project(td)
            with mock.patch("builtins.print"):
                self.assertEqual(vg.audio(path), 0)
            nb_file = path.parent / "audio" / "AUDIO_p1.ipynb"
            nb = json.loads(nb_file.read_text())
            text = "\n".join("".join(c["source"]) for c in nb["cells"])
            self.assertIn("KPipeline", text)
            self.assertIn("MMAudio", text)
            self.assertIn("musicgen", text)
            self.assertIn("05 · Projects/p1", text)
            self.assertIn("CC-BY-NC", text)
            receipts = json.loads((path.parent / "receipts.json").read_text())
            self.assertEqual(receipts["audio"]["engines"]["vo_engine"], "kokoro")

    def test_chatterbox_clone_variant_replaces_kokoro_cell(self):
        with tempfile.TemporaryDirectory() as td:
            path, _ = self._project(td, vo_engine="chatterbox")
            with mock.patch("builtins.print"):
                vg.audio(path)
            text = "\n".join("".join(c["source"]) for c in
                             json.loads((path.parent / "audio" / "AUDIO_p1.ipynb").read_text())["cells"])
            self.assertIn("ChatterboxTTS", text)
            self.assertIn("voice_ref.wav", text)
            self.assertNotIn("KPipeline", text)

    def test_mix_graph_ducks_the_bed_under_dialogue(self):
        inputs, graph, amap = vg.mix_graph(True, True, True, bed_gain_db=-6.0)
        self.assertEqual(amap, "[aout]")
        self.assertIn("sidechaincompress", graph)
        self.assertIn("[vo][fo]amix=inputs=2:normalize=0[dia0]", graph)
        self.assertIn("volume=-6.0dB", graph)
        self.assertEqual(inputs.count("-i"), 3)

    def test_mix_graph_splits_dialogue_before_the_ducker(self):
        """An ffmpeg filter output may only be consumed once — hence asplit."""
        _, graph, _ = vg.mix_graph(True, False, True)
        self.assertIn("asplit=2[dia][diaside]", graph)
        self.assertIn("[bed][diaside]sidechaincompress", graph)
        self.assertIn("[dia][bedduck]amix", graph)

    def test_mix_graph_loudnorm_lands_inside_the_graph(self):
        _, graph, amap = vg.mix_graph(True, False, True, loudnorm=True)
        self.assertIn("loudnorm=I=-16:TP=-1.5:LRA=11[aout]", graph)
        self.assertEqual(amap, "[aout]")
        self.assertEqual(graph.count("[aout]"), 1)
        _, plain, _ = vg.mix_graph(True, False, True)
        self.assertNotIn("loudnorm", plain)

    def test_mix_graph_without_bed_has_no_ducking(self):
        _, graph, amap = vg.mix_graph(False, True, False)
        self.assertNotIn("sidechaincompress", graph)
        self.assertEqual(amap, "[aout]")

    def test_mix_graph_with_nothing_returns_empty(self):
        self.assertEqual(vg.mix_graph(False, False, False), ([], "", ""))

    def test_mix_writes_a_mixed_variant(self):
        with tempfile.TemporaryDirectory() as td:
            path, project = self._project(td)
            project["shots"][0]["vo_text"] = "line one"
            path.write_text(json.dumps(project, indent=2))
            shots = path.parent / "shots"
            (shots / "s01-hook.mp4").write_bytes(b"video")
            (path.parent / "audio" / "vo").mkdir(parents=True, exist_ok=True)
            (path.parent / "audio" / "vo" / "s01-hook.wav").write_bytes(b"vo")
            (path.parent / "audio" / "bed.wav").write_bytes(b"bed")

            seen = {}

            def fake_run(cmd, **kwargs):
                seen["cmd"] = cmd
                pathlib.Path(cmd[-1]).write_bytes(b"mixed")
                return mock.Mock(returncode=0, stderr="", stdout="")

            with mock.patch.object(vg, "which", lambda b: "/usr/bin/" + b), \
                 mock.patch.object(vg, "subprocess") as sp:
                sp.run.side_effect = fake_run
                code = vg.mix(path)
            self.assertEqual(code, 3)          # shots 2 and 3 still have no media
            self.assertTrue((shots / "s01-hook-mix.mp4").exists())
            self.assertIn("sidechaincompress", " ".join(seen["cmd"]))
            receipts = json.loads((path.parent / "receipts.json").read_text())
            self.assertEqual(receipts["mix"]["s01-hook"]["status"], "mixed")

    def test_mix_without_stems_is_an_honest_error(self):
        with tempfile.TemporaryDirectory() as td:
            path, project = self._project(td)
            for shot in project["shots"]:
                (path.parent / "shots" / f"{shot['id']}.mp4").write_bytes(b"video")
            with mock.patch.object(vg, "which", lambda b: "/usr/bin/" + b):
                with self.assertRaises(vg.EngineError):
                    vg.mix(path)

    def test_shot_media_prefers_the_mixed_variant(self):
        with tempfile.TemporaryDirectory() as td:
            path, _ = self._project(td)
            shots = path.parent / "shots"
            (shots / "s01-hook.mp4").write_bytes(b"plain")
            (shots / "s01-hook-2x.mp4").write_bytes(b"up")
            (shots / "s01-hook-2x-mix.mp4").write_bytes(b"upmixed")
            self.assertEqual(vg.shot_media({"id": "s01-hook"}, vg.project_paths(path)).name,
                             "s01-hook-2x-mix.mp4")

    def test_verify_flags_a_file_with_stems_but_no_audio(self):
        with tempfile.TemporaryDirectory() as td:
            path, _ = self._project(td)
            (path.parent / "shots" / "s01-hook.mp4").write_bytes(b"m")
            (path.parent / "shots" / "s02-plate.mp4").write_bytes(b"m")
            (path.parent / "shots" / "s03-payoff.mp4").write_bytes(b"m")
            (path.parent / "audio" / "vo").mkdir(parents=True)
            (path.parent / "audio" / "vo" / "s01-hook.wav").write_bytes(b"vo")
            with mock.patch.object(vg, "which", lambda b: "/usr/bin/" + b), \
                 mock.patch.object(vg, "probe", lambda p: {"available": True, "width": 480, "height": 832,
                                                           "fps": 24.0, "duration": 5.0,
                                                           "video_codec": "h264", "audio_codec": None}):
                self.assertEqual(vg.verify(path), 3)

    def test_plan_carries_voice_and_foley_for_free_shots(self):
        with tempfile.TemporaryDirectory() as td:
            path, project = self._project(td)
            project["shots"][0]["vo_text"] = "hello"
            plan = vg.build_plan(project, has_key=False)
            engines = [s["engine"] for s in plan["shots"][0]["steps"]]
            self.assertIn("kokoro", engines)
            self.assertIn("mmaudio", engines)
            self.assertEqual(plan["estimate_usd"], 0.0)
            self.assertTrue(any("NON-COMMERCIAL" in w for w in plan["warnings"]))

    def test_paid_shots_do_not_queue_free_voice(self):
        with tempfile.TemporaryDirectory() as td:
            path, project = self._project(td)
            project["route"] = "paid"
            project["shots"][0]["vo_text"] = "hello"
            with mock.patch.dict(os.environ, {"MONARCH_ALLOW_PAID": "1"}):
                plan = vg.build_plan(project, has_key=True)
            engines = [s["engine"] for s in plan["shots"][0]["steps"]]
            self.assertEqual(engines, ["h3"])


class QualityTests(unittest.TestCase):
    """The free route renders 480p — the quality ladder must be explicit, not wishful."""

    def test_free_frames_match_the_queue(self):
        for aspect, (width, height) in vg.FREE_FRAMES.items():
            self.assertEqual((width, height), (width // 16 * 16, height // 16 * 16))
        self.assertEqual(vg.free_frame_size("9:16"), (480, 832))
        self.assertEqual(vg.free_frame_size("made-up"), (480, 832))

    def test_upscale_target_maths(self):
        project = {"aspect": "9:16", "delivery": {"upscale": "realesrgan", "factor": 2}}
        up = vg.upscale_target(project)
        self.assertEqual((up["in_width"], up["in_height"]), (480, 832))
        self.assertEqual((up["out_width"], up["out_height"]), (960, 1664))
        self.assertTrue(up["gpu"])
        off = vg.upscale_target({"aspect": "9:16", "delivery": {"upscale": "off"}})
        self.assertEqual(off["factor"], 1)
        self.assertEqual(off["out_height"], 832)
        lanczos = vg.upscale_target({"aspect": "16:9", "delivery": {"upscale": "lanczos"}})
        self.assertFalse(lanczos["gpu"])
        self.assertEqual(lanczos["engine"], "lanczos")

    def test_plan_warns_when_target_height_beats_the_free_route(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            data = json.loads(path.read_text())
            data["delivery"] = {"upscale": "lanczos", "factor": 2, "target_height": 1920}
            path.write_text(json.dumps(data, indent=2))
            plan = vg.build_plan(json.loads(path.read_text()), has_key=False)
            self.assertFalse(plan["delivery"]["meets_target"])
            self.assertTrue(any("target_height is 1920p" in w for w in plan["warnings"]))
            self.assertTrue(any("scale, not detail" in w for w in plan["warnings"]))

    def test_plan_is_honest_when_target_is_reachable(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            data = json.loads(path.read_text())
            data["delivery"] = {"upscale": "realesrgan", "factor": 2, "target_height": 1664}
            path.write_text(json.dumps(data, indent=2))
            plan = vg.build_plan(json.loads(path.read_text()), has_key=False)
            self.assertTrue(plan["delivery"]["meets_target"])
            self.assertFalse(any("target_height is" in w for w in plan["warnings"]))

    def test_upscale_writes_a_runnable_notebook(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            with mock.patch("builtins.print"):
                self.assertEqual(vg.upscale(path), 0)
            notebooks = list((path.parent / "upscale").glob("UPSCALE_*.ipynb"))
            self.assertEqual(len(notebooks), 1)
            nb = json.loads(notebooks[0].read_text())
            self.assertEqual(nb["nbformat"], 4)
            text = "\n".join("".join(cell["source"]) for cell in nb["cells"])
            self.assertIn("RealESRGANer", text)
            self.assertIn("05 · Projects/p1", text)
            self.assertIn("sharper, magar naya detail nahi", text)
            receipts = json.loads((path.parent / "receipts.json").read_text())
            self.assertEqual(receipts["upscale"]["factor"], 2)
            self.assertEqual(receipts["upscale"]["out"], [960, 1664])

    def test_upscale_lanczos_needs_no_gpu(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            with mock.patch("builtins.print"):
                self.assertEqual(vg.upscale(path, engine="lanczos", factor=2, only=["s02-plate"]), 0)
            nb_file = next((path.parent / "upscale").glob("*lanczos*.ipynb"))
            text = "\n".join("".join(c["source"]) for c in json.loads(nb_file.read_text())["cells"])
            self.assertIn("flags=lanczos", text)
            self.assertNotIn("RealESRGANer", text)
            self.assertIn('["s02-plate"]', text)

    def test_upscale_rejects_unknown_shots_and_off(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            with self.assertRaises(vg.EngineError):
                vg.upscale(path, only=["nope"])
            with self.assertRaises(vg.EngineError):
                vg.upscale(path, engine="off")

    def test_shot_media_prefers_the_upscaled_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free", template="hero-test")
            shots = path.parent / "shots"
            (shots / "s01-hero.mp4").write_bytes(b"silent")
            (shots / "s01-hero-talk.mp4").write_bytes(b"talk")
            (shots / "s01-hero-talk-2x.mp4").write_bytes(b"talk-2x")
            self.assertEqual(vg.shot_media({"id": "s01-hero"}, vg.project_paths(path)).name,
                             "s01-hero-talk-2x.mp4")

    def test_verify_enforces_target_height(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free", template="hero-test")
            data = json.loads(path.read_text())
            data["delivery"] = {"upscale": "realesrgan", "factor": 2, "target_height": 1920}
            path.write_text(json.dumps(data, indent=2))
            (path.parent / "shots" / "s01-hero.mp4").write_bytes(b"media")
            with mock.patch.object(vg, "which", lambda binary: "/usr/bin/" + binary), \
                 mock.patch.object(vg, "probe", lambda p: {"available": True, "width": 960, "height": 1664,
                                                           "fps": 24.0, "duration": 5.0,
                                                           "video_codec": "h264", "audio_codec": "aac"}):
                self.assertEqual(vg.verify(path), 3)

    def test_validate_rejects_nonsense_delivery(self):
        with tempfile.TemporaryDirectory() as td:
            path = make_project(pathlib.Path(td), route="free")
            data = json.loads(path.read_text())
            data["delivery"] = {"upscale": "magic", "factor": 3, "target_height": -5}
            problems = vg.validate_project(data, path)
            self.assertTrue(any("delivery.upscale" in p for p in problems))
            self.assertTrue(any("delivery.factor" in p for p in problems))
            self.assertTrue(any("delivery.target_height" in p for p in problems))


class DriveHomeTests(unittest.TestCase):
    """WF-07 delivery home must stay wired to the user's Drive folder."""

    def test_config_has_the_user_folder(self):
        cfg = vg.drive_config()
        self.assertEqual(cfg["root"]["id"], "1IBgfHFdigeDzaYkJuNoelhLiWLqRZ6d1")
        self.assertIn("Wf-07", cfg["root"]["name"])
        self.assertEqual(set(cfg["subfolders"]),
                         {"start_here", "engine", "notebooks", "knowledge", "projects", "masters"})

    def test_targets_point_at_projects_and_masters(self):
        dest = vg.drive_targets("monarch-reel-01")
        self.assertEqual(dest["project_folder"], "05 · Projects/monarch-reel-01/")
        self.assertEqual(dest["master_folder"], "06 · Masters & Receipts/")
        self.assertTrue(dest["projects_id"] and dest["masters_id"])
        self.assertIn("drive.google.com", dest["url"])

    def test_doctor_reports_the_drive_home(self):
        with mock.patch("builtins.print") as printed:
            self.assertEqual(vg.doctor(), 0)
        out = "".join(str(c.args[0]) for c in printed.call_args_list if c.args)
        self.assertIn("WF-07 drive home", out)

    def test_missing_config_is_not_a_crash(self):
        with mock.patch.object(vg, "DRIVE_CONFIG", pathlib.Path("/tmp/nope-drive.json")):
            self.assertEqual(vg.drive_config(), {})
            self.assertEqual(vg.drive_targets("x")["root"], "Wf-07 • Monarch Ai Agent")


if __name__ == "__main__":
    unittest.main()
