#!/usr/bin/env python3
"""Deterministic original sound bed/SFX, voice placement, subtitles and MP4 mux.
No reference audio is used. Master loudness is measured, then normalized in
FFmpeg's two-pass EBU R128 mode. Run --audio-only while picture renders.
"""
from __future__ import annotations
import argparse, hashlib, json, math, re, subprocess, wave
from pathlib import Path
import numpy as np
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 48000

def run(args, **kwargs):
    return subprocess.run([FF, '-hide_banner', *map(str,args)], check=True, **kwargs)

def write_wav(p, audio):
    audio=np.clip(audio,-.999,.999)
    with wave.open(str(p),'wb') as f:
        f.setnchannels(audio.shape[1] if audio.ndim==2 else 1)
        f.setsampwidth(2);f.setframerate(SR)
        f.writeframes((audio*32767).astype('<i2').tobytes())

def timecode(t):
    ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

def synth_event(kind, rng):
    durations={'tap':.17,'whoosh':.48,'metal':.42,'lift':.25,'pulse':.36,'warn':.65,'bell':.72}
    t=np.arange(round(durations[kind]*SR))/SR
    noise=rng.normal(0,1,len(t))
    def soft_noise(cut=25):
        return np.convolve(noise,np.ones(cut)/cut,mode='same')
    if kind=='whoosh':
        a=soft_noise(18)*np.sin(np.pi*t/t[-1])**2
    elif kind=='tap':
        a=(.7*np.sin(2*np.pi*(310*t-380*t*t))+.25*noise)*np.exp(-t*43)
    elif kind=='metal':
        a=sum(v*np.sin(2*np.pi*f*t) for f,v in [(2460,.50),(3319,.24),(5103,.13),(842,.2)])*np.exp(-t*18)
    elif kind=='lift':
        a=(soft_noise(11)+.16*np.sin(2*np.pi*(640*t+1250*t*t)))*np.sin(np.pi*t/t[-1])**2
    elif kind=='pulse':
        a=np.sin(2*np.pi*(135*t-35*t*t))*np.sin(np.pi*t/t[-1])**2*np.exp(-t*6)
    elif kind=='warn':
        a=(np.sin(2*np.pi*174.61*t)+.35*np.sin(2*np.pi*349.23*t))*np.sin(np.pi*np.minimum(t/.15,1)/2)*np.exp(-t*6)
    else:
        a=(np.sin(2*np.pi*587.33*t)+.18*np.sin(2*np.pi*1174.66*t))*np.sin(np.pi*np.minimum(t/.04,1)/2)*np.exp(-t*7)
    a[:min(240,len(a))]*=np.linspace(0,1,min(240,len(a)))
    return a

