"""MOBILEOPS-1: the phone-only state machine must refuse to lie.

The owner taps three times; everything else is a gate. These tests pin the
refusals: no clips -> no finish, no master -> no deliver, no link -> no handoff.
"""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import mobile_ops as mo  # noqa: E402

PROJECT = {
    "project_id": "p-demo",
    "title": "Demo reel",
    "shots": [
        {"id": "s01-hook", "prompt": "hook", "vo_text": "yeh meri line hai"},
        {"id": "s02-plate", "prompt": "plate"},
    ],
}


def write_project(base: pathlib.Path) -> pathlib.Path:
    pdir = base / "p-demo"
    for extra in ("shots", "audio/vo", "audio/foley", "delivery", "mobile"):
        (pdir / extra).mkdir(parents=True, exist_ok=True)
    path = pdir / "project.json"
    path.write_text(json.dumps(PROJECT, indent=2))
    return path


def touch(path: pathlib.Path, size: int = 2048) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)


class OpsCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = pathlib.Path(self._tmp.name)
        self.jobs = self.base / "jobs"
        self.proj = write_project(self.base)
        self._patch = mock.patch.object(mo, "JOB_ROOT", self.jobs)
        self._patch.start()

    def tearDown(self):
        self._patch.stop()
        self._tmp.cleanup()

    def new_job(self) -> dict:
        with mock.patch("builtins.print"):
            return mo.start(str(self.proj), title="Demo reel", job_id="j1")

    def planned(self) -> dict:
        job = self.new_job()

        def runner(args):
            if args[0] == "plan":
                (self.proj.parent / "plan.json").write_text(json.dumps({
                    "estimate_usd": 0.0, "estimate_with_retries_usd": 0.0, "paid_step_count": 0,
                    "free_only": True, "warnings": [],
                    "delivery": {"free_width": 480, "free_height": 832,
                                 "out_width": 960, "out_height": 1664},
                    "shots": [{"steps": [{"engine": "wan"}, {"engine": "kokoro"}]}],
                }))
            if args[0] == "mobile":
                touch(self.proj.parent / "mobile" / "MOBILE_p-demo.ipynb", 100)
            return 0, "ok"

        return mo.plan(job["job_id"], runner=runner)

    def handed(self) -> dict:
        job = self.planned()
        return mo.handoff(job["job_id"], colab="https://colab.research.google.com/drive/abc")

    def with_clips(self, ids=("s01-hook", "s02-plate")) -> dict:
        for sid in ids:
            touch(self.proj.parent / "shots" / f"{sid}.mp4")
        return self.handed()


class StartTests(OpsCase):
    def test_start_lands_in_intake(self):
        job = self.new_job()
        self.assertEqual(job["state"], "intake")
        self.assertTrue((self.jobs / "j1.json").exists())
        self.assertEqual(job["voice_text"], "yeh meri line hai")
        self.assertEqual(job["shots"], ["s01-hook", "s02-plate"])

    def test_start_refuses_duplicate_without_force(self):
        self.new_job()
        with self.assertRaises(mo.OpsError):
            self.new_job()

    def test_start_force_overwrites(self):
        self.new_job()
        with mock.patch("builtins.print"):
            job = mo.start(str(self.proj), job_id="j1", force=True)
        self.assertEqual(job["state"], "intake")
        self.assertEqual(len(job["history"]), 1)

    def test_unknown_project_is_named(self):
        with self.assertRaises(mo.OpsError):
            mo.start("nope-not-here", job_id="jx")


class PlanTests(OpsCase):
    def test_plan_records_notebook_and_free_estimate(self):
        job = self.planned()
        self.assertEqual(job["state"], "planned")
        self.assertEqual(job["notebook"], "mobile/MOBILE_p-demo.ipynb" if not job["notebook"]
                         else job["notebook"])
        self.assertTrue(job["notebook"].endswith("MOBILE_p-demo.ipynb"))
        self.assertEqual(job["plan"]["total_usd"], 0.0)
        self.assertEqual(job["plan"]["paid_steps"], 0)
        self.assertEqual(job["plan"]["engines"], ["kokoro", "wan"])
        self.assertEqual(job["plan"]["delivery"]["out_height"], 1664)

    def test_plan_failure_blocks_with_the_real_error(self):
        job = self.new_job()
        with self.assertRaises(mo.OpsError):
            mo.plan(job["job_id"], runner=lambda args: (1, "boom: ffmpeg missing"))
        blocked = mo.load_job(job["job_id"])
        self.assertEqual(blocked["state"], "blocked")
        self.assertIn("boom", blocked["blocker"]["detail"])

    def test_plan_never_claims_a_notebook_it_did_not_write(self):
        job = self.new_job()

        def runner(args):
            return 0, "ok"

        planned = mo.plan(job["job_id"], runner=runner)
        self.assertIsNone(planned["notebook"])
        self.assertFalse(planned["gates"]["notebook"]["ok"])


