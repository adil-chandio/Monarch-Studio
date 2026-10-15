"""Targeted V2 patch of the completed V1, NOT a new character/movie restart.

Only four close-up shots and the blade shot are re-rendered. The other 32 V1
shot bitstreams, all cut boundaries/camera/rig trajectories, and reference audio
are retained. V1 itself and its frozen renderer are never overwritten.
"""
from __future__ import annotations
import argparse
import hashlib
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
from PIL import Image,ImageOps,ImageDraw,ImageFont

import rigged_main_film as v1
from conform_reference_audio import media_hash

PATCH_SCENES={'close','blade'}


def expected_patch_shots(shots):
    return [i for i,s in enumerate(shots) if s[2] in PATCH_SCENES]


def face_gain_map(global_gain,mask,cap=1.12):
    protected=min(float(global_gain),cap)
    return float(global_gain)*(1-mask)+protected*mask


def clean_plate_composite(original_clean,clean_plate,foreground_mask):
    # Replace the old inpainting footprint only. Keep the surrounding room from V1.
    expanded=cv2.dilate(np.uint8(foreground_mask>0)*255,np.ones((61,61),np.uint8))
    blend=cv2.GaussianBlur(expanded.astype(np.float32)/255,(0,0),9)
    return original_clean*(1-blend[:,:,None])+clean_plate.astype(np.float32)*blend[:,:,None],blend


