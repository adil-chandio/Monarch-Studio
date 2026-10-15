"""Restore a complete saved edit from hash-verified encoded picture chunks.

No new character/image rendering; copies the locked canonical soundtrack.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import imageio_ffmpeg


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise FileExistsError('Refusing to overwrite existing output.')
    report=json.loads((a.root/'records/PICTURE_REPORT.json').read_text())
    rows=report['shots']
    if [int(s['shot']) for s in rows]!=list(range(37)):raise ValueError('Incomplete/reordered chunk set.')
    if sum(int(s['frames']) for s in rows)!=1332:raise ValueError('Not the full main-reference edit.')
    lines=[]
    for row in rows:
        part=a.root/'picture/chunks'/f"shot_{int(row['shot']):02d}.mp4"
        if sha(part)!=row['sha256']:raise ValueError('Picture chunk hash mismatch: '+str(part))
        lines.append("file '"+str(part.resolve()).replace("'","'\\''")+"'\n")
    concat=a.root/'RECOVERY_CONCAT.txt';concat.write_text(''.join(lines))
    picture=a.root/'RECOVERY_PICTURE_ONLY.mp4'
    if picture.exists():raise FileExistsError('Existing recovery picture; inspect before retrying.')
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-f','concat','-safe','0','-i',str(concat),
                    '-an','-c:v','copy','-movflags','+faststart',str(picture)],check=True)
    subprocess.run([sys.executable,str(a.root/'src/conform_reference_audio.py'),'--picture',str(picture),
                    '--audio-source',str(a.root/'components/ORIGINAL_REFERENCE_AUDIO.m4a'),
                    '--audit',str(a.root/'records/MAIN_REFERENCE_AUDIT.json'),'--output',str(a.output)],check=True)
    print('REASSEMBLED_COMPLETE_EDIT_WITHOUT_NEW_RENDER',a.output)


if __name__=='__main__':main()
