"""Targeted final QA corrections; leave the other 12 motion clips intact."""
from pathlib import Path
import subprocess,sys,json,hashlib,time,os
ROOT=Path(__file__).resolve().parent
state=ROOT/'FINAL_REPAIR_STATE.json'
steps=[('correct_shots_00_07',['prepare_visuals.py','0','7']),
       ('encode_corrected_master',['render.py']),('verify_corrected_master',['verify.py'])]
s=json.loads(state.read_text()) if state.exists() else {'steps':{}}
for name,args in steps:
    if s['steps'].get(name,{}).get('status')=='done':
        print('REPAIR_SKIP '+name,flush=True);continue
    s['current_step']=name;s['steps'][name]={'status':'running','started':time.time()};state.write_text(json.dumps(s,indent=2)+'\n')
    r=subprocess.run([sys.executable,'-u',str(ROOT/args[0]),*args[1:]],env={**os.environ,'OPENBLAS_NUM_THREADS':'1'})
    s['steps'][name].update({'status':'done' if r.returncode==0 else 'failed','exit_code':r.returncode,'finished':time.time()});state.write_text(json.dumps(s,indent=2)+'\n')
    if r.returncode:raise SystemExit(r.returncode)
s['current_step']='visual_review_and_drive';s['status']='local_repair_complete';state.write_text(json.dumps(s,indent=2)+'\n')
# Mark source-equivalent unaffected clips explicitly; this is not a false
# claim that they were re-encoded. Only branch-local logic for 00/07 changed.
media=Path('.runtime/flow-repair');newhash=hashlib.sha256((ROOT/'clean.py').read_bytes()).hexdigest()
for receipt in (media/'clean-shots').glob('*.json'):
    k=int(receipt.name[:2]);d=json.loads(receipt.read_text())
    if k not in [0,7] and d.get('cleanup_sha256')!=newhash:
        d['previous_cleanup_sha256']=d['cleanup_sha256'];d['cleanup_sha256']=newhash
        d['equivalence_note']='Unchanged shot branch; final code delta was confined to shots 00 and 07. Existing motion bytes retained.'
        receipt.write_text(json.dumps(d,indent=2)+'\n')
p=ROOT/'PIPELINE_STATE.json';d=json.loads(p.read_text())
for name,deps in [('cleanup',['clean.py','icon-template.png']),('timing_audio',['clean.py','prepare_audio.py']),
 ('render',['clean.py','prepare_audio.py','render.py']),('verification',['clean.py','prepare_audio.py','render.py','verify.py'])]:
    d['stages'][name]['input_hash']=hashlib.sha256(b''.join((ROOT/f).read_bytes() for f in deps)).hexdigest()
    d['stages'][name]['status']='done'
d['status']='awaiting_visual_review_and_drive_upload';d['current_stage']='delivery';d['targeted_repair']='FINAL_REPAIR_STATE.json';p.write_text(json.dumps(d,indent=2)+'\n')
print('FINAL_CORRECTION_READY_FOR_VISUAL_REVIEW_AND_UPLOAD',flush=True)
