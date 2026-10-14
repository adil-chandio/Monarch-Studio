"""Kinetic Urdu-English re-edit of supplied *moving* reference footage.

Not an image slideshow. Every output scene samples a different original
video sequence. Native motion is retained, scenes are recut to natural-speed
narration, old social UI/titles are removed, and separate depth typography,
continuous camera motion and short directional transitions are composited.
"""
from pathlib import Path
import os, json, math, subprocess, argparse, time, functools
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parent
MEDIA=Path(os.environ.get('FLOW_MEDIA',str(ROOT/'media'))).resolve()
DATA=json.loads((ROOT/'timeline.json').read_text())
FONTS=ROOT/'fonts'; FPS=30; SCALE=1.5; W,H=1080,1920
INK=(30,22,59); PURPLE=(112,91,173)
TITLES=DATA['titles'];CAPTIONS=DATA['captions'];SHOTS=DATA['shots']

@functools.lru_cache(maxsize=80)
def font(size,kind='head'):
    name={'head':'Anton-Regular.ttf','body':'BarlowCondensed-Medium.ttf','italic':'BarlowCondensed-MediumItalic.ttf'}[kind]
    return ImageFont.truetype(str(FONTS/name),int(round(size*SCALE)))

def ease(x):
    x=max(0.,min(1.,x));return x*x*(3-2*x)

def wrap(text,ft,width):
    words=text.split();lines=[];line=''
    for word in words:
        trial=(line+' '+word).strip()
        if ft.getlength(trial)>width and line:lines.append(line);line=word
        else:line=trial
    if line:lines.append(line)
    return lines

@functools.lru_cache(maxsize=64)
def title_art(index):
    d=TITLES[index];size=d['size'];lines=d['title'].split('\n')
    maxwidth=555*SCALE if d['position']!='right' else 302*SCALE
    while max(font(size).getlength(x) for x in lines)>maxwidth and size>45:size-=1
    ft=font(size);body=font(29,'italic');kick=font(29,'italic')
    if d['position']=='right':body=font(25,'italic');kick=font(27,'italic')
    # Font bounding boxes exclude the tall ascender margin.
    heights=[ft.getbbox(line)[3]-ft.getbbox(line)[1] for line in lines]
    gap=10*SCALE
    kw=kick.getlength(d['kicker']) if d['kicker'] else 0
    sw=body.getlength(d['sub']) if d['sub'] else 0
    # Auto-wrap connective phrases rather than shrinking them to illegibility.
    sublines=wrap(d['sub'],body,maxwidth) if d['sub'] else []
    subh=len(sublines)*35*SCALE
    kickh=39*SCALE if d['kicker'] else 0
    th=sum(heights)+max(0,len(lines)-1)*gap
    width=int(max(max(ft.getlength(s) for s in lines),kw,min(sw,maxwidth))+42*SCALE)
    height=int(kickh+th+(20*SCALE if sublines else 0)+subh+30*SCALE)
    im=Image.new('RGBA',(width,height),(0,0,0,0));dr=ImageDraw.Draw(im)
    cy=7*SCALE
    if d['kicker']:
        box=kick.getbbox(d['kicker']);dr.text(((width-kw)/2,cy-box[1]),d['kicker'],font=kick,fill=(*INK,235));cy+=kickh
    for li,line in enumerate(lines):
        bb=ft.getbbox(line);x=(width-ft.getlength(line))/2;y=cy-bb[1]
        # Subtle real extrusion in a separate plane, not a heavy cartoon stroke.
        for dep in range(8,0,-1):
            dr.text((x+dep*.60,y+dep*.83),line,font=ft,fill=(123-dep*2,105-dep*2,179-dep*2,245))
        dr.text((x,y),line,font=ft,fill=(*INK,255),stroke_width=0)
        cy+=heights[li]+gap
    if sublines:
        cy+=9*SCALE
        for line in sublines:
            bb=body.getbbox(line);dr.text(((width-body.getlength(line))/2,cy-bb[1]),line,font=body,fill=(*INK,245));cy+=35*SCALE
    return im

@functools.lru_cache(maxsize=64)
def caption_art(index):
    c=CAPTIONS[index];ft=font(30,'body');lines=wrap(c['text'],ft,600*SCALE)
    width=int(max(ft.getlength(x) for x in lines)+40*SCALE);height=int(len(lines)*35*SCALE+20*SCALE)
    im=Image.new('RGBA',(width,height),(0,0,0,0));d=ImageDraw.Draw(im)
    for i,line in enumerate(lines):
        b=ft.getbbox(line);x=(width-ft.getlength(line))/2;y=10*SCALE+i*35*SCALE-b[1]
        d.text((x,y),line,font=ft,fill=(*INK,255),stroke_width=1,stroke_fill=(220,219,249,225))
    return im


