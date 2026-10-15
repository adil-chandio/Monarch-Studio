"""Four-shot V3 enhancement over the preserved full V2.

Adds controlled arm articulation with rigid glove regions and staged echo FX;
corrects neutral-reveal headroom. Identity images, face/foot bone matrices,
all cut boundaries, original music and the other 33 V2 shots stay locked.
Still the approved photographic 2.5D method, not natural/reconstructed 3D.
"""
from __future__ import annotations
import argparse
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import time

import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image,ImageDraw,ImageOps

import rigged_main_film as v1

PATCH_SHOTS=(3,5,6,7)
PHASE_START,PHASE_END=394,492
HEADROOM_SHIFT_PX=60


def gesture_envelope(frame):
    if not PHASE_START<=frame<PHASE_END:return 0.
    u=(frame-PHASE_START)/(PHASE_END-PHASE_START-1)
    return float(v1.ease((u-.03)/.39)*(1-.30*v1.ease((u-.67)/.33)))


def echo_envelope(frame,k):
    if not PHASE_START<=frame<PHASE_END:return 0.
    u=(frame-PHASE_START)/(PHASE_END-PHASE_START-1)
    appear=float(v1.ease((u-(.02+.08*k))/.23))
    disappear=1-float(v1.ease((u-(.73+.035*k))/.24))
    return max(0.,min(1.,appear*disappear))


def hand_core_blend(side):
    x0,x1=(98,223) if side=='L' else (507,640)
    across=v1.ease((v1.X-x0)/8)*(1-v1.ease((v1.X-(x1-8))/8))
    vertical=v1.ease((v1.Y-300)/10)*(1-v1.ease((v1.Y-451)/34))
    return np.asarray(across*vertical,np.float32)


class GestureRig(v1.Rig):
    @classmethod
    def from_frozen(cls,old):
        obj=cls.__new__(cls);obj.__dict__=old.__dict__.copy()
        obj.weights={name:w.copy() for name,w in old.weights.items()}
        for side in ['L','R']:
            blend=hand_core_blend(side)
            for key in obj.names:obj.weights[key]*=1-blend
            obj.weights[f'hand.{side}']+=blend
        obj.arm_alpha={}
        for side in ['L','R']:
            q=sum(obj.weights[key] for key in [f'upper.{side}',f'fore.{side}',f'hand.{side}'])
            obj.arm_alpha[side]=obj.alpha*np.clip((q-.18)/.58,0,1)
        return obj

    def pose(self,t):
        base,error=super().pose(t)
        if not PHASE_START<=t*30<PHASE_END:return base,error
        e=gesture_envelope(t*30)
        for side,(aa,bb,ww,hh) in self.c['arms'].items():
            a=np.asarray(aa,float);w=np.asarray(ww,float)
            new_a=v1.point(base['spine'],a)
            old_target=v1.point(base[f'fore.{side}'],w)
            delta=np.array([-11.,-14.]) if side=='L' else np.array([9.,-12.])
            target=old_target+delta*e
            upper,fore,tip,residual=v1.ik(aa,bb,ww,new_a,target)
            base[f'upper.{side}']=upper;base[f'fore.{side}']=fore
            # A glove follows its forearm as one rigid object, instead of the
            # fingers being diluted by distant spine weights or stretched.
            grip=.24*math.sin(t*1.1+(0 if side=='L' else .4))
            base[f'hand.{side}']=fore@v1.about(ww,a=grip)
            error=max(error,residual)
        return base,error


def camera_for(index):
    a,b,name,z,roll,travel=next(s for s in v1.SHOTS if s[0]<=index<s[1])
    u=(index-a)/(b-a-1);t=index/30
    scale=z*(1+.045*float(v1.ease(u)))
    angle=roll+travel*float(v1.ease(u))+.3*math.sin(t*1.4)
    anchor=(360,550) if z>1.40 else (360,650)
    m=cv2.getRotationMatrix2D(anchor,angle,scale)
    m[0,2]+=1.5*math.sin(t*3.2);m[1,2]+=.9*math.sin(t*2.7)
    if 322<=index<356:m[1,2]+=HEADROOM_SHIFT_PX
    return m,scale


