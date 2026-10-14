"""WF-05 production policy: latest user feedback wins over historical effects.

Pure standard library; importing this module never reads media or starts jobs.
"""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path
from typing import Any

STYLE_ROOT=Path(__file__).resolve().parents[1]
POLICY_ID='wf05-clean-editorial-20261015'
class PolicyError(ValueError): pass

def read_json(path: Path) -> dict[str,Any]:
    return json.loads(path.read_text(encoding='utf-8'))

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def profile() -> dict[str,Any]:
    return read_json(STYLE_ROOT/'data/approved-profile.json')

def resolve(base: Path,value: str) -> Path:
    if not value or '://' in value:raise PolicyError('Stage media locally first; a URL is not a verified local file.')
    p=Path(value).expanduser()
    return p.resolve() if p.is_absolute() else (base/p).resolve()

def subtitle_mode(project: dict[str,Any]) -> str:
    typography=project.get('typography',{})
    mode=typography.get('subtitle_mode','off')
    if mode not in {'off','plain'}:
        raise PolicyError('V6 bottom pills / word-highlight strip are rejected. Allowed modes: off, explicitly requested plain.')
    if typography.get('caption_pills') or typography.get('word_highlighting'):
        raise PolicyError('Rejected lower-caption UI cannot be enabled in the approved production profile.')
    if mode=='plain' and typography.get('plain_subtitles_requested') is not True:
        raise PolicyError('Plain subtitle overlays require an explicit brief request; integrated scene type is the default.')
    return mode

def finite(value: Any) -> bool:
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)

