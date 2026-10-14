"""Original-set LIVE-ACTION VFX draft; explicitly not generated 3D acting.

The user's real recorded performance supplies every moving face/body pixel.
Only a uniform portrait crop, color/wardrobe grade, person matte and a newly
created set are used. No optical flow, canvas remap, mesh-warped photo, or
interpolated face/body frame. The simple black shirt grade is NOT a new blazer.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time

import cv2
import imageio_ffmpeg
import mediapipe as mp
import numpy as np
from PIL import Image

W,H,FPS=720,1280,30
FF=imageio_ffmpeg.get_ffmpeg_exe()
SHOTS=[
    dict(name='Vault / opening',kind='set',start=0.,duration=1.6),
    dict(name='Eye contact / turn',kind='actor',source='front',start=.4,duration=5.6),
    dict(name='Profile / hair',kind='actor',source='side',start=2.1,duration=3.6),
    dict(name='Three quarter',kind='actor',source='front',start=7.1,duration=5.0),
    dict(name='Reverse profile',kind='actor',source='front',start=14.,duration=4.6),
    dict(name='Return to lens',kind='actor',source='front',start=21.5,duration=3.6),
    dict(name='Lean / eye contact',kind='actor',source='front',start=27.,duration=5.0),
    dict(name='Side / turn away',kind='actor',source='side',start=5.8,duration=4.2),
    dict(name='Frontal performance',kind='actor',source='front',start=33.,duration=3.6),
    dict(name='Final gesture',kind='actor',source='front',start=35.3,duration=4.0),
    dict(name='Crown above MONARCH STUDIO',kind='brand',start=0.,duration=3.6),
]


def smooth(a,lo,hi):
    u=np.clip((a-lo)/(hi-lo),0,1)
    return u*u*(3-2*u)


def image(path):
    return np.asarray(Image.open(path).convert('RGB').resize((W,H),Image.Resampling.LANCZOS))


def decode(path,start,frames):
    p=subprocess.Popen([FF,'-v','error','-ss',str(start),'-i',str(path),'-an',
        '-vf',f'fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}',
        '-frames:v',str(frames),'-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for _ in range(frames):
            b=p.stdout.read(W*H*3)
            if len(b)!=W*H*3:
                err=p.stderr.read().decode(errors='replace')
                raise RuntimeError('Source ended before the planned cut; refusing to freeze or duplicate a frame. '+err)
            yield np.frombuffer(b,np.uint8).reshape(H,W,3).copy()
    finally:
        p.stdout.close();p.wait()
        if p.returncode:
            raise RuntimeError(f'Decode failed ({p.returncode}).')


class Matte:
    def __init__(self,bg):
        self.bg=cv2.GaussianBlur(bg,(0,0),1.1).astype(np.float32)/255
        self.person=mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=0)
        self.face=mp.solutions.face_mesh.FaceMesh(static_image_mode=False,max_num_faces=1,
            refine_landmarks=False,min_detection_confidence=.50,min_tracking_confidence=.50)
        self.chin=685.;self.cx=W/2
        self.Y,self.X=np.mgrid[:H,:W].astype(np.float32)
        self.edge_count=[]

    def frame(self,raw):
        # Uniform-scale crop: no change to relative facial/body proportions.
        raw=cv2.resize(raw[240:1280,67:652],(W,H),interpolation=cv2.INTER_LANCZOS4)
        small=cv2.resize(raw,(360,640),interpolation=cv2.INTER_AREA)
        prob=self.person.process(small).segmentation_mask
        prob=cv2.resize(prob,(W,H),interpolation=cv2.INTER_LINEAR)
        mask=smooth(prob,.54,.90).astype(np.float32)
        # Spatial edge treatment only. No frame is spatially warped or synthesized.
        binary=(prob>.56).astype(np.uint8)
        n,labels,stats,_=cv2.connectedComponentsWithStats(binary,8)
        if n>1:
            person_label=1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA]))
            connected=cv2.dilate((labels==person_label).astype(np.uint8),np.ones((7,7),np.uint8))
            mask*=connected
        mask=cv2.GaussianBlur(mask,(0,0),.80)
        detected=self.face.process(small)
        face_protect=np.zeros((H,W),np.uint8)
        neck_protect=np.zeros((H,W),np.uint8)
        fh=420.
        if detected.multi_face_landmarks:
            lm=detected.multi_face_landmarks[0].landmark
            # Neck boundary is smoothed as a color-mask parameter, never geometry.
            self.chin=lm[152].y*H
            self.cx=(lm[234].x+lm[454].x)*W/2
            pts=np.array([(p.x*W,p.y*H) for p in lm],np.int32)
            hull=cv2.convexHull(pts)
            cv2.fillConvexPoly(face_protect,hull,255)
            face_protect=cv2.dilate(face_protect,np.ones((17,17),np.uint8))
            fw=float(np.ptp(pts[:,0]));fh=float(np.ptp(pts[:,1]))
            neck=np.array([(self.cx-fw*.40,self.chin-16),
                           (self.cx+fw*.40,self.chin-16),
                           (self.cx+fw*.25,self.chin+fh*.32),
                           (self.cx,self.chin+fh*.72),
                           (self.cx-fw*.25,self.chin+fh*.32)],np.int32)
            cv2.fillConvexPoly(neck_protect,neck,255)
        rgb=raw.astype(np.float32)/255
        hsv=cv2.cvtColor(raw,cv2.COLOR_RGB2HSV).astype(np.float32)
        # Preserve real skin on neck/hands. Only lavender/white textile is graded.
        is_skin=((hsv[:,:,0]<28)&(hsv[:,:,1]>19)&(rgb[:,:,0]>rgb[:,:,2]*1.06)).astype(np.uint8)*255
        is_skin=cv2.morphologyEx(is_skin,cv2.MORPH_CLOSE,np.ones((11,11),np.uint8))
        protect=np.maximum(np.maximum(is_skin,face_protect),neck_protect).astype(np.float32)/255
        protect=cv2.GaussianBlur(protect,(0,0),1.7)
        lower=smooth(self.Y,self.chin-fh*.18,self.chin-fh*.08)
        cloth=lower*(1-protect)
        purple=((hsv[:,:,0]>89)&(hsv[:,:,0]<169)&(hsv[:,:,1]>24)).astype(np.float32)
        collar=purple*(1-face_protect.astype(np.float32)/255)*lower
        cloth=np.maximum(cloth,collar)
        cloth=cv2.GaussianBlur(cloth,(0,0),1.1)[...,None]
        lum=cv2.cvtColor(raw,cv2.COLOR_RGB2GRAY).astype(np.float32)/255
        folded=cv2.bilateralFilter(lum,9,.1,7)
        folded=cv2.GaussianBlur(folded,(0,0),5.5)
        # Dark textile with retained low-frequency folds, not a fabricated suit.
        tone=.016+.13*np.power(folded,1.65)
        black= tone[...,None]*np.array([.86,.92,1.0],np.float32)
        graded=np.clip(np.power(rgb,1.045)*np.array([.79,.83,.87],np.float32)-.011,0,1)
        actor=graded*(1-cloth)+black*cloth
        # A subtle consistent light gradient, no face highlights to conceal errors.
        key=(.90+.10*np.clip(1-self.X/W,0,1))[...,None]
        actor*=key
        a=mask[...,None]
        frame=actor*a+self.bg*(1-a)
        # Background remains calm; no haze, glitch, rubber-sheet or flash masks.
        vig=np.clip(1-.14*((self.X-W/2)/(W*.72))**2-.055*((self.Y-H/2)/(H*.75))**2,.68,1)
        frame*=vig[...,None]
        self.edge_count.append(float(np.mean((mask>.1)&(mask<.9))))
        return np.uint8(np.clip(frame*255+.5,0,255)),mask

    def close(self):
        self.person.close();self.face.close()


def writer(path,n):
    path.parent.mkdir(parents=True,exist_ok=True)
    return subprocess.Popen([FF,'-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}',
        '-r',str(FPS),'-i','pipe:0','-an','-frames:v',str(n),'-c:v','libx264','-threads','2',
        '-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(path)],stdin=subprocess.PIPE)


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--test',action='store_true')
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    bg=image(a.root/'vault-empty.png')
    if a.test:
        matte=Matte(bg)
        for source,t in [('front',1.5),('front',8),('front',31.5),('side',4)]:
            raw=next(decode(a.root/'raw'/f'{source}.mp4',t,1))
            frame,mask=matte.frame(raw)
            Image.fromarray(frame).save(a.out/f'{source}_{t}_composite.jpg',quality=95)
            Image.fromarray(np.uint8(mask*255)).save(a.out/f'{source}_{t}_mask.png')
        matte.close();print('COMPOSITE_SAMPLES_READY');return
    run={'method':'Live-action VFX composite using the user-recorded real performance',
         'identity_reshaping':False,'body_reshaping':False,'new_3d_body_performance':False,
         'new_blazer':False,'wardrobe':'Original shirt color-graded toward black; not generated tailoring',
         'fps':FPS,'width':W,'height':H,'frames':1332,'duration_seconds':44.4,
         'original_sound':True,'original_scene_art':True,'shots':[]}
    for i,shot in enumerate(SHOTS):
        n=round(shot['duration']*FPS);path=a.out/f'shot_{i:02d}.mp4'
        signature=hashlib.sha256(json.dumps(shot,sort_keys=True).encode()+(a.root/'vault-empty.png').read_bytes()+Path(__file__).read_bytes()).hexdigest()
        stamp=path.with_suffix('.json')
        if path.exists() and stamp.exists() and json.loads(stamp.read_text()).get('signature')==signature:
            print('RESUME_COMPLETE_SHOT',i,flush=True);run['shots'].append(json.loads(stamp.read_text()));continue
        print('RENDER_SHOT',i,shot['name'],n,'native video frames',flush=True)
        tmp=path.with_name(path.stem+'.partial.mp4');enc=writer(tmp,n);matte=None;t0=time.monotonic();count=0
        try:
            if shot['kind']=='actor':
                matte=Matte(bg)
                for k,raw in enumerate(decode(a.root/'raw'/f"{shot['source']}.mp4",shot['start'],n)):
                    frame,mask=matte.frame(raw);enc.stdin.write(frame.tobytes());count+=1
                    if k in [0,n//2,n-1]:Image.fromarray(frame).save(a.out/f'shot_{i:02d}_{k:04d}.jpg',quality=91)
                    if k%45==0:print('FRAME',i,k+1,'/',n,flush=True)
            else:
                still=bg if shot['kind']=='set' else image(a.root/'brand-final.png')
                for k in range(n):
                    # New environment establish and static 3D-rendered brand card.
                    # No static person image appears anywhere in the edit.
                    fade=1.0
                    if shot['kind']=='set':fade=.48+.52*smooth(k,0,24)
                    if shot['kind']=='brand':fade=1.-.82*smooth(k,n-18,n-1)
                    enc.stdin.write(np.uint8(still.astype(np.float32)*fade).tobytes());count+=1
            enc.stdin.close();rc=enc.wait()
            if rc or count!=n:raise RuntimeError(f'Encoding mismatch rc={rc} frames={count}/{n}')
            tmp.replace(path)
            rec={**shot,'output':path.name,'frame_count':count,'signature':signature,
                 'render_seconds':round(time.monotonic()-t0,2)}
            stamp.write_text(json.dumps(rec,indent=2));run['shots'].append(rec)
        finally:
            if matte:matte.close()
        print('SHOT_COMPLETE',i,path.stat().st_size,flush=True)
        (a.out/'EDIT_MANIFEST.json').write_text(json.dumps(run,indent=2))
    assert sum(s['frame_count'] for s in run['shots'])==1332
    print('LIVE_ACTION_EDIT_RENDER_COMPLETE',flush=True)


if __name__=='__main__':main()
