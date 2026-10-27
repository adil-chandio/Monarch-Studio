from __future__ import annotations
import base64, json, os, pathlib, sys, tempfile, unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
STYLE = ROOT / "styles/minimax-h3-video"
sys.path.insert(0, str(STYLE / "src"))
import h3_client as h3  # noqa: E402


def shot(**kw):
    base = {"id": "shot-01", "model": "MiniMax-H3", "resolution": "768P", "duration": 5,
            "ratio": "16:9", "prompt": "integrated_multimodal_description: [Shot 1] test"}
    base.update(kw)
    return base


class PayloadTests(unittest.TestCase):
    def test_text_to_video_requires_concrete_ratio(self):
        p = h3.build_payload(shot())
        self.assertEqual(p["ratio"], "16:9")
        self.assertEqual(p["content"], [{"type": "text", "text": shot()["prompt"]}])
        with self.assertRaises(h3.ConfigError):
            h3.build_payload(shot(ratio=None))
        with self.assertRaises(h3.ConfigError):
            h3.build_payload(shot(ratio="adaptive"))

    def test_keyframe_and_reference_are_mutually_exclusive(self):
        with tempfile.TemporaryDirectory() as td:
            img = pathlib.Path(td) / "frame.png"
            img.write_bytes(b"\x89PNG\r\n\x1a\nnot-really-a-png")
            h3.build_payload(shot(first_frame=str(img)))            # keyframe alone is fine
            h3.build_payload(shot(references=[str(img)]))           # reference alone is fine
            with self.assertRaises(h3.ConfigError):
                h3.build_payload(shot(first_frame=str(img), references=[str(img)]))

    def test_keyframe_forces_adaptive_ratio(self):
        p = h3.build_payload(shot(first_frame="https://example.com/a.png", ratio="9:16"))
        self.assertEqual(p["ratio"], "adaptive")

    def test_roles_are_labelled(self):
        p = h3.build_payload(shot(
            references=["https://example.com/1.png", "https://example.com/2.png"],
            reference_audio=["https://example.com/voice.mp3"],
            last_frame=None,
        ))
        roles = [c.get("role") for c in p["content"][1:]]
        self.assertEqual(roles, ["reference_image", "reference_image", "reference_audio"])

    def test_duration_and_resolution_guards(self):
        for bad in (3, 16):
            with self.subTest(duration=bad), self.assertRaises(h3.ConfigError):
                h3.build_payload(shot(duration=bad))
        with self.assertRaises(h3.ConfigError):
            h3.build_payload(shot(resolution="4K"))                  # not an H3 resolution
        with self.assertRaises(h3.ConfigError):
            h3.build_payload(shot(model="MiniMax-H3-Lite", resolution="2K"))

    def test_reference_image_count_and_empty_prompt(self):
        refs = [f"https://example.com/{i}.png" for i in range(10)]
        with self.assertRaises(h3.ConfigError):
            h3.build_payload(shot(references=refs))
        with self.assertRaises(h3.ConfigError):
            h3.build_payload(shot(prompt="   "))


class CostTests(unittest.TestCase):
    def test_published_rates(self):
        self.assertAlmostEqual(h3.shot_cost(shot(duration=10, resolution="768P")), 0.80)
        self.assertAlmostEqual(h3.shot_cost(shot(duration=10, resolution="2K")), 1.30)
        self.assertAlmostEqual(h3.shot_cost(shot(duration=15, resolution="2K")), 1.95)
        self.assertIsNone(h3.shot_cost(shot(model="Unknown", resolution="768P")))

    def test_extra_images_are_billed_after_five(self):
        refs = [f"https://example.com/{i}.png" for i in range(7)]
        self.assertAlmostEqual(h3.shot_cost(shot(references=refs)), 5 * 0.08 + 2 * 0.04)

    def test_reference_video_seconds_are_billed(self):
        self.assertAlmostEqual(h3.shot_cost(shot(reference_video_seconds=4)), 9 * 0.08)

    def test_estimate_totals(self):
        shots = [shot(duration=5), shot(id="shot-02", duration=10, resolution="2K")]
        self.assertAlmostEqual(h3.estimate(shots), 0.40 + 1.30)


class FileTests(unittest.TestCase):
    def test_data_url_and_as_url(self):
        with tempfile.TemporaryDirectory() as td:
            img = pathlib.Path(td) / "a.png"
            img.write_bytes(b"abc")
            url = h3.data_url(img)
            self.assertTrue(url.startswith("data:image/png;base64,"))
            self.assertEqual(base64.b64decode(url.split(",", 1)[1]), b"abc")
            self.assertEqual(h3.as_url("https://x.example/y.png"), "https://x.example/y.png")
            with self.assertRaises(h3.ConfigError):
                h3.data_url(pathlib.Path(td) / "missing.png")

    def test_load_shots_rejects_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td) / "shots.json"
            p.write_text(json.dumps({"shots": [shot(), shot()]}))
            with self.assertRaises(h3.ConfigError):
                h3.load_shots(str(p))
            p.write_text(json.dumps({"shots": [shot(), shot(id="shot-02")]}))
            self.assertEqual(len(h3.load_shots(str(p))), 2)

    def test_example_shotlist_is_valid(self):
        shots = h3.load_shots(str(STYLE / "data/shotlist.example.json"))
        self.assertGreaterEqual(len(shots), 3)
        for spec in shots:
            with self.subTest(shot=spec["id"]):
                h3.build_payload(spec, resolve_files=False)   # example must never fail validation


