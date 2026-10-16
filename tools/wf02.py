#!/usr/bin/env python3
"""WF-02 durable onboarding, preservation audit and portable recovery packaging.
No render, speech synthesis, cloud upload or Git operation is implicit.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
STYLE_REL = Path('styles/monarch-zackd-3d')
SKIP = {'.git', '.runtime', '.venv', 'venv', '__pycache__', 'node_modules', 'build', 'dist', 'coverage'}

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def contained(base, rel):
    p = (base / rel).resolve()
    if not p.is_relative_to(base.resolve()):
        raise ValueError(f'Path escapes archive root: {rel}')
    return p

def files(base):
    return sorted(p for p in base.rglob('*') if p.is_file() and not set(p.relative_to(base).parts) & SKIP and p.suffix not in {'.pyc', '.pyo'})

def verify_records(base, records):
    errors = []
    for rel, rec in records.items():
        p = contained(base, rel)
        if not p.is_file():
            errors.append(f'Missing preserved file: {rel}')
        elif p.stat().st_size != rec['size'] or sha(p) != rec['sha256']:
            errors.append(f'Preserved content changed: {rel}')
    return errors

def audit():
    s = ROOT / STYLE_REL
    style, workflow = load(s/'style.json'), load(s/'workflow.json')
    errors, checks = [], []
    for rel in workflow['required_paths']:
        if not contained(s, rel).is_file():
            errors.append(f'Missing required path: {rel}')
    checks.append('Required source, startup and knowledge paths')
    dna, quality = load(s/'STYLE_DNA.json'), load(s/'QUALITY_CONTRACT.json')
    if not (style['current_release_path'] == dna['baseline_release_path'] == quality['baseline_release_path'] == workflow['current_delivery']['project_path']):
        errors.append('Current release / DNA / quality / workflow disagree')
    shared = load(ROOT/'studio/registry.json')
    entry = next(w for w in shared['workflows'] if w['code'] == 'WF-02')
    if entry['current_delivery']['project_path'] != style['current_release_path']:
        errors.append('Shared registry current release drift')
    checks.append('Style/DNA/quality/workflow/shared registry alignment')
    inventory = load(s/'knowledge/history/PROJECT_SOURCE_INVENTORY.json')['files']
    errors += verify_records(s, inventory)
    current = {str(p.relative_to(s)) for p in files(s/'projects')}
    if current != set(inventory):
        errors.append('Project inventory scope changed; deliberately append new releases, never silently omit files')
    checks.append(f'Immutable project preservation ({len(inventory)} files)')
    coverage = load(s/'knowledge/history/COVERAGE.json')
    if coverage['full_original_chat_available'] is not False:
        errors.append('History must not falsely claim complete original chat')
    n = 0
    for task in coverage['tasks']:
        for rec in task['records']:
            errors += verify_records(s, {rec['path']: rec})
            original = contained(ROOT, rec['source_path'])
            if original.is_file() and sha(original) != rec['sha256']:
                errors.append(f'Raw history copy differs from original: {rec["source_path"]}')
            n += 1
        journal = s/'knowledge/history/raw'/task['task_id']/'JOURNAL.jsonl'
        previous = None
        for seq, line in enumerate(journal.read_text(encoding='utf-8').splitlines(), 1):
            event = json.loads(line)
            body = dict(event); claimed = body.pop('event_sha256')
            canonical = json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
            if event['seq'] != seq or event['prev_event_sha256'] != previous or hashlib.sha256(canonical).hexdigest() != claimed:
                errors.append(f'Archived journal chain invalid: {task["task_id"]} event {seq}')
            previous = claimed
    checks.append(f'Lossless available raw history, journal chains and coverage limits ({n} files)')
    catalog = load(s/'knowledge/history/RELEASE_CATALOG.json')
    if catalog['release_count'] != len(style['release_history']):
        errors.append('Release catalog/history count drift')
    for release in catalog['releases']:
        q = load(s/release['project_path']/'data/QUALITY_REPORT.json')
        if not q['passed'] or q['sha256'] != release['master_sha256']:
            errors.append(f'Release QA/catalog drift: {release["task_id"]}')
    checks.append(f'Evidence-linked delivered releases ({catalog["release_count"]})')
    if 'gratuitous HUD' not in dna['reject'] or 'mandatory' not in quality:
        errors.append('Binding no-clutter / quality contract absent')
    checks.append('Binding restraint and quality guardrails')
    return {'passed': not errors, 'checks': checks, 'errors': errors, 'project_files_verified': len(inventory), 'raw_history_files_verified': n, 'release_count': catalog['release_count'], 'latest_release_path': style['current_release_path'], 'limits': 'Preservation/onboarding audit, not a new render, complete missing-chat recovery or artistic/clinical certification.'}

def brief(topic):
    if not topic.strip():
        raise ValueError('Supply a real topic or reference')
    s = ROOT/STYLE_REL
    wf, quality = load(s/'workflow.json'), load(s/'QUALITY_CONTRACT.json')
    return {'workflow': 'WF-02', 'topic_or_reference': topic, 'status': 'planning_only_not_a_generated_video', 'first_action': 'python3 tools/continuity.py resume; inspect and query any recorded live process before starting', 'startup_entry': str(STYLE_REL/'START_HERE.md'), 'reading_order': [str(STYLE_REL/p) for p in quality['startup_reading_order']], 'baseline_project': str(STYLE_REL/wf['current_delivery']['project_path']), 'template': str(STYLE_REL/'templates/NEW_VIDEO_BRIEF.md'), 'plan_required': ['topic research, mechanism and factual/safety caveats', 'scope / original concept and causal storyboard', 'approved script and appropriate current-session voice selection for new speech', 'inherited vs new geometry, contact staging and shot plan', 'absolute-time camera/actor/material/light authoring', 'voice-first credited sound and phrase captions', 'current tests/A-B proofs and full-motion review', 'native render and actual encoded gates/sample review', 'verified separate delivery and permanent lesson append'], 'quality_contract': str(STYLE_REL/'QUALITY_CONTRACT.json'), 'do_not': ['blindly relabel the splinter film as a new topic', 'copy rejected V3 clutter', 'claim guaranteed perfection, clinical accuracy or retention', 'restart a live or completed render from missing caches', 'treat an old voice ID as cross-session portable synthesis identity'], 'format_defaults': quality['format_defaults'], 'case_specific_not_universal': quality['not_universal']}

def pack(out):
    result = audit()
    if not result['passed']:
        raise ValueError('Audit failed: '+ '; '.join(result['errors']))
    out = out.resolve()
    if not out.is_relative_to(ROOT) or out.is_relative_to((ROOT/STYLE_REL).resolve()):
        raise ValueError('Output must be inside workspace but outside permanent style')
    selected = {p.relative_to(ROOT): p for p in files(ROOT/STYLE_REL)}
    catalog = load(ROOT/STYLE_REL/'knowledge/history/RELEASE_CATALOG.json')
    for row in catalog['releases']:
        for prefix in ['operations/history', 'operations/continuity/checkpoints', 'operations/continuity/outbox', 'operations/continuity/receipts']:
            base = ROOT/prefix/row['task_id']
            if base.exists():
                selected.update({p.relative_to(ROOT): p for p in files(base)})
    # Dated active-task metadata is retained as a non-replaying snapshot, not
    # restored into workflows/current as if an old process were still active.
    active_path = ROOT/'workflows/current/ACTIVE_TASK.json'
    if active_path.exists():
        active = load(active_path)
        if active.get('style_id') == 'monarch-zackd-3d':
            for name in ['ACTIVE_TASK.json', 'RESUME.md', 'JOURNAL.jsonl', 'CHAT_TRANSCRIPT.jsonl', 'SYNC.json']:
                source = ROOT/'workflows/current'/name
                if source.is_file():
                    selected[Path('preservation_snapshot')/active['task_id']/name] = source
    for prefix in ['tools', 'tests', 'studio']:
        selected.update({p.relative_to(ROOT): p for p in files(ROOT/prefix)})
    for rel in ['AGENTS.md', 'README.md', '.gitignore', 'styles/registry.json', 'styles/README.md']:
        selected[Path(rel)] = ROOT/rel
    restore = b'''# WF-02 recovery pack\n\nRepo-relative paths are preserved. This is a scoped WF-02 recovery snapshot, NOT the entire unrelated multi-style repository or Git history. Prefer the verified GitHub branch for a full checkout. Read styles/monarch-zackd-3d/START_HERE.md; run python3 tools/continuity.py resume and python3 tools/wf02.py audit. No active live-render state is replayed from the old preservation task. Other style binaries/main merge are not included or claimed; full studio validation requires the full repository. Restore pinned disposable dependencies only when rebuilding. Historical masters stay at catalog Drive links. Complete missing chat/old synthesis voice identities cannot be recreated.\n'''
    entries = {}
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel, p in sorted(selected.items()):
            if p.name.startswith('.env') or p.suffix in {'.pem', '.key', '.p12', '.pfx'}:
                raise ValueError(f'Sensitive file rejected: {rel}')
            data = p.read_bytes();z.writestr(str(rel), data)
            entries[str(rel)] = {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        z.writestr('WF02_RESTORE.md', restore)
        entries['WF02_RESTORE.md'] = {'size': len(restore), 'sha256': hashlib.sha256(restore).hexdigest()}
        manifest = {'snapshot_policy': 'Available permanent WF02 source/history/shared tooling; not complete UI chat or full unrelated studio archive. Manifest excludes itself; cloud/Git sync receipt supplied separately.', 'files': entries}
        z.writestr('WF02_PACK_MANIFEST.json', json.dumps(manifest, indent=2, ensure_ascii=False)+'\n')
    with zipfile.ZipFile(out) as z:
        if z.testzip() is not None:
            raise ValueError('ZIP CRC verification failed')
        for rel, rec in entries.items():
            if hashlib.sha256(z.read(rel)).hexdigest() != rec['sha256']:
                raise ValueError(f'ZIP content mismatch: {rel}')
    data = out.read_bytes()
    return {'file': str(out.relative_to(ROOT)), 'files': len(entries)+1, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'md5': hashlib.md5(data).hexdigest(), 'verified': 'All ZIP members CRC/hash checked; no cloud/Git sync implied'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('audit')
    b = sub.add_parser('brief');b.add_argument('topic');b.add_argument('--out', type=Path)
    z = sub.add_parser('pack');z.add_argument('--out', type=Path, default=ROOT/'.runtime/WF02_STYLE_MEMORY_20261016.zip')
    args = p.parse_args()
    try:
        if args.cmd == 'audit':
            result = audit()
        elif args.cmd == 'brief':
            result = brief(args.topic)
            if args.out:
                dest = args.out.resolve();active = load(ROOT/'workflows/current/ACTIVE_TASK.json')
                if not dest.is_relative_to((ROOT/'workflows/current/payload').resolve()) or active.get('style_id') != 'monarch-zackd-3d' or active.get('status') in {'idle', 'completed'}:
                    raise ValueError('Writable briefs require an active WF02 task and a path inside workflows/current/payload')
                dest.parent.mkdir(parents=True, exist_ok=True);dest.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
        else:
            result = pack(args.out)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get('passed', True) else 1
    except (ValueError, OSError, KeyError) as exc:
        print(json.dumps({'passed': False, 'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
