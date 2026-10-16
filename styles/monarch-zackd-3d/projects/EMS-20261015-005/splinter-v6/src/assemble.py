#!/usr/bin/env python3
"""Deterministic original sound bed/SFX, voice placement, subtitles and MP4 mux.
No reference audio is used. Master loudness is measured, then normalized in
FFmpeg's two-pass EBU R128 mode. Run --audio-only while picture renders.
"""
from __future__ import annotations
import argparse, hashlib, json, math, re, subprocess, wave, sys
from pathlib import Path
import numpy as np
import imageio_ffmpeg
from sound_design import create_soundtrack

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
    controls=json.loads((ROOT/'data/motion.json').read_text())
    tl['sound_events']=[{**e,'anchor_time':controls['cues'][e['visual_cue']],'time':controls['cues'][e['visual_cue']]-e.get('pre_roll',0)} if e.get('visual_cue') else e for e in tl['sound_events']]
    effects,sound_report,music,foley=create_soundtrack(tl,voice)
    stereo=effects+voice[:,None]
    if np.max(np.abs(stereo))>=.99:raise ValueError('Premaster clips; reduce cue/bed gain before normalization')
    (out/'SOUND_DESIGN_REPORT.json').write_text(json.dumps(sound_report,indent=2)+'\n')
    write_wav(out/'voice_timeline.wav',voice)
    write_wav(out/'sound_design.wav',effects)
    write_wav(out/'music_score.wav',music)
    write_wav(out/'tactile_effects.wav',foley)
    write_wav(out/'premaster.wav',stereo)
    analysis=run(['-i',out/'premaster.wav','-af','loudnorm=I=-16:TP=-1.5:LRA=8:print_format=json','-f','null','-'],capture_output=True,text=True).stderr
    loud=json.loads(re.findall(r'\{\s*"input_i"[\s\S]*?\}',analysis)[-1])
    filt=('loudnorm=I=-16:TP=-1.5:LRA=8:linear=true:'
          f"measured_I={loud['input_i']}:measured_TP={loud['input_tp']}:"
          f"measured_LRA={loud['input_lra']}:measured_thresh={loud['input_thresh']}:"
          f"offset={loud['target_offset']}:print_format=json")
    result=run(['-loglevel','info','-y','-i',out/'premaster.wav','-af',filt,'-ar',SR,'-ac','2','-c:a','pcm_s24le',out/'mix.wav'],capture_output=True,text=True)
    measured=json.loads(re.findall(r'\{\s*"input_i"[\s\S]*?\}',result.stderr)[-1])
    receipt={'sample_rate':SR,'channels':2,'duration':n/SR,'voice_id':'voice-00','voice_selection':'The user-liked v2 WAV assets reused without resynthesis or time stretching','clips':receipts,'premaster_loudness':loud,'normalized_loudness':measured,'sound_design':'V6 perspective-rebalanced original arranged piano/cello/string score from credited CC-BY3.0 instrument notes;8 tightened procedural tactile cues with contact/release anchor timing. No reference audio. See music attribution and SOUND_DESIGN_REPORT.json.'}
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
    final=a.out/tl['master_filename']
    run(['-loglevel','error','-y','-i',picture,'-i',a.out/'mix.wav','-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar',SR,'-t',tl['duration'],'-movflags','+faststart','-metadata','title=KAANTA Macro Director Cut v6 | Monarch WF-02','-metadata','comment=Original3D educational Macro Director Cut v6. Original score arrangement: Monarch Studio. Instrument notes: FluidR3 GM via MIDI.js Soundfonts (Benjamin Gleitzman),CC BY3.0 US. github.com/gleitz/midi-js-soundfonts;creativecommons.org/licenses/by/3.0/us/. Samples arranged/processed. No reference audio. Not personalized medical advice.',final])
    receipt={'file':final.name,'size':final.stat().st_size,'sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'md5':hashlib.md5(final.read_bytes()).hexdigest(),'duration':tl['duration'],'fps':tl['fps'],'native_3d_size':[tl['width'],tl['height']],'reference_audio_used':False,'reference_frames_used':False}
    (a.out/'master-identity.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
