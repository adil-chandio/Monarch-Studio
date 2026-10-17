#!/usr/bin/env python3
"""Headless CPU path-traced Monarch 3D look/rig proof (not a release master).

Only three-dimensional OBJ surfaces, area/portal lights and a perspective camera
enter Mitsuba. The locked front portrait is baked ONCE to the static face mesh
as an albedo; no source/plate is placed as a 2D card and no facial pixels/mesh
vertices are displaced frame-by-frame. Subsequent animation is rigid-head,
mesh-body and camera transformations. Requires private fit_face.py output.
"""
from __future__ import annotations

import argparse
import math
import subprocess
import time
from pathlib import Path

import cv2
import mitsuba as mi
import numpy as np
from PIL import Image, ImageDraw, ImageFont

mi.set_variant("scalar_rgb")  # No display server / GL / GPU needed
T = mi.ScalarTransform4f


def smooth(x: float) -> float:
    x = max(0., min(1., x))
    return x*x*(3.-2.*x)


def pbr(rgb: list[float], rough: float = .6) -> dict:
    return {'type':'roughplastic','distribution':'ggx','alpha':rough,
            'diffuse_reflectance':{'type':'rgb','value':rgb}}


def diffuse(rgb: list[float]) -> dict:
    return {'type':'diffuse','reflectance':{'type':'rgb','value':rgb}}


def mesh(model: Path, name: str, material: dict, transform=None) -> dict:
    return {'type':'obj','filename':str(model/f'{name}.obj'),
            'face_normals':False,'to_world':transform or T(), 'bsdf':material}


def area(position: list[float], target: list[float], size: list[float], radiance: list[float]) -> dict:
    return {'type':'rectangle',
            'to_world':T.look_at(origin=position,target=target,up=[0,0,1]) @ T.scale([size[0],size[1],1]),
            'emitter':{'type':'area','radiance':{'type':'rgb','value':radiance}}}


def point(position: list[float], intensity: list[float]) -> dict:
    # Emitters do not become giant visible softbox cards in the camera frustum.
    return {'type':'point', 'position':position,
            'intensity':{'type':'rgb','value':intensity}}


def pose(seconds: float) -> dict[str,float]:
    # Temporal continuous easing, no noisy per-frame facial tracking.
    turn = smooth((seconds-.4)/2.25)
    return {'head_yaw':24*turn - 5*smooth((seconds-2.35)/.6),
            'head_nod':1.2*math.sin(seconds*2.7)-1.5*turn,
            'torso_lean':1.9*math.sin(seconds*1.65),
            'breath':.0034*math.sin(seconds*2.1),
            'camera_x':-.036+.065*smooth(seconds/3.2),
            'camera_z':-.072+.010*smooth(seconds/3.2)}


def build_scene(model: Path, seconds: float, width: int, height: int, spp: int) -> dict:
    anim=pose(seconds)
    # Chest and head are distinct rigid hierarchies. The head's material mesh
    # vertex coordinates never change between frames; yaw is a 3D transform.
    chest=T.translate([0, .0015*math.sin(seconds*1.8), anim['breath']]) @ T.rotate([1,0,0],anim['torso_lean'])
    head=chest @ T.rotate([0,0,1],anim['head_yaw']) @ T.rotate([1,0,0],anim['head_nod'])
    skin=pbr([.32,.168,.117],.41)
    charcoal=diffuse([.044,.049,.056]); stitch=diffuse([.068,.075,.083])
    hair=pbr([.014,.020,.025],.29)
    scene={'type':'scene',
        'integrator':{'type':'direct'},
        'sensor':{'type':'thinlens','fov':35,'focus_distance':.57,'aperture_radius':.0018,
                  'to_world':T.look_at(origin=[anim['camera_x'],-.56,anim['camera_z']],
                                       target=[0,.035,-.124],up=[0,0,1]),
                  'film':{'type':'hdrfilm','width':width,'height':height,'rfilter':{'type':'gaussian'}},
                  'sampler':{'type':'independent','sample_count':spp}},
        'env':{'type':'constant','radiance':{'type':'rgb','value':[.009,.011,.017]}},
        # Softboxes are well outside camera view, never huge white panels in frame.
        'key':point([-.48,-.28,.29],[3.6,3.05,2.55]),
        'fill':point([.50,-.20,.08],[.65,1.7,2.55]),
        'rim':point([.34,.38,.13],[.28,1.05,2.0]),
        'amber':point([-.34,.35,-.01],[1.2,.39,.13]),
        # The red portal and its light are actual area-emitting geometry BEHIND
        # the rig; the seated character, chamber and cables occupy real depth.
        'portal':area([0,1.38,-.20],[0,0,-.23],[.43,.62],[2.6,.055,.025]),
        'wall':{'type':'cube','to_world':T.translate([0,1.60,-.36]) @ T.scale([1.4,.08,1.15]),
                'bsdf':diffuse([.014,.012,.018])},
        'frame_left':{'type':'cube','to_world':T.translate([-.50,1.20,-.18]) @ T.scale([.035,.08,.70]),
                      'bsdf':pbr([.014,.018,.025],.28)},
        'frame_right':{'type':'cube','to_world':T.translate([.50,1.20,-.18]) @ T.scale([.035,.08,.70]),
                       'bsdf':pbr([.014,.018,.025],.28)},
        'chair':{'type':'cube','to_world':T.translate([0,.53,-.49]) @ T.scale([.14,.045,.30]),
                 'bsdf':pbr([.017,.020,.025],.58)},
        'cables':mesh(model,'cables',pbr([.019,.019,.025],.29)),
        'face':{'type':'obj','filename':str(model/'monarch_face_v5.obj'),
                'face_normals':False,'to_world':head,
                'bsdf':{'type':'roughplastic','distribution':'ggx','alpha':.40,
                        'diffuse_reflectance':{'type':'bitmap',
                                               'filename':str(model/'monarch_face_v5_albedo.png')}}},
        'skin':mesh(model,'skin',skin,head),
        'hair_front':mesh(model,'hair_front',{'type':'roughplastic','alpha':.46,
            'diffuse_reflectance':{'type':'bitmap','filename':str(model/'monarch_face_v5_albedo.png')}},head),
        'hair_back':mesh(model,'hair_back',hair,head),
        'hair_locks':mesh(model,'hair_locks',pbr([.022,.030,.036],.24),head),
        'hair_strands':mesh(model,'hair_strands',pbr([.033,.040,.046],.39),head),
        'coat':mesh(model,'coat',charcoal,chest),
        'shirt':mesh(model,'shirt',diffuse([.010,.012,.015]),chest),
        'lapels':mesh(model,'lapels',stitch,chest),
        'collar':mesh(model,'collar',diffuse([.016,.020,.024]),chest),
        'buttons':mesh(model,'buttons',pbr([.13,.11,.08],.28),chest),
    }
    for side in (-1,1):
        scene[f'sleeve_{side}']=mesh(model,f'sleeve_{side}',charcoal,chest)
        scene[f'cuff_{side}']=mesh(model,f'cuff_{side}',diffuse([.018,.021,.024]),chest)
        scene[f'hand_{side}']=mesh(model,f'hand_{side}',skin,chest)
    return scene


