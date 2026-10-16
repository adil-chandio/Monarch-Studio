#!/usr/bin/env python3
"""Register only a verified precision-cut delivery; preserve earlier source."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];TASK='EMS-20261015-004';STYLE='monarch-zackd-3d';BASE=ROOT/'styles'/STYLE;REL=f'projects/{TASK}/splinter-v5';P=ROOT/'workflows/current/payload/splinter-v5'
def read(p):return json.loads(p.read_text())
def save(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def main():
 assert read(ROOT/'workflows/current/ACTIVE_TASK.json')['task_id']==TASK
 r=read(P/'data/DELIVERY_RECEIPT.json');q=read(P/'data/QUALITY_REPORT.json');assert r['status']=='uploaded_and_hash_verified' and q['passed']
 master,source=r['master'],r['source_bundle'];assert master['id'] and source['id']
 wf=read(BASE/'workflow.json');old=wf['current_delivery'];history=wf.get('deliveries',[])
 if not any(d['drive_id']==old['drive_id'] for d in history):history.append(old)
 for d in history:
  if d['drive_id']==old['drive_id']:d['user_feedback']='User requested faster reference-paced motion/keyframes and refined detail/colour/premium SFX; prior no-clutter correction remains binding. Old source/master preserved.'
 current={'title':'KAANTA · Precision Cut v5','task_id':TASK,'project_path':REL,'drive_id':master['id'],'source_drive_id':source['id'],'md5':master['md5'],'sha256':master['sha256'],'width':1080,'height':1920,'fps':30,'duration_seconds':30.5,'rendered_frames':915,'gates':f"{q['checks_passed']}/{q['checks_total']}",'motion_checks':'12/12','user_visual_acceptance':'pending_review','previous_master_preserved':old['drive_id'],'publishing_credit_required':'FluidR3 sample attribution; see assets/music/ATTRIBUTION.md'}
 if not any(d['drive_id']==current['drive_id'] for d in history):history.append(current)
 wf.update(current_delivery=current,deliveries=history,state='DELIVERED_FOR_REVIEW');wf['runtime']['working_directory']=REL;wf['authorities']['release_folder_id']=r['folder']['id']
 wf['required_paths']=['README.md','style.json','knowledge/INDEX.md',f'{REL}/README.md',f'{REL}/src/film.js',f'{REL}/src/motion.mjs',f'{REL}/src/render.cjs',f'{REL}/src/assemble.py',f'{REL}/src/sound_design.py',f'{REL}/src/gate.py',f'{REL}/assets/models/cutaway.glb',f'{REL}/assets/music/ATTRIBUTION.md',f'{REL}/data/design.json',f'{REL}/data/motion.json',f'{REL}/data/MOTION_COMPARISON.json',f'{REL}/data/QUALITY_REPORT.json',f'{REL}/data/DELIVERY_RECEIPT.json'];save(BASE/'workflow.json',wf)
 s=read(BASE/'style.json');s.update(current_release=current['title'],current_release_path=REL,current_release_task=TASK,user_visual_acceptance='pending_review',primary_renderers=[f'{REL}/src/film.js',f'{REL}/src/render.cjs'],primary_gates=[f'{REL}/src/gate.py',f'{REL}/src/check_motion.mjs']);s['release_history']=[{'task_id':d['task_id'],'project_path':d['project_path'],'master_id':d['drive_id'],'title':d['title']} for d in history];save(BASE/'style.json',s)
 reg=read(ROOT/'studio/registry.json')
 for row in reg['workflows']:
  if row['code']=='WF-02':row.update(current_delivery=current,state='DELIVERED_FOR_REVIEW');row['authorities']['release_folder_id']=r['folder']['id']
 save(ROOT/'studio/registry.json',reg);reg=read(ROOT/'styles/registry.json')
 for row in reg['styles']:
  if row['style_id']==STYLE:row.update(latest_release=current['title'],latest_release_path=f'styles/{STYLE}/{REL}',status='DELIVERED_FOR_REVIEW')
 save(ROOT/'styles/registry.json',reg)
 (BASE/'README.md').write_text(f'''# Monarch 3D Explainers · WF-02

User-facing workflow: **Zack d3d animation**. Reference-informed original-finished3D explainers; no creator/voice impersonation, exact-copy or clinical-simulation claim.

## Current release

[**KAANTA · Precision Cut v5**]({REL}/README.md) — native1080×1920,30fps,30.5s. Faster authored approach/close/pull/camera windows with clear settles, stronger material detail/blue-warm separation, short real-scene shutter sampling and tightly anchored tactile effects. Original voice/duration unchanged. Clean-v4 constraints preserved: no HUD/panels/counters/page-turn/UI pings.

- [Watch v5]({master['url']})
- [Delivery folder]({r['folder']['url']})
- [Source kit]({source['url']})
- [V4→V5 motion comparison]({REL}/data/MOTION_COMPARISON.json)
- [Actual-master QA]({REL}/data/QUALITY_REPORT.json)
- [Verified receipt]({REL}/data/DELIVERY_RECEIPT.json)
- [Publishing music credit]({REL}/assets/music/ATTRIBUTION.md)

Technical delivery is not assumed user artistic approval. Native30fps remains30fps: the fast-motion shutter re-evaluates actual geometry within the output frame, not optical flow or a fake60fps conversion.

## Earlier versions preserved

- [v2](projects/EMS-20261014-001/splinter-v2/README.md) · [master](https://drive.google.com/file/d/10YyHXoz1avbHTrSzOW7xWZwiZUvTEMOT/view)
- [v3](projects/EMS-20261015-002/splinter-v3/README.md) · [master](https://drive.google.com/file/d/1Wl8S1M6jT3SNU6vEHJt9Kw3sePz0TH-i/view)
- [v4](projects/EMS-20261015-003/splinter-v4/README.md) · [master](https://drive.google.com/file/d/1Aw7InbA91uoiL2XHBTqPB_7J3vHQvolq/view)

## Operating contract

Resume continuity first. Inspect the actual reference/live folder, preserve lineage and specific user corrections, and animate real geometry. Faster should mean shorter purposeful action windows—not global voice acceleration or indiscriminate effects. More overlays/cues do not automatically improve quality. Keep supplied narration for exact rebuilds; audition a current-session voice for genuinely new speech, not by reusing an archived registration ID.

Render/decode the actual MP4, inspect encoded samples, measure sound and hash-verify delivery. Technical checks do not prove perfect art, clinical approval, ASMR response or audience retention. Retain sample/font credits and provide the publishing credit to the user.

The relative-path project can be mirrored with `python3 tools/studio.py hydrate wf02`; follow its README. Do not duplicate a running renderer. Masters are on Drive, not Git. Live parent: `1LTkHpkEUFSui8Lqyy8I0j5-1AceSziWX`. The earlier Powerful Personality/TABAHI ACTIVATE legacy WF-02 snapshot remains separate.
''')
 f=BASE/'knowledge/INDEX.md';text=f.read_text();text+=f'''

## KAANTA v5 — decisive action, not global speed-up

[Rebuild/source](../{REL}/README.md) · [comparison](../{REL}/data/MOTION_COMPARISON.json) · [motion QA](../{REL}/data/MOTION_QA.json) · [master QA](../{REL}/data/QUALITY_REPORT.json) · [sound anchors](../{REL}/data/SOUND_DESIGN_REPORT.json)

Preserve the clean-v4 correction. V5 shortens actual authored actions:surface pull1.17→0.42s,deep pull1.97→0.72s; camera moves0.40–0.58s with settles. Record comparisons against the real prior controls rather than claiming an unmeasured quality percentage. Faster moves benefit from short bounded real-scene shutter sampling; captions should remain center-time sharp and different scenes must never blend across the cut. A two-sample proof showed excessive contour separation, so the selected shutter is shorter and center-weighted across3 evaluations.

Material detail was changed in code: localized pad ridges/pore variations, cellular skin relief/fibrous dermis, directional wood grain and brushed steel. Release friction leads into the transient so its peak—not the clip start—can match the visual anchor. Numerical/per-frame checks supplement actual encoded-sample review; they do not certify taste/perfection. Voice and music sample publishing credit remain preserved.
''';f.write_text(text)
 f=ROOT/'README.md';text=f.read_text().replace('KAANTA v4 Cinema Cut delivered; v2/v3 preserved','KAANTA v5 Precision Cut delivered; earlier versions preserved');f.write_text(text)
 print('Verified v5 registered; complete continuity promotion then manifest/validate/test. Earlier source/master untouched.')
if __name__=='__main__':main()
