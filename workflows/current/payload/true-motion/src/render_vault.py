"""Resumable native-frame CPU renderer, not a 2D plate animation.

Rendered frame directories are fingerprinted by .blend SHA256/settings to prevent
mixing stale test frames with corrected scenes. Native render progress survives
an interrupted process while the workspace cache still exists.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import bpy


def main():
    p=argparse.ArgumentParser();p.add_argument('--blend',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--select',default='all',help='all, performance, crown, or comma-separated p1,p55,c24')
    p.add_argument('--width',type=int,default=540);p.add_argument('--samples',type=int,default=12)
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    settings={'blend_sha256':hashlib.sha256(args.blend.read_bytes()).hexdigest(),
              'width':args.width,'height':round(args.width*16/9),'samples':args.samples,
              'fps':24,'engine':'Blender Cycles CPU','image_interpolation':False}
    meta=args.output/'render_settings.json'
    if meta.exists() and json.loads(meta.read_text()) != settings:
        raise SystemExit('Stale frame settings or scene hash: use a fresh output directory. No old frames overwritten.')
    meta.write_text(json.dumps(settings,indent=2))
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve()))
    mapping={'p':bpy.data.scenes['01 / THE VAULT / FIXED-CAMERA MOTION'],
             'c':bpy.data.scenes['02 / MONARCH STUDIO / CROWN']}
    selections=[]
    if args.select in ['all','performance']:
        selections += [('p',i) for i in range(1,121)]
    if args.select in ['all','crown']:
        selections += [('c',i) for i in range(1,49)]
    if args.select not in ['all','performance','crown']:
        selections=[(s[0],int(s[1:])) for s in args.select.split(',')]
    start=time.monotonic();ledger=[];last=None
    for i,(which,frame) in enumerate(selections):
        scene=mapping[which];out=args.output/f'{which}{frame:04d}.png'
        if out.exists() and out.stat().st_size>1024:
            print(f'RESUME_FRAME {which}{frame:04d} already present',flush=True);continue
        scene.render.resolution_x=args.width;scene.render.resolution_y=round(args.width*16/9)
        scene.cycles.samples=args.samples;scene.render.threads_mode='FIXED';scene.render.threads=2
        scene.cycles.use_denoising=True;scene.render.use_persistent_data=True
        scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
        bpy.context.window.scene=scene;scene.frame_set(frame)
        # Atomic completed-frame file: an interrupted PNG will never be reused.
        temp=out.with_name(out.stem+'.partial.png');scene.render.filepath=str(temp.resolve())
        t=time.monotonic();bpy.ops.render.render(write_still=True,scene=scene.name)
        os.replace(temp,out)
        seconds=round(time.monotonic()-t,3)
        ledger.append({'frame':which+str(frame),'seconds':seconds,'bytes':out.stat().st_size})
        (args.output/'progress.json').write_text(json.dumps({'requested':len(selections),
            'completed_this_run':len(ledger),'elapsed_seconds':round(time.monotonic()-start,2),
            'last_frame':which+str(frame),'native_frames':ledger},indent=2))
        print(f'NATIVE_FRAME {i+1}/{len(selections)} {which}{frame:04d} {seconds:.2f}s',flush=True)
    print('NATIVE_RENDER_COMPLETE',round(time.monotonic()-start,2),'seconds',flush=True)


if __name__=='__main__':main()
