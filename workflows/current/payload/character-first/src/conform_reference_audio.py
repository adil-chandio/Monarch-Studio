"""Conform a COMPLETE supplied picture edit to the confirmed reference audio.

This does not generate character motion and does not create placeholder video.
Partial outros and identical reference/rejected-composite files are refused.
Passing these checks is NOT visual, identity or animation approval.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

import imageio_ffmpeg

FF=imageio_ffmpeg.get_ffmpeg_exe()
EXPECTED_FRAMES=1332
EXPECTED_FPS=30
KNOWN_DISALLOWED_PICTURES={
    '42e52d770f6b53338639d2d1a01e2e48':'the supplied reference itself',
    'bd9ac138749b658175c26873320a4a3c':'the rejected live-action composite',
}


def validate_picture_metrics(frames,fps,width,height,md5,duration=None):
    if md5 in KNOWN_DISALLOWED_PICTURES:
        raise ValueError('Not a new picture edit: '+KNOWN_DISALLOWED_PICTURES[md5])
    if frames!=EXPECTED_FRAMES:
        raise ValueError(f'Full picture required: {EXPECTED_FRAMES} frames, not {frames}. Do not pad an outro/slideshow to satisfy this check.')
    if abs(fps-EXPECTED_FPS)>.001:raise ValueError('Picture must be conformed to 30fps before audio muxing.')
    if width*16!=height*9:raise ValueError('Expected a 9:16 portrait picture edit.')
    if duration is not None and abs(duration-44.4)>1/30+.0001:
        raise ValueError('Picture duration does not match the 44.4-second main reference.')


def media_hash(path,audio=False,copy=False):
    cmd=[FF,'-v','error','-i',str(path),'-map','0:a:0' if audio else '0:v:0']
    if copy:cmd+=['-c:a' if audio else '-c:v','copy']
    cmd+=['-f','hash','-hash','sha256','-']
    return subprocess.check_output(cmd,text=True).strip().split('=',1)[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('--picture',type=Path,required=True)
    p.add_argument('--audio-source',type=Path,required=True)
    p.add_argument('--audit',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if not a.picture.is_file():raise FileNotFoundError('No complete new-character picture edit exists at the supplied path.')
    if a.output.exists():raise FileExistsError('Refusing to overwrite an existing output.')
    audit=json.loads(a.audit.read_text())
    if audit['reference_drive_id']!='1sYYhXs9fbHeHcQGOmH5IR7CvUSVr9Tmx':raise ValueError('Wrong main reference audit.')
    reader=imageio_ffmpeg.read_frames(str(a.picture));meta=next(reader);reader.close()
    n,seconds=imageio_ffmpeg.count_frames_and_secs(str(a.picture))
    md5=hashlib.md5(a.picture.read_bytes()).hexdigest()
    validate_picture_metrics(n,float(meta['fps']),*meta['size'],md5,duration=seconds)
    hashes=audit['audio_hashes']
    encoded=media_hash(a.audio_source,True,True)
    decoded=media_hash(a.audio_source,True,False)
    if encoded!=hashes['source_encoded_aac_payload_sha256'] or decoded!=hashes['source_decoded_pcm_sha256']:
        raise ValueError('Wrong/changed audio. Use the exact main-reference track, not the chair example, original-score draft or outro sting.')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    temporary=a.output.with_name(a.output.stem+'.partial.mp4')
    # Deliberately no -shortest/-t/audio filter: preserve the original AAC tail
    # (~44.536s decoded) even though the picture sequence is exactly 44.4s.
    subprocess.run([FF,'-v','error','-y','-i',str(a.picture),'-i',str(a.audio_source),
        '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','copy','-movflags','+faststart',str(temporary)],check=True)
    out_n,out_seconds=imageio_ffmpeg.count_frames_and_secs(str(temporary))
    assert out_n==EXPECTED_FRAMES,out_n
    assert media_hash(temporary,True,True)==encoded,'AAC packet payload changed'
    assert media_hash(temporary,True,False)==decoded,'Decoded audio changed'
    assert media_hash(temporary,False,True)==media_hash(a.picture,False,True),'Picture bitstream changed'
    os.replace(temporary,a.output)
    report={'status':'supplied_complete_picture_muxed_with_verified_reference_audio',
            'reference_drive_id':audit['reference_drive_id'],'picture_frames':out_n,
            'audio_encoded_payload_match':True,'audio_decoded_pcm_match':True,
            'picture_bitstream_unchanged':True,'audio_filters_or_replacement_music_used':False,
            'picture_generation_performed_by_this_tool':False,'visual_approval_claimed':False,
            'hash_limit':'Identical known wrong picture files are rejected; hashes do not detect every transcoded/altered misuse.',
            'file':str(a.output),'sha256':hashlib.sha256(a.output.read_bytes()).hexdigest()}
    a.output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