class PolishFilm(v1.Film):
    def __init__(self,root,metrics_csv,outro,clean_plate):
        cv2.setRNGSeed(0)
        super().__init__(root,metrics_csv,outro)
        p=np.asarray(ImageOps.fit(Image.open(clean_plate).convert('RGB'),(v1.W,v1.H),Image.Resampling.LANCZOS))
        plate=cv2.cvtColor(p,cv2.COLOR_RGB2BGR)
        rig=self.rigs['blade']
        visible=cv2.dilate(rig.mask,np.ones((65,65),np.uint8))==0
        difference=np.abs(rig.image.astype(np.float32)-plate.astype(np.float32))[visible]
        self.background_match={'median_abs_visible_bg_difference':float(np.median(difference)),
                               'mean_abs_visible_bg_difference':float(np.mean(difference)),
                               'geometric_warp_applied':False}
        if self.background_match['mean_abs_visible_bg_difference']>12:
            raise ValueError('Clean plate does not sufficiently match the locked camera/background.')
        self.blade_clean,self.patch_blend=clean_plate_composite(rig.clean,plate,rig.mask)

    def face_mask(self,rig,t,camera):
        x0,y0,x1,y1=rig.c['face_box']
        cx,cy=(x0+x1)/2,(y0+y1)/2
        rx=(x1-x0)*.64;ry=(y1-y0)*.68
        radius=((v1.X-cx)/rx)**2+((v1.Y-cy)/ry)**2
        mask=np.clip((1-radius)/.35,0,1).astype(np.float32)
        poses,_=rig.pose(t)
        combined=np.vstack([camera,[0.,0.,1.]])@poses['head']
        return cv2.warpAffine(mask,combined[:2],(v1.W,v1.H),flags=cv2.INTER_LINEAR)

    def patched_scene(self,index):
        t=index/v1.FPS;s=self.shot_for(index);start,end,name,z,roll,travel=s
        if name not in PATCH_SCENES:raise ValueError('This patch may not render an unaffected shot.')
        u=(index-start)/max(1,end-start-1);rig=self.rigs[name]
        actor,alpha,info=rig.render(t,metrics=False)
        clean=self.blade_clean if name=='blade' else rig.clean
        f=clean*(1-alpha[:,:,None])+actor*alpha[:,:,None]
        # Exact V1 camera parameters; no change to face/body geometry or framing.
        anchor=(360,630) if name=='close' else (400,700)
        scale=z*(1+.045*float(v1.ease(u)))
        angle=roll+travel*float(v1.ease(u))+.3*math.sin(t*1.4)
        camera=cv2.getRotationMatrix2D(anchor,angle,scale)
        camera[0,2]+=1.5*math.sin(t*3.2);camera[1,2]+=.9*math.sin(t*2.7)
        f=cv2.warpAffine(f,camera,(v1.W,v1.H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)
        f[:,:,2]*=1.05;f[:,:,0]*=.94
        gain=float(np.clip((self.luma[index]+17)/(self.local_mean[index]+17),.67,1.38))
        impulse=min(.22,max(0.,(self.luma[index]-self.local_mean[index]-12)/100))*95
        mask=self.face_mask(rig,t,camera) if name=='close' else np.zeros((v1.H,v1.W),np.float32)
        if name=='close':
            f*=face_gain_map(gain,mask)[:,:,None]*.92
            f+=impulse*(1-.85*mask[:,:,None])
        else:
            f*=gain*.92;f+=impulse
        # Retain the existing atmosphere and transient accents.
        dust=np.zeros((v1.H,v1.W),np.float32);face_center=None
        if name=='close':
            box=rig.c['face_box'];fc=np.array([(box[0]+box[2])/2,(box[1]+box[3])/2,1.])
            face_center=camera@fc;face_radius=max(box[2]-box[0],box[3]-box[1])*.8*scale
        for px,py,depth,speed,radius in self.particles:
            xx=int((px+8*math.sin(t*.3+depth))%v1.W);yy=int((py-t*speed)%v1.H)
            if face_center is not None and np.linalg.norm(np.array([xx,yy])-face_center)<face_radius:continue
            cv2.circle(dust,(xx,yy),max(1,int(radius)),5.,-1,cv2.LINE_AA)
        f+=cv2.GaussianBlur(dust,(0,0),.55)[:,:,None]
        if self.delta[index]>28:
            band_y=(index*73)%v1.H;h=2+(index%4)
            f[band_y:band_y+h]=np.roll(f[band_y:band_y+h],(index%9)-4,axis=1)
        f*=self.vignette
        f=f*(1-self.mark_a)+self.mark*self.mark_a
        info.update(frame=index,scene=name,face_light_protected=name=='close',clean_background_repair=name=='blade',geometry_changed=False,global_light_gain=gain)
        return np.uint8(np.clip(f,0,255)),info,mask


def preview(film,root,work,v1_movie):
    work.mkdir(parents=True,exist_ok=True)
    indices=[789,1083,1120,1172,907,924,952]
    for index in indices:
        before=work/f'v1_{index:04d}.png'
        subprocess.run([v1.FF,'-v','error','-y','-ss',str(index/v1.FPS),'-i',str(v1_movie),'-frames:v','1',str(before)],check=True)
        after,info,mask=film.patched_scene(index)
        cv2.imwrite(str(work/f'v2_{index:04d}.png'),after)
        if info['scene']=='close':
            b=cv2.imread(str(before));m=mask>.7
            info['before_face_mean_luma']=float(cv2.cvtColor(b,cv2.COLOR_BGR2GRAY)[m].mean())
            info['after_face_mean_luma']=float(cv2.cvtColor(after,cv2.COLOR_BGR2GRAY)[m].mean())
            info['before_face_highlight_fraction']=float((b.max(axis=2)[m]>235).mean())
            info['after_face_highlight_fraction']=float((after.max(axis=2)[m]>235).mean())
        (work/f'metrics_{index:04d}.json').write_text(json.dumps(info,indent=2)+'\n')
    for group,ids in [('FACE',[789,1083]),('BLADE',[907,924])]:
        board=Image.new('RGB',(1440,1320),'#11171d');d=ImageDraw.Draw(board)
        for row,i in enumerate(ids):
            for col,version in enumerate(['v1','v2']):
                im=ImageOps.contain(Image.open(work/f'{version}_{i:04d}.png').convert('RGB'),(720,620))
                x=col*720+(720-im.width)//2;y=row*660+30
                board.paste(im,(x,y));d.text((col*720+16,row*660+10),f'{version.upper()} | {i/v1.FPS:.3f}s',fill='white')
        board.save(work/f'{group}_COMPARISON.jpg',quality=94)
    print('TARGETED_POLISH_PREVIEW_READY',flush=True)


def patch_render(film,root,work,base_cache,v1_report,picture,plate):
    work.mkdir(parents=True,exist_ok=True);chunks=work/'chunks';chunks.mkdir(exist_ok=True)
    report=json.loads(v1_report.read_text())
    if v1.sha(v1.__file__)!=report['settings']['renderer_sha256']:
        raise ValueError('The frozen V1 renderer changed; cannot certify unchanged geometry/coverage.')
    for name,h in report['settings']['images'].items():
        if v1.sha(root/'assets'/name)!=h:raise ValueError('V1 source art changed: '+name)
    patch=expected_patch_shots(v1.SHOTS)
    assert patch==[20,25,30,32,34]
    cfg={'v1_picture_sha256':report['sha256'],'v1_renderer_sha256':report['settings']['renderer_sha256'],
         'patch_renderer_sha256':v1.sha(__file__),'plate_sha256':v1.sha(plate),'patch_shots':patch,
         'all_cut_boundaries_unchanged':True,'character_geometry_redesigned':False,'music_changed':False}
    settings=work/'patch_settings.json'
    if settings.exists() and json.loads(settings.read_text())!=cfg:raise ValueError('Stale polish cache; choose a fresh work directory.')
    settings.write_text(json.dumps(cfg,indent=2)+'\n')
    results=[];start_time=time.monotonic()
    for n,(a,b,name,*_) in enumerate(v1.SHOTS):
        dest=chunks/f'shot_{n:02d}.mp4';stamp=dest.with_suffix('.json');source=base_cache/'chunks'/dest.name
        old=report['shots'][n]
        if n not in patch:
            if not source.exists() or v1.sha(source)!=old['sha256']:raise ValueError('Missing/changed frozen V1 chunk '+str(n))
            if dest.exists() and v1.sha(dest)!=old['sha256']:raise ValueError('Unexpected V2 chunk conflict '+str(n))
            if not dest.exists():
                try:os.link(source,dest)
                except OSError:shutil.copy2(source,dest)
            row={'shot':n,'scene':name,'frames':b-a,'action':'reused_byte_identical_v1','sha256':v1.sha(dest)}
            stamp.write_text(json.dumps(row,indent=2)+'\n');results.append(row);continue
        if dest.exists() and stamp.exists():
            old_patch=json.loads(stamp.read_text())
            if v1.sha(dest)==old_patch.get('sha256') and old_patch.get('frames')==b-a:
                results.append(old_patch);print('REUSE_COMPLETED_PATCH',n,flush=True);continue
        temp=dest.with_name(dest.stem+'.partial.mp4')
        enc=subprocess.Popen([v1.FF,'-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{v1.W}x{v1.H}',
            '-r',str(v1.FPS),'-i','pipe:0','-an','-frames:v',str(b-a),'-c:v','libx264','-threads','2',
            '-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(temp)],stdin=subprocess.PIPE)
        try:
            for frame in range(a,b):
                img,_,_=film.patched_scene(frame);enc.stdin.write(img.tobytes())
            enc.stdin.close();code=enc.wait()
            if code:raise RuntimeError('Patch encode failed: '+str(n))
        except BaseException:enc.kill();enc.wait();raise
        count,secs=imageio_ffmpeg.count_frames_and_secs(str(temp));assert count==b-a
        os.replace(temp,dest)
        row={'shot':n,'scene':name,'frames':count,'action':'targeted_polish_patch','sha256':v1.sha(dest)}
        stamp.write_text(json.dumps(row,indent=2)+'\n');results.append(row)
        print('PATCH_COMPLETE',n,name,count,'frames',flush=True)
    assert len(results)==37
    for row in results:
        if row['shot'] not in patch:assert row['sha256']==report['shots'][row['shot']]['sha256']
    concat=work/'concat.txt';concat.write_text(''.join("file '"+str((chunks/f'shot_{n:02d}.mp4').resolve())+"'\n" for n in range(37)))
    picture.parent.mkdir(parents=True,exist_ok=True)
    if picture.exists():raise FileExistsError('Refusing to overwrite an existing picture export.')
    temp=picture.with_name(picture.stem+'.partial.mp4')
    subprocess.run([v1.FF,'-v','error','-y','-f','concat','-safe','0','-i',str(concat),'-an','-c:v','copy','-movflags','+faststart',str(temp)],check=True)
    frames,seconds=imageio_ffmpeg.count_frames_and_secs(str(temp));assert frames==1332 and abs(seconds-44.4)<.034
    os.replace(temp,picture)
    result={'status':'targeted_full_picture_polish_complete','file':str(picture),'sha256':v1.sha(picture),
            'frames':frames,'seconds':seconds,'fps':30,'width':720,'height':1280,
            'changed_shots':patch,'changed_frames':sum(v1.SHOTS[i][1]-v1.SHOTS[i][0] for i in patch),
            'reused_shots':37-len(patch),'reused_frames':1332-sum(v1.SHOTS[i][1]-v1.SHOTS[i][0] for i in patch),
            'unchanged_shots_byte_identical':True,'cut_timing_changed':False,'camera_or_rig_trajectories_changed':False,
            'identity_images_changed':False,'method':'same approved limited image-based 2.5D',
            'changes':['Clean reconstructed backdrop replaces only the old blade-inpainting footprint.','Bright portrait pulses retain skin detail without changing facial geometry; background pulses remain.'],
            'background_match':film.background_match,'settings':cfg,'shots':results,
            'render_seconds':round(time.monotonic()-start_time,2),'visual_approval_claimed':False,'reference_audio_mux_pending':True}
    (work/'POLISH_REPORT.json').write_text(json.dumps(result,indent=2)+'\n')
    print('FULL_V2_PICTURE_READY',picture,'reused',result['reused_shots'],'shots',flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True)
    p.add_argument('--metrics',type=Path,required=True);p.add_argument('--outro',type=Path,required=True)
    p.add_argument('--plate',type=Path,required=True);p.add_argument('--v1-movie',type=Path,required=True)
    p.add_argument('--v1-report',type=Path,required=True);p.add_argument('--base-cache',type=Path,required=True)
    p.add_argument('--output',type=Path);p.add_argument('--preview',action='store_true');a=p.parse_args()
    film=PolishFilm(a.root,a.metrics,a.outro,a.plate)
    if a.preview:preview(film,a.root,a.work,a.v1_movie)
    else:
        if not a.output:raise ValueError('--output required')
        patch_render(film,a.root,a.work,a.base_cache,a.v1_report,a.output,a.plate)


if __name__=='__main__':main()
