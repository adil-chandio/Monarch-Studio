"""Tests for tools/cloud_reel.py — the agent-triggered cloud bridge (git in, git out)."""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import cloud_reel as cr  # noqa: E402


class QueueTests(unittest.TestCase):
    def test_queue_job_writes_the_spec_pointer(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(cr, "JOBS", pathlib.Path(td) / "jobs"), \
                 mock.patch.object(cr, "ROOT", ROOT):
                path = cr.queue_job("reel-local-01")
                payload = json.loads(path.read_text())
        self.assertEqual(payload["id"], "reel-local-01")
        self.assertTrue(payload["spec"].endswith("reel-local-01/reel.json"))

    def test_queue_job_refuses_a_missing_spec(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(cr, "JOBS", pathlib.Path(td)), \
                 mock.patch.object(cr, "ROOT", pathlib.Path(td)):
                with self.assertRaises(cr.CloudError):
                    cr.queue_job("nope", spec="does/not/exist.json")

    def test_enqueue_can_skip_the_push(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(cr, "JOBS", pathlib.Path(td)), \
                 mock.patch.object(cr, "ROOT", ROOT):
                result = cr.enqueue("reel-local-01", None, push=False)
        self.assertFalse(result["pushed"])


class ReceiptTests(unittest.TestCase):
    def test_no_artifact_branch_means_pending(self):
        with mock.patch.object(cr, "run", lambda *a, **k: ""), \
             mock.patch("subprocess.run", lambda *a, **k: mock.Mock(returncode=1, stdout="", stderr="")):
            self.assertIsNone(cr.cloud_receipt("reel-local-01"))

    def test_receipt_of_another_job_is_ignored(self):
        blob = mock.Mock(returncode=0, stdout=json.dumps({"job": "someone-else", "md5": "x"}))
        with mock.patch.object(cr, "run", lambda *a, **k: ""), \
             mock.patch("subprocess.run", lambda *a, **k: blob):
            self.assertIsNone(cr.cloud_receipt("reel-local-01"))

    def test_receipt_for_this_job_is_returned(self):
        payload = {"job": "reel-local-01", "md5": "abc", "master": "reel-local-01_MASTER.mp4"}
        blob = mock.Mock(returncode=0, stdout=json.dumps(payload))
        with mock.patch.object(cr, "run", lambda *a, **k: ""), \
             mock.patch("subprocess.run", lambda *a, **k: blob):
            self.assertEqual(cr.cloud_receipt("reel-local-01")["md5"], "abc")


class FetchTests(unittest.TestCase):
    def test_md5_mismatch_is_refused(self):
        """Cloud ne jo bheja aur yahan jo aaya — match hona zaroori hai."""
        with tempfile.TemporaryDirectory() as td:
            dest = pathlib.Path(td) / "in"
            receipt = {"job": "j", "md5": "0" * 32, "master": "j_MASTER.mp4"}
            blob = mock.Mock(returncode=0, stdout=b"not the same file")
            with mock.patch.object(cr, "wait", lambda *a, **k: receipt), \
                 mock.patch.object(cr, "run", lambda *a, **k: ""), \
                 mock.patch("subprocess.run", lambda *a, **k: blob):
                with self.assertRaises(cr.CloudError) as caught:
                    cr.fetch("j", dest, timeout=1)
        self.assertIn("md5 mismatch", str(caught.exception))

    def test_fetch_writes_master_and_receipt_when_md5_matches(self):
        payload = b"hello master bytes"
        good = cr.md5_bytes(payload) if hasattr(cr, "md5_bytes") else None
        with tempfile.TemporaryDirectory() as td:
            dest = pathlib.Path(td) / "in"
            if good is None:
                import hashlib
                good = hashlib.md5(payload).hexdigest()
            receipt = {"job": "j", "md5": good, "master": "j_MASTER.mp4", "bytes": len(payload)}
            blob = mock.Mock(returncode=0, stdout=payload)
            with mock.patch.object(cr, "wait", lambda *a, **k: receipt), \
                 mock.patch.object(cr, "run", lambda *a, **k: ""), \
                 mock.patch("subprocess.run", lambda *a, **k: blob):
                result = cr.fetch("j", dest, timeout=1)
            self.assertEqual(result["md5"], good)
            self.assertTrue((dest / "j_MASTER.mp4").exists())
            self.assertTrue((dest / "cloud_receipt.json").exists())


class WorkflowTests(unittest.TestCase):
    def test_reel_workflow_is_push_triggered_and_publishes_to_git(self):
        text = (ROOT / ".github/workflows/cloud-reel.yml").read_text()
        self.assertIn("cloud/jobs/*.json", text)
        self.assertIn("cloud-artifacts", text)          # artifacts objects.* ke bajaye git se
        self.assertIn("tools/reel_render.py", text)

    def test_ai_workflow_runs_on_cpu_torch_and_publishes_its_own_branch(self):
        text = (ROOT / ".github/workflows/cloud-ai-clip.yml").read_text()
        self.assertIn("download.pytorch.org/whl/cpu", text)
        self.assertIn("cloud/ai_jobs/*.json", text)
        self.assertIn("cloud-ai-artifacts", text)
        self.assertIn("tools/cloud_ai_clip.py", text)


if __name__ == "__main__":
    unittest.main()
