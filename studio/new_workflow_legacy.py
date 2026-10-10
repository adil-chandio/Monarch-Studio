#!/usr/bin/env python3
"""Scaffold a new MONARCH STUDIO workflow locally and append its row to MONARCH_STUDIO_REGISTRY.md.

usage: python3 studio/new_workflow.py --wf 03 --name "Neon Kinetic Type" --key "neon type go" \
           --style "kinetic typography, 1080x1920, After-Effects-like Python renderer" [--status Planned]

Creates workflows/<slug>/{HUB.md,RESUME_STATE.md,CHECKLIST.md} from studio/WORKFLOW_TEMPLATE.md and appends a
registry row with the platform URL cells left as TODO (fill them after the Drive folder, Google Doc, Notion page
and Linear project exist — steps 2-5 of the checklist). Refuses to reuse a WF code or a name/key already present.
"""
import argparse, datetime, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REG = ROOT / "MONARCH_STUDIO_REGISTRY.md"
TPL = ROOT / "studio" / "WORKFLOW_TEMPLATE.md"

CHECKLIST = """# WF-{wf} · {name} — add-a-workflow checklist (tick in order)
- [ ] 1 Define code/name/key/style/local root  (done by new_workflow.py: {date})
- [ ] 2 Google Drive folder "WF-{wf} · {name}" inside MONARCH STUDIO (1-wAt4bgYVn7q15uq22ZnRY8z5iIQaI-l)  → id: ______
- [ ] 3 Google Doc "WF-{wf} · {name} — HUB" moved into that folder, sections filled  → id: ______
- [ ] 4 Notion Projects-DB page "WF-{wf} · {name}" + top LINKS callout + Doc 00; row in Workflows DB (8e8f1c1c-30c9-4b15-badd-cff77d64a80b) related to the page  → page id: ______
- [ ] 5 Linear project "WF-{wf} · {name}" (team MON) body §0 = state + LINKS; issue "00 · RESUME KEY {key}" + 3 attachments  → project id: ______ / issue: MON-___
- [ ] 6 Registry rows updated: Linear registry body + MON-55 · Google Doc registry · Notion Workflows DB · MONARCH_STUDIO_REGISTRY.md (URL cells filled)
- [ ] 7 workflows/{slug}/RESUME_STATE.md uploaded to the Drive folder (repeat at the end of every working turn)
- [ ] 8 Round-trip test from all four platforms passed; ids/URLs reported in the reply
"""

def slugify(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wf", required=True, help="two-digit code, e.g. 03")
    ap.add_argument("--name", required=True)
    ap.add_argument("--key", required=True, help="unique resume key / chat trigger")
    ap.add_argument("--style", required=True, help="style / engine one-liner")
    ap.add_argument("--status", default="Planned", choices=["Active", "Parked", "Legacy", "Planned"])
    a = ap.parse_args()
    wf = a.wf.zfill(2)
    slug = f"wf{wf}_{slugify(a.name)}"
    reg = REG.read_text(encoding="utf-8")
    if re.search(rf"^\| WF-{wf} \|", reg, re.M):
        sys.exit(f"WF-{wf} already exists in {REG.name}; WF codes are never reused.")
    for needle, what in ((f"| {a.name} |", "name"), (f"`{a.key}`", "resume key")):
        if needle in reg:
            sys.exit(f"{what} {needle!r} already present in the registry; it must be unique.")
    d = ROOT / "workflows" / slug
    if d.exists():
        sys.exit(f"{d} already exists.")
    d.mkdir(parents=True)
    date = datetime.date.today().isoformat()
    sub = {"WF": wf, "NAME": a.name, "KEY": a.key, "STYLE": a.style, "STATUS": a.status, "DATE": date, "SLUG": slug,
           "NOTION_URL": "TODO", "LINEAR_PROJECT_ID": "TODO", "LINEAR_ISSUE_URL": "TODO", "DRIVE_URL": "TODO", "GDOC_URL": "TODO"}
    hub = TPL.read_text(encoding="utf-8")
    for k, v in sub.items():
        hub = hub.replace("{{" + k + "}}", v)
    (d / "HUB.md").write_text(hub, encoding="utf-8")
    (d / "RESUME_STATE.md").write_text(
        f"# RESUME STATE — WF-{wf} · {a.name} (key \"{a.key}\")\n\n## {date} — scaffolded\nNothing built yet. "
        f"Newest block goes on top. Upload this file to the workflow's Drive folder at the end of every working turn.\n",
        encoding="utf-8")
    (d / "CHECKLIST.md").write_text(CHECKLIST.format(wf=wf, name=a.name, key=a.key, slug=slug, date=date), encoding="utf-8")
    row = (f"| WF-{wf} | {a.name} | `{a.key}` | {a.status.upper()} ({date}) | {a.style} | TODO (Notion page URL + id; row id) | "
           f"TODO (Linear project id → resume issue URL) | TODO (Drive folder id/URL) | TODO (Google Doc HUB id/URL) | "
           f"workflows/{slug}/ | (none yet) |")
    marker = "\nNext free code: **WF-"
    i = reg.find(marker)
    if i < 0:
        sys.exit("registry marker 'Next free code' not found; append the row by hand.")
    nxt = f"\nNext free code: **WF-{int(wf) + 1:02d}**."
    end = reg.find("\n", i + 1)
    reg = reg[:i].rstrip("\n") + "\n" + row + "\n" + nxt + reg[end:]
    REG.write_text(reg, encoding="utf-8")
    print(f"created {d.relative_to(ROOT)}/ (HUB.md, RESUME_STATE.md, CHECKLIST.md) and appended the WF-{wf} row to {REG.name}.")
    print("next: Drive folder → Google Doc HUB → Notion page + Workflows row → Linear project + resume issue → fill the TODO cells → round-trip test.")

if __name__ == "__main__":
    main()
