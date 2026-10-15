from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import rigged_main_film as v1
from polish_full_v2 import expected_patch_shots,face_gain_map,clean_plate_composite


class PolishV2Tests(unittest.TestCase):
    def test_only_five_shots_are_patched(self):
        patch=expected_patch_shots(v1.SHOTS)
        self.assertEqual(patch,[20,25,30,32,34])
        changed=sum(v1.SHOTS[i][1]-v1.SHOTS[i][0] for i in patch)
        self.assertEqual(changed,159)
        self.assertEqual(len(v1.SHOTS)-len(patch),32)
        self.assertEqual(v1.END-changed,1173)

    def test_highlight_protection_does_not_change_background_gain(self):
        mask=np.array([0.,.5,1.],np.float32)
        np.testing.assert_allclose(face_gain_map(1.38,mask),[1.38,1.25,1.12],atol=1e-6)

    def test_low_gain_is_not_further_darkened(self):
        mask=np.linspace(0,1,101,dtype=np.float32)
        np.testing.assert_allclose(face_gain_map(.67,mask),np.full(101,.67),atol=1e-6)

    def test_background_patch_preserves_distant_pixels_and_inputs(self):
        before=np.full((256,256,3),40,np.float32)
        new=np.full((256,256,3),90,np.float32)
        matte=np.zeros((256,256),np.uint8);matte[124:132,124:132]=255
        result,blend=clean_plate_composite(before,new,matte)
        np.testing.assert_array_equal(result[0,0],[40,40,40])
        self.assertGreater(float(result[128,128,0]),85)
        self.assertTrue(np.all(before==40));self.assertTrue(np.all(new==90))
        self.assertGreaterEqual(float(blend.min()),0)
        self.assertLessEqual(float(blend.max()),1.000001)

    def test_gain_correction_is_bounded_and_monotone(self):
        mask=np.linspace(0,1,51,dtype=np.float32)
        values=face_gain_map(1.38,mask)
        self.assertTrue(np.all(np.diff(values)<=1e-7))
        self.assertGreaterEqual(float(values.min()),1.11999)
        self.assertLessEqual(float(values.max()),1.38001)


if __name__=='__main__':unittest.main()
