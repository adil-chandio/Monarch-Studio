"""Assemble the full, explicitly labelled live-action alternative draft.

No reference soundtrack is copied. Source speech is not used. All music and
sound accents below are synthesized from oscillators/noise for this edit.
Technical verification never certifies likeness, photorealism, or user approval.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import wave

import imageio_ffmpeg
import numpy as np
from scipy.signal import butter, sosfilt

FF=imageio_ffmpeg.get_ffmpeg_exe()
SR=48000
DURATION=44.4


def sound(path):
    rng=np.random.default_rng(7194)
    t=np.arange(round(SR*DURATION),dtype=np.float32)/SR
    bed=(.032*np.sin(2*np.pi*55*t)+.011*np.sin(2*np.pi*110.06*t))* (.70+.18*np.sin(2*np.pi*.065*t))
    out=np.stack([bed.copy(),bed.copy()],axis=1)
    def add(start,x,level=1.,pan=0.):
        i=round(start*SR);n=min(len(x),len(out)-i)
        if n<=0:return
        l=np.sqrt((1-pan)/2);r=np.sqrt((1+pan)/2)
        out[i:i+n,0]+=np.asarray(x[:n],np.float32)*level*l
        out[i:i+n,1]+=np.asarray(x[:n],np.float32)*level*r
    def kick(length=.36):
        q=np.arange(round(length*SR),dtype=np.float32)/SR
        f=47+76*np.exp(-q*40)
        return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-q*14)*(1-np.exp(-q*700))
    beats=np.arange(1.6,40.75,.6)
    hp=butter(2,2400,btype='highpass',fs=SR,output='sos')
    for k,start in enumerate(beats):
        add(start,kick(),.25 if k%4==0 else .145)
        for off in [0,.30]:
            q=np.arange(round(.07*SR),dtype=np.float32)/SR
            h=sosfilt(hp,rng.normal(size=len(q))).astype(np.float32)*np.exp(-q*65)
            add(start+off,h,.024,(-.34 if k%2 else .34))
        if k%2:
            q=np.arange(round(.16*SR),dtype=np.float32)/SR
            n=rng.normal(size=len(q)).astype(np.float32)*np.exp(-q*25)
            add(start,n,.049,.10)
    boundaries=[1.6,7.2,10.8,15.8,20.4,24.,29.,33.2,36.8,40.8]
    for k,start in enumerate(boundaries):
        q=np.arange(round(.42*SR),dtype=np.float32)/SR
        rush=sosfilt(butter(2,[340,2300],btype='bandpass',fs=SR,output='sos'),rng.normal(size=len(q)))
        rush*=np.sin(np.pi*q/.42)**2
        add(max(0,start-.32),rush,.070,(-.38 if k%2 else .38))
        add(start,kick(.45),.24)
    q=np.arange(round(3.4*SR),dtype=np.float32)/SR
    for f,a,pan in [(440,.10,-.2),(660,.065,.20),(880,.035,-.1),(1320,.028,.3)]:
        ch=np.sin(2*np.pi*f*q)*np.exp(-q*1.4)*(1-np.exp(-q*120))
        add(40.84,ch,a,pan)
    out*=np.minimum(1,t/.18)[:,None]
    out*=np.minimum(1,(DURATION-t)/.55)[:,None]
    out=np.clip(out,-.93,.93)
    with wave.open(str(path),'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR)
        w.writeframes(np.int16(out*32767).tobytes())


def main():
    p=argparse.ArgumentParser();p.add_argument('--shots',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((a.shots/'EDIT_MANIFEST.json').read_text())
    assert len(manifest['shots'])==11,'Every shot must be completed before muxing.'
    assert sum(s['frame_count'] for s in manifest['shots'])==1332
    concat=a.shots/'concat.txt'
    concat.write_text(''.join("file '"+str((a.shots/s['output']).resolve()).replace("'","'\\''")+"'\n" for s in manifest['shots']))
    raw=a.shots/'original_score.wav';normal=a.shots/'original_score_48k.wav'
    sound(raw)
    print('NORMALIZE_ORIGINAL_AUDIO',flush=True)
    r=subprocess.run([FF,'-hide_banner','-y','-i',str(raw),'-af',
        'loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json','-ar','48000','-c:a','pcm_s16le',str(normal)],capture_output=True,text=True,check=True)
    logs=r.stderr;lo=logs.rfind('{');hi=logs.rfind('}')
    normalization=json.loads(logs[lo:hi+1]) if lo>=0 else {'raw_log':logs[-1000:]}
    final=a.out/'MONARCH_VAULT_LIVE_ACTION_DRAFT.mp4';tmp=a.out/'MONARCH_VAULT_LIVE_ACTION_DRAFT.partial.mp4'
    print('MUX_COMPLETE_EDIT',flush=True)
    subprocess.run([FF,'-v','error','-y','-f','concat','-safe','0','-i',str(concat),'-i',str(normal),
        '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000',
        '-t','44.4','-movflags','+faststart',str(tmp)],check=True)
    tmp.replace(final)
    print('VERIFY_FULL_DECODE',flush=True)
    n,secs=imageio_ffmpeg.count_frames_and_secs(str(final))
    assert n==1332,(n,secs)
    assert abs(secs-44.4)<.05,secs
    probe=subprocess.run([FF,'-hide_banner','-i',str(final)],capture_output=True,text=True).stderr
    assert '720x1280' in probe and '30 fps' in probe and '48000 Hz' in probe and 'stereo' in probe,probe
    report={
        'status':'complete_live_action_alternative_draft_not_the_requested_generated_3d_final',
        'file':final.name,'bytes':final.stat().st_size,
        'sha256':hashlib.sha256(final.read_bytes()).hexdigest(),
        'md5':hashlib.md5(final.read_bytes()).hexdigest(),
        'width':720,'height':1280,'fps':30,'decoded_frames':n,'duration_seconds':secs,
        'method':manifest['method'],'source_motion':'Actual personal footage supplied by the user',
        'body_warps':False,'optical_flow':False,'generated_body_performance':False,
        'wardrobe':'Original recorded shirt with a black color grade. Not a newly generated tailored suit.',
        'background':'New AI-generated original vault environment from this task',
        'ending':'New 3D-rendered gold crown placed above MONARCH STUDIO; static held brand card',
        'audio':'Original oscillator/noise sound design; no copied reference audio or source speech',
        'audio_normalization':normalization,
        'technical_checks':{'full_decode':True,'frame_count':True,'duration':True,'portrait_resolution':True,'audio_48k_stereo':True},
        'visual_acceptance':{'user_approved':False,'perfect_face_or_costume_match_claimed':False,
            'known_limits':['Original selfie footage is soft/filtered.',
                'Automatic hair/shoulder matting and clothing color masks can be imperfect.',
                'This does not create new full-body fight/walk choreography like the reference.',
                'The generated photoreal concept image is not presented as a moving 3D character.']}}
    (a.out/'DELIVERY_README.json').write_text(json.dumps(report,indent=2))
    for second,name in [(3.0,'REVIEW_FRAME.jpg'),(42.2,'CROWN_ENDING.jpg')]:
        subprocess.run([FF,'-v','error','-y','-ss',str(second),'-i',str(final),'-frames:v','1','-q:v','2',str(a.out/name)],check=True)
    print('DELIVERED_LOCAL',final,final.stat().st_size,'bytes',n,'frames',secs,'seconds',flush=True)


if __name__=='__main__':main()