class HandoffTests(OpsCase):
    def test_handoff_needs_a_real_colab_link(self):
        job = self.planned()
        with self.assertRaises(mo.OpsError):
            mo.handoff(job["job_id"], colab=None)

    def test_handoff_rejects_other_urls(self):
        job = self.planned()
        with self.assertRaises(mo.OpsError):
            mo.handoff(job["job_id"], colab="https://example.com/notebook")

    def test_handoff_card_has_no_cli_for_the_owner(self):
        job = self.handed()
        text = mo.card(job)
        for forbidden in ("python3", "pip install", "ffmpeg", "--", ".json"):
            self.assertNotIn(forbidden, text)
        self.assertIn("Run all", text)
        self.assertIn("colab.research.google.com", text)


class CheckTests(OpsCase):
    def test_no_clips_blocks_with_a_rerun_instruction(self):
        job = self.handed()
        checked = mo.check(job["job_id"])
        self.assertEqual(checked["state"], "blocked")
        self.assertIn("Run all", mo.card(checked))

    def test_partial_lists_missing_shots(self):
        job = self.with_clips(ids=("s01-hook",))
        checked = mo.check(job["job_id"])
        self.assertEqual(checked["state"], "partial")
        self.assertIn("s02-plate", mo.card(checked))

    def test_all_clips_make_it_clip_ready(self):
        job = self.with_clips()
        checked = mo.check(job["job_id"])
        self.assertEqual(checked["state"], "clip_ready")
        self.assertTrue(checked["gates"]["clips"]["ok"])

    def test_empty_file_is_not_a_clip(self):
        job = self.handed()
        touch(self.proj.parent / "shots" / "s01-hook.mp4", size=0)
        touch(self.proj.parent / "shots" / "s02-plate.mp4", size=0)
        checked = mo.check(job["job_id"])
        self.assertEqual(checked["state"], "blocked")

    def test_2x_clip_counts_as_the_shot(self):
        job = self.handed()
        touch(self.proj.parent / "shots" / "s01-hook-2x.mp4")
        touch(self.proj.parent / "shots" / "s02-plate-2x.mp4")
        self.assertEqual(mo.check(job["job_id"])["state"], "clip_ready")


class IngestTests(OpsCase):
    """Phone reality: Drive mount fails, the notebook hands back a ZIP."""

    def _zip(self, files: dict[str, int]) -> pathlib.Path:
        import zipfile
        target = self.base / "out.zip"
        with zipfile.ZipFile(target, "w") as bundle:
            for name, size in files.items():
                src = self.base / "payload" / name
                src.parent.mkdir(parents=True, exist_ok=True)
                src.write_bytes(b"x" * size)
                bundle.write(src, name)
        return target

    def test_zip_unpacks_and_unblocks_the_job(self):
        job = self.handed()
        checked = mo.check(job["job_id"])
        self.assertEqual(checked["state"], "blocked")
        bundle = self._zip({"shots/s01-hook.mp4": 4096, "shots/s02-plate.mp4": 4096})
        after = mo.ingest(job["job_id"], bundle)
        self.assertEqual(after["state"], "clip_ready")
        self.assertEqual(after["ingest"]["files"], 2)
        self.assertTrue(after["gates"]["ingest"]["ok"])

    def test_zip_without_media_is_refused(self):
        job = self.handed()
        bundle = self._zip({"notes.txt": 10})
        with self.assertRaises(mo.OpsError):
            mo.ingest(job["job_id"], bundle)

    def test_zip_path_escape_is_refused(self):
        import zipfile
        job = self.handed()
        target = self.base / "evil.zip"
        with zipfile.ZipFile(target, "w") as bundle:
            bundle.writestr("../../escape.mp4", b"x" * 100)
        with self.assertRaises(mo.OpsError):
            mo.ingest(job["job_id"], target)
        self.assertFalse((self.base / "escape.mp4").exists())

    def test_missing_zip_is_named(self):
        job = self.handed()
        with self.assertRaises(mo.OpsError):
            mo.ingest(job["job_id"], self.base / "nope.zip")


