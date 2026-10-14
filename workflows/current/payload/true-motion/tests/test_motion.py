import importlib.util
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from motion_math import two_bone,targets,ease


class MotionTests(unittest.TestCase):
    def test_solver_preserves_bone_lengths(self):
        for t in np.linspace(0,5,120):
            pose=targets(t)
            root=pose['root']
            for side,s in [('L',-1),('R',1)]:
                hip=np.array([s*.100,0,.940])+root
                joint,tip,error=two_bone(hip,pose['feet'][side],.429,.424,[s*.1,-.65,.55])
                self.assertAlmostEqual(np.linalg.norm(joint-hip),.429,places=8)
                self.assertAlmostEqual(np.linalg.norm(tip-joint),.424,places=8)
                self.assertLess(error,1e-6)

    def test_planted_feet_do_not_slide(self):
        for side in ['L','R']:
            pts=np.array([targets(t)['feet'][side] for t in np.linspace(2.1,5,90)])
            self.assertLess(float(np.max(np.ptp(pts,axis=0))),1e-10)

    def test_right_foot_stays_planted_for_entire_step(self):
        pts=np.array([targets(t)['feet']['R'] for t in np.linspace(0,5,120)])
        np.testing.assert_allclose(pts,np.tile([.105,0,.095],(120,1)),atol=1e-12)

    def test_left_foot_lifts_and_advances(self):
        pts=np.array([targets(t)['feet']['L'] for t in np.linspace(0,5,120)])
        self.assertGreater(float(np.ptp(pts[:,1])),.249)
        self.assertGreater(float(np.ptp(pts[:,2])),.052)

    def test_zero_length_aim_is_finite(self):
        joint,tip,error=two_bone([0,0,0],[0,0,0],.4,.4,[0,0,-1])
        self.assertTrue(np.all(np.isfinite(joint)))
        self.assertTrue(np.all(np.isfinite(tip)))

    def test_out_of_reach_target_never_stretches(self):
        j,t,e=two_bone([0,0,0],[4,0,0],.4,.4,[0,0,1])
        self.assertAlmostEqual(np.linalg.norm(j),.4,places=8)
        self.assertAlmostEqual(np.linalg.norm(t-j),.4,places=8)
        self.assertGreater(e,3.1)

    def test_monotone_ease(self):
        e=[ease(t) for t in np.linspace(-1,2,500)]
        self.assertEqual(e[0],0);self.assertEqual(e[-1],1)
        self.assertTrue(np.all(np.diff(e)>=0))

    def test_live_action_is_not_labelled_generated_3d(self):
        s=(ROOT/'src/composite_live.py').read_text()
        self.assertIn("'new_3d_body_performance':False",s)
        self.assertIn("'new_blazer':False",s)
        self.assertNotIn('cv2.remap(',s)
        self.assertNotIn('calcOpticalFlow',s)

    def test_skinning_inherits_root_transform(self):
        s=(ROOT/'src/build_vault.py').read_text()
        self.assertIn('obj.parent=RIG;obj.matrix_world=world',s)

    def test_renderer_refuses_mixed_stale_frames(self):
        s=(ROOT/'src/render_vault.py').read_text()
        self.assertIn('blend_sha256',s)
        self.assertIn('Stale frame settings or scene hash',s)
        self.assertIn('os.replace(temp,out)',s)


if __name__=='__main__':unittest.main()
