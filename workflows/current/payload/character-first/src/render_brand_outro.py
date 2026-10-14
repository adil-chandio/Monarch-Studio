"""Native 3.6-second crown/type MOTION-GRAPHICS component, not human animation.

Uses the already-defined brand geometry/fonts. No photograph, character still,
body warp, live-action footage, optical flow or frame interpolation is involved.
The 44.4-second character film remains incomplete; this renders only its ending.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time
import wave

import imageio_ffmpeg
import numpy as np
from PIL import Image,ImageChops,ImageDraw,ImageFilter,ImageFont,ImageOps

from brand_end import W,H,FONTS,spaced_text

FPS=30
FRAMES=108
DURATION=FRAMES/FPS
SR=48000
FF=imageio_ffmpeg.get_ffmpeg_exe()


def smooth(value,start,end):
    u=max(0.,min(1.,(value-start)/(end-start)))
    return u*u*(3-2*u)


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def settings():
    return {'version':1,'width':W,'height':H,'fps':FPS,'frames':FRAMES,
            'duration':DURATION,'kind':'native_vector_brand_motion_graphics',
            'character_animation':False,
            'source_sha256':digest(__file__),
            'brand_source_sha256':digest(Path(__file__).with_name('brand_end.py')),
            'fonts':{n:digest(FONTS/n) for n in ['DejaVuSans.ttf','DejaVuSerif.ttf']}}


def crop_layer(im):
    box=im.getchannel('A').getbbox()
    return im.crop(box),box[:2]


def layers():
    ramp=Image.linear_gradient('L').resize((W,H))
    bg=ImageOps.colorize(ramp,(15,23,29),(5,9,12)).convert('RGBA')
    light=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(light)
    d.ellipse((10,260,1070,1230),fill=(109,89,58,31))
    bg=Image.alpha_composite(bg,light.filter(ImageFilter.GaussianBlur(170)))
    d=ImageDraw.Draw(bg)
    d.line((140,443,940,443),fill=(54,51,41,255),width=1)
    d.line((140,1329,940,1329),fill=(54,51,41,255),width=1)
    # Same five-point crown, rendered at 2x for clean moving vector edges.
    box=(350,625,730,865);cw,ch=360,194;x,y=360,635
    mask2=Image.new('L',((box[2]-box[0])*2,(box[3]-box[1])*2),0);m=ImageDraw.Draw(mask2)
    pts=[(.08,.92),(0,.12),(.20,.47),(.25,.06),(.405,.43),(.50,0),
         (.595,.43),(.75,.06),(.80,.47),(1,.12),(.92,.92)]
    points=[((x+a*cw-box[0])*2,(y+b*ch-box[1])*2) for a,b in pts]
    m.polygon(points,fill=255)
    m.rounded_rectangle(((x+cw*.077-box[0])*2,(y+ch*.99-box[1])*2,
                         (x+cw*.923-box[0])*2,(y+ch*1.13-box[1])*2),radius=14,fill=255)
    for px,py in [(x,y+ch*.12),(x+cw*.25,y+ch*.06),(x+cw*.50,y),(x+cw*.75,y+ch*.06),(x+cw,y+ch*.12)]:
        xx=(px-box[0])*2;yy=(py-box[1])*2;m.ellipse((xx-8,yy-8,xx+8,yy+8),fill=255)
    mask=mask2.resize((380,240),Image.Resampling.LANCZOS)
    rgb=Image.new('RGB',mask.size);g=ImageDraw.Draw(rgb)
    for row in range(rgb.height):
        u=max(0.,min(1.,(row+box[1]-y)/(ch*1.14)))
        if u<.36:f=u/.36;a,b=(239,214,164),(187,143,72)
        elif u<.69:f=(u-.36)/.33;a,b=(187,143,72),(243,216,163)
        else:f=(u-.69)/.31;a,b=(243,216,163),(142,101,48)
        col=tuple(round(aa+(bb-aa)*f) for aa,bb in zip(a,b));g.line((0,row,380,row),fill=col)
    crown=rgb.convert('RGBA');crown.putalpha(mask)
    name=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(name)
    spaced_text(d,'MONARCH',951,ImageFont.truetype(str(FONTS/'DejaVuSerif.ttf'),86),(229,209,170,255),10)
    studio=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(studio)
    spaced_text(d,'STUDIO',1080,ImageFont.truetype(str(FONTS/'DejaVuSans.ttf'),37),(208,180,128,255),18)
    return {'bg':bg,'crown':(crown,box[:2]),'name':crop_layer(name),'studio':crop_layer(studio)}


def place(base,layer,pos,opacity=1.,dy=0):
    if opacity<=0:return
    sprite=layer.copy()
    if opacity<1:sprite.putalpha(sprite.getchannel('A').point(lambda v:round(v*opacity)))
    base.alpha_composite(sprite,(round(pos[0]),round(pos[1]+dy)))


def frame(index,art):
    t=index/FPS
    bg=art['bg'].copy()
    crown,pos=art['crown'];sprite=crown.copy()
    if .65<t<1.90:
        xx,yy=np.meshgrid(np.arange(sprite.width,dtype=np.float32),np.arange(sprite.height,dtype=np.float32))
        travel=-160+(t-.65)/1.25*760
        v=np.exp(-((xx+yy*.48-travel)/24)**2)*.25
        glint=Image.new('RGBA',sprite.size,(255,244,215,0))
        alpha=np.uint8(v*np.asarray(sprite.getchannel('A')))
        glint.putalpha(Image.fromarray(alpha));sprite=Image.alpha_composite(sprite,glint)
    enter=smooth(t,.06,.53)
    place(bg,sprite,pos,enter,18*(1-enter))
    n=smooth(t,.20,.68);place(bg,*art['name'],opacity=n,dy=9*(1-n))
    s=smooth(t,.35,.79);place(bg,*art['studio'],opacity=s,dy=5*(1-s))
    line=smooth(t,.49,.91)
    if line:
        d=ImageDraw.Draw(bg);half=round(165*line)
        d.line((540-half,1200,540+half,1200),fill=(160,129,77,round(255*line)),width=2)
    # Designed fade on the entire graphic, never a face/body deformation.
    visibility=smooth(t,0,.22)*(1-smooth(t,3.15,(FRAMES-1)/FPS))
    rgb=bg.convert('RGB')
    if visibility<1:rgb=rgb.point(lambda v:round(v*visibility))
    return rgb


def synthesize_score():
    n=round(SR*DURATION);t=np.arange(n,dtype=np.float64)/SR
    audio=np.zeros((n,2),np.float64);rng=np.random.default_rng(20261015)
    def add(at,mono,gain=1.,pan=0.):
        i=round(at*SR);count=min(len(mono),n-i)
        if count<=0:return
        audio[i:i+count,0]+=mono[:count]*gain*math.sqrt((1-pan)/2)
        audio[i:i+count,1]+=mono[:count]*gain*math.sqrt((1+pan)/2)
    # A restrained air lead-in, a low impact, and original damped metallic partials.
    q=np.arange(round(.53*SR))/SR
    noise=rng.normal(size=len(q));air=np.concatenate(([0.],np.diff(noise)))
    air=np.convolve(air,np.hanning(13)/np.hanning(13).sum(),mode='same')
    add(0,air*np.sin(np.pi*q/.53)**2,.032,-.12)
    q=np.arange(round(2.8*SR))/SR
    bass=np.sin(2*np.pi*(55*q+17*(1-np.exp(-q*26))/26))*(1-np.exp(-q*95))*np.exp(-q*7)
    add(.48,bass,.21)
    bell=np.zeros_like(q)
    for frequency,gain,decay in [(440,.018,1.35),(880,.049,1.9),(1320,.027,2.25),(2363,.008,4.1)]:
        bell+=gain*np.sin(2*np.pi*frequency*q)*(1-np.exp(-q*150))*np.exp(-q*decay)
    add(.50,bell,1.,.06)
    for delay,gain,pan in [(.061,.24,-.50),(.113,.17,.50),(.193,.11,-.3),(.301,.07,.3)]:
        add(.50+delay,bell,gain,pan)
    audio*=np.minimum(1,t/.015)[:,None]
    audio*=np.minimum(1,(DURATION-t)/.27)[:,None]
    assert np.all(np.isfinite(audio))
    return np.asarray(np.clip(audio,-.9,.9),np.float32)


def write_wav(path,audio):
    with wave.open(str(path),'wb') as f:
        f.setnchannels(2);f.setsampwidth(2);f.setframerate(SR)
        f.writeframes(np.int16(audio*32767).tobytes())


def last_json(text):
    start=text.rfind('{');end=text.rfind('}')
    if start<0:raise RuntimeError('Audio measurement JSON was not returned.')
    return json.loads(text[start:end+1])


def main():
    p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.report.parent.mkdir(parents=True,exist_ok=True);expected=settings()
    if a.report.exists():
        old=json.loads(a.report.read_text())
        if old.get('settings')==expected:
            if a.output.exists() and digest(a.output)==old.get('sha256'):
                print('REUSE_COMPLETED_OUTRO',a.output,flush=True);return
            raise RuntimeError('Completed receipt exists but output is absent/different. Recover the exact saved component instead of regenerating it.')
    if a.output.exists():raise RuntimeError('Existing output is not a verified matching completed render; refusing to overwrite it.')
    config=a.work/'render_settings.json'
    if config.exists() and json.loads(config.read_text())!=expected:
        raise RuntimeError('Stale brand-frame cache; use a new work directory for changed settings.')
    config.write_text(json.dumps(expected,indent=2)+'\n')
    frames=a.work/'frames';frames.mkdir(exist_ok=True);art=layers();started=time.monotonic()
    for i in range(FRAMES):
        out=frames/f'f{i:04d}.png'
        if out.exists():
            with Image.open(out) as im:
                if im.size!=(W,H):raise RuntimeError('Mismatched cached frame dimensions')
                im.verify()
        else:
            temporary=out.with_suffix('.partial.png');frame(i,art).save(temporary,compress_level=4);os.replace(temporary,out)
        (a.work/'progress.json').write_text(json.dumps({'completed_through_frame':i,'frames':FRAMES,'character_animation':False}))
        if i%15==0 or i==FRAMES-1:print('BRAND_FRAME',i+1,'/',FRAMES,flush=True)
    raw=a.work/'original_crown_sting.wav';normal=a.work/'original_crown_sting_normalized.wav'
    write_wav(raw,synthesize_score())
    sound=subprocess.run([FF,'-hide_banner','-y','-i',str(raw),'-af',
        'loudnorm=I=-18:TP=-2:LRA=7:print_format=json','-ar',str(SR),'-c:a','pcm_s16le',str(normal)],capture_output=True,text=True,check=True)
    normalized=last_json(sound.stderr)
    temporary=a.output.with_name(a.output.stem+'.partial.mp4')
    subprocess.run([FF,'-v','error','-y','-framerate',str(FPS),'-start_number','0','-i',str(frames/'f%04d.png'),
        '-i',str(normal),'-map','0:v:0','-map','1:a:0','-frames:v',str(FRAMES),'-t',str(DURATION),
        '-vf','scale=iw:ih:out_color_matrix=bt709:out_range=tv,format=yuv420p',
        '-c:v','libx264','-threads','2','-preset','medium','-crf','17',
        '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',
        '-c:a','aac','-b:a','192k','-ar',str(SR),'-movflags','+faststart',str(temporary)],check=True)
    decoded,seconds=imageio_ffmpeg.count_frames_and_secs(str(temporary))
    assert decoded==FRAMES and abs(seconds-DURATION)<.035,(decoded,seconds)
    meta=subprocess.run([FF,'-hide_banner','-i',str(temporary)],capture_output=True,text=True).stderr
    assert f'{W}x{H}' in meta and '30 fps' in meta and '48000 Hz' in meta and 'stereo' in meta,meta
    measured=subprocess.run([FF,'-hide_banner','-i',str(temporary),'-vn','-af',
        'loudnorm=I=-18:TP=-2:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
    final_audio=last_json(measured.stderr)
    assert float(final_audio['input_tp'])<=-1.,final_audio
    os.replace(temporary,a.output)
    report={'status':'completed_brand_component_only','file':str(a.output),'bytes':a.output.stat().st_size,
            'sha256':digest(a.output),'md5':hashlib.md5(a.output.read_bytes()).hexdigest(),
            'settings':expected,'decoded_frames':decoded,'duration_seconds':seconds,
            'audio':'Original synthesized air/sub-impact/metallic-partial sting; no reference music or voice used.',
            'normalization':normalized,'encoded_audio_measurement':final_audio,
            'character_motion_frames':0,'brand_motion_frames':decoded,'complete_character_film':False,
            'body_warps':False,'source_footage_used':False,'render_seconds':round(time.monotonic()-started,2),
            'checks':{'full_decode':True,'frame_count':True,'duration':True,'native_1080_portrait':True,
                      'aac_48k_stereo':True,'encoded_true_peak_below_minus_1_dbtp':True}}
    tmp=a.report.with_suffix('.partial.json');tmp.write_text(json.dumps(report,indent=2)+'\n');os.replace(tmp,a.report)
    print('BRAND_COMPONENT_COMPLETE',a.output,decoded,'frames',seconds,'seconds',flush=True)


if __name__=='__main__':main()