class FinishTests(OpsCase):
    def _runner(self, calls, fail_on=None, exit_code=3):
        def runner(args):
            calls.append(args[0])
            if fail_on and args[0] == fail_on:
                return exit_code, "verify: 1 shot below target height"
            if args[0] == "assemble":
                project = pathlib.Path(args[1])
                touch(project.parent / "delivery" / "p-demo_MASTER.mp4")
            return 0, "ok"
        return runner

    def test_finish_runs_mix_verify_assemble_in_order(self):
        job = self.with_clips()
        calls: list[str] = []
        with mock.patch.object(mo, "_probe", return_value={}):
            finished = mo.finish(job["job_id"], runner=self._runner(calls))
        self.assertEqual(calls, ["mix", "verify", "assemble"])
        self.assertEqual(finished["state"], "assembled")
        self.assertEqual(len(finished["master"]["md5"]), 32)
        self.assertTrue(finished["gates"]["mix"]["ok"])

    def test_finish_uses_loudnorm_for_phone_delivery(self):
        job = self.with_clips()
        seen: list[list[str]] = []

        def runner(args):
            seen.append(args)
            if args[0] == "assemble":
                touch(self.proj.parent / "delivery" / "p-demo_MASTER.mp4")
            return 0, "ok"

        with mock.patch.object(mo, "_probe", return_value={}):
            mo.finish(job["job_id"], runner=runner)
        self.assertIn("--loudnorm", seen[0])

    def test_finish_refuses_without_clips(self):
        job = self.handed()
        with self.assertRaises(mo.OpsError):
            mo.finish(job["job_id"], runner=lambda args: (0, ""))

    def test_verify_failure_stops_before_assemble(self):
        job = self.with_clips()
        calls: list[str] = []
        with self.assertRaises(mo.OpsError):
            mo.finish(job["job_id"], runner=self._runner(calls, fail_on="verify"))
        self.assertEqual(calls, ["mix", "verify"])
        blocked = mo.load_job(job["job_id"])
        self.assertEqual(blocked["state"], "blocked")
        self.assertEqual(blocked["blocker"]["stage"], "verify")

    def test_missing_master_is_a_blocker(self):
        job = self.with_clips()
        with self.assertRaises(mo.OpsError):
            mo.finish(job["job_id"], runner=lambda args: (0, "ok"))
        self.assertEqual(mo.load_job(job["job_id"])["state"], "blocked")


class AdoptTests(OpsCase):
    """Colab makes the master; the sandbox only reads the receipt (no Drive access)."""

    def _receipt(self, *, md5_ok=True, bytes_=1024, height=1664, audio="aac") -> pathlib.Path:
        path = self.base / "colab_master_receipt.json"
        path.write_text(json.dumps({
            "project": "p-demo", "master": "p-demo_MASTER.mp4", "shots": ["s01-hook.mp4"],
            "info": {"name": "p-demo_MASTER.mp4", "width": 960, "height": height, "duration": 2.0,
                     "fps": 24.0, "audio_codec": audio, "bytes": bytes_,
                     "md5": "a" * 32 if md5_ok else ""},
            "made_on": "colab-t4"}))
        return path

    def test_adopt_records_the_master_it_did_not_make(self):
        job = self.with_clips()
        mo.check(job["job_id"])
        adopted = mo.adopt(job["job_id"], self._receipt())
        self.assertEqual(adopted["state"], "assembled")
        self.assertEqual(adopted["master"]["md5"], "a" * 32)
        self.assertEqual(adopted["master"]["probe"]["height"], 1664)
        self.assertTrue(adopted["gates"]["master"]["ok"])
        self.assertEqual(adopted["master"]["evidence"], "colab_master_receipt.json")

    def test_adopt_refuses_a_receipt_without_md5(self):
        job = self.with_clips()
        with self.assertRaises(mo.OpsError):
            mo.adopt(job["job_id"], self._receipt(md5_ok=False))

    def test_adopt_refuses_zero_byte_master(self):
        job = self.with_clips()
        with self.assertRaises(mo.OpsError):
            mo.adopt(job["job_id"], self._receipt(bytes_=0))

    def test_adopt_refuses_missing_height(self):
        job = self.with_clips()
        with self.assertRaises(mo.OpsError):
            mo.adopt(job["job_id"], self._receipt(height=0))

    def test_adopted_master_can_be_delivered_and_carded(self):
        job = self.with_clips()
        mo.check(job["job_id"])
        mo.adopt(job["job_id"], self._receipt())
        delivered = mo.deliver(job["job_id"], master_id="drive-master-1",
                               url="https://drive.google.com/file/d/drive-master-1/view")
        self.assertEqual(delivered["state"], "delivered")
        card = mo.card(delivered)
        self.assertIn("960×1664", card)
        self.assertIn("audio: aac", card)
        self.assertIn("drive-master-1", card)


