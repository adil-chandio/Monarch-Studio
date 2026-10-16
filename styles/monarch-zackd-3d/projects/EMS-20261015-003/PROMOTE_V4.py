#!/usr/bin/env python3
"""Promote only a hash-verified v4 delivery; never overwrite old project source."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];TASK='EMS-20261015-003';STYLE='monarch-zackd-3d'
BASE=ROOT/'styles'/STYLE;REL=f'projects/{TASK}/splinter-v4';P=ROOT/'workflows/current/payload/splinter-v4'
def read(p):return json.loads(p.read_text())
def save(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def main():
 assert read(ROOT/'workflows/current/ACTIVE_TASK.json')['task_id']==TASK
 r=read(P/'data/DELIVERY_RECEIPT.json');q=read(P/'data/QUALITY_REPORT.json');assert r['status']=='uploaded_and_hash_verified' and q['passed']
 master,source=r['master'],r['source_bundle'];assert master['id'] and source['id']
 wf=read(BASE/'workflow.json');old=wf['current_delivery'];history=wf.get('deliveries',[])
 if not any(d['drive_id']==old['drive_id'] for d in history):history.append(old)
 for d in history:
  if d['drive_id']==old['drive_id']:d['user_feedback']='Core video liked, but unnecessary additions were rejected as cluttered/cheap. User requested a restrained premium/cinematic/tactile redesign. Source/master preserved.'
 current={'title':'KAANTA · Cinema Cut v4','task_id':TASK,'project_path':REL,'drive_id':master['id'],'source_drive_id':source['id'],'md5':master['md5'],'sha256':master['sha256'],'width':1080,'height':1920,'fps':30,'duration_seconds':30.5,'rendered_frames':915,'gates':f"{q['checks_passed']}/{q['checks_total']}",'motion_checks':'9/9','user_visual_acceptance':'pending_review','previous_master_preserved':old['drive_id'],'publishing_credit_required':'FluidR3 sample attribution; see assets/music/ATTRIBUTION.md'}
 history.append(current);wf.update(current_delivery=current,deliveries=history,state='DELIVERED_FOR_REVIEW');wf['runtime']['working_directory']=REL;wf['authorities']['release_folder_id']=r['folder']['id']
 wf['required_paths']=['README.md','style.json','knowledge/INDEX.md',f'{REL}/README.md',f'{REL}/src/film.js',f'{REL}/src/motion.mjs',f'{REL}/src/render.cjs',f'{REL}/src/assemble.py',f'{REL}/src/sound_design.py',f'{REL}/src/gate.py',f'{REL}/assets/models/cutaway.glb',f'{REL}/assets/music/ATTRIBUTION.md',f'{REL}/data/design.json',f'{REL}/data/motion.json',f'{REL}/data/QUALITY_REPORT.json',f'{REL}/data/DELIVERY_RECEIPT.json'];save(BASE/'workflow.json',wf)
 style=read(BASE/'style.json');style.update(current_release=current['title'],current_release_path=REL,current_release_task=TASK,user_visual_acceptance='pending_review',primary_renderers=[f'{REL}/src/film.js',f'{REL}/src/render.cjs'],primary_gates=[f'{REL}/src/gate.py',f'{REL}/src/check_motion.mjs']);style['release_history']=[{'task_id':x['task_id'],'project_path':x['project_path'],'master_id':x['drive_id'],'title':x['title']} for x in history];save(BASE/'style.json',style)
 reg=read(ROOT/'studio/registry.json')
 for row in reg['workflows']:
  if row['code']=='WF-02':row.update(current_delivery=current,state='DELIVERED_FOR_REVIEW');row['authorities']['release_folder_id']=r['folder']['id']
 save(ROOT/'studio/registry.json',reg)
 reg=read(ROOT/'styles/registry.json')
 for row in reg['styles']:
  if row['style_id']==STYLE:row.update(latest_release=current['title'],latest_release_path=f'styles/{STYLE}/{REL}',status='DELIVERED_FOR_REVIEW')
 save(ROOT/'styles/registry.json',reg)
 (BASE/'README.md').write_text(f'''# Monarch 3D Explainers · WF-02

User-facing workflow: **Zack d 3d animation**. Reference-informed original-finished animated3D explainers; no creator/voice impersonation or exact-copy/clinical-simulation claim.

## Current release — restraint over accumulation

[**KAANTA · Cinema Cut v4**]({REL}/README.md) — 1080×1920,30fps,30.5s. The user's correction was to remove unnecessary cheap-feeling additions, not keep stacking effects. No HUD/chapter/cards/counters/page-turn; plain captions; two brief real extruded-type beats; refined scene/shading;8 tactile cues and a new original arranged piano/cello/string score. Earlier narration retained. Technical delivery does not assume user artistic approval.

- [Watch v4]({master['url']})
- [Delivery folder]({r['folder']['url']})
- [Source kit]({source['url']})
- [Actual-master QA]({REL}/data/QUALITY_REPORT.json)
- [Verified receipt]({REL}/data/DELIVERY_RECEIPT.json)
- [Music publishing credit]({REL}/assets/music/ATTRIBUTION.md) — retain attribution when posting; credits belong in the description, not over the clean image.

## Earlier versions preserved

- [v2 source](projects/EMS-20261014-001/splinter-v2/README.md) · [master](https://drive.google.com/file/d/10YyHXoz1avbHTrSzOW7xWZwiZUvTEMOT/view)
- [v3 source](projects/EMS-20261015-002/splinter-v3/README.md) · [master](https://drive.google.com/file/d/1Wl8S1M6jT3SNU6vEHJt9Kw3sePz0TH-i/view)

## Operating contract

Resume continuity first. Inspect the actual reference and live Drive folder. Keep provenance, clear Urdu-English claims, and actual geometry animation. Preserve user-liked material while acting on specific corrections. More overlays/cues are not automatically better. Use fixed included voice clips for exact rebuilds; audition a current-session voice only for new speech, not by reusing an archived registration ID.

Render/decode the actual MP4, inspect encoded samples, measure audio and hash-verify uploads. Do not turn technical checks into claims of perfect art, guaranteed ASMR/retention or clinical approval. Follow source/sample licenses and pass publishing credits to the user.

The current project is relative-path portable; `python3 tools/studio.py hydrate wf02` creates a disposable byte-preserving mirror. Native software rendering is expensive; do not duplicate an active renderer. Large masters stay on Drive.

Live parent: `1LTkHpkEUFSui8Lqyy8I0j5-1AceSziWX`. The historical **Powerful Personality / TABAHI ACTIVATE** WF-02 snapshot remains separate and unchanged.
''')
 f=BASE/'knowledge/INDEX.md';s=f.read_text();s+=f'''

## KAANTA v4 — user's explicit restraint correction

[Source/rebuild](../{REL}/README.md) · [design controls](../{REL}/data/design.json) · [motion controls](../{REL}/data/motion.json) · [sound/score](../{REL}/data/SOUND_DESIGN_REPORT.json) · [type/full-frame proof](../{REL}/data/DETERMINISM_REPORT.json) · [actual-master QA](../{REL}/data/QUALITY_REPORT.json) · [publishing credit](../{REL}/assets/music/ATTRIBUTION.md)

The user liked the core but called gratuitous additions cheap/cringe. Respond with subtraction, not a higher effect count: remove interface framing, pills/panels, alerts and page-turns; let anatomy and voice lead. Use real3D typography sparingly (two story beats, not constant competing layers). Simplify camera direction changes and oscillatory object motion. Cleaner selective cut-face shading/polygon offsets avoid fake floating shadows/acne; revised membrane/adipose surfaces preserve depth without toy-like clutter.

V4's8 soft procedural textures are distinct from its original arranged music. The score uses selected, credited FluidR3 CC-BY3.0 instrument-note recordings, not a reference song. Preserve the publishing credit in description/source and tell the user. Musical buildup and negative space can be measured; artistic taste/retention/ASMR cannot be certified by those measurements.

Ephemeral runtime files were missing on restoration. Recover dependencies and needed reference media from recorded sources without restarting completed versions. Keep previous project/master hashes unchanged.
''';f.write_text(s)
 f=ROOT/'README.md';s=f.read_text().replace('KAANTA v3 Motion Edition delivered; v2 preserved','KAANTA v4 Cinema Cut delivered; v2/v3 preserved');f.write_text(s)
 print('v4 registered. Complete continuity promotion, refresh manifest, validate/test. Old source/master unchanged.')
if __name__=='__main__':main()
