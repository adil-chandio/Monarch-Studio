"""Objective WF-05 export checks. Technical success is not aesthetic approval."""
from __future__ import annotations
import hashlib,json,re,struct,subprocess
from pathlib import Path
import cv2
import numpy as np
import imageio_ffmpeg
from policy import assert_valid,resolve,subtitle_mode,sha256

def verify(project_path:Path,video:Path|None=None):
    project_path=project_path.resolve();base=project_path.parent;p,t=assert_valid(project_path)
    video=video.resolve() if video else resolve(base,p['output']);ff=imageio_ffmpeg.get_ffmpeg_exe()
    report={'schema_version':1,'project_id':p['project_id'],'policy_id':p['policy_id'],'technical_pass':False,'visual_review_approved':False,'caption_policy_pass':False,'checks':{},'limitations':['Full decode and samples are not an independent human listening test.','Pixel changes alone cannot certify independent subject motion or aesthetic quality.']}
    checks=report['checks'];checks['file_exists']=video.is_file()
    if not video.is_file():return report
    report.update({'path':str(video),'size_bytes':video.stat().st_size,'sha256':sha256(video),'md5':hashlib.md5(video.read_bytes()).hexdigest()})
    probe=subprocess.run([ff,'-hide_banner','-i',str(video)],capture_output=True,text=True).stderr
    checks['h264_high_yuv420p']='h264 (High)' in probe and 'yuv420p' in probe
    checks['1080x1920_30fps']='1080x1920' in probe and '30 fps' in probe
    checks['aac_stereo_48k']='Audio: aac' in probe and '48000 Hz' in probe and 'stereo' in probe
    decode=subprocess.run([ff,'-v','error','-xerror','-i',str(video),'-map','0:v:0','-map','0:a:0','-f','null','-'],capture_output=True,text=True)
    checks['full_decode']=decode.returncode==0;report['decode_error']=decode.stderr
    atoms=[]
    with video.open('rb') as f:
        while True:
            h=f.read(8)
            if len(h)<8:break
            size,kind=struct.unpack('>I4s',h);header=8
            if size==1:
                raw=f.read(8)
                if len(raw)!=8:break
                size=struct.unpack('>Q',raw)[0];header=16
            if size<header:break
            atoms.append(kind.decode('ascii','replace'));f.seek(size-header,1)
    checks['faststart']='moov' in atoms and 'mdat' in atoms and atoms.index('moov')<atoms.index('mdat')
    cap=cv2.VideoCapture(str(video));frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));checks['frame_count']=frames==round(t['duration']*30);report['frames']=frames
    sampled=[];reviewdir=base/'reviews/encoded';reviewdir.mkdir(parents=True,exist_ok=True);dark=[]
    for i,s in enumerate(t['shots']):
        for n,frac in enumerate([.18,.52,.86]):
            at=s['start']+frac*(s['end']-s['start']);cap.set(cv2.CAP_PROP_POS_MSEC,at*1000);ok,f=cap.read()
            if not ok:dark.append(at);continue
            if f.mean()<6:dark.append(at)
            name=f'shot-{i:02d}-{n}.jpg';cv2.imwrite(str(reviewdir/name),f,[cv2.IMWRITE_JPEG_QUALITY,90]);sampled.append({'time':round(at,3),'file':str((reviewdir/name).relative_to(base))})
    cap.release();checks['no_sampled_black_frames']=not dark;report['samples']=sampled
    raw=subprocess.check_output([ff,'-v','error','-i',str(video),'-vn','-ar','48000','-ac','2','-f','f32le','pipe:1'])
    audio=np.frombuffer(raw,dtype='<f4');peak=float(np.max(np.abs(audio))) if audio.size else 0;rms=float(np.sqrt(np.mean(audio*audio))) if audio.size else 0
    checks['decoded_audio_present']=rms>.02;checks['no_sample_clipping']=0<peak<1
    report['sample_peak_dbfs']=round(20*np.log10(max(peak,1e-9)),2);report['rms_dbfs']=round(20*np.log10(max(rms,1e-9)),2)
    receipt_path=base/'RENDER_RECEIPT.json';receipt=json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
    checks['render_receipt_matches']=receipt.get('sha256')==report['sha256'] and receipt.get('policy_id')==p['policy_id']
    checks['approved_caption_policy']=receipt.get('subtitle_mode')==subtitle_mode(p) and receipt.get('caption_pills') is False and receipt.get('word_highlighting') is False
    report['caption_policy_pass']=checks['approved_caption_policy'];report['technical_pass']=all(checks.values())
    human=base/'qa-review.json'
    if human.exists():
        review=json.loads(human.read_text());required=['approved_for_delivery','actual_motion_reviewed','subject_edges_intact','typography_legible','no_rejected_bottom_pills','no_social_tags_or_end_card','narration_scene_alignment_reviewed','factual_claims_reviewed']
        report['visual_review_approved']=all(review.get(k) is True for k in required)
        report['audio_listening_scope']=review.get('audio_listening_scope','not recorded')
    (base/'QA.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
