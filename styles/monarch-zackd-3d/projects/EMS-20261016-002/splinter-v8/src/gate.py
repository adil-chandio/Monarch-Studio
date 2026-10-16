#!/usr/bin/env python3
"""Decode and measure the actual delivered MP4; never certify from filenames.
The visual sampling sheet supplements technical checks; it is not clinical QA.
"""
from __future__ import annotations
import argparse, hashlib, json, re, struct, subprocess
from pathlib import Path
import av
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parents[1]
FF=imageio_ffmpeg.get_ffmpeg_exe()

def atom_order(p):
    order=[]
    with p.open('rb') as f:
        offset=0;size=p.stat().st_size
        while offset+8<=size:
            f.seek(offset);n,kind=struct.unpack('>I4s',f.read(8))
            if n==1:n=struct.unpack('>Q',f.read(8))[0]
            if n==0:n=size-offset
            if n<8:break
            order.append(kind.decode('latin1'));offset+=n
    return order

def longest_run(values):
    best=cur=0
    for val in values:
        cur=cur+1 if val else 0;best=max(best,cur)
    return best

def main():
    ap=argparse.ArgumentParser();ap.add_argument('master',type=Path);ap.add_argument('--out',type=Path,default=ROOT/'build');args=ap.parse_args()
    p=args.master.resolve();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    tl=json.loads((ROOT/'data/timeline.json').read_text());expected=round(tl['duration']*tl['fps'])
    checks=[]
    def check(name,passed,details):checks.append({'name':name,'passed':bool(passed),'details':details})
    with av.open(str(p)) as c:
        v=c.streams.video[0];a=c.streams.audio[0]
        info={'video_codec':v.codec_context.name,'width':v.width,'height':v.height,'fps':float(v.average_rate),'pixel_format':v.codec_context.format.name,'duration':float(c.duration/av.time_base),'audio_codec':a.codec_context.name,'audio_rate':a.codec_context.sample_rate,'audio_channels':a.codec_context.channels}
    check('H.264 portrait native-size delivery',info['video_codec']=='h264' and [info['width'],info['height']]==[1080,1920] and info['pixel_format']=='yuv420p',info)
    check('Frame rate and container duration',abs(info['fps']-tl['fps'])<.001 and abs(info['duration']-tl['duration'])<.06,info)
    check('AAC stereo 48kHz',info['audio_codec']=='aac' and info['audio_rate']==48000 and info['audio_channels']==2,info)
    times=[.8,4.82,7.8,9.3,12.4,17.4,20.3,23.7,27.4,29.9];sample_indices={round(t*tl['fps']):t for t in times}
    fast_times=[4.30,4.63,4.82,5.05,5.15,5.23,5.34,5.46,26.25,26.54,26.71,26.95,27.10,27.30,27.52,27.67]
    fast_indices={round(t*tl['fps']):t for t in fast_times};fast_captures=[]
    captures=[];hashes=[];scene_hashes=[];pts=[];deltas=[];warm_occupancy=[];previous=None;decode_error=None;count=0
    try:
        with av.open(str(p)) as c:
            for i,f in enumerate(c.decode(video=0)):
                pts.append(float(f.pts*f.time_base));gray=f.reformat(width=270,height=480,format='gray').to_ndarray()
                roi=gray[115:355,12:258].copy()
                if True:
                    color=f.reformat(width=135,height=240,format='rgb24').to_ndarray()[60:207,5:130]
                    warm=(color[:,:,0]>color[:,:,1]*1.05)&(color[:,:,0]>color[:,:,2]*1.18)&(color[:,:,0]>70)
                    warm_occupancy.append(float(warm.mean()))
                hashes.append(hashlib.sha256(roi.tobytes()).hexdigest());scene_hashes.append(hashlib.sha256(gray[:365,2:268].tobytes()).hexdigest())
                if previous is not None:deltas.append(float(np.abs(roi.astype(np.int16)-previous.astype(np.int16)).mean()))
                previous=roi
                if i in sample_indices:
                    image=f.to_image();image.thumbnail((216,384));captures.append((sample_indices[i],image))
                if i in fast_indices:
                    im=f.to_image();im.thumbnail((180,320));fast_captures.append((fast_indices[i],im))
                count+=1
    except Exception as exc:decode_error=repr(exc)
    check('Every expected frame decodes',decode_error is None and count==expected,{'decoded':count,'expected':expected,'error':decode_error})
    check('Continuous monotonic video timestamps',len(pts)>1 and all(abs((b-a)-1/tl['fps'])<.0001 for a,b in zip(pts,pts[1:])),{'first':pts[0] if pts else None,'last':pts[-1] if pts else None})
    run=longest_run([h1==h2 for h1,h2 in zip(hashes,hashes[1:])])
    ctrl=json.loads((ROOT/'data/motion.json').read_text())
    action_activity=[]
    for label,start,end in [('surface approach','surface_approach_start','surface_approach_end'),('surface close','surface_close_start','surface_contact'),('surface pull','surface_pull_start','surface_clear'),('deep approach','deep_approach_start','deep_approach_end'),('deep close','deep_close_start','deep_contact'),('deep pull','deep_pull_start','deep_clear')]:
        a=round(ctrl['cues'][start]*tl['fps']);b=round(ctrl['cues'][end]*tl['fps']);hs=scene_hashes[a:b+1];action_activity.append({'action':label,'frames':len(hs),'unique':len(set(hs))})
    check('Authored fast action windows show actual picture motion',all(x['unique']>=max(3,x['frames']*.7) for x in action_activity),{'actions':action_activity,'whole_film_unique_anatomy_crops':len(set(hashes)),'longest_identical_crop_run_seconds':run/tl['fps'],'note':'Deliberate settles/holds are allowed; the contract is independently rendered3D with faster authored actions, not fake jitter to maximize uniqueness.'})
    check('Anatomy remains visible through every frame',bool(warm_occupancy) and min(warm_occupancy)>.08,{'minimum_warm_tissue_fraction':min(warm_occupancy) if warm_occupancy else 0,'frames_checked':len(warm_occupancy),'excluded_interval':None,'purpose':'Detect lost/blank 3D frames rather than treating animated captions/background as sufficient motion.'})
    audio_frames=0;audio_samples=0
    with av.open(str(p)) as c:
        for f in c.decode(audio=0):audio_frames+=1;audio_samples+=f.samples
    check('Entire audio stream decodes',audio_frames>0 and abs(audio_samples/48000-tl['duration'])<.06,{'frames':audio_frames,'decoded_seconds':audio_samples/48000})
    proc=subprocess.run([FF,'-hide_banner','-i',str(p),'-af','loudnorm=I=-16:TP=-1.5:LRA=8:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
    loud=json.loads(re.findall(r'\{\s*"input_i"[\s\S]*?\}',proc.stderr)[-1])
    check('Final AAC loudness and true peak',abs(float(loud['input_i'])+16)<=1 and float(loud['input_tp'])<=-1,{'integrated_lufs':float(loud['input_i']),'true_peak_dbtp':float(loud['input_tp']),'lra_lu':float(loud['input_lra'])})
    order=atom_order(p)
    check('Fast-start MP4',('moov' in order and 'mdat' in order and order.index('moov')<order.index('mdat')),{'top_level_atoms':order})
    check('Caption intervals in bounds',all(0<=c['start']<c['end']<=tl['duration'] for c in tl['captions']),{'phrases':len(tl['captions']),'alignment':'Phrase-timed, not word-level forced alignment'})
    text=' '.join(c['text'] for c in tl['captions'])
    check('Explicit no-guarantee and professional-care ending',all(s in text for s in ['har baar nahi','intezaar mat karo','doctor se madad lo','mat khodo']),{'messages':'Conditional expulsion, do not wait, doctor for warning signs, do not dig'})
    receipts=[]
    for file in sorted(out.glob('chunk-*.mp4.json')):receipts.append(json.loads(file.read_text()))
    coverage=[f for r in receipts for f in range(r['start'],r['end'])]
    check('Native-frame render receipts cover the master exactly',coverage==list(range(expected)) and all([r['width'],r['height'],r['fps']]==[1080,1920,tl['fps']] for r in receipts) and len({r['signature'] for r in receipts})==1,{'chunks':len(receipts),'covered_frames':len(coverage),'signatures':sorted({r['signature'] for r in receipts})})

    motion=json.loads((ROOT/'data/MOTION_QA.json').read_text())
    check('Retained actor/director checks pass',motion['passed'],{'passed':motion['checks_passed'],'total':motion['checks_total'],'scope':'Shot-local C2 rails, explicit semantic cuts, new surface/cell/focus views, retained voice/script and finite frame states'})
    locks=json.loads((ROOT/'data/VOICE_LOCK.json').read_text())['files']
    matched={name:hashlib.sha256((ROOT/'assets/vo'/name).read_bytes()).hexdigest()==expected for name,expected in locks.items()}
    check('User-liked narration assets remain unchanged',all(matched.values()),matched)
    h=hashlib.sha256()
    for name in ['index.html','src/film.js','src/director.mjs','src/focus-pass.js','src/motion.mjs','src/render.cjs','data/timeline.json','data/motion.json','data/design.json','data/shot_plan.json','assets/fonts/Montserrat-Cinema.typeface.json','assets/models/cutaway.glb']:h.update((ROOT/name).read_bytes())
    h.update(b'1080');h.update(b'canvas-png')
    check('Current picture source matches all recorded frame signatures',all(r['signature']==h.hexdigest() for r in receipts),{'source_signature':h.hexdigest()})
    design=json.loads((ROOT/'data/design.json').read_text())
    js=(ROOT/'src/film.js').read_text();overlay=js[js.index('function overlay(t)'):js.index('window.renderAt=')]
    no_hud=('roundBox' not in js and 'CELLS MOVE IN' not in js and 'INFECTION KA WAIT' not in js and overlay.count('fillText(')==1 and 'strokeText(c.text' in overlay)
    duration=sum(c['end']-c['start'] for c in design['typography'])
    check('Reject decorative clutter; allow only captions and two timed type beats',no_hud and len(design['typography'])==2 and duration<5,{'visible_3d_type_beats':len(design['typography']),'total_type_seconds':duration,'caption_layers':1,'hud_boxes_counters_chapter_headers':0,'page_flip':False})
    geometry=json.loads((ROOT/'data/DETERMINISM_REPORT.json').read_text())
    meshes=geometry.get('geometry',{}).get('heroTextMeshes',[])
    check('Typography is measured extruded3D geometry, not a fake-shadow label',len(meshes)==2 and all(x['type']=='TextGeometry' and x['vertices']>100 and x['depth']>0 for x in meshes),meshes)
    check('Complete-frame revisits return to identical pixels',geometry['passed'],{'scope':'Full frame, out-of-order evaluation including geometry/camera/subtitles'})
    sounds=json.loads((out/'SOUND_DESIGN_REPORT.json').read_text());levels=sounds['music_section_rms_dbfs']
    check('Restrained story-linked textures replace UI pings',sounds['cue_count']==8 and not sounds['ui_beeps_chimes_or_alerts'],{'cue_count':sounds['cue_count'],'voice_over_bed_db':sounds['voice_rms_dbfs']-sounds['sound_design_rms_dbfs'],'stereo_correlation':sounds['stereo_correlation']})
    check('Measured score builds and gives the warning line breathing space',levels['build']>levels['hook']+3 and levels['breathing_space']<levels['build']-8,levels)
    check('Mix preserves voice priority and mono compatibility',sounds['voice_rms_dbfs']-sounds['sound_design_rms_dbfs']>12 and sounds['stereo_correlation']>.7,{'voice_rms_dbfs':sounds['voice_rms_dbfs'],'bed_rms_dbfs':sounds['sound_design_rms_dbfs'],'stereo_correlation':sounds['stereo_correlation']})
    licenses=json.loads((ROOT/'assets/music/SAMPLE_PROVENANCE.json').read_text())
    samples_ok=all(hashlib.sha256((ROOT/'assets/music'/s['instrument']/(s['note']+'.mp3')).read_bytes()).hexdigest()==s['sha256'] for s in licenses['samples'])
    check('Credited music samples and publishing attribution accompany the source',samples_ok and (ROOT/'assets/music/ATTRIBUTION.md').exists(),{'sample_count':len(licenses['samples']),'license':licenses['license'],'reference_audio_copied':False})
    plan=json.loads((ROOT/'data/shot_plan.json').read_text());expected_shots={};expected_groups={}
    for frame in range(expected):
        shot=next(s for s in plan['shots'] if s['start']<=frame/tl['fps']<s['end'])
        expected_shots[shot['id']]=expected_shots.get(shot['id'],0)+1;expected_groups[shot['scene']]=expected_groups.get(shot['scene'],0)+1
    actual_shots={};actual_groups={}
    for receipt in receipts:
        for key,count in receipt.get('shotFrames',{}).items():actual_shots[key]=actual_shots.get(key,0)+count
        for key,count in receipt.get('sceneGroups',{}).items():actual_groups[key]=actual_groups.get(key,0)+count
    check('Native renderer actually visited every new shot and scene group',actual_shots==expected_shots and actual_groups==expected_groups,{'shots':actual_shots,'scene_groups':actual_groups,'expected_groups':expected_groups})
    measured_geometry=geometry.get('geometry',{})
    check('New surface and detailed hero cells are actual measured geometry',measured_geometry.get('newSurfaceVertices',0)>10000 and measured_geometry.get('newHeroCells')==3 and measured_geometry.get('heroNucleusLobesPerCell')==3,measured_geometry)
    focus_proof=json.loads((ROOT/'data/FOCUS_QA.json').read_text())
    check('Geometry-depth focus changes the image, not the caption canvas',focus_proof['passed'],focus_proof)
    lock=json.loads((ROOT/'data/NARRATION_LOCK.json').read_text())
    check('User-selected original script,caption reading copy and voice placements are retained',tl['narration']==lock['narration'] and tl['captions']==lock['captions'],{'baseline':lock['baseline'],'scope_choice':plan['scope_choice']})
    shutter=ctrl['shutter'];expected_shutter=sum(any(a<=f/tl['fps']<=b for a,b in shutter['windows']) and not any(abs(f/tl['fps']-c)<=shutter['no_cross_scene_blend_seconds'] for c in plan['intentional_cuts']) for f in range(expected))
    actual_shutter=sum(r.get('shutterFrames',0) for r in receipts);evaluations=sum(r.get('sceneEvaluations',0) for r in receipts)
    check('Fast-motion blur is accounted real3D sampling, not optical flow',actual_shutter==expected_shutter and evaluations==expected+2*expected_shutter and shutter['samples']==3,{'output_frames':expected,'real_scene_evaluations':evaluations,'shutter_output_frames':actual_shutter,'exposure_seconds':2*shutter['half_exposure_seconds'],'captions':'drawn once at center time after geometry-depth focus','no_blend_across_cuts':plan['intentional_cuts']})
    focus_frames=sum(r.get('focusFrames',0) for r in receipts)
    expected_focus=next(c['details']['depth_focus_frames'] for c in motion['checks'] if c['name']=='Every frame has finite, correctly scoped camera/focus state')
    check('Depth-focus coverage matches the authored shot plan',focus_frames==expected_focus,{'rendered_focus_frames':focus_frames,'expected_focus_frames':expected_focus,'method':'geometry-depth-guided separable Gaussian, not calibrated optics'})
    anchored=[e for e in sounds['events'] if e.get('visual_cue')]
    errors=[{'cue':e['visual_cue'],'seconds':e['measured_peak_time']-ctrl['cues'][e['visual_cue']]} for e in anchored]
    check('Measured contact/release transients match authored visual anchors',len(errors)==5 and all(abs(e['seconds'])<1/tl['fps'] for e in errors),errors)
    check('Voice placement and playback rate are retained',[(c['start'],c['duration']) for c in tl['narration']]==[(.24,6.6),(7,8.4),(15.56,6.36),(22.08,7.32)],{'narration_time_stretch':False,'total_duration':tl['duration']})
    organic=json.loads((ROOT/'data/ORGANIC_QA.json').read_text())
    check('Retained organic membranes change actual pixels and return deterministically',organic['passed'],{'repeat_exact':organic['repeatIsExact'],'moves':organic['membranesMove'],'bounded':organic['bounded'],'samples':len(organic['samples']),'scope':organic['scope']})
    upgrade=json.loads((ROOT/'data/UPGRADE_QA.json').read_text())
    check('V8 whole-film views and returned contact arcs differ from V7',upgrade['passed'],upgrade)
    check('V8 dermal micro-bundles are measured real geometry',measured_geometry.get('v8DermalBundleCount')==36 and measured_geometry.get('v8DermalBundleVertices',0)>5000,{'bundles':measured_geometry.get('v8DermalBundleCount'),'vertices':measured_geometry.get('v8DermalBundleVertices'),'limit':'stylized texture geometry, not histology'})
    # QC contact sheet is derived from the encoded master, never source stills.
    sheet=Image.new('RGB',(1080,840),'#071e2b');draw=ImageDraw.Draw(sheet)
    font=ImageFont.truetype(str(ROOT/'assets/fonts/Montserrat-VF.ttf'),20)
    for j,(time,im) in enumerate(captures):
        x=(j%5)*216;y=(j//5)*420;sheet.paste(im,(x,y));draw.text((x+12,y+390),f'{time:04.1f}s',font=font,fill='#d9ebed')
    sheet.save(out/'QA_CONTACT_SHEET.jpg',quality=92)
    strip=Image.new('RGB',(1440,690),'#102632');sd=ImageDraw.Draw(strip)
    for j,(time,im) in enumerate(fast_captures):
        x=j%8*180;y=j//8*345;strip.paste(im,(x,y));sd.text((x+7,y+323),f'{time:.2f}s',font=font,fill='#dee8eb')
    strip.save(out/'QA_FAST_ACTIONS.jpg',quality=94)
    report={'passed':all(c['passed'] for c in checks),'checks_passed':sum(c['passed'] for c in checks),'checks_total':len(checks),'master':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'md5':hashlib.md5(p.read_bytes()).hexdigest(),'metadata':info,'checks':checks,'manual_review':{'status':'pending','contact_sheet':'QA_CONTACT_SHEET.jpg','scope':'Sampled visual sequence, typography, skin/forceps framing and warning labels. No claim of independent clinician review or audible pronunciation certification.'}}
    (out/'QUALITY_REPORT.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(report,indent=2,ensure_ascii=False));raise SystemExit(0 if report['passed'] else 1)

if __name__=='__main__':main()
