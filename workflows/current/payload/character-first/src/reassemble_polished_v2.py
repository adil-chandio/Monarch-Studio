"""Losslessly reassemble the saved V2 picture chunks and canonical soundtrack.

Recovery only: no image generation, character rerigging or changed edit timing.
The direct, checksum-verified full movie download is preferable when available.
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
        for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise FileExistsError('Refusing to overwrite an existing movie.')
    report=json.loads((a.root/'records/POLISH_REPORT.json').read_text())
    if [int(row['shot']) for row in report['shots']]!=list(range(37)):
        raise ValueError('Incomplete or reordered picture chunk set.')
    lines=[]
    for row in report['shots']:
        n=int(row['shot'])
        if not 0<=n<37:raise ValueError('Invalid shot index.')
        part=a.root/'picture/chunks'/f'shot_{n:02d}.mp4'
        if sha(part)!=row['sha256']:raise ValueError('Wrong picture chunk: '+str(n))
        lines.append("file '"+str(part.resolve()).replace("'","'\\''")+"'\n")
    concat=a.root/'RECOVERY_CONCAT.txt';concat.write_text(''.join(lines))
    picture=a.root/'RECOVERY_PICTURE_ONLY.mp4'
    if picture.exists():raise FileExistsError('Existing recovery picture; inspect before retrying.')
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-f','concat','-safe','0','-i',str(concat),
                    '-an','-c:v','copy','-movflags','+faststart',str(picture)],check=True)
    subprocess.run([sys.executable,str(a.root/'src/conform_reference_audio.py'),'--picture',str(picture),
                    '--audio-source',str(a.root/'components/ORIGINAL_REFERENCE_AUDIO.m4a'),
                    '--audit',str(a.root/'records/MAIN_REFERENCE_AUDIT.json'),'--output',str(a.output)],check=True)
    print('RECOVERED_V2_WITHOUT_NEW_PICTURE_RENDER',a.output)


if __name__=='__main__':main()
