from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import rigged_main_film as r


class RiggedFullTests(unittest.TestCase):
    def test_complete_main_reference_picture_span(self):
        self.assertEqual((r.W,r.H,r.FPS,r.END),(720,1280,30,1332))
        self.assertEqual(r.SHOTS[0][0],0);self.assertEqual(r.SHOTS[-1][1],1332)
        self.assertEqual(sum(b-a for a,b,*_ in r.SHOTS),1332)
        for a,b in zip(r.SHOTS,r.SHOTS[1:]):self.assertEqual(a[1],b[0])

    def test_reachable_ik_preserves_lengths_and_joint_connection(self):
        a=np.array([0.,0.]);b=np.array([1.,2.]);c=np.array([2.,4.]);new_a=np.array([.2,.3]);goal=np.array([2.,3.8])
        up,fore,tip,error=r.ik(a,b,c,new_a,goal)
        self.assertLess(error,1e-8)
        np.testing.assert_allclose(r.point(up,b),r.point(fore,b),atol=1e-8)
        np.testing.assert_allclose(r.point(fore,c),tip,atol=1e-8)
        self.assertAlmostEqual(np.linalg.norm(r.point(up,b)-r.point(up,a)),np.linalg.norm(b-a),places=8)
        self.assertAlmostEqual(np.linalg.norm(r.point(fore,c)-r.point(fore,b)),np.linalg.norm(c-b),places=8)

    def test_unreachable_target_is_clamped_not_stretched(self):
        up,fore,tip,error=r.ik([0,0],[0,2],[1,4],[0,0],[10,0])
        self.assertGreater(error,5)
        for m in [up,fore]:np.testing.assert_allclose(np.linalg.svd(m[:2,:2])[1],[1,1],atol=1e-10)

    def test_face_core_is_inside_rigid_head_zone(self):
        for name,c in r.CONFIG.items():
            if c.get('prop_only'):continue
            x0,y0,x1,y1=c['face_box'];a,b,d,e=c['head_zone']
            self.assertTrue(a<=x0<x1<=d and b<=y0<y1<=e,name)

    def test_different_reference_scene_is_not_an_input(self):
        self.assertTrue(all(c['file'].endswith('.png') for c in r.CONFIG.values()))
        self.assertEqual({c['file'] for c in r.CONFIG.values()},{'01_RAISED_HAND.png','02_OPEN_ARMS.png','03_RED_ANGLE.png','04_CLOSE_SMIRK.png','05_BLADE_POV.png'})

    def test_motion_method_is_disclosed(self):
        text=Path(r.__file__).read_text()
        self.assertIn("'image_space_skinning_used':True",text)
        self.assertIn("'natural_ai_performance':False",text)
        self.assertIn("'pixel_perfect_choreography_claimed':False",text)
        self.assertIn('2.5D  /  RIGGED CHARACTER RECREATION',text)


if __name__=='__main__':unittest.main()
