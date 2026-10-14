"""Resumable per-shot cleanup. A completed, hash-matching shot is never rerun."""
from pathlib import Path
import sys, subprocess, hashlib, json, time, os
import cv2
import imageio_ffmpeg
from clean import cleanup, CUTS, NAMES

ROOT=Path(__file__).resolve().parent
MEDIA=Path(os.environ.get('FLOW_MEDIA',str(ROOT/'media'))).resolve()
OUT=MEDIA/'clean-shots'; OUT.mkdir(parents=True,exist_ok=True)
VERSION=hashlib.sha256((ROOT/'clean.py').read_bytes()).hexdigest()
ff=imageio_ffmpeg.get_ffmpeg_exe()
only={int(x) for x in sys.argv[1:]} if len(sys.argv)>1 else set(range(14))
for k in sorted(only):
    dest=OUT/f'{k:02d}-{NAMES[k]}.mp4'; receipt=dest.with_suffix('.json')
    if dest.exists() and receipt.exists() and json.loads(receipt.read_text()).get('cleanup_sha256')==VERSION:
        print(f'SKIP {k:02d} verified existing shot',flush=True);continue
    a=int(round(CUTS[k]*30));b=int(round(CUTS[k+1]*30));n=b-a
    print(f'START {k:02d} {NAMES[k]} source frames {a}:{b}',flush=True)
    cap=cv2.VideoCapture(str(MEDIA/'reference.mp4'));cap.set(cv2.CAP_PROP_POS_FRAMES,a)
    temp=dest.with_name(dest.stem+'.partial.mp4')
    cmd=[ff,'-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','bgr24',
         '-s','720x1280','-r','30','-i','pipe:0','-an','-c:v','libx264','-crf','16',
         '-preset','fast','-threads','2','-pix_fmt','yuv420p','-movflags','+faststart',str(temp)]
    enc=subprocess.Popen(cmd,stdin=subprocess.PIPE);start=time.monotonic();count=0
    try:
        for i in range(a,b):
            ok,frame=cap.read()
            if not ok:raise RuntimeError(f'Missing source frame {i}')
            clean=cleanup(frame,i/30,k)
            enc.stdin.write(clean.tobytes());count+=1
            if i==(a+b)//2:cv2.imwrite(str(OUT/f'{k:02d}-check.jpg'),clean)
        enc.stdin.close()
        if enc.wait()!=0:raise RuntimeError('Encoder failed')
        if count!=n:raise RuntimeError('Incomplete shot')
        temp.replace(dest)
        receipt.write_text(json.dumps({'source_start_frame':a,'source_end_frame':b,
            'frames':count,'cleanup_sha256':VERSION,'name':NAMES[k],
            'elapsed_seconds':round(time.monotonic()-start,2)},indent=2)+'\n')
        print(f'DONE {k:02d} {count} changing source frames in {time.monotonic()-start:.1f}s',flush=True)
    finally:
        cap.release()
        if enc.poll() is None:enc.terminate()
print('CLEAN_SHOTS_READY',flush=True)
