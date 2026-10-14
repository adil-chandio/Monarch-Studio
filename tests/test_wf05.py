from __future__ import annotations
import copy,importlib.util,json,subprocess,sys,tempfile,unittest,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STYLE=ROOT/'styles/premium-motion-editing'
sys.path.insert(0,str(STYLE/'src'))
import policy
from wf05 import new_project


def fixture(base:Path):
    p={'schema_version':1,'style_id':'premium-motion-editing','project_id':'fixture','topic':'Synthetic test only','mode':'case_replay','timeline':'timeline.json','media_dir':'media','audio_mix':'media/mix.wav','output':'delivery/test.mp4','font_dir':None,'format':{'width':1080,'height':1920,'fps':30},'typography':{'subtitle_mode':'off'},'rights_status':'own','script_status':'approved','motion_review':'approved','policy_id':policy.POLICY_ID}
    t={'schema_version':1,'fps':30,'duration':.6,'shots':[{'name':'test','start':0,'end':.6,'path':'test.mp4','motion_kind':'actual_video','depth_rect':[.12,.3,.9,.85],'transition':'depth_push'}],'titles':[{'start':0,'end':.6,'position':'top','kicker':'synthetic fixture','title':'TEST','sub':'not a delivered film','size':64}],'captions':[{'start':0,'end':.6,'text':'This is a test caption.'}],'voice_clips':[]}
    (base/'media').mkdir();(base/'project.json').write_text(json.dumps(p));(base/'timeline.json').write_text(json.dumps(t));return p,t

class WF05PolicyTests(unittest.TestCase):
    def test_latest_caption_policy_is_binding(self):
        d=policy.profile();self.assertEqual(d['typography']['subtitle_mode'],'off');self.assertFalse(d['typography']['caption_pills']);self.assertFalse(d['typography']['word_highlighting'])
    def test_rejected_caption_modes_fail(self):
        for mode in ['pills','pill','karaoke','word_highlight']:
            with self.subTest(mode=mode),self.assertRaises(policy.PolicyError):policy.subtitle_mode({'typography':{'subtitle_mode':mode}})
        for key in ['caption_pills','word_highlighting']:
            with self.subTest(key=key),self.assertRaises(policy.PolicyError):policy.subtitle_mode({'typography':{key:True}})
    def test_plain_requires_explicit_request(self):
        with self.assertRaises(policy.PolicyError):policy.subtitle_mode({'typography':{'subtitle_mode':'plain'}})
        self.assertEqual(policy.subtitle_mode({'typography':{'subtitle_mode':'plain','plain_subtitles_requested':True}}),'plain')
    def test_new_project_does_not_copy_case_content(self):
        with tempfile.TemporaryDirectory() as td:
            out=new_project(Path(td)/'new','Attention and choice','attention')
            data=json.loads((out/'timeline.json').read_text());self.assertEqual(data['shots'],[]);self.assertFalse(list(out.rglob('*.mp3')))
            p,_,issues=policy.validate(out/'project.json',False);self.assertTrue(issues);self.assertEqual(p['topic'],'Attention and choice')
            with self.assertRaises(policy.PolicyError):new_project(out,'Duplicate','duplicate')
    def test_permanent_style_is_not_a_workspace(self):
        with self.assertRaises(policy.PolicyError):new_project(STYLE/'projects/would-overwrite','Bad','bad')
    def test_integrated_bottom_headline_remains_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);p,t=fixture(base);t['titles'][0]['position']='bottom';(base/'timeline.json').write_text(json.dumps(t))
            self.assertEqual(policy.validate(base/'project.json',False)[2],[])
    def test_new_topic_cannot_silently_use_case_marked_media(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);p,t=fixture(base);p['mode']='new_production';t['shots'][0]['case_origin']='einstein-flow-state';(base/'project.json').write_text(json.dumps(p));(base/'timeline.json').write_text(json.dumps(t))
            self.assertTrue(any('historical case media' in x for x in policy.validate(base/'project.json',False)[2]))
    def test_missing_media_is_not_a_completed_project(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);fixture(base);issues=policy.validate(base/'project.json',True)[2];self.assertTrue(any('missing actual motion' in x for x in issues));self.assertTrue(any('Missing mixed audio' in x for x in issues))
    def test_delivery_fails_until_all_real_receipts_match(self):
        q={'technical_pass':True,'visual_review_approved':True,'caption_policy_pass':True,'md5':'abc','size_bytes':10};m={'drive_id':'a-real-result-in-runtime','independent_get_verified':True,'md5':'abc','size':10};r={'drive_id':'a-real-source-result-in-runtime','independent_get_verified':True,'local_md5':'def','remote_md5':'def'}
        self.assertFalse(policy.delivery_gate(q,m,r,False)['complete']);self.assertTrue(policy.delivery_gate(q,m,r,True)['complete'])
        m['size']=9;self.assertFalse(policy.delivery_gate(q,m,r,True)['complete'])
    def test_frame_grid_gap_and_unreviewed_strength_fail(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);p,t=fixture(base);t['shots'][0].update({'start':.1,'camera':{'z_strength':3.0}});(base/'timeline.json').write_text(json.dumps(t))
            issues=policy.validate(base/'project.json',False)[2];self.assertTrue(any('frame grid' in x for x in issues));self.assertTrue(any('depth strength' in x for x in issues))