class FlowTests(unittest.TestCase):
    def test_run_shot_records_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td)
            created = {}

            def fake_request(method, url, key, payload=None, timeout=120):
                if method == "POST":
                    created["payload"] = payload
                    return {"task_id": "4242"}
                return {"task": {"status": "succeeded", "ratio": "16:9",
                                 "usage": {"output_seconds": 5},
                                 "content": {"url": "https://cdn.example/shot.mp4"}}}

            def fake_download(url, dest):
                dest.write_bytes(b"fake-mp4-bytes")
                return dest

            with mock.patch.object(h3, "_request", fake_request), \
                 mock.patch.object(h3, "download", fake_download), \
                 mock.patch.object(h3.time, "sleep", lambda *_: None):
                receipt = h3.run_shot(shot(), "test-key", out, timeout=5)

            self.assertEqual(receipt["task_id"], "4242")
            self.assertEqual(receipt["usage"]["output_seconds"], 5)
            self.assertEqual(receipt["bytes"], len(b"fake-mp4-bytes"))
            self.assertEqual(receipt["md5"], h3.md5(out / "shot-01.mp4"))
            self.assertEqual(created["payload"]["model"], "MiniMax-H3")

    def test_poll_surfaces_failure(self):
        with mock.patch.object(h3, "query_task", lambda t, k: {"status": "failed", "id": t}):
            with self.assertRaises(h3.TaskError):
                h3.poll("1", "k", timeout=1, interval=0)

    def test_cli_dry_run_needs_no_key(self):
        env = {k: v for k, v in os.environ.items() if k != "MINIMAX_API_KEY"}
        with mock.patch.dict(os.environ, env, clear=True):
            rc = h3.main(["run", str(STYLE / "data/shotlist.example.json")])
        self.assertEqual(rc, 0)

    def test_cli_run_without_key_exits_2(self):
        env = {k: v for k, v in os.environ.items() if k != "MINIMAX_API_KEY"}
        with mock.patch.dict(os.environ, env, clear=True):
            rc = h3.main(["run", str(STYLE / "data/shotlist.example.json"), "--yes"])
        self.assertEqual(rc, 2)


class FreeRouteTests(unittest.TestCase):
    """The free T4 notebook must stay runnable and honest about its limits."""

    NOTEBOOK = STYLE / "colab/MONARCH_T4_FREE_BRIDGE.ipynb"

    def _nb(self):
        return json.loads(self.NOTEBOOK.read_text())

    def test_notebook_json_and_cells_compile(self):
        nb = self._nb()
        self.assertEqual(nb["metadata"]["accelerator"], "GPU")
        code_cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
        self.assertGreaterEqual(len(code_cells), 8)
        for i, cell in enumerate(code_cells):
            src = "\n".join(line for line in "".join(cell["source"]).splitlines()
                             if not line.strip().startswith("!"))
            compile(src, f"free-cell-{i}", "exec")   # raises on a syntax error

    def test_spend_and_tunnel_defaults_are_off(self):
        joined = self.NOTEBOOK.read_text()
        self.assertIn("TUNNEL_ENABLED = False", joined)
        self.assertIn("QUEUE_ENABLED = False", joined)
        self.assertNotIn("背景", joined)

    def test_free_notebook_uses_a_free_model_not_h3(self):
        joined = self.NOTEBOOK.read_text()
        self.assertIn("Wan-AI/Wan2.1-T2V-1.3B-Diffusers", joined)
        self.assertNotIn("api.minimax.io", joined)

    def test_free_jobs_example_is_valid(self):
        data = json.loads((STYLE / "data/free_jobs.example.json").read_text())
        jobs = data["jobs"]
        self.assertGreaterEqual(len(jobs), 3)
        ids = [j["id"] for j in jobs]
        self.assertEqual(len(ids), len(set(ids)))
        for job in jobs:
            with self.subTest(job=job["id"]):
                self.assertGreater(len(job["prompt"]), 40)
                self.assertEqual((int(job["frames"]) - 1) % 4, 0, "Wan needs num_frames = 4k+1")
                self.assertIn(int(job["width"]) % 16, (0,), "Wan wants width/height divisible by 16")
                self.assertIn(int(job["height"]) % 16, (0,))


