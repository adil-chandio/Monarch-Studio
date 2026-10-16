from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('wf02', ROOT/'tools/wf02.py')
wf02 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wf02)

class Wf02KnowledgeTests(unittest.TestCase):
    def test_preservation_audit_and_latest_alignment(self):
        report = wf02.audit()
        self.assertTrue(report['passed'], report['errors'])
        self.assertGreaterEqual(report['release_count'], 7)
        self.assertGreater(report['project_files_verified'], 500)
        self.assertGreater(report['raw_history_files_verified'], 30)

    def test_new_topic_brief_is_not_a_canned_render(self):
        brief = wf02.brief('Why do ears pop on an airplane?')
        self.assertEqual(brief['workflow'], 'WF-02')
        self.assertEqual(brief['status'], 'planning_only_not_a_generated_video')
        self.assertIn('splinter', ' '.join(brief['do_not']))
        self.assertIn('duration', brief['case_specific_not_universal'])
        self.assertTrue((ROOT/brief['startup_entry']).is_file())

    def test_empty_topic_rejected(self):
        with self.assertRaises(ValueError):
            wf02.brief('  ')

    def test_history_coverage_does_not_invent_full_chat(self):
        coverage = json.loads((ROOT/wf02.STYLE_REL/'knowledge/history/COVERAGE.json').read_text())
        self.assertFalse(coverage['full_original_chat_available'])
        self.assertTrue(any(row['transcript_roles'].get('assistant', 0) == 0 for row in coverage['tasks']))

    def test_hash_guard_detects_changes_without_mutating_real_projects(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            p = base/'sample.txt';p.write_text('original')
            records = {'sample.txt': {'size': p.stat().st_size, 'sha256': wf02.sha(p)}}
            self.assertEqual(wf02.verify_records(base, records), [])
            p.write_text('modified')
            self.assertTrue(wf02.verify_records(base, records))

    def test_archive_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                wf02.contained(Path(tmp), '../outside.txt')

if __name__ == '__main__':
    unittest.main()