def grade(hdr: np.ndarray, frame: int) -> np.ndarray:
    # Global film curve/bloom/grain: NEVER warps/composites the face region.
    c=np.maximum(0,hdr.astype(np.float32))
    c=(c*(2.51*c+.03))/(c*(2.43*c+.59)+.14)  # ACES approximation
    c=np.clip(c,0,1)**(1/2.2)
    c8=np.uint8(np.clip(c*255,0,255))
    glow=cv2.GaussianBlur(np.maximum(c8.astype(np.float32)-184.,0.),(0,0),12.)
    c8=np.uint8(np.clip(c8.astype(np.float32)+glow*.065,0,255))
    rng=np.random.default_rng(frame+7221)
    noise=rng.normal(0,1.2,(c8.shape[0],c8.shape[1],1))
    return np.uint8(np.clip(c8.astype(np.float32)+noise,0,255))


def draw_proof_label(rgb: np.ndarray, frame: int) -> np.ndarray:
    im=Image.fromarray(rgb);d=ImageDraw.Draw(im)
    w,h=im.size
    size=max(13,int(w*.025))
    try:font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',size)
    except OSError:font=ImageFont.load_default()
    d.text((w*.05,h*.91),'3D MESH / RIG TEST   -   NOT FINAL',font=font,fill=(235,193,112),stroke_width=1,stroke_fill=(18,20,25))
    d.text((w*.05,h*.935),'Monarch v5 face  /  charcoal blazer  /  no face warp',font=font,
           fill=(172,181,196),stroke_width=1,stroke_fill=(17,19,23))
    return np.asarray(im)


def render(model: Path, output: Path, duration: float, fps: int, width: int, height: int, spp: int, still: float | None) -> None:
    if any(token in output.stem.upper() for token in ('MASTER', 'FINAL', 'DELIVERY')):
        raise ValueError('This look-dev renderer cannot label its output a final master')
    for required in ('monarch_face_v5.obj','monarch_face_v5_albedo.png','model_manifest.json','coat.obj','hair_front.obj'):
        if not (model / required).is_file():
            raise FileNotFoundError(f'Missing private fitted 3D asset: {model / required}')
    output.parent.mkdir(parents=True,exist_ok=True)
    total=1 if still is not None else max(1,int(round(duration*fps)))
    ffmpeg=None
    if still is None:
        from imageio_ffmpeg import get_ffmpeg_exe
        ffmpeg=subprocess.Popen([get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-y',
                                  '-f','rawvideo','-pix_fmt','rgb24','-s',f'{width}x{height}',
                                  '-r',str(fps),'-i','-','-c:v','libx264','-preset','fast',
                                  '-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],
                                 stdin=subprocess.PIPE)
    started=time.monotonic()
    try:
        for f in range(total):
            seconds=still if still is not None else f/fps
            scene=mi.load_dict(build_scene(model,seconds,width,height,spp))
            image=mi.render(scene,spp=spp)
            frame=draw_proof_label(grade(image.numpy(),f),f)
            if still is not None:
                Image.fromarray(frame).save(output)
            else:
                assert ffmpeg and ffmpeg.stdin
                ffmpeg.stdin.write(frame.tobytes())
            if f%max(fps//2,1)==0 or f==total-1:
                print(f'{f+1}/{total} (t={seconds:.2f}s) elapsed={time.monotonic()-started:.1f}s',flush=True)
    finally:
        if ffmpeg:
            assert ffmpeg.stdin
            ffmpeg.stdin.close()
            code=ffmpeg.wait()
            if code:raise RuntimeError(f'Video encode failed with code {code}')
    print(f'Wrote {output}; time {time.monotonic()-started:.1f}s',flush=True)


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--duration',type=float,default=3.0)
    p.add_argument('--fps',type=int,default=24)
    p.add_argument('--width',type=int,default=540)
    p.add_argument('--height',type=int,default=960)
    p.add_argument('--spp',type=int,default=16)
    p.add_argument('--still',type=float)
    a=p.parse_args()
    render(a.model,a.output,a.duration,a.fps,a.width,a.height,a.spp,a.still)


if __name__=='__main__':main()
