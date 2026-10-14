"""Restore exact saved assets from a downloaded, hash-pinned design ZIP.

Standard library only: works in a fresh workspace before image dependencies are
installed. Never regenerates art, overwrites a different file, or contacts APIs.
Download the recorded ZIP using the authenticated Drive connector first.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import shutil
import tempfile
import zipfile

from validate_assets import verify_asset


def safe_destination(root,relative):
    rel=PurePosixPath(relative)
    if rel.is_absolute() or '..' in rel.parts or '\\' in relative:
        raise ValueError('Unsafe asset path: '+relative)
    destination=(root/Path(*rel.parts)).resolve()
    if not destination.is_relative_to(root.resolve()):
        raise ValueError('Asset path leaves destination root: '+relative)
    return destination


def recover(archive,ledger,root):
    archive=Path(archive);root=Path(root)
    assets=ledger.get('assets',[])
    packs=[a for a in assets if a['role']=='design_zip']
    if len(packs)!=1:raise ValueError('One exact design ZIP receipt is required.')
    if verify_asset({**packs[0],'path':str(archive)})['status']!='verified':
        raise ValueError('Archive bytes do not match the saved ZIP receipt. Restore the recorded Drive file.')
    plans=[]
    with zipfile.ZipFile(archive) as z:
        names=set(z.namelist())
        # Preflight every path/conflict before writing anything.
        for a in assets:
            destination=safe_destination(root,a['relative_path'])
            if destination.exists() and verify_asset({**a,'path':str(destination)})['status']!='verified':
                raise ValueError('Refusing to overwrite a different existing file: '+str(destination))
            if a['role']!='design_zip':
                if a['relative_path'] not in names:raise ValueError('Saved asset absent from ZIP: '+a['relative_path'])
                info=z.getinfo(a['relative_path'])
                if info.file_size!=a['bytes']:raise ValueError('Unexpected asset size in ZIP: '+a['relative_path'])
            plans.append((a,destination))
        restored=[];reused=[]
        for a,destination in plans:
            if destination.is_file():reused.append(a['role']);continue
            destination.parent.mkdir(parents=True,exist_ok=True)
            fd,name=tempfile.mkstemp(prefix='.restore-',suffix='.partial',dir=destination.parent)
            os.close(fd);temp=Path(name)
            try:
                source=archive.open('rb') if a['role']=='design_zip' else z.open(a['relative_path'])
                with source, temp.open('wb') as f:shutil.copyfileobj(source,f,1024*1024)
                if verify_asset({**a,'path':str(temp)})['status']!='verified':
                    raise ValueError('Restored asset hash mismatch: '+a['role'])
                os.replace(temp,destination);restored.append(a['role'])
            finally:temp.unlink(missing_ok=True)
    return {'restored':restored,'reused':reused,'regenerated':0,
            'animation_created':False,'arena_service_repair_claimed':False}


def main():
    p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--ledger',type=Path,required=True);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--report',type=Path);a=p.parse_args()
    try:result=recover(a.archive,json.loads(a.ledger.read_text()),a.root)
    except (ValueError,OSError,zipfile.BadZipFile) as e:print('RECOVERY_BLOCKED:',e);return 2
    if a.report:a.report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return 0


if __name__=='__main__':raise SystemExit(main())