HAS_RENDER=all(importlib.util.find_spec(m) is not None for m in ['cv2','PIL','numpy','imageio_ffmpeg'])
@unittest.skipUnless(HAS_RENDER,'Install requirements/render.txt for compositor smoke tests')
class WF05RenderTests(unittest.TestCase):
    def test_off_caption_pixels_and_project_cache_isolation(self):
        import numpy as np
        from render_project import Compositor
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);p,t=fixture(base);frame=np.full((1920,1080,3),220,np.uint8)
            one=Compositor(p,t,base);out=one.overlay(frame,.3,t['shots'][0]);self.assertTrue(np.array_equal(out[1660:],frame[1660:]))
            two_p=copy.deepcopy(p);two_p['typography']={'subtitle_mode':'plain','plain_subtitles_requested':True};two=Compositor(two_p,t,base);plain=two.overlay(frame,.3,t['shots'][0]);self.assertFalse(np.array_equal(plain[1660:],out[1660:]))
            t2=copy.deepcopy(t);t2['titles'][0]['title']='NEXT';third=Compositor(p,t2,base);self.assertNotEqual(one.title_art(0)[0].tobytes(),third.title_art(0)[0].tobytes())
    def test_prepared_motion_encodes_and_verifies_without_fake_user_approval(self):
        import cv2,numpy as np
        from render_project import render
        from verify_output import verify
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);p,t=fixture(base)
            writer=cv2.VideoWriter(str(base/'media/test.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(180,320))
            self.assertTrue(writer.isOpened())
            for i in range(18):
                f=np.full((320,180,3),(240,218,220),np.uint8);cv2.circle(f,(45+i*3,155),19,(90,60,60),-1);cv2.rectangle(f,(120-i*2,205),(135-i*2,230),(140,90,90),-1);writer.write(f)
            writer.release()
            sr=48000;x=.15*np.sin(2*np.pi*220*np.arange(round(.6*sr))/sr);st=np.stack([x,x],axis=1)
            with wave.open(str(base/'media/mix.wav'),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes((st*32767).astype('<i2').tobytes())
            a=render(base/'project.json');self.assertEqual(a['frames'],18);self.assertFalse(a['caption_pills'])
            b=render(base/'project.json');self.assertEqual(a['sha256'],b['sha256'])
            q=verify(base/'project.json');self.assertTrue(q['technical_pass'],q);self.assertTrue(q['caption_policy_pass']);self.assertFalse(q['visual_review_approved'])

if __name__=='__main__':unittest.main()
