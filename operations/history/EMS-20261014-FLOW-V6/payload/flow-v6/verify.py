"""Fail-closed technical delivery checks plus actual encoded-frame review.

No claim of human auditory review or independently fact-checked history is
made. Visual sheets are sampled from the finished MP4, not render inputs.
"""
from pathlib import Path
import json,subprocess,re,hashlib,struct,sys,os
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parent;MEDIA=Path(os.environ.get('FLOW_MEDIA',str(ROOT/'media'))).resolve()
VIDEO=Path(sys.argv[1] if len(sys.argv)>1 else str(ROOT/'delivery'/'Flow_State_UrduEnglish_V6.mp4'))
DATA=json.loads((ROOT/'timeline.json').read_text());ff=imageio_ffmpeg.get_ffmpeg_exe()
assert VIDEO.exists() and VIDEO.stat().st_size>1000000, 'Missing/truncated master'
info=subprocess.run([ff,'-hide_banner','-i',str(VIDEO)],capture_output=True,text=True).stderr
(MEDIA/'probe.txt').write_text(info)
assert 'h264 (High)' in info and 'yuv420p' in info,'Browser codec mismatch'
assert '1080x1920' in info and '30 fps' in info,'Dimensions/rate mismatch'
assert 'Audio: aac' in info and '48000 Hz' in info,'Audio encoding mismatch'
decode=subprocess.run([ff,'-v','error','-xerror','-i',str(VIDEO),'-map','0:v:0','-map','0:a:0','-f','null','-'],capture_output=True,text=True)
assert decode.returncode==0,decode.stderr
# Top-level MP4 atom order: mobile/web delivery must have early moov.
atoms=[]
with VIDEO.open('rb') as f:
    while True:
        h=f.read(8)
        if len(h)<8:break
        size,kind=struct.unpack('>I4s',h);kind=kind.decode('ascii','replace')
        if size==1:size=struct.unpack('>Q',f.read(8))[0];header=16
        else:header=8
        atoms.append(kind)
        if size<8:break
        f.seek(size-header,1)
assert 'moov' in atoms and 'mdat' in atoms and atoms.index('moov')<atoms.index('mdat'),'Not faststart'
cap=cv2.VideoCapture(str(VIDEO));count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));fps=cap.get(cv2.CAP_PROP_FPS)
assert count==round(DATA['duration']*30),(count,DATA['duration'])
# Contact-sheet samples after compositing / AAC muxing.
times=[]
for s in DATA['shots']:
    for frac in [.18,.52,.86]:times.append(s['start']+(s['end']-s['start'])*frac)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
icon=cv2.imread(str(ROOT/'icon-template.png'),cv2.IMREAD_GRAYSCALE)
black=[];tag_candidates=[]
for page in range(0,len(times),9):
    canvas=Image.new('RGB',(900,1680),(24,22,31));d=ImageDraw.Draw(canvas)
    for j,t in enumerate(times[page:page+9]):
        cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=cap.read();assert ok,('Cannot read encoded frame',t)
        if f.mean()<6:black.append(t)
        small=cv2.resize(f,(720,1280));gray=cv2.cvtColor(small,cv2.COLOR_BGR2GRAY)
        for x0,y0,x1,y1 in [(570,264,719,411),(40,800,191,955)]:
            roi=gray[y0:y1,x0:x1]
            score=float(np.max(np.abs(cv2.matchTemplate(roi,icon,cv2.TM_CCOEFF_NORMED))))
            if score>.75:tag_candidates.append({'time':round(t,3),'score':round(score,3)})
        a=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB));a.thumbnail((297,528))
        x=j%3*300;y=j//3*560;canvas.paste(a,(x,y+25));d.text((x+4,y+3),f'{t:.2f}s',font=font,fill='white')
    canvas.save(MEDIA/f'encoded-review-{page//9+1}.jpg',quality=94)
cap.release()
# Frame-to-frame provenance checks operate on each moving SOURCE clip,
# independent of captions: no slideshow can pass by animating text alone.
motion=[]
for s in DATA['shots']:
    c=cv2.VideoCapture(str(MEDIA/s['path']));n=int(c.get(cv2.CAP_PROP_FRAME_COUNT));imgs=[]
    for p in [.18,.48,.79]:
        c.set(cv2.CAP_PROP_POS_FRAMES,min(n-1,int(n*p)));ok,im=c.read();assert ok
        imgs.append(cv2.resize(im[320:880,70:650],(160,160)).astype(np.float32))
    c.release()
    delta=float(np.mean(np.abs(imgs[2]-imgs[0])))
    motion.append({'shot':s['name'],'source_frames':n,'central_motion_delta':round(delta,3)})
    assert n>25 and delta>.15,('Unexpected static source',s['name'],delta)
# Decode final AAC to check clipping/peak, not just pre-encode WAV.
audio=subprocess.check_output([ff,'-v','error','-i',str(VIDEO),'-vn','-ar','48000','-ac','2','-f','f32le','pipe:1'])
a=np.frombuffer(audio,dtype='<f4').reshape(-1,2)
peak=float(np.max(np.abs(a)));rms=float(np.sqrt(np.mean(a*a)))
assert peak<1.0,('Clipped AAC output',peak)
assert rms>.02,('Missing/very quiet narration',rms)
assert not black,('Unexpected black frames',black)
report={'status':'technical_checks_passed' if not tag_candidates else 'visual_attention_required',
        'path':str(VIDEO),'frames':count,'duration_seconds':count/fps,'dimensions':[1080,1920],
        'codec':'H.264 High / yuv420p + AAC stereo 48 kHz','faststart':True,'full_decode_exit':decode.returncode,
        'size_bytes':VIDEO.stat().st_size,'sha256':hashlib.sha256(VIDEO.read_bytes()).hexdigest(),
        'md5':hashlib.md5(VIDEO.read_bytes()).hexdigest(),'speech_speed':1.0,
        'aac_sample_peak_dbfs':round(20*np.log10(max(peak,1e-9)),2),
        'aac_rms_dbfs':round(20*np.log10(max(rms,1e-9)),2),'black_frames':black,
        'possible_social_icons':tag_candidates,'motion_provenance':motion,
        'visual_samples':len(times),'visual_review':'pending agent review of encoded-review sheets',
        'audio_review_scope':'Decoded, timed, level/peak checked; not an independent human listening test.'}
# Voice files must still be the exact selected originals.
provenance=json.loads((ROOT/'PROVENANCE.json').read_text())
for item in provenance['speech_recovery']['files']:
    assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256'],('Voice changed',item['path'])
v5=json.loads((ROOT/'V5_DELIVERY.json').read_text())
assert report['sha256']!=v5['master']['sha256'],'V6 must not be a renamed V5 copy'
report['original_voice_files_verified']=True
report['version']='V6'
report['parent_master_drive_id']=v5['master']['drive_id']
report['caption_highlight_scope']='Word-paced approximation within retained phrase-level timing; no ASR-certified word timing claimed.'
(ROOT/'QA.json').write_text(json.dumps(report,indent=2)+'\n')
print('TECHNICAL_QA_READY '+json.dumps({k:report[k] for k in ['status','duration_seconds','frames','size_bytes','aac_sample_peak_dbfs','possible_social_icons']}),flush=True)
if tag_candidates:sys.exit(2)
