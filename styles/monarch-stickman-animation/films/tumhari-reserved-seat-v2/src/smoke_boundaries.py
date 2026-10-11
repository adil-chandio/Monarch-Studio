#!/usr/bin/env python3
"""Render every V2 cut boundary at -2/0/+2 frames and reject broken transitions."""
from __future__ import annotations
import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import render as r

P=Path(__file__).resolve().parent.parent
STYLE='WF01' if r.FPS==30 else 'WF03'

def font(n):
    for q in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf'):
        if Path(q).exists():return ImageFont.truetype(q,n)
    return ImageFont.load_default()

def metrics(im):
    a=np.asarray(im.resize((192,108),Image.Resampling.BILINEAR),np.float32)
    l=.2126*a[...,0]+.7152*a[...,1]+.0722*a[...,2]
    return float(l.mean()),float((l<3).mean()),a

def main():
    rows=[];cache={};all_ok=True
    for b in r.BEATS[1:]:
        bid=int(b['id']);t=float(b['t0']);frames=[];ms=[]
        for off in (-2,0,2):
            i=max(0,min(int(r.DUR*r.FPS)-1,round(t*r.FPS)+off))
            im=r.render_frame(i).convert('RGB');frames.append(im)
            mean,blank,a=metrics(im);ms.append((mean,blank,a))
        dpre=float(np.abs(ms[1][2]-ms[0][2]).mean());dpost=float(np.abs(ms[2][2]-ms[1][2]).mean())
        # Boundary frames may intentionally flash near-black/white; full-film tonal gates remain strict.
        tonal=all(5<m[0]<250 and m[1]<.97 for m in ms)
        ok=tonal and dpre>.015 and dpost>.015 and all(x.size==(1920,1080) for x in frames)
        all_ok &= ok
        rows.append({'beat':bid,'boundary_s':t,'frames':[round(t*r.FPS)+o for o in (-2,0,2)],'mean_luma':[round(m[0],3) for m in ms],'pre_delta':round(dpre,4),'post_delta':round(dpost,4),'pass':bool(ok)})
        if bid in (2,7,12,21,25,34):cache[bid]=frames
    art=P/'artifacts';art.mkdir(exist_ok=True)
    report={'style':STYLE,'fps':r.FPS,'boundaries_tested':len(rows),'frames_rendered':len(rows)*3,'all_pass':bool(all_ok),'minimum_pre_delta':min(x['pre_delta'] for x in rows),'minimum_post_delta':min(x['post_delta'] for x in rows),'rows':rows}
    (art/f'TRANSITION_BOUNDARY_SMOKE_{STYLE}.json').write_text(json.dumps(report,indent=2)+'\n')
    cw,ch=320,180;top=50;sheet=Image.new('RGB',(cw*6,top+ch*3),(14,15,18));d=ImageDraw.Draw(sheet)
    d.text((20,16),f'{STYLE} V2 · TRANSITION BOUNDARY SMOKE · BEFORE / CUT / AFTER',font=font(20),fill=(230,225,210))
    for col,bid in enumerate((2,7,12,21,25,34)):
        for row,im in enumerate(cache[bid]):
            thumb=im.resize((cw,ch),Image.Resampling.LANCZOS);sheet.paste(thumb,(col*cw,top+row*ch))
            dd=ImageDraw.Draw(sheet);dd.rectangle([col*cw+4,top+row*ch+4,col*cw+92,top+row*ch+29],fill=(8,9,12))
            dd.text((col*cw+9,top+row*ch+8),f'B{bid:02d} {(-2,0,2)[row]:+d}f',font=font(14),fill=(232,83,77) if STYLE=='WF01' else (84,197,218))
    out=art/f'TRANSITION_BOUNDARY_SMOKE_{STYLE}.jpg';sheet.save(out,quality=92,subsampling=0)
    print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2));print(out)
    raise SystemExit(0 if all_ok else 1)
if __name__=='__main__':main()