class EnhancedFilm(v1.Film):
    def __init__(self,root,metrics,clean_plate):
        cv2.setRNGSeed(0)
        super().__init__(root,metrics,None)
        self.frozen_open=self.rigs['open']
        rig=GestureRig.from_frozen(self.frozen_open)
        image=np.asarray(ImageOps.fit(Image.open(clean_plate).convert('RGB'),(v1.W,v1.H),Image.Resampling.LANCZOS))
        clean=cv2.cvtColor(image,cv2.COLOR_RGB2BGR).astype(np.float32)
        # Reuse the existing matching V2 room plate, colour-match it on visible
        # background only, and repair just the arm-disocclusion regions.
        outside=cv2.dilate(rig.mask,np.ones((55,55),np.uint8))==0
        parameters=[]
        for c in range(3):
            x=clean[:,:,c][outside];y=rig.image[:,:,c].astype(np.float32)[outside]
            valid=(x>15)&(x<225)&(y>15)&(y<225)
            x=x[valid][::8];y=y[valid][::8]
            gain=float(np.clip(np.cov(x,y,bias=True)[0,1]/max(float(np.var(x)),1e-6),.90,1.10))
            offset=float(np.clip(np.median(y-gain*x),-12,12))
            clean[:,:,c]=np.clip(clean[:,:,c]*gain+offset,0,255)
            parameters.append({'gain':gain,'offset':offset})
        difference=np.abs(clean-rig.image.astype(np.float32))[outside]
        self.clean_match={'mean_visible_bg_difference_after_match':float(difference.mean()),
                          'colour_parameters':parameters,'geometric_warp_applied':False}
        if self.clean_match['mean_visible_bg_difference_after_match']>10:
            raise ValueError('Existing clean plate is not a safe match for the arm backdrop.')
        arm=np.maximum(rig.arm_alpha['L'],rig.arm_alpha['R'])
        repair=cv2.dilate(np.uint8(arm>.12)*255,np.ones((49,49),np.uint8))
        repair=cv2.GaussianBlur(repair.astype(np.float32)/255,(0,0),8)
        rig.clean=rig.clean*(1-repair[:,:,None])+clean*repair[:,:,None]
        self.rigs['open']=rig

    def staged_echoes(self,f,rig,index):
        t=index/30
        for side in ['L','R']:
            aa,bb,ww,hh=[np.array(p,float) for p in rig.c['arms'][side]]
            l1=np.linalg.norm(bb-aa);l2=np.linalg.norm(ww-bb)
            for k,tilt in enumerate([-32,0,32]):
                strength=.18*echo_envelope(index,k)
                if strength<.001:continue
                angle=-90+tilt+3.5*math.sin(t*1.1+k)
                if side=='R':angle=-180-angle
                direction=np.array([math.cos(math.radians(angle)),math.sin(math.radians(angle))])
                elbow=aa+direction*l1;wrist=elbow+direction*l2;hand=wrist+direction*np.linalg.norm(hh-ww)
                mats=[v1.bone_matrix(aa,bb,aa,elbow),v1.bone_matrix(bb,ww,elbow,wrist),v1.bone_matrix(ww,hh,wrist,hand)]
                keys=[f'upper.{side}',f'fore.{side}',f'hand.{side}'];total=sum(rig.weights[key] for key in keys)+1e-7
                for key,mat in zip(keys,mats):
                    alpha=rig.arm_alpha[side]*rig.weights[key]/total
                    ghost=245-cv2.warpAffine(rig.image.astype(np.float32),mat[:2],(v1.W,v1.H))*.45
                    a=cv2.warpAffine(alpha,mat[:2],(v1.W,v1.H))[:,:,None]*strength
                    f=f*(1-a)+ghost*a
        return f

    def enhanced_scene(self,index,metrics=False):
        a,b,name,*_=self.shot_for(index)
        n=next(i for i,s in enumerate(v1.SHOTS) if s[0]==a)
        if n not in PATCH_SHOTS:raise ValueError('V3 may not render an unselected shot.')
        t=index/30;rig=self.rigs[name];actor,alpha,info=rig.render(t,metrics)
        f=rig.clean.copy()
        if name=='open':f=self.staged_echoes(f,rig,index)
        f=f*(1-alpha[:,:,None])+actor*alpha[:,:,None]
        camera,scale=camera_for(index)
        f=cv2.warpAffine(f,camera,(v1.W,v1.H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)
        gray=cv2.cvtColor(np.uint8(np.clip(f,0,255)),cv2.COLOR_BGR2GRAY).astype(np.float32)
        f=gray[:,:,None]*.91+f*.09
        gain=float(np.clip((self.luma[index]+17)/(self.local_mean[index]+17),.67,1.38))
        f*=gain*.84
        impulse=max(0.,(self.luma[index]-self.local_mean[index]-12)/100)
        f+=min(.22,impulse)*95
        dust=np.zeros((v1.H,v1.W),np.float32)
        box=rig.c['face_box'];fc=np.array([(box[0]+box[2])/2,(box[1]+box[3])/2,1.])
        centre=camera@fc;radius=max(box[2]-box[0],box[3]-box[1])*.8*scale
        for px,py,depth,speed,r in self.particles:
            x=int((px+8*math.sin(t*.3+depth))%v1.W);y=int((py-t*speed)%v1.H)
            if np.linalg.norm(np.array([x,y])-centre)<radius:continue
            cv2.circle(dust,(x,y),max(1,int(r)),5.,-1,cv2.LINE_AA)
        f+=cv2.GaussianBlur(dust,(0,0),.55)[:,:,None]
        f*=self.vignette;f=f*(1-self.mark_a)+self.mark*self.mark_a
        info.update(frame=index,scene=name,shot=n,gesture_envelope=gesture_envelope(index) if name=='open' else 0.,
                    camera_headroom_shift_px=HEADROOM_SHIFT_PX if n==3 else 0,identity_art_changed=False)
        if name=='open':
            old,_=self.frozen_open.pose(t);new,_=rig.pose(t)
            info['face_matrix_changed']=not np.allclose(old['head'],new['head'],atol=1e-12)
            info['foot_matrix_changed']=any(not np.allclose(old[f'foot.{s}'],new[f'foot.{s}'],atol=1e-12) for s in ['L','R'])
            info['hand_follow_error']=max(float(np.linalg.norm(v1.point(new[f'hand.{s}'],rig.c['arms'][s][2])-v1.point(new[f'fore.{s}'],rig.c['arms'][s][2]))) for s in ['L','R'])
        return np.uint8(np.clip(f,0,255)),info


def preview(film,work,baseline):
    work.mkdir(parents=True,exist_ok=True)
    indices=[322,339,355,400,420,440,460,480,491]
    metrics=[]
    for i in indices:
        before=work/f'v2_{i:04d}.png'
        subprocess.run([v1.FF,'-v','error','-y','-ss',str(i/30),'-i',str(baseline),'-frames:v','1',str(before)],check=True)
        frame,info=film.enhanced_scene(i,True);cv2.imwrite(str(work/f'v3_{i:04d}.png'),frame);metrics.append(info)
    (work/'PREVIEW_METRICS.json').write_text(json.dumps({'samples':metrics,'clean_plate_match':film.clean_match},indent=2)+'\n')
    for name,ids in [('HEADROOM',[339,355]),('GESTURE',[420,460])]:
        board=Image.new('RGB',(1440,1320),'#11171d');d=ImageDraw.Draw(board)
        for row,i in enumerate(ids):
            for col,v in enumerate(['v2','v3']):
                im=ImageOps.contain(Image.open(work/f'{v}_{i:04d}.png').convert('RGB'),(720,620))
                x=col*720+(720-im.width)//2;y=row*660+30;board.paste(im,(x,y));d.text((col*720+16,row*660+9),f'{v.upper()} | {i/30:.3f}s',fill='white')
        board.save(work/f'{name}_COMPARISON.jpg',quality=94)
    print('V3_PRIVATE_PREVIEW_READY',flush=True)


def render(film,root,work,base_chunks,base_report,picture,plate):
    work.mkdir(parents=True,exist_ok=True);chunks=work/'chunks';chunks.mkdir(exist_ok=True)
    prior=json.loads(base_report.read_text());assert len(prior['shots'])==37
    cfg={'method':'same limited photographic 2.5D','v1_source_sha256':v1.sha(v1.__file__),
         'v3_source_sha256':v1.sha(__file__),'plate_sha256':v1.sha(plate),
         'images':{p.name:v1.sha(p) for p in sorted((root/'assets').glob('*.png'))},
         'metrics_sha256':film.metrics_sha256,'patch_shots':list(PATCH_SHOTS),
         'new_identity_art':False,'cut_timing_changed':False,'music_changed':False}
    settings=work/'render_settings.json'
    if settings.exists() and json.loads(settings.read_text())!=cfg:raise ValueError('Stale V3 cache; choose a new directory.')
    settings.write_text(json.dumps(cfg,indent=2)+'\n');rows=[];t0=time.monotonic()
    for n,(a,b,name,*_) in enumerate(v1.SHOTS):
        dest=chunks/f'shot_{n:02d}.mp4';receipt=dest.with_suffix('.json');old=prior['shots'][n]
        if n not in PATCH_SHOTS:
            source=base_chunks/dest.name
            if not source.exists() or v1.sha(source)!=old['sha256']:raise ValueError('Missing/changed V2 chunk '+str(n))
            if dest.exists() and v1.sha(dest)!=old['sha256']:raise ValueError('Unexpected chunk conflict '+str(n))
            if not dest.exists():
                try:os.link(source,dest)
                except OSError:shutil.copy2(source,dest)
            row={'shot':n,'scene':name,'frames':b-a,'action':'reused_byte_identical_v2','sha256':v1.sha(dest)}
            receipt.write_text(json.dumps(row,indent=2)+'\n');rows.append(row);continue
        if dest.exists() and receipt.exists():
            saved=json.loads(receipt.read_text())
            if v1.sha(dest)==saved.get('sha256') and saved.get('frames')==b-a:rows.append(saved);print('REUSE_V3_PATCH',n,flush=True);continue
        temp=dest.with_name(dest.stem+'.partial.mp4')
        enc=subprocess.Popen([v1.FF,'-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s','720x1280','-r','30',
            '-i','pipe:0','-an','-frames:v',str(b-a),'-c:v','libx264','-threads','2','-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(temp)],stdin=subprocess.PIPE)
        checks=[]
        try:
            for i in range(a,b):
                frame,info=film.enhanced_scene(i,metrics=(i%10==0 or i in [a,b-1]))
                enc.stdin.write(frame.tobytes())
                if 'min_inverse_jacobian' in info:checks.append(info)
            enc.stdin.close();code=enc.wait()
            if code:raise RuntimeError('V3 shot encode failed')
        except BaseException:enc.kill();enc.wait();raise
        count,seconds=imageio_ffmpeg.count_frames_and_secs(str(temp));assert count==b-a
        os.replace(temp,dest);row={'shot':n,'scene':name,'frames':count,'action':'motion_headroom_polish','sha256':v1.sha(dest),'rig_checks':checks}
        receipt.write_text(json.dumps(row,indent=2)+'\n');rows.append(row)
        print('V3_SHOT_COMPLETE',n,name,count,'frames',flush=True)
    assert len(rows)==37
    concat=work/'concat.txt';concat.write_text(''.join("file '"+str((chunks/f'shot_{i:02d}.mp4').resolve())+"'\n" for i in range(37)))
    if picture.exists():raise FileExistsError('Refusing to overwrite existing V3 picture.')
    picture.parent.mkdir(parents=True,exist_ok=True);temp=picture.with_name(picture.stem+'.partial.mp4')
    subprocess.run([v1.FF,'-v','error','-y','-f','concat','-safe','0','-i',str(concat),'-an','-c:v','copy','-movflags','+faststart',str(temp)],check=True)
    count,seconds=imageio_ffmpeg.count_frames_and_secs(str(temp));assert count==1332 and abs(seconds-44.4)<.034
    os.replace(temp,picture)
    report={'status':'full_v3_picture_enhancement_complete','file':str(picture),'sha256':v1.sha(picture),
            'frames':count,'seconds':seconds,'fps':30,'width':720,'height':1280,
            'changed_shots':list(PATCH_SHOTS),'changed_frames':132,'reused_shots':33,'reused_frames':1200,
            'identity_images_changed':False,'face_and_foot_bone_matrices_changed':False,'shot_timing_changed':False,
            'changes':['Neutral reveal framing retains whole hair/head silhouette.','Controlled outward/upward palm gesture with rigid glove regions and unit bone lengths.','Arm echoes build and recede in staggered phases instead of constant pulsing.','Existing clean plate reused locally around arm disocclusions; no new character art.'],
            'method':'same approved limited image-based 2.5D, not natural/reconstructed 3D',
            'v2_face_and_blade_fixes_preserved_by_chunk_reuse':True,'clean_plate_match':film.clean_match,
            'settings':cfg,'shots':rows,'render_seconds':round(time.monotonic()-t0,2),'user_visual_approval':False}
    (work/'V3_PICTURE_REPORT.json').write_text(json.dumps(report,indent=2)+'\n')
    print('FULL_V3_PICTURE_READY',picture,flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True)
    p.add_argument('--metrics',type=Path,required=True);p.add_argument('--plate',type=Path,required=True)
    p.add_argument('--baseline',type=Path,required=True);p.add_argument('--base-chunks',type=Path,required=True)
    p.add_argument('--base-report',type=Path,required=True);p.add_argument('--output',type=Path);p.add_argument('--preview',action='store_true')
    a=p.parse_args();film=EnhancedFilm(a.root,a.metrics,a.plate)
    if a.preview:preview(film,a.work,a.baseline)
    else:
        if not a.output:raise ValueError('--output required')
        render(film,a.root,a.work,a.base_chunks,a.base_report,a.output,a.plate)


if __name__=='__main__':main()
