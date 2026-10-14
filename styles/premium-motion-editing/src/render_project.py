"""WF-05 approved compositor: project data, real moving clips, clean type.

Derived from the observed V5/V6 mechanics. No Einstein-specific text, voice,
shot order or geometry is embedded here. The historical sources remain intact
under projects/einstein-flow-state/versions for forensic reproduction.
"""
from __future__ import annotations
import json,math,subprocess,time,hashlib
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg
from policy import STYLE_ROOT,PolicyError,assert_valid,resolve,sha256,subtitle_mode
from motion import camera,cut,tilt_title
W,H,FPS,SCALE=1080,1920,30,1.5
INK=(30,22,59)

def ease(x):
    x=max(0.,min(1.,x));return x*x*(3-2*x)

class Compositor:
    def __init__(self,project:dict,timeline:dict,base:Path):
        self.project=project;self.data=timeline;self.base=base
        self.mode=subtitle_mode(project)
        self.font_dir=resolve(base,project['font_dir']) if project.get('font_dir') else STYLE_ROOT/'assets/fonts'
        self.fonts={};self.title_cache={};self.caption_cache={}
        self.media=resolve(base,project.get('media_dir','media'))
        self.layout_receipts=[]
        for i in range(len(timeline['titles'])):self.title_art(i)

    def font(self,size,kind='head'):
        key=(int(round(size*SCALE)),kind)
        if key not in self.fonts:
            name={'head':'Anton-Regular.ttf','body':'BarlowCondensed-Medium.ttf','italic':'BarlowCondensed-MediumItalic.ttf'}[kind]
            self.fonts[key]=ImageFont.truetype(str(self.font_dir/name),key[0])
        return self.fonts[key]

    def wrap(self,text,ft,width):
        lines=[];line=''
        for word in text.split():
            test=(line+' '+word).strip()
            if line and ft.getlength(test)>width:lines.append(line);line=word
            else:line=test
        if line:lines.append(line)
        return lines

    def title_art(self,index):
        if index in self.title_cache:return self.title_cache[index]
        d=self.data['titles'][index];size=float(d.get('size',82));lines=d['title'].split('\n')
        # RTL/shaping is a separate renderer capability, not fake tiny glyphs.
        if any('\u0590'<=c<='\u08ff' for c in d['title']+d.get('kicker','')+d.get('sub','')):
            raise PolicyError('Use Roman Urdu or provide a tested RTL/shaping backend; this Latin-font adapter must not emit tofu glyphs.')
        maxwidth=float(d.get('max_width',.77))*W
        while max(self.font(size).getlength(x) for x in lines)>maxwidth and size>48:size-=1
        ft=self.font(size)
        if max(ft.getlength(x) for x in lines)>maxwidth:raise PolicyError(f'Title {index} cannot fit readably; rewrite/line-break it rather than shrinking further.')
        body=self.font(29,'italic');kicker=self.font(29,'italic');kick=d.get('kicker','');sub=d.get('sub','')
        sublines=self.wrap(sub,body,maxwidth) if sub else []
        if len(lines)>2 or len(sublines)>2:raise PolicyError('Keep integrated text concise: maximum two headline and two connective lines.')
        kh=39*SCALE if kick else 0
        heights=[ft.getbbox(x)[3]-ft.getbbox(x)[1] for x in lines]
        width=int(max([ft.getlength(x) for x in lines]+[kicker.getlength(kick)]+[body.getlength(x) for x in sublines or ['']])+42*SCALE)
        height=int(kh+sum(heights)+(len(lines)-1)*10*SCALE+(20*SCALE if sublines else 0)+len(sublines)*35*SCALE+30*SCALE)
        im=Image.new('RGBA',(width,height));dr=ImageDraw.Draw(im);y=7*SCALE
        if kick:
            bb=kicker.getbbox(kick);dr.text(((width-kicker.getlength(kick))/2,y-bb[1]),kick,font=kicker,fill=(*INK,240));y+=kh
        for j,line in enumerate(lines):
            bb=ft.getbbox(line);x=(width-ft.getlength(line))/2;ty=y-bb[1]
            for z in range(13,0,-1):dr.text((x+z*.67,ty+z*.95),line,font=ft,fill=(123-z*2,105-z*2,179-z*2,245))
            dr.text((x,ty),line,font=ft,fill=(*INK,255));y+=heights[j]+10*SCALE
        for line in sublines:
            bb=body.getbbox(line);y+=3*SCALE;dr.text(((width-body.getlength(line))/2,y-bb[1]),line,font=body,fill=(*INK,245));y+=32*SCALE
        pos=d.get('position','top')
        ax=float(d.get('anchor_x',500/720 if pos=='right' else .5))
        ay=float(d.get('anchor_y',{'top':145/1280,'bottom':888/1280,'right':766/1280}[pos]))
        x=int(ax*W-width/2);top=int(ay*H)
        if x<18 or x+width>W-18 or top<25 or top+height>H-95:
            raise PolicyError(f'Title {index} leaves the readable/safe canvas; adjust anchor/word count, not microscopic font size.')
        self.layout_receipts.append({'index':index,'box':[x,top,x+width,top+height],'font_base':size,'position':pos})
        self.title_cache[index]=(im,x,top);return im,x,top

    def paste_title(self,canvas,index,t,held=False):
        d=self.data['titles'][index];im,x,y=self.title_art(index);age=max(0,t-d['start'])
        if not held and age<.34:
            a=ease(age/.34);im=Image.fromarray(tilt_title(np.array(im),age/.34,1 if d.get('position')=='top' else -1));y+=int((1-a)*24*SCALE)
        canvas.paste(im,(x,y),im)

    def plain_caption(self,index):
        if index in self.caption_cache:return self.caption_cache[index]
        d=self.data.get('captions',[])[index];ft=self.font(30,'body');lines=self.wrap(d['text'],ft,.84*W)
        if len(lines)>2:raise PolicyError('Requested plain subtitle phrase is too long; split timing windows.')
        width=int(max(ft.getlength(x) for x in lines)+36*SCALE);height=int(len(lines)*37*SCALE+20*SCALE)
        im=Image.new('RGBA',(width,height));draw=ImageDraw.Draw(im)
        for i,line in enumerate(lines):
            b=ft.getbbox(line);draw.text(((width-ft.getlength(line))/2,10*SCALE+i*37*SCALE-b[1]),line,font=ft,fill=(*INK,255),stroke_width=1,stroke_fill=(220,219,249,225))
        self.caption_cache[index]=im;return im

    def overlay(self,frame,t,shot):
        im=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)).convert('RGBA')
        active=[i for i,d in enumerate(self.data['titles']) if d['start']<=t<d['end']]
        if active:
            i=active[-1];d=self.data['titles'][i]
            if d.get('position') in {'bottom','right'}:
                prior=[j for j,v in enumerate(self.data['titles'][:i]) if v.get('position')=='top' and v['start']>=shot['start']-.13]
                if prior:self.paste_title(im,prior[-1],t,held=True)
            self.paste_title(im,i,t)
        # Crucial user policy: OFF by default. No pill, box or active-word
        # renderer exists in this production module.
        if self.mode=='plain':
            active=[i for i,d in enumerate(self.data.get('captions',[])) if d['start']<=t<d['end']]
            if active:
                i=active[-1];d=self.data['captions'][i];art=self.plain_caption(i)
                a=min(ease((t-d['start'])/.1),ease((d['end']-t)/.09))
                if a<.999:art=art.copy();art.putalpha(art.getchannel('A').point(lambda p:int(p*a)))
                im.paste(art,((W-art.width)//2,int(1167*SCALE-art.height/2)),art)
        return np.asarray(im.convert('RGB'))

    def read_frames(self,shot):
        path=resolve(self.media,shot['path']);cap=cv2.VideoCapture(str(path));fps=cap.get(cv2.CAP_PROP_FPS)
        if fps<=0:raise PolicyError(f'Undecodable source clip: {path}')
        start=max(0,int(round(float(shot.get('source_in',0))*fps)))
        cap.set(cv2.CAP_PROP_POS_FRAMES,start);end=shot.get('source_out');end=int(round(float(end)*fps)) if end is not None else None
        count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if (end if end is not None else count)-start>300:
            cap.release();raise PolicyError('Prepare shot-local source clips (maximum 300 native frames in this adapter) or use a tested streaming extension; do not preload an entire long reference.')
        frames=[];i=start
        while end is None or i<end:
            ok,f=cap.read()
            if not ok:break
            i+=1
            if f.shape[:2]==(1282,720):f=f[1:-1]
            if abs(f.shape[1]/f.shape[0]-9/16)>.015:
                raise PolicyError('Source aspect needs a deliberate prepared crop/letterbox; do not stretch unrelated framing.')
            if f.shape[:2]!=(1280,720):f=cv2.resize(f,(720,1280),interpolation=cv2.INTER_CUBIC)
            frames.append(f)
        cap.release()
        if len(frames)<2:raise PolicyError('A still image is not a prepared motion clip.')
        return frames

    def sample(self,frames,p,shot):
        p=float(np.clip(p,0,1));q=.015+.97*(p-.018*math.sin(p*2*math.pi));f=q*(len(frames)-1);i=int(f);j=min(i+1,len(frames)-1)
        source=cv2.addWeighted(frames[i],1-(f-i),frames[j],f-i,0)
        c=shot.get('camera',{})
        return camera(source,p,rect=shot.get('depth_rect',[.06,.20,.94,.80]),z_strength=float(c.get('z_strength',.045)),direction=int(c.get('direction',1)),vertical_drift=float(c.get('vertical_drift',-7)),roll_degrees=float(c.get('roll_degrees',.65)))


def render(project_path:Path,preview=False):
    project_path=project_path.resolve();p,t=assert_valid(project_path);base=project_path.parent;comp=Compositor(p,t,base)
    output=resolve(base,p.get('output','delivery/approved-edit.mp4'));output.parent.mkdir(parents=True,exist_ok=True)
    source_fingerprints={s['path']:sha256(resolve(comp.media,s['path'])) for s in t['shots']}
    fingerprint=hashlib.sha256(json.dumps({'project':p,'timeline':t,'sources':source_fingerprints,'audio':sha256(resolve(base,p['audio_mix'])),'engine':sha256(Path(__file__)),'motion':sha256(Path(__file__).with_name('motion.py'))},sort_keys=True).encode()).hexdigest()
    receipt_path=base/'RENDER_RECEIPT.json'
    if not preview and output.exists() and receipt_path.exists():
        old=json.loads(receipt_path.read_text())
        if old.get('input_fingerprint')==fingerprint and old.get('sha256')==sha256(output):
            print('SKIP verified identical existing render');return old
        raise PolicyError('An output already exists with different inputs/hash. Use a new versioned output; never silently overwrite a delivery.')
    if preview:
        dest=base/'reviews';dest.mkdir(exist_ok=True)
        for i,s in enumerate(t['shots']):
            frames=comp.read_frames(s);at=s['start']+.52*(s['end']-s['start']);f=comp.sample(frames,.52,s);full=cv2.resize(f,(W,H),interpolation=cv2.INTER_CUBIC);Image.fromarray(comp.overlay(full,at,s)).save(dest/f'shot-{i:02d}.png')
        return {'preview_only':True,'directory':str(dest)}
    expected=round(t['duration']*FPS)
    if sum(round(s['end']*FPS)-round(s['start']*FPS) for s in t['shots'])!=expected:raise PolicyError('Rounded scene intervals do not cover exactly the output frame budget.')
    partial=output.with_name(output.stem+'.partial.mp4')
    ff=imageio_ffmpeg.get_ffmpeg_exe();log=base/'encode.log'
    cmd=[ff,'-hide_banner','-loglevel','warning','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','pipe:0','-i',str(resolve(base,p['audio_mix'])),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-profile:v','high','-level:v','4.1','-crf','18','-maxrate','7M','-bufsize','14M','-preset','fast','-threads','4','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-movflags','+faststart','-t',str(t['duration']),str(partial)]
    started=time.monotonic();done=0;prev=None
    with log.open('w') as logs:
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=logs)
        try:
            for i,s in enumerate(t['shots']):
                frames=comp.read_frames(s);print(f'RENDER {i+1}/{len(t["shots"])} {s.get("name",i)}',flush=True)
                for n in range(round(s['start']*FPS),round(s['end']*FPS)):
                    at=n/FPS;local=at-s['start'];q=local/(s['end']-s['start']);f=comp.sample(frames,q,s)
                    f=cut(f,prev,local,s.get('transition','depth_push'),s.get('camera',{}).get('direction',1))
                    image=comp.overlay(cv2.resize(f,(W,H),interpolation=cv2.INTER_CUBIC),at,s);proc.stdin.write(image.tobytes());done+=1
                prev=comp.sample(frames,1,s);del frames
            proc.stdin.close();rc=proc.wait()
            if rc or done!=expected:raise PolicyError(f'Encoding incomplete: exit {rc}, {done}/{expected} frames.')
        finally:
            # Closing this job's input lets its own encoder exit; do not kill
            # another recorded render just because a status stream timed out.
            if proc.stdin and not proc.stdin.closed:proc.stdin.close()
            if proc.poll() is None:proc.wait()
    partial.replace(output)
    receipt={'schema_version':1,'project_id':p['project_id'],'style_id':'premium-motion-editing','policy_id':p['policy_id'],'subtitle_mode':comp.mode,'caption_pills':False,'word_highlighting':False,'frames':done,'duration':done/FPS,'size':output.stat().st_size,'sha256':sha256(output),'input_fingerprint':fingerprint,'source_hashes':source_fingerprints,'layout_boxes':comp.layout_receipts,'elapsed_seconds':round(time.monotonic()-started,2),'output':str(output),'status':'encoded_only_not_delivered'}
    receipt_path.write_text(json.dumps(receipt,indent=2)+'\n');print('RENDER_READY_NOT_DELIVERED',flush=True);return receipt
