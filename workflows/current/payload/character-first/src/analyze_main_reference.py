"""Measure the USER-CONFIRMED main reference, not the unrelated chair film.

Reference pixels are used for private analysis only. Audio may be stream-copied
per the user's explicit same-music request. Transition scores are candidates,
not an automatic claim of editorial/animation equivalence.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess

import imageio_ffmpeg
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps

FF=imageio_ffmpeg.get_ffmpeg_exe()
EXPECTED_MD5='42e52d770f6b53338639d2d1a01e2e48'
DRIVE_ID='1sYYhXs9fbHeHcQGOmH5IR7CvUSVr9Tmx'
W,H=180,320


def audio_hash(path,copy=False):
    cmd=[FF,'-v','error','-i',str(path),'-map','0:a:0','-vn']
    if copy:cmd+=['-c:a','copy']
    cmd+=['-f','hash','-hash','sha256','-']
    return subprocess.check_output(cmd,text=True).strip().split('=',1)[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True)
    p.add_argument('--work',type=Path,required=True);p.add_argument('--records',type=Path,required=True)
    a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True);a.records.mkdir(parents=True,exist_ok=True)
    assert hashlib.md5(a.input.read_bytes()).hexdigest()==EXPECTED_MD5,'Wrong/changed reference file; do not silently use a different video.'
    records=[];frames=[];old=None;oldhist=None
    with (a.work/'frame_pts.log').open('w') as log:
        proc=subprocess.Popen([FF,'-hide_banner','-nostats','-i',str(a.input),'-an',
            '-vf',f'scale={W}:{H},showinfo','-fps_mode','passthrough','-pix_fmt','rgb24',
            '-f','rawvideo','pipe:1'],stdout=subprocess.PIPE,stderr=log)
        while True:
            raw=proc.stdout.read(W*H*3)
            if not raw:break
            assert len(raw)==W*H*3,'Truncated analysis frame'
            rgb=np.frombuffer(raw,np.uint8).reshape(H,W,3).copy();frames.append(rgb)
            f=rgb.astype(np.float32);gray=f@np.array([.2126,.7152,.0722],np.float32)
            hist=np.histogram(gray,bins=32,range=(0,256))[0].astype(float)/(W*H)
            diff=float(np.abs(gray-old).mean()) if old is not None else 0.
            hd=float(np.abs(hist-oldhist).sum()) if oldhist is not None else 0.
            records.append({'frame':len(records),'mean_luma':round(float(gray.mean()),4),
                'mean_abs_luma_change':round(diff,4),'histogram_l1_change':round(hd,5),
                'black_fraction':round(float((gray<8).mean()),5),'bright_fraction':round(float((gray>245).mean()),5),
                'red_mean':round(float(f[:,:,0].mean()),4),'green_mean':round(float(f[:,:,1].mean()),4),'blue_mean':round(float(f[:,:,2].mean()),4)})
            old=gray;oldhist=hist
        proc.stdout.close();code=proc.wait();assert code==0,code
    text=(a.work/'frame_pts.log').read_text()
    pts=[float(x) for x in re.findall(r'\bn:\s*\d+\s+pts:\s*-?\d+\s+pts_time:([0-9.e+\-]+)',text)]
    assert len(pts)==len(records),(len(pts),len(records))
    for r,t in zip(records,pts):r['pts_seconds']=t
    with (a.records/'REFERENCE_FRAME_METRICS.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]),lineterminator='\n');writer.writeheader();writer.writerows(records)
    # Candidate list keeps adjacent flash edges; don't automatically merge them into cuts.
    events=[r for r in records[1:] if r['mean_abs_luma_change']>13 or r['histogram_l1_change']>1.1]
    (a.records/'TRANSITION_CANDIDATES.json').write_text(json.dumps({'scope':'Candidate visual discontinuities; manual classification required.','events':events},indent=2)+'\n')
    for page,times in enumerate([[.25,1,2.5,4,6,8,10,12,14,16,18,20],
                                 [21,22,23,24,25,26,27,28,29,30,31,32],
                                 [33,34,35,36,37,38,39,40,41,42,43,44.1]],1):
        sheet=Image.new('RGB',(840,1184),'#12171b');d=ImageDraw.Draw(sheet)
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
        d.text((12,10),f'ORIGINAL MAIN REFERENCE / PAGE {page} / NOT A NEW RENDER',font=font,fill='#e4dbca')
        for i,t in enumerate(times):
            k=int(np.argmin(np.abs(np.array(pts)-t)));x=(i%4)*210;y=52+(i//4)*374
            im=Image.fromarray(frames[k]).resize((200,356),Image.Resampling.LANCZOS)
            sheet.paste(im,(x+5,y+18));d.text((x+7,y),f'{pts[k]:.3f}s  f{k}',font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',13),fill='white')
        sheet.save(a.work/f'REFERENCE_TIMELINE_{page}.jpg',quality=94)
    audio=a.work/'ORIGINAL_REFERENCE_AUDIO.m4a'
    subprocess.run([FF,'-v','error','-y','-i',str(a.input),'-map','0:a:0','-vn','-c:a','copy','-movflags','+faststart',str(audio)],check=True)
    hashes={'source_encoded_aac_payload_sha256':audio_hash(a.input,True),'extracted_encoded_aac_payload_sha256':audio_hash(audio,True),
            'source_decoded_pcm_sha256':audio_hash(a.input),'extracted_decoded_pcm_sha256':audio_hash(audio)}
    assert hashes['source_encoded_aac_payload_sha256']==hashes['extracted_encoded_aac_payload_sha256']
    assert hashes['source_decoded_pcm_sha256']==hashes['extracted_decoded_pcm_sha256']
    pcm=subprocess.check_output([FF,'-v','error','-i',str(audio),'-map','0:a:0','-f','s16le','-c:a','pcm_s16le','-'])
    audio_samples=np.frombuffer(pcm,np.int16).reshape(-1,2)
    audio_duration=len(audio_samples)/44100
    report={'reference_drive_id':DRIVE_ID,'reference_url':f'https://drive.google.com/file/d/{DRIVE_ID}/view',
            'reference_name':a.input.name,'md5':EXPECTED_MD5,'bytes':a.input.stat().st_size,
            'container_duration_reported':44.55,'drive_duration_reported_ms':44399,
            'video_width':720,'video_height':1280,'nominal_video_fps':30,
            'decoded_video_frames':len(records),'first_video_pts':pts[0],'last_video_pts':pts[-1],
            'video_duration_from_pts_seconds':round(pts[-1]-pts[0]+1/30,6),
            'audio_codec':'AAC-LC','audio_rate':44100,'audio_channels':2,'decoded_audio_samples_per_channel':len(audio_samples),
            'decoded_audio_duration_seconds':audio_duration,'audio_copy_path':str(audio),'audio_copy_bytes':audio.stat().st_size,
            'audio_copy_md5':hashlib.md5(audio.read_bytes()).hexdigest(),'audio_hashes':hashes,
            'audio_encoded_payload_match':True,'audio_decoded_pcm_match':True,
            'audio_policy':'Use this user-supplied source music unchanged for the reference-matched full edit; no original-score/outro-sting substitution.',
            'rights_note':'Source provided by user for this edit. No independent licensing clearance is claimed.',
            'other_chat_policy':'Chair/cables 6s/21s chat is a technique/workflow example ONLY, never this edit\'s visual/audio/timing reference.',
            'transition_candidates':len(events),'final_character_film_created':False}
    (a.records/'MAIN_REFERENCE_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    print('REFERENCE_ANALYSIS_COMPLETE')


if __name__=='__main__':main()
