#!/usr/bin/env python3
"""Reference-informed perspective turnover using each real animated frame.
The transition masks the single intentional scene change, not the anatomy's
continuous camera rails. Only its containing chunk is recomposited. Results
are fingerprinted/resumable; the old v2 and raw v3 chunks are never modified.
"""
import argparse,hashlib,io,json,math,subprocess
from pathlib import Path
import av
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageEnhance
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[1]
FF=imageio_ffmpeg.get_ffmpeg_exe()

def ease(x):
    x=max(0,min(1,x));return x*x*x*(x*(x*6-15)+10)

def projection(angle,w,h,dist):
    points=[]
    for x,y in [(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]:
        z=-x*math.sin(angle);q=dist/(dist-z)
        points.append((w/2+x*math.cos(angle)*q,h/2+y*q))
    return points

def coeffs(dest,src):
    a=[];b=[]
    for (x,y),(u,v) in zip(dest,src):
        a.append([x,y,1,0,0,0,-u*x,-u*y]);b.append(u)
        a.append([0,0,0,x,y,1,-v*x,-v*y]);b.append(v)
    return np.linalg.solve(np.array(a),np.array(b)).tolist()

def background(w,h):
    y=np.linspace(0,1,h)[:,None,None]
    top=np.array([7,27,44.])[None,None,:];bottom=np.array([18,56,73.])[None,None,:]
    rgb=np.broadcast_to(top*(1-y)+bottom*y,(h,w,3)).copy()
    xx,yy=np.meshgrid(np.linspace(-1,1,w),np.linspace(-1,1,h))
    glow=np.exp(-(xx*xx+yy*yy)*2.8)*15
    rgb[:,:,1]+=glow;rgb[:,:,2]+=glow
    return Image.fromarray(np.clip(rgb,0,255).astype('uint8'))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--prepare-only',action='store_true');args=ap.parse_args()
    out=args.out.resolve();tl=json.loads((ROOT/'data/timeline.json').read_text());cfg=json.loads((ROOT/'data/postfx.json').read_text());motion=json.loads((ROOT/'data/motion.json').read_text())
    center=motion['cues'][cfg['center_cue']];dur=cfg['duration'];start=center-dur/2;end=center+dur/2;fps=tl['fps'];chunk_size=90
    chunk_start=(int(start*fps)//chunk_size)*chunk_size
    if int(end*fps)>=chunk_start+chunk_size:raise ValueError('Transition must fit in one encoded chunk; split the post pass otherwise.')
    raw=out/f'chunk-{chunk_start:05d}.mp4'
    if not raw.exists():raise SystemExit('Wait until the native transition-containing chunk is complete.')
    image=out/f'turnover-{chunk_start:05d}.mp4';receipt=out/'POSTFX_REPORT.json'
    h=hashlib.sha256();h.update(raw.read_bytes());h.update(Path(__file__).read_bytes());h.update(json.dumps([cfg,center,fps],sort_keys=True).encode());signature=h.hexdigest()
    cached=False
    if image.exists() and receipt.exists():
        prior=json.loads(receipt.read_text());cached=prior['signature']==signature and prior['output_bytes']==image.stat().st_size
    if not cached:
        c=av.open(str(raw));v=c.streams.video[0];w,h=v.width,v.height;bg=background(w,h)
        cmd=[FF,'-hide_banner','-loglevel','error','-y','-f','image2pipe','-framerate',str(fps),'-vcodec','png','-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','16','-vf','scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p','-color_range','tv','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-movflags','+faststart',str(image)]
        enc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE);count=0;changed=[]
        try:
            for i,frame in enumerate(c.decode(video=0)):
                t=(chunk_start+i)/fps;im=frame.to_image()
                if start<t<end:
                    if t<=center:angle=(math.pi/2)*ease((t-start)/(dur/2))
                    else:angle=-(math.pi/2)*(1-ease((t-center)/(dur/2)))
                    dst=projection(angle,w,h,w*cfg['perspective_distance_in_widths']);composite=bg.copy()
                    if abs(math.cos(angle))*w>1.5:
                        alpha=Image.new('L',(w,h));ImageDraw.Draw(alpha).polygon(dst,fill=255)
                        shadow=Image.new('RGBA',(w,h));ImageDraw.Draw(shadow).polygon([(x+12,y+9) for x,y in dst],fill=(0,0,0,95));shadow=shadow.filter(ImageFilter.GaussianBlur(16))
                        composite.paste(shadow,(0,0),shadow)
                        warped=im.transform((w,h),Image.Transform.PERSPECTIVE,coeffs(dst,[(0,0),(w,0),(w,h),(0,h)]),resample=Image.Resampling.BICUBIC)
                        warped=ImageEnhance.Brightness(warped).enhance(.84+.16*abs(math.cos(angle)))
                        composite.paste(warped,(0,0),alpha)
                        ImageDraw.Draw(composite).line(dst+[dst[0]],fill=(70,121,139),width=1)
                    else:
                        ImageDraw.Draw(composite).line([(w//2,0),(w//2,h)],fill=(94,157,177),width=2)
                    im=composite;changed.append(chunk_start+i)
                if i in [20,23,26,28,30,32,34,37,40]:im.resize((270,480)).save(out/f'turnover-review-{i:02d}.png')
                payload=io.BytesIO();im.save(payload,format='PNG',compress_level=1);enc.stdin.write(payload.getvalue());count+=1
            enc.stdin.close();error=enc.stderr.read().decode();code=enc.wait()
            if code:raise RuntimeError(error)
        finally:
            c.close()
            if enc.poll() is None:enc.kill()
        report={'signature':signature,'source_chunk':raw.name,'source_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'output_chunk':image.name,'output_bytes':image.stat().st_size,'output_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'frames_in_chunk':count,'changed_frames':changed,'start':start,'center':center,'end':end,'source_frame_rate':fps,'interpolated_frames':0,'scope':cfg['scope']}
        receipt.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    else:print('Verified cached turnover chunk; no recomposition repeated.')
    if args.prepare_only:return
    total=round(tl['duration']*fps);parts=[]
    for f in range(0,total,chunk_size):
        name=image.name if f==chunk_start else f'chunk-{f:05d}.mp4'
        if not (out/name).exists():raise SystemExit('Native picture not complete: '+name)
        parts.append(f"file '{name}'")
    listing=out/'concat-polished.txt';listing.write_text('\n'.join(parts)+'\n')
    subprocess.run([FF,'-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(out/'picture-polished.mp4')],check=True)
    print('Polished native-frame picture ready:',out/'picture-polished.mp4')

if __name__=='__main__':main()
