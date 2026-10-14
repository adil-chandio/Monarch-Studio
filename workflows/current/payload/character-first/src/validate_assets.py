"""Verify saved art without regenerating it; report exact Drive recovery IDs.

No network calls, credentials, motion generation or visual-approval inference.
"""
import argparse
import hashlib
import json
from pathlib import Path


def verify_asset(asset,root=None):
    p=(Path(root)/asset['relative_path']) if root is not None else Path(asset['path'])
    result={'role':asset['role'],'path':str(p),'drive_id':asset.get('drive_id'),
            'status':'missing','visual_approval_claimed':False}
    if not p.is_file():
        result['next_action']='Restore this exact Drive file ID, then verify again. Do not regenerate the character.'
        return result
    sha=hashlib.sha256();md5=hashlib.md5()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            sha.update(chunk);md5.update(chunk)
    matches=(p.stat().st_size==asset['bytes'] and sha.hexdigest()==asset['sha256'] and md5.hexdigest()==asset['md5'])
    result['status']='verified' if matches else 'mismatch'
    if not matches:result['next_action']='Preserve the differing file; restore the hash-matching Drive copy separately.'
    return result


def verify_manifest(data,root=None):
    if not data.get('assets'):raise ValueError('The asset manifest is empty; no completed work was verified.')
    results=[verify_asset(a,root) for a in data['assets']]
    return {'all_files_verified':all(x['status']=='verified' for x in results),
            'results':results,'animation_exists':bool(data.get('animation_exists',False)),
            'scope':'File-integrity check only, not a visual/identity/motion quality verdict.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--ledger',type=Path,required=True)
    p.add_argument('--root',type=Path);p.add_argument('--report',type=Path)
    a=p.parse_args()
    try:report=verify_manifest(json.loads(a.ledger.read_text()),a.root)
    except ValueError as e:print(str(e));return 2
    for r in report['results']:print(r['status'].upper(),r['role'],'Drive:',r.get('drive_id'))
    if a.report:a.report.write_text(json.dumps(report,indent=2)+'\n')
    return 0 if report['all_files_verified'] else 2


if __name__=='__main__':raise SystemExit(main())
