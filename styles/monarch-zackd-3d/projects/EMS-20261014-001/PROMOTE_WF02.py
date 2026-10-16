#!/usr/bin/env python3
"""Register a completed, uploaded WF-02 release. Run only BEFORE continuity
complete, then promote this payload via that controller in the same operation.
This does not touch old WF-02 snapshots, old masters, or any remote service.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
PAYLOAD=ROOT/'workflows/current/payload'
PROJECT=PAYLOAD/'splinter-v2'
TASK='EMS-20261014-001'
STYLE='monarch-zackd-3d'
BASE=ROOT/'styles'/STYLE
REL=f'projects/{TASK}/splinter-v2'

def load(p):return json.loads(p.read_text())
def write(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')

def main():
    state=load(ROOT/'workflows/current/ACTIVE_TASK.json')
    if state['task_id']!=TASK:raise SystemExit('Wrong active task; do not re-run archived promotion helper.')
    receipt=load(PROJECT/'data/DELIVERY_RECEIPT.json');qa=load(PROJECT/'data/QUALITY_REPORT.json')
    if receipt.get('status')!='uploaded_and_hash_verified' or not qa['passed']:
        raise SystemExit('Cannot promote: verified master, source upload and QA are required.')
    master,source=receipt['master'],receipt['source_bundle']
    if not master.get('id') or not source.get('id'):raise SystemExit('Missing real Drive delivery IDs')
    basepath=f'styles/{STYLE}'
    BASE.mkdir(parents=True,exist_ok=True);(BASE/'knowledge').mkdir(exist_ok=True)
    write(BASE/'style.json',{'schema_version':1,'style_id':STYLE,'name':'Monarch 3D Explainers · WF-02','user_workflow_name':'Zack d 3d animation','workflow_code':'WF-02','path':basepath,'lifecycle':'permanent','active_work_is_allowed_here':False,'workflow_contract':'workflow.json','knowledge_index':'knowledge/INDEX.md','primary_renderers':[f'{REL}/src/film.js',f'{REL}/src/render.cjs'],'primary_gates':[f'{REL}/src/gate.py'],'current_release':'KAANTA · Urdu-English v2','current_release_path':REL,'current_release_task':TASK,'reproducibility':'R1_source_and_fixed_voice_assets','user_visual_acceptance':'pending_review'})
    delivery={'title':'KAANTA · Urdu-English v2','task_id':TASK,'project_path':REL,'drive_id':master['id'],'source_drive_id':source['id'],'md5':master['md5'],'sha256':master['sha256'],'width':1080,'height':1920,'fps':24,'duration_seconds':30.5,'rendered_frames':732,'gates':f"{qa['checks_passed']}/{qa['checks_total']}",'user_visual_acceptance':'pending_review'}
    required=['README.md','style.json','knowledge/INDEX.md',f'{REL}/README.md',f'{REL}/src/film.js',f'{REL}/src/render.cjs',f'{REL}/src/assemble.py',f'{REL}/src/gate.py',f'{REL}/assets/models/cutaway.glb',f'{REL}/data/timeline.json',f'{REL}/data/QUALITY_REPORT.json',f'{REL}/data/DELIVERY_RECEIPT.json']
    write(BASE/'workflow.json',{'schema_version':2,'code':'WF-02','style_id':STYLE,'slug':'wf02','name':'Monarch 3D Explainers · WF-02','path':basepath,'trigger':{'token':'WF2','grammar':'WF2 <topic or reference>','mode':'reference_review_then_voice_audition_and_actual_3d_render'},'state':'DELIVERED_FOR_REVIEW','default_format':{'width':1080,'height':1920,'fps':24,'loudness_lufs':-16},'runtime':{'hydrate_layout':'portable_style_mirror','working_directory':REL},'current_delivery':delivery,'required_paths':required,'authorities':{'drive_folder_id':'1LTkHpkEUFSui8Lqyy8I0j5-1AceSziWX','release_folder_id':receipt['folder']['id']},'legacy_boundary':'The historical Powerful Personality / TABAHI ACTIVATE WF-02 snapshot is preserved separately and is not this runtime.'})
    (BASE/'README.md').write_text(f'''# Monarch 3D Explainers · WF-02

User-facing workflow: **Zack d 3d animation**. This is a reference-informed, original-finished **animated 3D explainer** workflow; it is not a promise of exact duplication or creator/voice impersonation.

## Current release

[**KAANTA · Skin ke andar kya hota hai? · Urdu-English v2**]({REL}/README.md) — 30.5 seconds, native 1080 × 1920, 24 fps. Technically delivered; user visual approval is not assumed.

- [Watch the MP4]({master['url']})
- [Delivery folder]({receipt['folder']['url']})
- [Source package]({source['url']})
- [Script, medical sources and lineage]({REL}/docs/SCRIPT_AND_PRODUCTION.md)
- [Measured quality report]({REL}/data/QUALITY_REPORT.json)
- [Verified delivery receipt]({REL}/data/DELIVERY_RECEIPT.json)

## Operating contract

1. Resume the repository's active task before starting another film.
2. Inspect the actual supplied reference and the live workflow folder. Do not infer source from a title alone, or discard newer remote assets.
3. Reuse provenanced user assets where appropriate, and distinguish recovered work from newly created work.
4. Write easy Urdu-English narration; check factual claims and uncertainty. For new narration, audition a voice in the current session. Archived voice IDs are **not** registrations in a new session; fixed WAV assets are included for exact rebuilds.
5. Animate actual meshes, cameras and scene elements. Do not relabel an image slideshow as 3D character animation.
6. Render, decode and check the actual MP4; measure loudness and inspect encoded-frame samples.
7. Upload the master, script, subtitles and reproducible source to the user's confirmed Drive folder. Verify real IDs/hashes before marking delivery complete.
8. Preserve source, limitations, tests, failures/fixes and receipts. Keep large masters on Drive.

## Portable execution

The project is already relative-path portable. Its README has dependency and render commands. `python3 tools/studio.py hydrate wf02` makes a disposable style mirror with unchanged source bytes; the project lives at `{REL}` within that runtime.

## Legacy naming boundary

The live Drive folder `1LTkHpkEUFSui8Lqyy8I0j5-1AceSziWX` was verified on 15 October 2026 as **WF-02 · Zack d 3d animation**. The older studio snapshot used WF-02 for **Powerful Personality / TABAHI ACTIVATE**. That historical snapshot remains untouched; it is not retroactively renamed or merged into this implementation.
''',encoding='utf-8')
    (BASE/'knowledge/INDEX.md').write_text(f'''# WF-02 durable knowledge

- [Film source and rebuild guide](../{REL}/README.md)
- [Reference study, exact generated script, medical scope](../{REL}/docs/SCRIPT_AND_PRODUCTION.md)
- [Source IDs and hashes](../{REL}/data/SOURCES.json)
- [Actual master QA](../{REL}/data/QUALITY_REPORT.json)
- [Voice/mix measurements](../{REL}/data/AUDIO_REPORT.json)
- [GLB validation](../{REL}/data/GLTF_VALIDATION.json)
- [Absolute-time geometry regression](../{REL}/data/DETERMINISM_REPORT.json)
- [Initial full-frame probe, retained honestly](../{REL}/data/DETERMINISM_INITIAL_FULLFRAME.json)
- [Final delivery receipt](../{REL}/data/DELIVERY_RECEIPT.json)

## Lessons retained

- A current Drive folder can contain newer production assets absent from the checkout. Inspect it before rebuilding from zero.
- This task recovered an animated GLB but no final MP4 in that project folder. Reuse was explicitly credited, not claimed as new modelling.
- Minimal Linux lacked NSS/NSPR libraries for Chromium. Extracting the pinned package's bundled libraries fixed the offline renderer without storing credentials or system installations.
- File-scheme `fetch` is not a reliable GLTF-loader transport. The renderer intercepts a virtual browser origin and serves only allowlisted local source/vendor files.
- Imported position morphs lacked normal morphs. Generate normal deltas for a correctly lit swelling dome.
- Never multiply an animated object's scale each absolute-time frame; cached constant tracks may not restore it. Assign scale absolutely and test out-of-order/repeated timestamps.
- Batch repeated cells with hardware instancing but preserve their independent animated transforms. The film is still actual geometry animation.
- Keep the clinical explanation conditional: spontaneous expulsion is not guaranteed, and infection is not treatment. Distinguish the shallow example from the deep-fragment example.
- Technical tests do not certify artistic perfection, every pronunciation, or clinical validity. Retain those limits in the delivery record.
- Repository tests must clean only their own compatibility runtimes, not `clean all` while unrelated renders are running. Dependency virtual environments must remain outside the integrity manifest.
''',encoding='utf-8')
    regpath=ROOT/'studio/registry.json';reg=load(regpath)
    reg['workflows']=[w for w in reg['workflows'] if w['code']!='WF-02']
    reg['workflows'].append({'code':'WF-02','style_id':STYLE,'slug':'wf02','name':'Monarch 3D Explainers · WF-02','path':basepath,'trigger':'WF2 <topic or reference>','state':'DELIVERED_FOR_REVIEW','reconciliation':'live_2026-10-15_3d_folder_separate_from_preserved_legacy_snapshot','reproducibility':'R1_source_and_fixed_voice_assets','current_delivery':delivery,'authorities':{'drive_folder_id':'1LTkHpkEUFSui8Lqyy8I0j5-1AceSziWX','release_folder_id':receipt['folder']['id']}})
    reg['workflows'].sort(key=lambda w:w['code']);write(regpath,reg)
    stylepath=ROOT/'styles/registry.json';lib=load(stylepath)
    lib['styles']=[s for s in lib['styles'] if s['style_id']!=STYLE]
    lib['styles'].append({'style_id':STYLE,'name':'Monarch 3D Explainers · WF-02','workflow_code':'WF-02','trigger':'WF2 <topic or reference>','path':basepath,'contract':basepath+'/workflow.json','status':'DELIVERED_FOR_REVIEW','knowledge_index':basepath+'/knowledge/INDEX.md','latest_release':'KAANTA · Urdu-English v2','latest_release_path':basepath+'/'+REL})
    lib['styles'].sort(key=lambda s:s['workflow_code']);write(stylepath,lib)
    readme=ROOT/'README.md';txt=readme.read_text();line='| **Monarch 3D Explainers · WF-02** | `WF2 <topic or reference>` | KAANTA v2 delivered for review; native portrait 3D | [`styles/monarch-zackd-3d`](styles/monarch-zackd-3d/) |\n'
    if line not in txt:txt=txt.replace('| **Monarch Noir Film**',line+'| **Monarch Noir Film**')
    readme.write_text(txt)
    idx=ROOT/'styles/README.md';txt=idx.read_text();line='| `monarch-zackd-3d` | Monarch 3D Explainers · WF-02 | `WF2 <topic or reference>` | [`monarch-zackd-3d/`](monarch-zackd-3d/) |\n'
    if line not in txt:txt=txt.replace('| `monarch-noir-film`',line+'| `monarch-noir-film`')
    idx.write_text(txt)
    reconciliation=ROOT/'docs/RECONCILIATION.md';txt=reconciliation.read_text()
    heading='## 2026-10-15 · Live WF-02 3D workflow registration'
    if heading not in txt:
        txt+='\n\n'+heading+'\n\nThe current user-named Drive folder `1LTkHpkEUFSui8Lqyy8I0j5-1AceSziWX` was read live as **WF-02 · Zack d 3d animation**. KAANTA is registered under `styles/monarch-zackd-3d`. The earlier **Powerful Personality / TABAHI ACTIVATE** legacy snapshot is preserved unchanged and is not this renderer. The recovered SPLINTER GLB is explicitly provenanced; the new film does not claim that pre-existing geometry was authored from scratch in this task. Delivery is technical completion for user review, not assumed artistic or clinician approval.\n'
        reconciliation.write_text(txt)
    print('WF-02 registration prepared. Now run continuity.py complete --destination styles/monarch-zackd-3d/projects, then refresh the integrity manifest and validate.')

if __name__=='__main__':main()
