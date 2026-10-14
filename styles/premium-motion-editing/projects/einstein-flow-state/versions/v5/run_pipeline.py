"""One resumable job, no manual 'continue' required between local stages.

A failed stage stops the chain and records the exact resume command.
Completed stages use input fingerprints and existing outputs. Upload is an
interactive connector operation and is intentionally NOT reported as done
by this local process. DELIVERY_GATE.json stays closed until its real Drive
ID and checksum verification are recorded by the active agent.
"""
import sys,json,subprocess,hashlib,os,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MEDIA=Path(os.environ.get('FLOW_MEDIA',str(ROOT/'media'))).resolve();MEDIA.mkdir(parents=True,exist_ok=True)
STATE=ROOT/'PIPELINE_STATE.json'
state=json.loads(STATE.read_text()) if STATE.exists() else {'stages':{},'status':'running'}
STAGES=[
 ('cleanup','prepare_visuals.py',['clean.py','icon-template.png'],MEDIA/'clean-shots'/'13-art.mp4'),
 ('timing_audio','prepare_audio.py',['clean.py','prepare_audio.py'],MEDIA/'mix.wav'),
 ('render','render.py',['clean.py','prepare_audio.py','render.py'],ROOT/'delivery'/'Flow_State_UrduEnglish_V5.mp4'),
 ('verification','verify.py',['clean.py','prepare_audio.py','render.py','verify.py'],ROOT/'QA.json')
]

def save():STATE.write_text(json.dumps(state,indent=2)+'\n')
for name,script,deps,out in STAGES:
    digest=hashlib.sha256(b''.join((ROOT/d).read_bytes() for d in deps)).hexdigest()
    old=state['stages'].get(name,{})
    artifacts_exist=out.exists()
    if name=='cleanup':
        artifacts_exist=artifacts_exist and len(list((MEDIA/'clean-shots').glob('*.mp4')))==14 and len(list((MEDIA/'clean-shots').glob('*.json')))==14
    if old.get('status')=='done' and old.get('input_hash')==digest and artifacts_exist:
        print('RESUME_SKIP '+name,flush=True);continue
    state['status']='running';state['current_stage']=name
    state['exact_resume_command']=f'{sys.executable} {ROOT / "run_pipeline.py"}'
    state['stages'][name]={'status':'running','input_hash':digest,'started_at':time.time()};save()
    print('STAGE_START '+name,flush=True)
    result=subprocess.run([sys.executable,'-u',str(ROOT/script)],env={**os.environ,'OPENBLAS_NUM_THREADS':'1'})
    state['stages'][name].update({'status':'done' if result.returncode==0 else 'failed','exit_code':result.returncode,'ended_at':time.time()})
    if result.returncode:
        state['status']='blocked';save();print('PIPELINE_BLOCKED '+name,flush=True);sys.exit(result.returncode)
    save();print('STAGE_DONE '+name,flush=True)
state['status']='awaiting_visual_review_and_drive_upload';state['current_stage']='delivery';save()
(ROOT/'DELIVERY_GATE.json').write_text(json.dumps({'complete':False,'local_render':True,'technical_qa':True,
 'visual_review':False,'drive_master':None,'drive_checksum_verified':False,'recovery_bundle':None,
 'next_action':'Review actual encoded frames, present master, upload master and recovery bundle, verify Drive checksum; only then mark delivery complete.'},indent=2)+'\n')
print('LOCAL_PIPELINE_FINISHED__DELIVERY_NOT_YET_COMPLETE',flush=True)
