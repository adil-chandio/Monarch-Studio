from pathlib import Path
import sys
import unittest
import numpy as np
from PIL import ImageChops

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import render_brand_outro as r


class OutroTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.art=r.layers()

    def test_native_component_settings_are_not_character_motion(self):
        s=r.settings()
        self.assertEqual((s['width'],s['height'],s['fps'],s['frames']),(1080,1920,30,108))
        self.assertEqual(r.DURATION,3.6)
        self.assertFalse(s['character_animation'])
        self.assertEqual(s['kind'],'native_vector_brand_motion_graphics')

    def test_black_first_and_last_frames(self):
        for i in [0,r.FRAMES-1]:
            im=r.frame(i,self.art)
            self.assertEqual(im.getextrema(),((0,0),(0,0),(0,0)))

    def test_crown_remains_above_name(self):
        crown,cp=self.art['crown'];name,np_=self.art['name'];studio,sp=self.art['studio']
        self.assertLess(cp[1]+crown.height+18,np_[1])
        self.assertLess(np_[1]+name.height+9,sp[1])
        self.assertGreater(r.frame(45,self.art).crop((100,900,980,1160)).getextrema()[0][1],200)

    def test_glint_frames_are_actually_different(self):
        d=ImageChops.difference(r.frame(31,self.art),r.frame(39,self.art))
        self.assertIsNotNone(d.getbbox())

    def test_original_sting_length_and_safe_raw_samples(self):
        a=r.synthesize_score()
        self.assertEqual(a.shape,(172800,2))
        self.assertTrue(np.all(np.isfinite(a)))
        self.assertLess(float(np.abs(a).max()),.5)
        self.assertLess(float(np.abs(a[0]).max()),1e-8)
        self.assertLess(float(np.abs(a[-1]).max()),1e-5)


if __name__=='__main__':unittest.main()
