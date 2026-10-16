#!/usr/bin/env python3
"""Promote verified V6 new-shot delivery; retain all prior project bytes."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];TASK='EMS-20261015-005';STYLE='monarch-zackd-3d';BASE=ROOT/'styles'/STYLE;REL=f'projects/{TASK}/splinter-v6';P=ROOT/'workflows/current/payload/splinter-v6'
def load(p):return json.loads(p.read_text())
def save(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def main():
 assert load(ROOT/'workflows/current/ACTIVE_TASK.json')['task_id']==TASK
 r=load(P/'data/DELIVERY_RECEIPT.json');q=load(P/'data/QUALITY_REPORT.json');assert r['status']=='uploaded_and_hash_verified' and q['passed']
 m,s=r['master'],r['source_bundle'];assert m['id'] and s['id']
 wf=load(BASE/'workflow.json');old=wf['current_delivery'];history=wf.get('deliveries',[])
 if not any(x['drive_id']==old['drive_id'] for x in history):history.append(old)
 for x in history:
  if x['drive_id']==old['drive_id']:x['user_feedback']='Requested further enhancement and explicitly chose new cinematic shots with the same voice/script. Clean-frame constraint remains binding. Earlier source/master retained.'
 current={'title':'KAANTA · Macro Director Cut v6','task_id':TASK,'project_path':REL,'drive_id':m['id'],'source_drive_id':s['id'],'md5':m['md5'],'sha256':m['sha256'],'width':1080,'height':1920,'fps':30,'duration_seconds':30.5,'rendered_frames':915,'gates':f"{q['checks_passed']}/{q['checks_total']}",'director_checks':'13/13','user_visual_acceptance':'pending_review','scope_choice':'new_shots_same_voice','previous_master_preserved':old['drive_id'],'publishing_credit_required':'FluidR3 attribution;assets/music/ATTRIBUTION.md'}
 if not any(x['drive_id']==current['drive_id'] for x in history):history.append(current)
 wf.update(current_delivery=current,deliveries=history,state='DELIVERED_FOR_REVIEW');wf['runtime']['working_directory']=REL;wf['authorities']['release_folder_id']=r['folder']['id']
 wf['required_paths']=['README.md','style.json','knowledge/INDEX.md',f'{REL}/README.md',f'{REL}/src/film.js',f'{REL}/src/director.mjs',f'{REL}/src/focus-pass.js',f'{REL}/src/render.cjs',f'{REL}/src/assemble.py',f'{REL}/src/gate.py',f'{REL}/assets/models/cutaway.glb',f'{REL}/assets/music/ATTRIBUTION.md',f'{REL}/data/shot_plan.json',f'{REL}/data/NARRATION_LOCK.json',f'{REL}/data/DIRECTOR_QA.json',f'{REL}/data/FOCUS_QA.json',f'{REL}/data/QUALITY_REPORT.json',f'{REL}/data/DELIVERY_RECEIPT.json'];save(BASE/'workflow.json',wf)
 style=load(BASE/'style.json');style.update(current_release=current['title'],current_release_path=REL,current_release_task=TASK,user_visual_acceptance='pending_review',primary_renderers=[f'{REL}/src/film.js',f'{REL}/src/render.cjs'],primary_gates=[f'{REL}/src/gate.py',f'{REL}/src/check_motion.mjs',f'{REL}/src/check_focus.cjs']);style['release_history']=[{'task_id':d['task_id'],'project_path':d['project_path'],'master_id':d['drive_id'],'title':d['title']} for d in history];save(BASE/'style.json',style)
 reg=load(ROOT/'studio/registry.json')
 for row in reg['workflows']:
  if row['code']=='WF-02':row.update(current_delivery=current,state='DELIVERED_FOR_REVIEW');row['authorities']['release_folder_id']=r['folder']['id']
 save(ROOT/'studio/registry.json',reg);reg=load(ROOT/'styles/registry.json')
 for row in reg['styles']:
  if row['style_id']==STYLE:row.update(latest_release=current['title'],latest_release_path=f'styles/{STYLE}/{REL}',status='DELIVERED_FOR_REVIEW')
 save(ROOT/'styles/registry.json',reg)
 (BASE/'README.md').write_text(f'''# Monarch 3D Explainers · WF-02

User-facing workflow: **Zack d3d animation**. Reference-informed original-finished animated3D, not creator/voice impersonation, exact duplication or clinical simulation.

## Current release

[**KAANTA · Macro Director Cut v6**]({REL}/README.md) — native1080×1920,30fps,30.5s. User explicitly selected new cinematic shots with original narration/script preserved. V6 has oblique fingertip and metal-contact macros,an independently authored intact-surface insert,hero-cell tracking/internal detail,geometry-depth selective focus and new semantic shot staging. Clean composition retained; scope approval is not assumed approval of the final art.

- [Watch v6]({m['url']})
- [Delivery folder]({r['folder']['url']})
- [Source kit]({s['url']})
- [Shot plan]({REL}/data/shot_plan.json)
- [Director/voice lock proof]({REL}/data/DIRECTOR_QA.json)
- [Focus/caption proof]({REL}/data/FOCUS_QA.json)
- [Actual-master QA]({REL}/data/QUALITY_REPORT.json)
- [Delivery receipt]({REL}/data/DELIVERY_RECEIPT.json)
- [Required publishing music credit]({REL}/assets/music/ATTRIBUTION.md)

## Earlier releases retained

- [v2](projects/EMS-20261014-001/splinter-v2/README.md)
- [v3](projects/EMS-20261015-002/splinter-v3/README.md)
- [v4](projects/EMS-20261015-003/splinter-v4/README.md)
- [v5](projects/EMS-20261015-004/splinter-v5/README.md) · [master](https://drive.google.com/file/d/18kKI_5vkVOJKFUmTAEr7Tp4ZaVK6wb2M/view)

## Operating contract

Resume continuity first. Repeated vague enhancement requests can require a scope choice rather than another expensive minor-polish render. Here the user chose new shots/same voice—not a script rewrite. Preserve that choice and earlier no-clutter corrections.

Use actual geometry, source lineage and clear Urdu-English medical caveats. Reuse fixed voice assets for exact rebuilds; audition a current-session voice only for new speech. Explicit semantic cuts can be appropriate cinema; test continuity inside shots, not a fictitious single-take contract. Keep captions sharp after scene focus/shutter and verify focus actually changes3D imagery.

Render/decode the actual master,inspect encoded scenes,measure sound,hash-verify cloud uploads and retain licenses/credit. Technical tests cannot certify perfect art,ASMR response,retention or clinician approval.

The relative-path project can be mirrored with `python3 tools/studio.py hydrate wf02`; follow its README. Do not duplicate a running renderer. Large masters are on Drive. Live parent is `1LTkHpkEUFSui8Lqyy8I0j5-1AceSziWX`; the historical Powerful Personality/TABAHI ACTIVATE WF-02 snapshot remains separate.
''')
 f=BASE/'knowledge/INDEX.md';text=f.read_text();text+=f'''

## KAANTA v6 — new shots, same voice (explicit scope choice)

[Source/rebuild](../{REL}/README.md) · [shot/focus plan](../{REL}/data/shot_plan.json) · [director proof](../{REL}/data/DIRECTOR_QA.json) · [focus A/B proof](../{REL}/data/FOCUS_QA.json) · [voice/script lock](../{REL}/data/NARRATION_LOCK.json) · [final QA](../{REL}/data/QUALITY_REPORT.json)

The user chose a meaningful shot-design rebuild while keeping narration/script—not another count of added effects. V6 adds an independent radial skin-surface insert,three detailed hero-cell groups,cell tracking and geometry-depth focus. Eight of nine camera views differ materially; one useful wide anchor stays. Eight declared semantic cuts are intentional, with C2 control inside shots. No shutter blending across cuts.

A sparse depth-focus gather produced visible duplicate contours; a depth-guided separable Gaussian replaced it. A rectangular grid hole and reversed radial winding were corrected before freezing production. The inherited cross-section draws actors in front of its reveal plane; use a separate intact-surface insert rather than falsely treating those offsets as physical buried geometry. Focus A/B changes the scene PNG but leaves raw caption pixels identical. Preserve limits:stylized anatomy,approximate focus,not clinician-verified microscopy/optics or universal aesthetic certification.

Eight tactile cues and the original arranged score are rebalanced for macro perspective. Retain the included FluidR3 CC-BY publishing credit. Prior source/master files remain unchanged.
''';f.write_text(text)
 f=ROOT/'README.md';text=f.read_text().replace('KAANTA v5 Precision Cut delivered; earlier versions preserved','KAANTA v6 Macro Director Cut delivered; earlier versions preserved');f.write_text(text)
 print('V6 registered; complete continuity promotion,refresh manifest,validate/test. Earlier source untouched.')
if __name__=='__main__':main()
