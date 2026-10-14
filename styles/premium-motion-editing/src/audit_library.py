#!/usr/bin/env python3
"""Coverage and source-equality audit for the WF-05 permanent library."""
from pathlib import Path
import argparse,hashlib,json
S=Path(__file__).resolve().parents[1];ROOT=S.parents[1]

def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def run(write=False):
    checks=[]
    def check(name,passed,detail=''):checks.append({'check':name,'pass':bool(passed),'detail':detail})
    wf=json.loads((S/'workflow.json').read_text())
    for rel in wf['required_paths']:check('required:'+rel,(S/rel).exists())
    profile=json.loads((S/'data/approved-profile.json').read_text());typ=profile['typography']
    check('latest_caption_rejection',typ['subtitle_mode']=='off' and typ['caption_pills'] is False and typ['word_highlighting'] is False)
    copied=[]
    for ver,task,folder in [('v5','EMS-20261014-FLOW-REPAIR','flow-repair'),('v6','EMS-20261014-FLOW-V6','flow-v6')]:
        orig=ROOT/'operations/history'/task/'payload'/folder;dest=S/'projects/einstein-flow-state/versions'/ver
        for p in sorted(orig.rglob('*')):
            if not p.is_file() or any(x in {'__pycache__','media','delivery'} for x in p.relative_to(orig).parts):continue
            q=dest/p.relative_to(orig);same=q.exists() and h(p)==h(q)
            check('historical_bytes:'+ver+'/'+p.relative_to(orig).as_posix(),same)
            copied.append({'version':ver,'path':q.relative_to(S).as_posix(),'sha256':h(q) if q.exists() else None,'source':p.relative_to(ROOT).as_posix(),'exact_copy':same})
    check('historical_case_files_present',len(copied)>=60,str(len(copied)))
    for ver in ['v5','v6']:
        d=json.loads((S/f'projects/einstein-flow-state/versions/{ver}/DELIVERY.json').read_text())
        check('verified_delivery:'+ver,d['status']=='complete_verified' and d['master']['independent_get_verified'] and d['recovery']['independent_get_verified'])
    coverage=json.loads((S/'data/coverage.json').read_text()) if (S/'data/coverage.json').exists() else {'requirements':[]}
    for row in coverage['requirements']:
        for rel in row.get('paths',[]):check('coverage:'+row['id']+':'+rel,(S/rel).exists())
    entries=[]
    for p in sorted(S.rglob('*')):
        if not p.is_file() or any(x in {'__pycache__','media','delivery'} for x in p.relative_to(S).parts):continue
        if p.name in {'SOURCE_INVENTORY.json','LIBRARY_AUDIT.json'}:continue
        entries.append({'path':p.relative_to(S).as_posix(),'bytes':p.stat().st_size,'sha256':h(p)})
    report={'schema_version':1,'checks':checks,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'files':len(entries),'bytes':sum(x['bytes'] for x in entries),'historical_exact_copies':len(copied),'scope':'Available evidence and library paths only; not a claim to recover unavailable pre-init history or all historical scratch pixels.'}
    if write:
        (S/'records/SOURCE_INVENTORY.json').write_text(json.dumps({'schema_version':1,'files':entries,'historical_copies':copied,'self_exclusions':['SOURCE_INVENTORY.json','LIBRARY_AUDIT.json']},indent=2)+'\n')
        # The inventory itself is a required path and is now present.
        for c in report['checks']:
            if c['check'].endswith(':records/SOURCE_INVENTORY.json'):c['pass']=(S/'records/SOURCE_INVENTORY.json').is_file()
        report['passed']=sum(x['pass'] for x in report['checks']);report['failed']=sum(not x['pass'] for x in report['checks'])
        (S/'records/LIBRARY_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');a=ap.parse_args();r=run(a.write)
    print(json.dumps({k:v for k,v in r.items() if k!='checks'},indent=2))
    for c in r['checks']:
        if not c['pass']:print('FAIL',c['check'],c['detail'])
    raise SystemExit(1 if r['failed'] else 0)
