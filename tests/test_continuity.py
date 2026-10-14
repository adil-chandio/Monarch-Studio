from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SOURCE_ROOT = Path(__file__).resolve().parents[1]


class ContinuityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "tools").mkdir()
        shutil.copy2(SOURCE_ROOT / "tools" / "continuity.py", self.root / "tools" / "continuity.py")
        (self.root / "operations" / "continuity").mkdir(parents=True)
        (self.root / "operations" / "continuity" / "remote-targets.json").write_text('{"targets": {}}\n')
        self.cli = [sys.executable, str(self.root / "tools" / "continuity.py")]

    def tearDown(self) -> None:
        self.temp.cleanup()

    def call(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        proc = subprocess.run(self.cli + list(args), cwd=self.root, text=True, capture_output=True)
        if check and proc.returncode:
            self.fail(f"continuity command failed: {' '.join(args)}\n{proc.stdout}\n{proc.stderr}")
        return proc

    def test_full_task_checkpoint_and_completion_lifecycle(self) -> None:
        self.call(
            "init", "--task-id", "TEST-001", "--title", "Recovery test",
            "--style", "test-style", "--goal", "Do not lose state",
            "--acceptance", "Journal verifies", "--next-action", "Log the instruction",
        )
        prompt = "Continue exactly from the durable state 🔥"
        self.call("log", "--kind", "user", "--actor", "user", "--message", prompt)
        self.call("checkpoint", "--summary", "Prompt recorded.", "--next-action", "Run test action.")

        report = json.loads(self.call("status", "--json").stdout)
        self.assertTrue(report["journal_valid"])
        self.assertEqual(report["active_task"]["checkpoint_sequence"], 1)
        self.assertEqual(report["journal_events"], 3)
        transcript = (self.root / "workflows" / "current" / "CHAT_TRANSCRIPT.jsonl").read_text()
        self.assertIn(prompt, transcript)
        checkpoint = report["active_task"]["last_checkpoint_path"]
        self.assertTrue((self.root / checkpoint / "checkpoint.json").exists())

        self.call("complete", "--summary", "Lifecycle passed.")
        idle = json.loads((self.root / "workflows" / "current" / "ACTIVE_TASK.json").read_text())
        self.assertEqual(idle["status"], "idle")
        self.assertTrue((self.root / "operations" / "history" / "TEST-001" / "JOURNAL.jsonl").exists())

    def test_completed_checkpoint_can_be_archived_without_restart(self) -> None:
        self.call("init", "--task-id", "TEST-TERMINAL", "--title", "Terminal checkpoint", "--goal", "Preserve delivered work")
        self.call("checkpoint", "--summary", "Delivered", "--next-action", "Archive only", "--status", "completed")
        self.call("complete", "--summary", "Archived without reopening production")
        idle = json.loads((self.root / "workflows/current/ACTIVE_TASK.json").read_text())
        self.assertEqual(idle["status"], "idle")
        self.assertEqual(idle["completed_task"], "TEST-TERMINAL")
        self.assertTrue((self.root / "operations/history/TEST-TERMINAL/JOURNAL.jsonl").exists())

    def test_archive_collision_does_not_mutate_state(self) -> None:
        self.call("init", "--task-id", "TEST-COLLISION", "--title", "Collision", "--goal", "No overwrite")
        (self.root / "operations/history/TEST-COLLISION").mkdir(parents=True)
        state = self.root / "workflows/current/ACTIVE_TASK.json"
        before = state.read_bytes()
        result = self.call("complete", "--summary", "Must refuse", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(before, state.read_bytes())

    def test_journal_tampering_is_detected(self) -> None:
        self.call("init", "--task-id", "TEST-002", "--title", "Tamper test", "--goal", "Detect changes")
        self.call("log", "--kind", "result", "--message", "Original result")
        journal = self.root / "workflows" / "current" / "JOURNAL.jsonl"
        journal.write_text(journal.read_text().replace("Original result", "Changed result"))
        proc = self.call("status", check=False)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("INVALID", proc.stdout)


if __name__ == "__main__":
    unittest.main()
