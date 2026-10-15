import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'src'))
from validate_assets import verify_asset,verify_manifest
from assemble_design import panel,story
from brand_end import build


class DesignTests(unittest.TestCase):
    def fixture(self,p,data=b'fixture'):
        p.write_bytes(data)
        return {'role':'test','path':str(p),'relative_path':p.name,'bytes':len(data),
                'md5':hashlib.md5(data).hexdigest(),'sha256':hashlib.sha256(data).hexdigest(),
                'drive_id':'test-fixture-no-network'}

    def test_exact_asset_passes_integrity_only(self):
        with tempfile.TemporaryDirectory() as t:
            a=self.fixture(Path(t)/'a.png');r=verify_asset(a)
            self.assertEqual(r['status'],'verified')
            self.assertFalse(r['visual_approval_claimed'])

    def test_changed_file_is_not_reused(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'a.png';a=self.fixture(p);p.write_bytes(b'different')
            self.assertEqual(verify_asset(a)['status'],'mismatch')

    def test_missing_image_requests_exact_recovery_not_regeneration(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'a.png';a=self.fixture(p);p.unlink();r=verify_asset(a)
            self.assertEqual(r['status'],'missing')
            self.assertIn('Do not regenerate',r['next_action'])

    def test_empty_manifest_is_not_success(self):
        with self.assertRaises(ValueError):verify_manifest({'assets':[]})

    def test_layout_preserves_aspect_ratio(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'tall.png';Image.new('RGB',(100,200),'red').save(p)
            im=Image.new('RGB',(200,120),'white');panel(im,p,(0,0,200,120),bg='white')
            # A 1:2 image becomes 60x120, never a stretched 200x120.
            self.assertEqual(im.getpixel((70,0)),(255,0,0))
            self.assertEqual(im.getpixel((129,119)),(255,0,0))
            self.assertEqual(im.getpixel((69,0)),(255,255,255))
            self.assertEqual(im.getpixel((130,119)),(255,255,255))

    def test_absent_shots_do_not_fabricate_a_storyboard(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertIsNone(story(Path(t),Path(t)))

    def test_brand_is_native_portrait_still(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'brand.png';build(p)
            with Image.open(p) as im:
                self.assertEqual(im.size,(1080,1920));self.assertEqual(im.mode,'RGB')
                self.assertGreater(sum(im.getpixel((540,750))),sum(im.getpixel((50,750))))

    def test_full_plan_discloses_limited_2_5d_method(self):
        p=json.loads((BASE/'records/ANIMATION_PLAN.json').read_text())
        self.assertEqual(p['rendered_character_frames'],844)
        self.assertEqual(p['rendered_brand_frames'],150)
        self.assertEqual(p['rendered_frames'],1332)
        self.assertEqual(p['natural_3d_character_frames'],0)
        self.assertTrue(p['actual_video_file'].endswith('MONARCH_REFERENCE_2_5D_FULL_V1.mp4'))
        self.assertEqual(p['status'],'FULL_2_5D_RECREATION_V1_RENDERED_FOR_REVIEW')
        self.assertFalse(p['user_visual_approval'])
        self.assertTrue(all(c['render_status']=='rendered_2_5d_picture' for c in p['cuts']))
        self.assertEqual(p['cuts'][0]['in_frame'],0)
        self.assertEqual(p['cuts'][-1]['out_frame_exclusive'],p['planned_total_frames'])
        for a,b in zip(p['cuts'],p['cuts'][1:]):self.assertEqual(a['out_frame_exclusive'],b['in_frame'])
        self.assertEqual(p['planned_total_frames']/p['planned_fps'],44.4)


if __name__=='__main__':unittest.main()