class DeliveryTests(OpsCase):
    def _assembled(self) -> dict:
        job = self.with_clips()

        def runner(args):
            if args[0] == "assemble":
                touch(self.proj.parent / "delivery" / "p-demo_MASTER.mp4")
            return 0, "ok"

        with mock.patch.object(mo, "_probe", return_value={"width": 960, "height": 1664,
                                                           "fps": 30.0, "duration": 10.0,
                                                           "video_codec": "h264",
                                                           "audio_codec": "aac"}):
            return mo.finish(job["job_id"], runner=runner)

    def test_deliver_requires_assembly(self):
        job = self.with_clips()
        with self.assertRaises(mo.OpsError):
            mo.deliver(job["job_id"], master_id="x")

    def test_deliver_records_the_receipt(self):
        job = self._assembled()
        delivered = mo.deliver(job["job_id"], master_id="drive-123",
                               url="https://drive.google.com/file/d/drive-123/view")
        self.assertEqual(delivered["state"], "delivered")
        receipt = delivered["receipt"]
        self.assertEqual(receipt["master"]["drive_id"], "drive-123")
        self.assertEqual(len(receipt["master"]["md5"]), 32)
        self.assertTrue(all(receipt["gates"].values()))
        text = mo.card(delivered)
        self.assertIn("960×1664", text)
        self.assertIn("audio: aac", text)

    def test_delivered_is_terminal(self):
        job = self._assembled()
        mo.deliver(job["job_id"], master_id="drive-123")
        with self.assertRaises(mo.OpsError):
            mo.transition(mo.load_job(job["job_id"]), "clip_ready")


class StateMachineTests(OpsCase):
    def test_every_state_has_an_owner_action(self):
        for state in mo.STATES:
            self.assertIn(state, mo.NEXT_ACTION)
            user, agent = mo.NEXT_ACTION[state]
            self.assertTrue(user and agent, state)

    def test_illegal_jump_is_refused(self):
        job = self.new_job()
        with self.assertRaises(mo.OpsError):
            mo.transition(job, "delivered")

    def test_blocked_can_return_to_work(self):
        job = self.handed()
        mo.check(job["job_id"])
        blocked = mo.load_job("j1")
        touch(self.proj.parent / "shots" / "s01-hook.mp4")
        touch(self.proj.parent / "shots" / "s02-plate.mp4")
        self.assertEqual(mo.check("j1")["state"], "clip_ready")
        self.assertIn("blocked", [h["to"] for h in blocked["history"]])

    def test_status_and_list_do_not_crash_on_empty_root(self):
        with mock.patch("builtins.print"):
            self.assertEqual(mo.status(), 0)
            self.assertEqual(mo.main(["list"]), 0)

    def test_job_survives_a_reload(self):
        self.handed()
        again = mo.load_job("j1")
        self.assertEqual(again["state"], "handed_off")
        self.assertEqual(again["colab_url"],
                         "https://colab.research.google.com/drive/abc")
        self.assertGreaterEqual(len(again["history"]), 3)


if __name__ == "__main__":
    unittest.main()
