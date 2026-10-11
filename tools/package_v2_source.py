#!/usr/bin/env python3
"""Create deterministic, reviewable source ZIPs for V2 film packages.

The archive excludes generated build media and post-upload receipts so its hash
can be recorded in those receipts without a circular dependency. File ordering,
timestamps and permissions are normalized.
"""
from __future__ import annotations
import argparse,hashlib,zipfile
from pathlib import Path

EXCLUDE_NAMES={"DELIVERY_RECEIPT.md","DELIVERY_RECEIPT.json","EXTERNAL_SYNC.json","SOURCE_CONTENT_MANIFEST.sha256"}

def included(root:Path):
    for p in sorted(x for x in root.rglob('*') if x.is_file()):
        rel=p.relative_to(root)
        if 'build' in rel.parts or '__pycache__' in rel.parts or p.suffix=='.pyc':continue
        if p.name in EXCLUDE_NAMES:continue
        yield p,rel

def main():
    ap=argparse.ArgumentParser();ap.add_argument('package',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
    root=a.package.resolve();a.output.parent.mkdir(parents=True,exist_ok=True)
    rows=[]
    for p,rel in included(root):rows.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {rel.as_posix()}")
    manifest=root/'artifacts'/'SOURCE_CONTENT_MANIFEST.sha256';manifest.write_text('\n'.join(rows)+'\n')
    files=list(included(root))+[(manifest,manifest.relative_to(root))]
    with zipfile.ZipFile(a.output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p,rel in sorted(files,key=lambda x:x[1].as_posix()):
            info=zipfile.ZipInfo(rel.as_posix(),(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=(0o100644<<16)
            z.writestr(info,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    data=a.output.read_bytes();print(f"{a.output} {len(data)} bytes sha256={hashlib.sha256(data).hexdigest()} md5={hashlib.md5(data).hexdigest()}")
if __name__=='__main__':main()
