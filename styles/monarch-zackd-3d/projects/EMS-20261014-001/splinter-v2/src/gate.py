#!/usr/bin/env python3
"""Decode and measure the actual delivered MP4; never certify from filenames.
The visual sampling sheet supplements technical checks; it is not clinical QA.
"""
from __future__ import annotations
import argparse, hashlib, json, re, struct, subprocess
from pathlib import Path
import av
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parents[1]
FF=imageio_ffmpeg.get_ffmpeg_exe()

def atom_order(p):
    order=[]
    with p.open('rb') as f:
        offset=0;size=p.stat().st_size
        while offset+8<=size:
            f.seek(offset);n,kind=struct.unpack('>I4s',f.read(8))
            if n==1:n=struct.unpack('>Q',f.read(8))[0]
            if n==0:n=size-offset
            if n<8:break
            order.append(kind.decode('latin1'));offset+=n
    return order

def longest_run(values):
    best=cur=0
    for val in values:
        cur=cur+1 if val else 0;best=max(best,cur)
    return best

def main():
    ap=argparse.ArgumentParser();ap.add_argument('master',type=Path);ap.add_argument('--out',type=Path,default=ROOT/'build');args=ap.parse_args()
    p=args.master.resolve();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    tl=json.loads((ROOT/'data/timeline.json').read_text());expected=round(tl['duration']*tl['fps'])
    checks=[]
    def check(name,passed,details):checks.append({'name':name,'passed':bool(passed),'details':details})
    with av.open(str(p)) as c:
        v=c.streams.video[0];a=c.streams.audio[0]
        info={'video_codec':v.codec_context.name,'width':v.width,'height':v.height,'fps':float(v.average_rate),'pixel_format':v.codec_context.format.name,'duration':float(c.duration/av.time_base),'audio_codec':a.codec_context.name,'audio_rate':a.codec_context.sample_rate,'audio_channels':a.codec_context.channels}
    check('H.264 portrait native-size delivery',info['video_codec']=='h264' and [info['width'],info['height']]==[1080,1920] and info['pixel_format']=='yuv420p',info)
    check('Frame rate and container duration',abs(info['fps']-tl['fps'])<.001 and abs(info['duration']-tl['duration'])<.06,info)
    check('AAC stereo 48kHz',info['audio_codec']=='aac' and info['audio_rate']==48000 and info['audio_channels']==2,info)
    times=[.8,4.9,8.4,10.7,13.7,17.4,20.3,23.9,27.2,29.9];sample_indices={round(t*tl['fps']):t for t in times}
    captures=[];hashes=[];pts=[];deltas=[];previous=None;decode_error=None;count=0
    try:
        with av.open(str(p)) as c:
            for i,f in enumerate(c.decode(video=0)):
                pts.append(float(f.pts*f.time_base));gray=f.reformat(width=270,height=480,format='gray').to_ndarray()
                roi=gray[115:355,12:258].copy()
                hashes.append(hashlib.sha256(roi.tobytes()).hexdigest())
                if previous is not None:deltas.append(float(np.abs(roi.astype(np.int16)-previous.astype(np.int16)).mean()))
                previous=roi
                if i in sample_indices:
                    image=f.to_image();image.thumbnail((216,384));captures.append((sample_indices[i],image))
                count+=1
    except Exception as exc:decode_error=repr(exc)
    check('Every expected frame decodes',decode_error is None and count==expected,{'decoded':count,'expected':expected,'error':decode_error})
    check('Continuous monotonic video timestamps',len(pts)>1 and all(abs((b-a)-1/tl['fps'])<.0001 for a,b in zip(pts,pts[1:])),{'first':pts[0] if pts else None,'last':pts[-1] if pts else None})
    run=longest_run([h1==h2 for h1,h2 in zip(hashes,hashes[1:])])
    check('Moving picture is not a held-slide render',len(set(hashes))>=expected*.93 and run/tl['fps']<.75,{'unique_anatomy_crop_hashes':len(set(hashes)),'longest_identical_crop_run_seconds':run/tl['fps'],'mean_frame_delta_8bit':float(np.mean(deltas)) if deltas else None,'note':'Small downsampled anatomy-region changes measured, not a claim that physiology is physically simulated.'})
    audio_frames=0;audio_samples=0
    with av.open(str(p)) as c:
        for f in c.decode(audio=0):audio_frames+=1;audio_samples+=f.samples
    check('Entire audio stream decodes',audio_frames>0 and abs(audio_samples/48000-tl['duration'])<.06,{'frames':audio_frames,'decoded_seconds':audio_samples/48000})
    proc=subprocess.run([FF,'-hide_banner','-i',str(p),'-af','loudnorm=I=-16:TP=-1.5:LRA=8:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
    loud=json.loads(re.findall(r'\{\s*"input_i"[\s\S]*?\}',proc.stderr)[-1])
    check('Final AAC loudness and true peak',abs(float(loud['input_i'])+16)<=1 and float(loud['input_tp'])<=-1,{'integrated_lufs':float(loud['input_i']),'true_peak_dbtp':float(loud['input_tp']),'lra_lu':float(loud['input_lra'])})
    order=atom_order(p)
    check('Fast-start MP4',('moov' in order and 'mdat' in order and order.index('moov')<order.index('mdat')),{'top_level_atoms':order})
    check('Caption intervals in bounds',all(0<=c['start']<c['end']<=tl['duration'] for c in tl['captions']),{'phrases':len(tl['captions']),'alignment':'Phrase-timed, not word-level forced alignment'})
    text=' '.join(c['text'] for c in tl['captions'])
    check('Explicit no-guarantee and professional-care ending',all(s in text for s in ['har baar nahi','intezaar mat karo','doctor se madad lo','mat khodo']),{'messages':'Conditional expulsion, do not wait, doctor for warning signs, do not dig'})
    receipts=[]
    for file in sorted(out.glob('chunk-*.mp4.json')):receipts.append(json.loads(file.read_text()))
    coverage=[f for r in receipts for f in range(r['start'],r['end'])]
    check('Native-frame render receipts cover the master exactly',coverage==list(range(expected)) and all([r['width'],r['height'],r['fps']]==[1080,1920,tl['fps']] for r in receipts) and len({r['signature'] for r in receipts})==1,{'chunks':len(receipts),'covered_frames':len(coverage),'signatures':sorted({r['signature'] for r in receipts})})
    # QC contact sheet is derived from the encoded master, never source stills.
    sheet=Image.new('RGB',(1080,840),'#071e2b');draw=ImageDraw.Draw(sheet)
    font=ImageFont.truetype(str(ROOT/'assets/fonts/Montserrat-VF.ttf'),20)
    for j,(time,im) in enumerate(captures):
        x=(j%5)*216;y=(j//5)*420;sheet.paste(im,(x,y));draw.text((x+12,y+390),f'{time:04.1f}s',font=font,fill='#d9ebed')
    sheet.save(out/'QA_CONTACT_SHEET.jpg',quality=92)
    report={'passed':all(c['passed'] for c in checks),'checks_passed':sum(c['passed'] for c in checks),'checks_total':len(checks),'master':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'md5':hashlib.md5(p.read_bytes()).hexdigest(),'metadata':info,'checks':checks,'manual_review':{'status':'pending','contact_sheet':'QA_CONTACT_SHEET.jpg','scope':'Sampled visual sequence, typography, skin/forceps framing and warning labels. No claim of independent clinician review or audible pronunciation certification.'}}
    (out/'QUALITY_REPORT.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(report,indent=2,ensure_ascii=False));raise SystemExit(0 if report['passed'] else 1)

if __name__=='__main__':main()