def validate(project_path: Path,check_media: bool=True) -> tuple[dict,dict,list[str]]:
    project_path=project_path.resolve();base=project_path.parent;p=read_json(project_path);issues=[]
    if p.get('style_id')!='premium-motion-editing':issues.append('Wrong style_id; do not mix WF-01/WF-03/WF-04 with WF-05.')
    for key in ['project_id','topic']:
        val=str(p.get(key,''))
        if not val or val.startswith('REPLACE_'):issues.append(f'{key} is not a real brief value.')
    if p.get('mode') not in {'new_production','reference_adaptation','case_replay'}:issues.append('Choose a valid production mode.')
    if p.get('policy_id')!=POLICY_ID:issues.append('Current user-approved policy must be acknowledged by exact policy_id.')
    try:subtitle_mode(p)
    except PolicyError as exc:issues.append(str(exc))
    if p.get('format',{})!={'width':1080,'height':1920,'fps':30}:issues.append('This tested adapter supports 1080x1920/30fps. Other formats require a separately tested adapter, not stretching.')
    if p.get('rights_status') not in {'provided_by_user','licensed','own'}:issues.append('Source rights/provenance review is pending.')
    if p.get('script_status')!='approved':issues.append('Script/meaning/fact-claim review must be approved before rendering.')
    if p.get('motion_review')!='approved':issues.append('Independent subject/layer motion must be reviewed; a camera-only slideshow is not approved.')
    try:
        timeline_path=resolve(base,p.get('timeline',''));t=read_json(timeline_path)
    except (OSError,ValueError) as exc:
        return p,{},issues+[f'Timeline unavailable: {exc}']
    duration=t.get('duration');fps=t.get('fps')
    if not finite(duration) or duration<=0:issues.append('Timeline duration must be positive and finite.')
    if fps!=30:issues.append('Timeline FPS must match the tested 30fps adapter.')
    shots=t.get('shots',[])
    if not shots:issues.append('No shots. A new topic needs real prepared motion clips, not an automatic Einstein replay.')
    cursor=0.
    try:media=resolve(base,p.get('media_dir','media'))
    except PolicyError as exc:issues.append(str(exc));media=base
    for i,s in enumerate(shots):
        a,b=s.get('start'),s.get('end')
        if not (finite(a) and finite(b) and b>a):issues.append(f'Shot {i}: invalid interval.');continue
        if round(a*30)!=round(cursor*30):issues.append(f'Shot {i}: timeline gap/overlap on the frame grid.')
        if round(b*30)<=round(a*30):issues.append(f'Shot {i}: interval has no output frame.')
        cursor=b
        if p.get('mode')=='new_production' and (s.get('case_origin') or 'einstein-flow-state' in str(s.get('path',''))):issues.append(f'Shot {i}: historical case media is not a new topic by default.')
        if s.get('motion_kind') not in {'actual_video','independent_layers'}:issues.append(f'Shot {i}: declare actual_video or independently animated layers; camera_only is not sufficient.')
        rect=s.get('depth_rect',[.06,.20,.94,.80])
        if len(rect)!=4 or not all(finite(x) and 0<=x<=1 for x in rect) or rect[0]>=rect[2] or rect[1]>=rect[3]:issues.append(f'Shot {i}: invalid normalized depth rectangle.')
        cam=s.get('camera',{})
        if not finite(cam.get('z_strength',.045)) or not 0<=cam.get('z_strength',.045)<=.12:issues.append(f'Shot {i}: unreviewed depth strength.')
        if not finite(cam.get('roll_degrees',.65)) or not 0<=cam.get('roll_degrees',.65)<=3:issues.append(f'Shot {i}: unreviewed roll strength.')
        if s.get('transition','depth_push') not in {'depth_push','diagonal_whip','feathered_cut'}:issues.append(f'Shot {i}: unsupported transition; choose a deliberate tested treatment.')
        if check_media:
            try:
                path=resolve(media,s.get('path',''))
                if not path.is_file():issues.append(f'Shot {i}: missing actual motion file {path.name}.')
                elif s.get('sha256') and sha256(path)!=s['sha256']:issues.append(f'Shot {i}: source hash mismatch.')
            except PolicyError as exc:issues.append(f'Shot {i}: {exc}')
    if finite(duration) and shots and abs(cursor-duration)>1/30+.00001:issues.append('Shots do not cover the full declared duration.')
    for i,title in enumerate(t.get('titles',[])):
        a,b=title.get('start'),title.get('end')
        if not (finite(a) and finite(b) and b>a and a>=0 and finite(duration) and b<=duration+.001):issues.append(f'Title {i}: invalid time interval.')
        if not str(title.get('title','')).strip():issues.append(f'Title {i}: blank headline.')
        if title.get('position','top') not in {'top','bottom','right'}:issues.append(f'Title {i}: unsupported anchor.')
        # A bottom integrated headline is intentional. It is NOT the rejected
        # permanent lower-caption pill strip.
    if not t.get('titles'):issues.append('The editorial type track is empty.')
    if check_media:
        try:
            audio=resolve(base,p.get('audio_mix',''))
            if not audio.is_file():issues.append('Missing mixed audio; do not encode a silent placeholder.')
        except PolicyError as exc:issues.append(str(exc))
    for i,v in enumerate(t.get('voice_clips',[])):
        if v.get('speed',1.0)!=1.0 and not p.get('explicit_voice_speed_request'):issues.append(f'Voice {i}: arbitrary speed-up is not approved.')
        if p.get('mode')=='new_production' and v.get('case_origin'):issues.append(f'Voice {i}: do not use Einstein narration for an unrelated new script.')
    return p,t,issues

def assert_valid(path: Path,check_media=True):
    p,t,issues=validate(path,check_media)
    if issues:raise PolicyError('\n'.join(issues))
    return p,t

def delivery_gate(qa: dict,master: dict,recovery: dict,presented: bool) -> dict:
    """Validate factual API receipts supplied by the active agent, never invent them."""
    checks={
      'technical':qa.get('technical_pass') is True,
      'visual':qa.get('visual_review_approved') is True,
      'caption_policy':qa.get('caption_policy_pass') is True,
      'master_id':bool(master.get('drive_id')),
      'master_remote_get':master.get('independent_get_verified') is True,
      'master_hash':bool(qa.get('md5')) and master.get('md5')==qa.get('md5'),
      'master_size':qa.get('size_bytes',0)>0 and master.get('size')==qa.get('size_bytes'),
      'recovery_id':bool(recovery.get('drive_id')),
      'recovery_hash':bool(recovery.get('local_md5')) and recovery.get('remote_md5')==recovery.get('local_md5'),
      'recovery_remote_get':recovery.get('independent_get_verified') is True,
      'presented':presented is True,
    }
    return {'complete':all(checks.values()),'checks':checks,'missing':[k for k,v in checks.items() if not v]}
