#!/usr/bin/env python3
"""Review-only low-resolution master: never call this native final QA."""
import json,hashlib
from pathlib import Path
import av,numpy as np
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parents[1];out=root/'build/preview';movie=out/'KAANTA_v8_REVIEW_270x480.mp4'
samples={round(t*30):t for t in [.8,4.82,7.8,9.3,12.4,17.4,20.3,23.7,27.4,29.9]}
count=0;pts=[];captures=[];warm=[]
with av.open(str(movie)) as c:
 v=c.streams.video[0];metadata={'width':v.width,'height':v.height,'fps':float(v.average_rate),'duration':c.duration/av.time_base}
 for i,f in enumerate(c.decode(video=0)):
  count+=1;pts.append(float(f.pts*f.time_base));rgb=f.to_ndarray(format='rgb24')[120:414,10:260]
  warm.append(float(((rgb[:,:,0]>rgb[:,:,1]*1.05)&(rgb[:,:,0]>rgb[:,:,2]*1.18)&(rgb[:,:,0]>70)).mean()))
  if i in samples:captures.append((samples[i],f.to_image()))
checks={'review_resolution_only':[metadata['width'],metadata['height']]==[270,480],'all_915_frames_decode':count==915,'fps_30':metadata['fps']==30,'duration_30_5':abs(metadata['duration']-30.5)<.06,'timestamps_continuous':all(abs(b-a-1/30)<.0001 for a,b in zip(pts,pts[1:])),'tissue_visible_every_frame':min(warm)>.08}
sheet=Image.new('RGB',(1350,1010),'#102632');draw=ImageDraw.Draw(sheet)
for j,(t,im) in enumerate(captures):
 x=j%5*270;y=j//5*505;sheet.paste(im,(x,y));draw.text((x+8,y+484),f'REVIEW 270px {t:.2f}s',fill='white')
sheet.save(out/'PREVIEW_ENCODED_SHEET.jpg',quality=94)
result={'passed':all(checks.values()),'review_only':True,'checks':checks,'metadata':metadata,'decoded_frames':count,'minimum_tissue_fraction':min(warm),'sha256':hashlib.sha256(movie.read_bytes()).hexdigest(),'limitations':'Low-resolution full-motion review. Not the native1080x1920 final, not medical/ear/retention/perfection certification. Encoded sampling sheet supplements complete-stream decode checks.'}
(out/'PREVIEW_QA.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 1)
