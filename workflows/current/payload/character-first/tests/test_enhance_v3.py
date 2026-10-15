from pathlib import Path
import sys
import math
import unittest
import numpy as np
import cv2

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import rigged_main_film as v1
from enhance_motion_v3 import PATCH_SHOTS,PHASE_START,PHASE_END,HEADROOM_SHIFT_PX,gesture_envelope,echo_envelope,hand_core_blend,GestureRig,camera_for


class EnhanceV3Tests(unittest.TestCase):
    def test_only_four_known_shots_change(self):
        self.assertEqual(PATCH_SHOTS,(3,5,6,7))
        count=sum(v1.SHOTS[i][1]-v1.SHOTS[i][0] for i in PATCH_SHOTS)
        self.assertEqual(count,132);self.assertEqual(v1.END-count,1200)
        self.assertTrue(set(PATCH_SHOTS).isdisjoint({20,25,30,32,34}))

    def test_gesture_envelope_is_bounded_and_scoped(self):
        values=[gesture_envelope(i) for i in range(300,550)]
        self.assertGreaterEqual(min(values),0);self.assertLessEqual(max(values),1)
        self.assertEqual(gesture_envelope(PHASE_START-1),0)
        self.assertEqual(gesture_envelope(PHASE_END),0)
        self.assertGreater(gesture_envelope(440),.9)

    def test_echoes_build_in_staggered_order_without_flash_spikes(self):
        self.assertGreater(echo_envelope(407,0),echo_envelope(407,1))
        self.assertGreaterEqual(echo_envelope(407,1),echo_envelope(407,2))
        for k in range(3):
            x=np.array([echo_envelope(i,k) for i in range(PHASE_START,PHASE_END)])
            self.assertGreaterEqual(float(x.min()),0);self.assertLessEqual(float(x.max()),1)
            self.assertLess(float(np.abs(np.diff(x)).max()),.08)
            self.assertEqual(echo_envelope(PHASE_END,k),0)

    def test_glove_core_masks_do_not_touch_face_or_feet(self):
        left,right=hand_core_blend('L'),hand_core_blend('R')
        self.assertEqual(float(left[380,157]),1);self.assertEqual(float(right[380,580]),1)
        for a in [left,right]:
            self.assertEqual(float(a[300,360]),0)
            self.assertEqual(float(a[1170,290]),0)
            self.assertGreaterEqual(float(a.min()),0);self.assertLessEqual(float(a.max()),1)

    def test_camera_change_is_only_reveal_y_framing(self):
        for i in [322,339,355,420,480]:
            a,b,name,z,roll,travel=next(s for s in v1.SHOTS if s[0]<=i<s[1]);t=i/30;u=(i-a)/(b-a-1)
            scale=z*(1+.045*float(v1.ease(u)));angle=roll+travel*float(v1.ease(u))+.3*math.sin(t*1.4)
            old=cv2.getRotationMatrix2D((360,550) if z>1.4 else (360,650),angle,scale)
            old[0,2]+=1.5*math.sin(t*3.2);old[1,2]+=.9*math.sin(t*2.7)
            new,_=camera_for(i);delta=new-old
            expected=np.zeros((2,3));expected[1,2]=HEADROOM_SHIFT_PX if 322<=i<356 else 0
            np.testing.assert_allclose(delta,expected,atol=1e-10)

    def test_face_feet_and_hand_volume_constraints(self):
        old=v1.Rig.__new__(v1.Rig);old.c=v1.CONFIG['open'];old.name='open'
        new=GestureRig.__new__(GestureRig);new.c=v1.CONFIG['open'];new.name='open'
        for frame in [394,420,440,460,491]:
            a,_=old.pose(frame/30);b,_=new.pose(frame/30)
            for key in ['head','foot.L','foot.R']:np.testing.assert_allclose(a[key],b[key],atol=1e-12)
            for side in ['L','R']:
                np.testing.assert_allclose(np.linalg.svd(b[f'hand.{side}'][:2,:2])[1],[1,1],atol=1e-10)
                wrist=new.c['arms'][side][2]
                np.testing.assert_allclose(v1.point(b[f'hand.{side}'],wrist),v1.point(b[f'fore.{side}'],wrist),atol=1e-10)


if __name__=='__main__':unittest.main()
