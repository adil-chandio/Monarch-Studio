import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from recover_design_assets import recover,safe_destination


def receipt(role,relative,data):
    return {'role':role,'relative_path':relative,'path':relative,'bytes':len(data),
            'md5':hashlib.md5(data).hexdigest(),'sha256':hashlib.sha256(data).hexdigest()}


class RecoveryTests(unittest.TestCase):
    def fixture(self,base):
        archive=base/'download.zip';data=b'original test image bytes'
        with zipfile.ZipFile(archive,'w') as z:z.writestr('character/front.png',data)
        ledger={'assets':[receipt('front_master','character/front.png',data),
                          receipt('design_zip','delivery/design.zip',archive.read_bytes())]}
        return archive,ledger

    def test_recovers_and_reuses_without_regeneration(self):
        with tempfile.TemporaryDirectory() as t:
            base=Path(t);a,l=self.fixture(base);root=base/'assets'
            first=recover(a,l,root);self.assertEqual(len(first['restored']),2)
            stamp=(root/'character/front.png').stat().st_mtime_ns
            second=recover(a,l,root);self.assertEqual(second['restored'],[])
            self.assertEqual(len(second['reused']),2);self.assertEqual(second['regenerated'],0)
            self.assertEqual((root/'character/front.png').stat().st_mtime_ns,stamp)

    def test_different_existing_art_is_preserved(self):
        with tempfile.TemporaryDirectory() as t:
            base=Path(t);a,l=self.fixture(base);root=base/'assets';p=root/'character/front.png'
            p.parent.mkdir(parents=True);p.write_bytes(b'user edited image')
            with self.assertRaisesRegex(ValueError,'Refusing to overwrite'):recover(a,l,root)
            self.assertEqual(p.read_bytes(),b'user edited image')

    def test_wrong_archive_is_rejected_before_writes(self):
        with tempfile.TemporaryDirectory() as t:
            base=Path(t);a,l=self.fixture(base);a.write_bytes(b'bad archive');root=base/'assets'
            with self.assertRaisesRegex(ValueError,'Archive bytes'):recover(a,l,root)
            self.assertFalse(root.exists())

    def test_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            for path in ['../secret','/absolute.png','folder/../../secret','folder\\secret']:
                with self.assertRaises(ValueError):safe_destination(Path(t),path)


if __name__=='__main__':unittest.main()