def paste_title(im,index,t,held=False,shot_index=0):
    d=TITLES[index];art=title_art(index)
    age=max(0,t-d['start']);enter=ease(age/.25)
    if held:enter=1.
    if enter<.999:
        # Depth/overshoot entrance with a directional rise. The label remains
        # perfectly readable at rest instead of continuously warping glyphs.
        scale=.82+.18*enter+.025*math.sin(enter*math.pi)
        art=art.resize((max(1,int(art.width*scale)),max(1,int(art.height*scale))),Image.Resampling.BICUBIC)
        art=art.copy();art.putalpha(art.getchannel('A').point(lambda a:int(a*enter)))
    x=(W-art.width)//2
    if d['position']=='top':y=int((85 if shot_index==9 else 145)*SCALE)
    elif d['position']=='right':
        x=int(500*SCALE-art.width/2);y=int(766*SCALE)
    else:
        y=int(888*SCALE)
        if shot_index==3:y=int(913*SCALE)
        if shot_index==13:y=int(896*SCALE)
    y+=int((1-enter)*24*SCALE)
    # A separate text plane drifting very slightly against the live footage.
    x+=int(2.1*SCALE*math.sin(age*.7))
    im.paste(art,(x,y),art)


def overlay_type(frame,t,k):
    im=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)).convert('RGBA')
    shot=SHOTS[k]
    candidates=[i for i,s in enumerate(TITLES) if s['start']<=t<s['end']]
    if candidates:
        i=candidates[-1];current=TITLES[i]
        if current['position'] in ['bottom','right']:
            previous=[j for j,s in enumerate(TITLES[:i]) if s['position']=='top' and s['start']>=shot['start']-.13]
            if previous:paste_title(im,previous[-1],t,held=True,shot_index=k)
        paste_title(im,i,t,shot_index=k)
    active=[i for i,c in enumerate(CAPTIONS) if c['start']<=t<c['end']]
    if active:
        idx=active[-1];c=CAPTIONS[idx];art=caption_art(idx)
        a=min(ease((t-c['start'])/.095),ease((c['end']-t)/.085))
        if a<.99:
            art=art.copy();art.putalpha(art.getchannel('A').point(lambda v:int(v*a)))
        im.paste(art,((W-art.width)//2,int(1167*SCALE-art.height/2)),art)
    # Closing hold fades softly into lavender, never the original social card.
    if t>DATA['duration']-.25:
        a=ease((t-(DATA['duration']-.25))/.25)*.18
        veil=Image.new('RGBA',(W,H),(195,192,232,int(a*255)));im=Image.alpha_composite(im,veil)
    return np.asarray(im.convert('RGB'))


def load_frames(shot):
    path=MEDIA/shot['path']
    if not path.exists():raise RuntimeError('Missing cleaned motion source '+str(path))
    cap=cv2.VideoCapture(str(path));frames=[]
    while True:
        ok,f=cap.read()
        if not ok:break
        frames.append(f)
    cap.release()
    if len(frames)<12:raise RuntimeError('Truncated source shot '+str(path))
    return frames


def sample(frames,p,k):
    # Guard source cuts while keeping the native object entry/animation.
    p=np.clip(p,0.,1.);q=.015+.97*(p-.018*math.sin(p*2*math.pi))
    f=q*(len(frames)-1);i=int(f);j=min(i+1,len(frames)-1);blend=f-i
    a=cv2.addWeighted(frames[i],1-blend,frames[j],blend,0)
    zoom=1.008+.020*math.sin(math.pi*p)+.012*p
    angle=.28*math.sin(math.pi*2*p)*(-1 if k%2 else 1)
    mat=cv2.getRotationMatrix2D((360,640),angle,zoom)
    mat[0,2]+=5*math.sin(p*math.pi)*(-1 if k%2 else 1)
    mat[1,2]-=4*p
    a=cv2.warpAffine(a,mat,(720,1280),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)
    return a


def transition(cur,prev,local,k):
    if prev is None or local>=.17:return cur
    e=ease(local/.17)
    direction=1 if k%2 else -1
    # Depth match cut and very short directional whip, not a long slideshow
    # dissolve. The reference objects continue moving throughout the shot.
    mat=cv2.getRotationMatrix2D((360,640),.4*(1-e)*direction,1+.07*(1-e))
    mat[0,2]+=(1-e)*55*direction
    incoming=cv2.warpAffine(cur,mat,(720,1280),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)
    outgoing=cv2.warpAffine(prev,np.float32([[1,0,-e*75*direction],[0,1,0]]),(720,1280),borderMode=cv2.BORDER_REFLECT_101)
    mixed=cv2.addWeighted(outgoing,1-e,incoming,e,0)
    kernel=int((1-abs(e-.5)*2)*13)//2*2+1
    if kernel>1:mixed=cv2.blur(mixed,(kernel,1))
    return mixed


def run(output,preview=False):
    ff=imageio_ffmpeg.get_ffmpeg_exe();output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    cmd=[ff,'-hide_banner','-loglevel','warning','-y','-f','rawvideo','-pix_fmt','rgb24',
         '-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-i',str(MEDIA/'mix.wav'),
         '-map','0:v:0','-map','1:a:0','-c:v','libx264','-profile:v','high','-level:v','4.1',
         '-crf','18','-preset','fast','-threads','4','-pix_fmt','yuv420p',
         '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',
         '-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-movflags','+faststart',
         '-t',str(DATA['duration']),str(output)]
    log=open(MEDIA/'encode.log','w');enc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
    start=time.monotonic();done=0;last=None
    try:
        for k,s in enumerate(SHOTS):
            frames=load_frames(s);a=round(s['start']*FPS);b=round(s['end']*FPS)
            print(f'RENDER {k+1:02d}/14 {s["name"]} timeline {s["start"]:.2f}-{s["end"]:.2f}',flush=True)
            for n in range(a,b):
                t=n/FPS;local=t-s['start'];p=local/(s['end']-s['start'])
                base=sample(frames,p,k);base=transition(base,last,local,k)
                full=cv2.resize(base,(W,H),interpolation=cv2.INTER_CUBIC)
                image=overlay_type(full,t,k)
                enc.stdin.write(image.tobytes());done+=1
                if n==(a+b)//2:
                    Image.fromarray(image).save(MEDIA/f'final-shot-{k:02d}.jpg',quality=94)
            last=sample(frames,1,k);del frames
            print(f'SHOT_DONE {k+1:02d} frames_total={done} elapsed={time.monotonic()-start:.1f}s',flush=True)
        enc.stdin.close();rc=enc.wait();log.close()
        if rc:raise RuntimeError(f'FFmpeg failed with {rc}; inspect encode.log')
        expected=round(DATA['duration']*FPS)
        if done!=expected:raise RuntimeError(f'Frame count mismatch {done} != {expected}')
        receipt={'path':str(output),'frames':done,'duration':done/FPS,'size':output.stat().st_size,
                 'elapsed_seconds':round(time.monotonic()-start,2),'encoder_exit':rc,
                 'motion_source':'user-supplied actual animation, 14 independently retimed source clips',
                 'speech_speed':1.0,'newly_generated_images':0,'newly_generated_voice_clips':0}
        (ROOT/'RENDER_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print('FINAL_RENDER_READY '+json.dumps(receipt),flush=True)
    finally:
        if enc.poll() is None:enc.terminate()


def stills():
    from PIL import ImageDraw
    times=[]
    for s in SHOTS:
        times.append(s['start']+.6*(s['end']-s['start']))
    for page in range(0,len(times),8):
        canvas=Image.new('RGB',(960,912),(24,22,33));d=ImageDraw.Draw(canvas)
        for j,t in enumerate(times[page:page+8]):
            k=page+j;s=SHOTS[k];frames=load_frames(s);p=(t-s['start'])/(s['end']-s['start'])
            image=overlay_type(cv2.resize(sample(frames,p,k),(W,H),interpolation=cv2.INTER_CUBIC),t,k)
            Image.fromarray(image).save(MEDIA/f'layout-{k:02d}.jpg',quality=94)
            small=Image.fromarray(image);small.thumbnail((236,420));x=j%4*240;y=j//4*456
            canvas.paste(small,(x,y+27));d.text((x+4,y+3),f'{k:02d} {t:.1f}s',fill='white')
            del frames
        canvas.save(MEDIA/f'layout-sheet-{page//8+1}.jpg',quality=95)
    print('LAYOUT_REVIEW_READY',flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--stills',action='store_true')
    ap.add_argument('--output',default=str(ROOT/'delivery'/'Flow_State_UrduEnglish_V5.mp4'));args=ap.parse_args()
    if args.stills:stills()
    else:run(args.output)