class FreeDocsTests(unittest.TestCase):
    def test_free_routes_doc_states_h3_is_paid(self):
        text = (STYLE / "knowledge/05_FREE_ROUTES.md").read_text()
        self.assertIn("MiniMax-H3 free nahi hai", text)
        for needle in ["0.08", "0.13", "Colab ToS", "Wan 2.1 T2V 1.3B", "Drive-based job queue"]:
            with self.subTest(needle=needle):
                self.assertIn(needle, text)


sys.path.insert(0, str(STYLE / "src"))
import route_planner as rp  # noqa: E402


class ToolRegistryTests(unittest.TestCase):
    def setUp(self):
        self.reg = rp.load_registry()
        self.models = rp.models_by_id(self.reg)

    def test_every_model_is_complete_and_reachable(self):
        for m in self.reg["models"]:
            with self.subTest(model=m["id"]):
                self.assertIn(m["tier"], self.reg["tiers"])
                for key in ("name", "maker", "licence", "tasks", "native_audio", "vram_gb",
                            "speed_5s", "confidence", "best_for"):
                    self.assertIn(key, m)
                self.assertIsInstance(m["native_audio"], bool)

    def test_no_model_claims_audio_it_does_not_have(self):
        # only H3 (api/local) and LTX-2.5 ship native audio in this menu
        audio_models = {m["id"] for m in self.reg["models"] if m["native_audio"]}
        self.assertEqual(audio_models, {"minimax-h3-api", "minimax-h3-local", "ltx-25"})

    def test_t4_models_are_not_paid_and_fit_16gb(self):
        for m in self.reg["models"]:
            if m["tier"] == "t4_free":
                with self.subTest(model=m["id"]):
                    self.assertEqual(m["cost_usd_per_second"], 0)
                    self.assertLessEqual(m["vram_gb"], 16)

    def test_h3_api_rates_match_docs(self):
        h3 = self.models["minimax-h3-api"]
        self.assertEqual(h3["cost_usd_per_second"], {"768P": 0.08, "2K": 0.13})

    def test_local_h3_cannot_do_2k(self):
        self.assertEqual(self.models["minimax-h3-local"]["max_resolution"], "768P")


class RoutePlannerTests(unittest.TestCase):
    def test_every_need_has_a_plan(self):
        for need in rp.NEEDS:
            with self.subTest(need=need):
                plan = rp.build_plan(need, free=True, duration=15)
                self.assertEqual(plan["need"], need)
                self.assertTrue(plan["steps"])
                self.assertTrue(plan["models"])
                for mid in plan["models"]:
                    self.assertIn(mid, rp.models_by_id(rp.load_registry()))

    def test_free_plans_cost_nothing(self):
        for need in rp.NEEDS:
            with self.subTest(need=need):
                self.assertEqual(rp.build_plan(need, free=True, duration=30)["cost_usd"], 0.0)

    def test_paid_talking_hero_prices_both_resolutions(self):
        plan = rp.build_plan("talking_hero", free=False, duration=30)
        self.assertEqual(plan["cost_usd"], {"768P": 2.4, "2K": 3.9})

    def test_paid_cost_scales_with_duration(self):
        self.assertAlmostEqual(rp.paid_cost(rp.models_by_id(rp.load_registry())["minimax-h3-api"],
                                            "2K", 15), 1.95)

    def test_free_talking_plan_uses_the_lipsync_chain(self):
        plan = rp.build_plan("talking_hero", free=True, duration=10)
        self.assertIn("latentsync-15", plan["models"])
        self.assertIn("wan21-t2v-1.3b", plan["models"])
        self.assertTrue(any("LatentSync" in s for s in plan["steps"]))

    def test_shots_needed_rounds_up(self):
        self.assertEqual(rp.shots_needed(5), 1)
        self.assertEqual(rp.shots_needed(6), 2)
        self.assertEqual(rp.shots_needed(30), 6)

    def test_unknown_need_is_rejected(self):
        with self.assertRaises(ValueError):
            rp.build_plan("make_me_famous", free=True, duration=5)

    def test_licences_are_attached_to_each_plan(self):
        plan = rp.build_plan("broll_plate", free=True, duration=5)
        self.assertEqual(set(plan["licence_notes"]), set(plan["models"]))

    def test_cli_list_and_plan_exit_zero(self):
        self.assertEqual(rp.main(["list"]), 0)
        self.assertEqual(rp.main(["plan", "--need", "talking_hero", "--free", "--duration", "30"]), 0)
        self.assertEqual(rp.main(["plan", "--need", "lipsync_only", "--json"]), 0)


class NextLevelDocTests(unittest.TestCase):
    def test_doc_covers_free_talking_chain_and_tiers(self):
        text = (STYLE / "knowledge/06_NEXT_LEVEL_TOOLBOX.md").read_text()
        for needle in ["LatentSync 1.5", "Wan 2.1 T2V 1.3B", "HunyuanVideo 1.5", "LTX-2.5",
                       "free talking Monarch", "sm_75", "2K"]:
            with self.subTest(needle=needle):
                self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
