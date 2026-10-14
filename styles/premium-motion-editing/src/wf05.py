#!/usr/bin/env python3
"""Portable WF-05 entry point. No media generation occurs on import/inspect."""
from __future__ import annotations
import argparse,json,shutil,sys
from pathlib import Path
from policy import STYLE_ROOT,PolicyError,assert_valid,profile,validate

def new_project(path: Path,topic: str,project_id: str):
    path=path.resolve()
    if path==STYLE_ROOT or STYLE_ROOT in path.parents:
        raise PolicyError('Permanent style knowledge is not an active workspace. Use workflows/current/payload/<project>.')
    if path.exists() and any(path.iterdir()):raise PolicyError('Project directory already contains work; resume it, do not overwrite it.')
    if not topic.strip() or not project_id.strip():raise PolicyError('Topic and project ID are required.')
    path.mkdir(parents=True,exist_ok=True)
    for name in ['brief.json','project.json','timeline.json','asset-register.csv','shot-plan.csv','qa-review.json','delivery-receipt.json']:
        shutil.copy2(STYLE_ROOT/'templates'/name,path/name)
    p=json.loads((path/'project.json').read_text());p.update({'topic':topic,'project_id':project_id});(path/'project.json').write_text(json.dumps(p,indent=2)+'\n')
    b=json.loads((path/'brief.json').read_text());b['topic']=topic;(path/'brief.json').write_text(json.dumps(b,indent=2)+'\n')
    for name in ['media','delivery','records']:(path/name).mkdir()
    (path/'START_HERE.md').write_text(f'# {project_id}\n\nTopic: {topic}\n\nThis is a new brief, not an Einstein replay. Fill the argument, rights, shot/motion plan, approved script and matching narration. Do not replace missing motion with slides. Integrated type is default; V6 bottom pills are rejected.\n\nRun `python3 <WF05>/src/wf05.py validate project.json` before rendering. Keep the active task/process ledger in the repository continuity controller. A delivered receipt requires real files and verified cloud hashes.\n')
    return path

def main(argv=None):
    ap=argparse.ArgumentParser(description='WF-05 Premium Motion Editing: approved clean typography and real motion')
    sub=ap.add_subparsers(dest='cmd',required=True)
    sub.add_parser('inspect',help='Show approved policy without rendering')
    n=sub.add_parser('new',help='Scaffold a NEW active brief; never copies case footage/narration');n.add_argument('--project-dir',required=True,type=Path);n.add_argument('--topic',required=True);n.add_argument('--project-id',required=True)
    v=sub.add_parser('validate');v.add_argument('project',type=Path);v.add_argument('--plan-only',action='store_true',help='Still validates policy/script/plan; defers physical media existence only')
    r=sub.add_parser('render');r.add_argument('project',type=Path);r.add_argument('--preview',action='store_true',help='Render sampled PNGs only, not a delivered master')
    q=sub.add_parser('verify');q.add_argument('project',type=Path);q.add_argument('--video',type=Path)
    args=ap.parse_args(argv)
    try:
        if args.cmd=='inspect':print(json.dumps(profile(),indent=2,ensure_ascii=False));return 0
        if args.cmd=='new':print(new_project(args.project_dir,args.topic,args.project_id));return 0
        if args.cmd=='validate':
            _,_,issues=validate(args.project,check_media=not args.plan_only)
            for issue in issues:print('FAIL '+issue)
            if not issues:print('PASS approved policy and project inputs'+(' (media deferred)' if args.plan_only else ''))
            return 1 if issues else 0
        if args.cmd=='render':
            assert_valid(args.project)
            from render_project import render
            render(args.project,preview=args.preview);return 0
        if args.cmd=='verify':
            from verify_output import verify
            result=verify(args.project,args.video)
            print(json.dumps(result,indent=2));return 0 if result['technical_pass'] else 1
    except (PolicyError,FileNotFoundError,ValueError) as exc:
        print(f'WF-05 blocked: {exc}',file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
