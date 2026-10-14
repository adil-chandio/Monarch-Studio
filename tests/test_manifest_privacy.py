"""Transient/private media must not enter the durable repository manifest."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT=Path(__file__).resolve().parents[1]/'tools/studio.py'
spec=importlib.util.spec_from_file_location('studio_manifest_privacy',SCRIPT)
studio=importlib.util.module_from_spec(spec)
spec.loader.exec_module(studio)


class ManifestPrivacyTests(unittest.TestCase):
    def test_private_staging_and_outputs_are_excluded(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for relative in ['.cache/identity/front.mp4','.venv/lib/model.bin',
                             'google_drive/personal-face.png','deliverables/review.mp4',
                             'workflows/current/payload/src/render.py','docs/guide.md']:
                p=root/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('fixture')
            with patch.object(studio,'ROOT',root),patch.object(studio,'MANIFEST_PATH',root/'.studio-manifest.json'):
                files={str(p.relative_to(root)) for p in studio.eligible_repo_files()}
            self.assertEqual(files,{'workflows/current/payload/src/render.py','docs/guide.md'})

    def test_large_private_download_does_not_affect_manifest_input_list(self):
        self.assertTrue({'.cache','.venv','google_drive','deliverables'}.issubset(studio.SKIP_PARTS))


if __name__=='__main__':unittest.main()
