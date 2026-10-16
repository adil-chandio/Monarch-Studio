#!/usr/bin/env python3
"""Promote the verified enhancement without overwriting the user-liked v2.
Run from the active payload, then continuity.py complete in the same operation.
"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
TASK='EMS-20261015-002';STYLE='monarch-zackd-3d'
BASE=ROOT/'styles'/STYLE;REL=f'projects/{TASK}/splinter-v3'
P=ROOT/'workflows/current/payload/splinter-v3'
def load(p):return json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def main():
    assert load(ROOT/'workflows/current/ACTIVE_TASK.json')['task_id']==TASK
    r=load(P/'data/DELIVERY_RECEIPT.json');qa=load(P/'data/QUALITY_REPORT.json')
    assert r['status']=='uploaded_and_hash_verified' and qa['passed']
    assert r['master']['id'] and r['source_bundle']['id']
    master,source=r['master'],r['source_bundle']
    wf=load(BASE/'workflow.json');old=wf['current_delivery'];history=wf.get('deliveries',[])
    if not any(d.get('drive_id')==old['drive_id'] for d in history):
        history.append({**old,'user_feedback':'User liked v2 and requested smoother motion/keyframing and more satisfying sound effects. Preserved unchanged.'})
    current={'title':'KAANTA · Motion Edition v3','task_id':TASK,'project_path':REL,'drive_id':master['id'],'source_drive_id':source['id'],'md5':master['md5'],'sha256':master['sha256'],'width':1080,'height':1920,'fps':30,'duration_seconds':30.5,'rendered_frames':915,'gates':f"{qa['checks_passed']}/{qa['checks_total']}",'motion_checks':'9/9','user_visual_acceptance':'pending_review','previous_master_preserved':old['drive_id']}
    if not any(d.get('drive_id')==current['drive_id'] for d in history):history.append(current)
    wf.update(current_delivery=current,deliveries=history,state='DELIVERED_FOR_REVIEW')
    wf['default_format']['fps']=30;wf['runtime']['working_directory']=REL
    wf['authorities']['release_folder_id']=r['folder']['id']
    wf['required_paths']=['README.md','style.json','knowledge/INDEX.md',f'{REL}/README.md',f'{REL}/src/film.js',f'{REL}/src/motion.mjs',f'{REL}/src/render.cjs',f'{REL}/src/assemble.py',f'{REL}/src/transition.py',f'{REL}/src/gate.py',f'{REL}/assets/models/cutaway.glb',f'{REL}/data/timeline.json',f'{REL}/data/motion.json',f'{REL}/data/QUALITY_REPORT.json',f'{REL}/data/DELIVERY_RECEIPT.json']
    save(BASE/'workflow.json',wf)
    style=load(BASE/'style.json');style.update(current_release=current['title'],current_release_path=REL,current_release_task=TASK,user_visual_acceptance='pending_review',primary_renderers=[f'{REL}/src/film.js',f'{REL}/src/render.cjs'],primary_gates=[f'{REL}/src/gate.py',f'{REL}/src/check_motion.mjs'])
    style['release_history']=[{'task_id':x['task_id'],'project_path':x['project_path'],'master_id':x['drive_id'],'title':x['title']} for x in history];save(BASE/'style.json',style)
    reg=load(ROOT/'studio/registry.json')
    for row in reg['workflows']:
        if row['code']=='WF-02':row.update(current_delivery=current,state='DELIVERED_FOR_REVIEW');row['authorities']['release_folder_id']=r['folder']['id']
    save(ROOT/'studio/registry.json',reg)
    reg=load(ROOT/'styles/registry.json')
    for row in reg['styles']:
        if row['style_id']==STYLE:row.update(latest_release=current['title'],latest_release_path=f'styles/{STYLE}/{REL}',status='DELIVERED_FOR_REVIEW')
    save(ROOT/'styles/registry.json',reg)
    (BASE/'README.md').write_text(f'''# Monarch 3D Explainers · WF-02

User-facing workflow: **Zack d 3d animation**. Reference-informed original-finished animated 3D explainers; no claim of creator impersonation, exact duplication or clinical simulation.

## Current release

[**KAANTA · Motion Edition v3**]({REL}/README.md) — native 1080 × 1920, 30 fps, 30.5 seconds. Continuous C2 camera rails, new grip rig, synchronized cell paths, perspective turnover and 23 original sound cues. User-liked narration retained byte-for-byte. Technically delivered; new-version visual approval is not assumed.

- [Watch v3]({master['url']})
- [V3 folder]({r['folder']['url']})
- [Editable source kit]({source['url']})
- [Editable motion controls]({REL}/data/motion.json)
- [Actual-master QA]({REL}/data/QUALITY_REPORT.json)
- [Verified receipt]({REL}/data/DELIVERY_RECEIPT.json)

## Preserved earlier release

[KAANTA v2](projects/EMS-20261014-001/splinter-v2/README.md), [original master](https://drive.google.com/file/d/10YyHXoz1avbHTrSzOW7xWZwiZUvTEMOT/view). The user liked it and asked for a motion/sound enhancement. Its source, master and hashes remain unchanged.

## Operating contract

Resume continuity first. Inspect the actual reference/live folder, keep source lineage, write clear Urdu-English claims, and animate real geometry. Audition a voice in the current session for new speech; use the fixed included WAVs for exact rebuilds—archived voice IDs are not new registrations. Render and decode the actual MP4, inspect encoded samples, measure audio, and hash-verify Drive uploads before claiming completion. Technical gates do not imply artistic or clinician approval.

The current project is relative-path portable. `python3 tools/studio.py hydrate wf02` creates a disposable byte-preserving mirror. Follow the project README for dependencies and render commands. Large masters remain on Drive rather than Git.

The live WF-02 Drive parent is `1LTkHpkEUFSui8Lqyy8I0j5-1AceSziWX`. The old **Powerful Personality / TABAHI ACTIVATE** WF-02 snapshot remains a separate historical workflow; it is not renamed or merged into this implementation.
''')
    idx=BASE/'knowledge/INDEX.md';text=idx.read_text();text+=f'''

## KAANTA v3 — motion / sound enhancement

- [v3 source and rebuild guide](../{REL}/README.md)
- [Editable C2 camera/actor controls](../{REL}/data/motion.json)
- [915-frame motion sample table](../{REL}/data/MOTION_SAMPLES.csv)
- [Motion QA](../{REL}/data/MOTION_QA.json)
- [Strict full-frame determinism](../{REL}/data/DETERMINISM_REPORT.json)
- [Turnover provenance](../{REL}/data/POSTFX_REPORT.json)
- [Sound/voice comparison](../{REL}/data/SOUND_COMPARISON.json)
- [Delivery receipt](../{REL}/data/DELIVERY_RECEIPT.json)

Lessons: preserve the liked version and voice; use absolute C2 rails instead of camera resets; close/lock a measured jaw gap before moving wood; place cells during the actual sentence; share motion cues with SFX; keep a turn-over transition frame-native and record its containing-chunk recomposition. Explicit CPU 2D canvas contexts resolved the small cold brand-mark raster difference, enabling strict full-frame tests. Lossless composite capture matched native browser screenshots. A VSM/clearcoat-free trial did not help performance and was not used. Native30fps is real rendering, not interpolated24fps. Avoid overstating mathematical smoothness as universal artistic perfection.
''';idx.write_text(text)
    readme=ROOT/'README.md';text=readme.read_text().replace('KAANTA v2 delivered for review; native portrait 3D','KAANTA v3 Motion Edition delivered; v2 preserved');readme.write_text(text)
    print('v3 registered without changing v2 source/master. Complete continuity promotion, then manifest/validate/test.')
if __name__=='__main__':main()