def make_audio(tl,out):
    n=round(tl['duration']*SR);voice=np.zeros(n,np.float64)
    receipts=[]
    for clip in tl['narration']:
        p=ROOT/'assets/vo'/clip['file']
        raw=run(['-loglevel','error','-i',p,'-af','highpass=f=70,lowpass=f=11000,acompressor=threshold=0.20:ratio=2:attack=8:release=80:makeup=1.1','-ar',SR,'-ac','1','-f','f32le','pipe:1'],capture_output=True).stdout
        a=np.frombuffer(raw,dtype='<f4').astype(np.float64)
        start=round(clip['start']*SR)
        if start+len(a)>n:raise ValueError('Voice exceeds picture duration')
        voice[start:start+len(a)]+=a
        receipts.append({'file':clip['file'],'start':clip['start'],'measured_duration':len(a)/SR,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    rng=np.random.default_rng(20261015);t=np.arange(n)/SR
    # Quiet D-minor/add-nine pad: newly synthesized, not sampled music.
    pad=np.zeros(n)
    for f,amp in [(73.416,.0032),(146.832,.0028),(220,.0018),(293.665,.0013),(349.228,.0010),(329.628,.0007)]:
        pad+=amp*np.sin(2*np.pi*f*t+.15*np.sin(2*np.pi*.12*t))*(.8+.2*np.sin(2*np.pi*.18*t+f))
    pad*=np.clip(t/1.1,0,1)*np.clip((tl['duration']-t)/1.4,0,1)
    pad*=np.where((t>18.85)&(t<22.15),.28,1)
    # Sample-envelope voice ducking; reduces bed under speech instead of raising it.
    envelope=np.convolve(np.abs(voice[::240]),np.ones(41)/41,mode='same')
    duck=np.interp(np.arange(n),np.arange(len(envelope))*240,envelope)
    duck=1-.63*np.clip(duck/.10,0,1)
    pad*=duck
    stereo=np.stack([pad,pad],axis=1)
    for event in tl['sound_events']:
        a=synth_event(event['kind'],rng)*event['gain']
        start=round(event['time']*SR);count=min(len(a),n-start)
        pan=.20*math.sin(event['time']*1.7)
        stereo[start:start+count,0]+=a[:count]*(1-pan)
        stereo[start:start+count,1]+=a[:count]*(1+pan)
    effects=stereo.copy();stereo+=voice[:,None]
    write_wav(out/'voice_timeline.wav',voice)
    write_wav(out/'original_sound_design.wav',effects)
    write_wav(out/'premaster.wav',stereo)
    analysis=run(['-i',out/'premaster.wav','-af','loudnorm=I=-16:TP=-1.5:LRA=8:print_format=json','-f','null','-'],capture_output=True,text=True).stderr
    loud=json.loads(re.findall(r'\{\s*"input_i"[\s\S]*?\}',analysis)[-1])
    filt=('loudnorm=I=-16:TP=-1.5:LRA=8:linear=true:'
          f"measured_I={loud['input_i']}:measured_TP={loud['input_tp']}:"
          f"measured_LRA={loud['input_lra']}:measured_thresh={loud['input_thresh']}:"
          f"offset={loud['target_offset']}:print_format=json")
    result=run(['-loglevel','info','-y','-i',out/'premaster.wav','-af',filt,'-ar',SR,'-ac','2','-c:a','pcm_s24le',out/'mix.wav'],capture_output=True,text=True)
    measured=json.loads(re.findall(r'\{\s*"input_i"[\s\S]*?\}',result.stderr)[-1])
    receipt={'sample_rate':SR,'channels':2,'duration':n/SR,'voice_id':'voice-00','voice_selection':'Current-session user audition choice','clips':receipts,'premaster_loudness':loud,'normalized_loudness':measured,'sound_design':'Original NumPy synthesis; no reference audio or downloaded music'}
    (out/'audio-report.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
    srt='\n\n'.join(f"{i}\n{timecode(c['start'])} --> {timecode(c['end'])}\n{c['text']}" for i,c in enumerate(tl['captions'],1))+'\n'
    (out/'KAANTA_Roman_Urdu.srt').write_text(srt)
    print(json.dumps({'audio_complete':True,'duration':n/SR,'loudness':measured},indent=2))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=ROOT/'build');ap.add_argument('--audio-only',action='store_true');ap.add_argument('--picture',type=Path);ap.add_argument('--reuse-audio',action='store_true');a=ap.parse_args()
    a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=True)
    tl=json.loads((ROOT/'data/timeline.json').read_text())
    if not a.reuse_audio or not (a.out/'mix.wav').exists():make_audio(tl,a.out)
    if a.audio_only:return
    picture=a.picture or a.out/'picture.mp4'
    if not picture.exists():raise SystemExit('Picture does not exist: run the native-frame renderer first.')
    final=a.out/'KAANTA_WF02_1080x1920_FINAL.mp4'
    run(['-loglevel','error','-y','-i',picture,'-i',a.out/'mix.wav','-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar',SR,'-t',tl['duration'],'-movflags','+faststart','-metadata','title=KAANTA | Monarch WF-02','-metadata','comment=Original-finished 3D educational visualization. Urdu narration; Roman Urdu captions. Not personalized medical advice.',final])
    receipt={'file':final.name,'size':final.stat().st_size,'sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'md5':hashlib.md5(final.read_bytes()).hexdigest(),'duration':tl['duration'],'fps':tl['fps'],'native_3d_size':[tl['width'],tl['height']],'reference_audio_used':False,'reference_frames_used':False}
    (a.out/'master-identity.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
