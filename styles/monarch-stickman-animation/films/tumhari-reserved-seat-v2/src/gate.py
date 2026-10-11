#!/usr/bin/env python3
"""Measured V2 delivery and immutable-parent delta gates for TUMHARI RESERVED SEAT."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parent
STYLE=PROJECT.parents[1]
REPO=STYLE.parents[1]
KIND="wf01" if "stickman" in STYLE.name else "wf03"
EXPECT_FPS=30 if KIND=="wf01" else 24
TARGET_LUFS=-13.0 if KIND=="wf01" else -16.0


def ffmpeg_exe():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def run(cmd):
    return subprocess.run(cmd,text=True,capture_output=True)


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha(path):
    h=hashlib.sha256()
    for f in sorted(x for x in path.rglob("*") if x.is_file() and "__pycache__" not in x.parts):
        h.update(f.relative_to(path).as_posix().encode()+b"\0")
        h.update(hashlib.sha256(f.read_bytes()).digest())
    return h.hexdigest()


def probe(path):
    p=run([ffmpeg_exe(),"-hide_banner","-i",str(path)])
    s=p.stderr+p.stdout
    dm=re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)",s)
    dur=int(dm.group(1))*3600+int(dm.group(2))*60+float(dm.group(3)) if dm else None
    vm=re.search(r"Video: ([^,]+).*?,\s*(\d{3,5})x(\d{3,5}).*?,\s*([\d.]+) fps",s)
    am=re.search(r"Audio: ([^,]+),\s*(\d+) Hz,\s*([^,]+)",s)
    return {"duration":dur,"video_codec":vm.group(1).strip() if vm else None,"width":int(vm.group(2)) if vm else None,"height":int(vm.group(3)) if vm else None,"fps":float(vm.group(4)) if vm else None,"audio_codec":am.group(1).strip() if am else None,"sample_rate":int(am.group(2)) if am else None,"channels":am.group(3).strip() if am else None,"raw":s}


def loudness(path):
    p=run([ffmpeg_exe(),"-hide_banner","-i",str(path),"-af","ebur128=peak=true","-f","null","-"])
    tail=(p.stderr+p.stdout).split("Summary:")[-1]
    im=re.search(r"Integrated loudness:.*?I:\s*([\-\d.]+) LUFS",tail,re.S)
    lm=re.search(r"Loudness range:.*?LRA:\s*([\-\d.]+) LU",tail,re.S)
    pm=re.search(r"True peak:.*?Peak:\s*([\-\d.]+) dBFS",tail,re.S)
    return {"integrated_lufs":float(im.group(1)) if im else None,"lra_lu":float(lm.group(1)) if lm else None,"true_peak_dbfs":float(pm.group(1)) if pm else None}


def picture_metrics(path):
    cmd=[ffmpeg_exe(),"-v","error","-i",str(path),"-vf","fps=6,scale=192:108:flags=area","-f","rawvideo","-pix_fmt","rgb24","-"]
    raw=subprocess.check_output(cmd)
    frame_bytes=192*108*3;n=len(raw)//frame_bytes
    a=np.frombuffer(raw[:n*frame_bytes],np.uint8).reshape(n,108,192,3).astype(np.float32)
    l=.2126*a[...,0]+.7152*a[...,1]+.0722*a[...,2]
    diff=np.abs(a[1:]-a[:-1]).mean(axis=(1,2,3))
    return {"samples":n,"mean_luma":float(l.mean()),"dark_share":float((l<30).mean()),"p99_luma":float(np.percentile(l,99)),"motion_min":float(diff.min()),"motion_median":float(np.median(diff)),"motion_p95":float(np.percentile(diff,95)),"near_identical_pairs":int((diff<.015).sum()),"empty_samples":int((l.mean(axis=(1,2))<1.0).sum())}


def main():
    if len(sys.argv)!=2:raise SystemExit("usage: gate.py FINAL.mp4")
    path=Path(sys.argv[1]);
    if not path.exists():raise SystemExit(f"missing: {path}")
    pr=probe(path);au=loudness(path);pic=picture_metrics(path)
    dna=json.loads((PROJECT/"DNA.json").read_text());tl=json.loads((PROJECT/"MASTER_TIMELINE.json").read_text());am=json.loads((PROJECT/"artifacts"/"AUDIO_BUILD_METRICS.json").read_text())
    delta=json.loads((PROJECT/"artifacts"/"THREEX_DELTA.json").read_text())
    aq=json.loads((PROJECT/"artifacts"/"AUDIO_QC.json").read_text())
    provenance=json.loads((PROJECT/"PROVENANCE.json").read_text())
    smoke=json.loads((PROJECT/"artifacts"/("TRANSITION_BOUNDARY_SMOKE_WF01.json" if KIND=="wf01" else "TRANSITION_BOUNDARY_SMOKE_WF03.json")).read_text())
    import csv
    with (PROJECT/"artifacts"/"VISUAL_ENHANCEMENT_LEDGER.csv").open() as f: visual_rows=list(csv.DictReader(f))
    parent=PROJECT.parent/"tumhari-reserved-seat"
    checks=[]
    def check(name,ok,measured,target):checks.append({"name":name,"pass":bool(ok),"measured":measured,"target":target})
    check("container/codecs",pr["video_codec"] and "h264" in pr["video_codec"] and pr["audio_codec"] and "aac" in pr["audio_codec"],f"{pr['video_codec']} / {pr['audio_codec']}","h264 / aac")
    check("resolution",(pr["width"],pr["height"])==(1920,1080),f"{pr['width']}x{pr['height']}","1920x1080")
    check("frame rate",pr["fps"] is not None and abs(pr["fps"]-EXPECT_FPS)<.01,pr["fps"],EXPECT_FPS)
    check("duration",pr["duration"] is not None and abs(pr["duration"]-74.0)<=.12,pr["duration"],"74.0 ± 0.12 s")
    check("audio format",pr["sample_rate"]==48000 and pr["channels"]=="stereo",f"{pr['sample_rate']} Hz {pr['channels']}","48000 Hz stereo")
    check("integrated loudness",au["integrated_lufs"] is not None and abs(au["integrated_lufs"]-TARGET_LUFS)<=1.0,au["integrated_lufs"],f"{TARGET_LUFS} ± 1 LUFS")
    check("decoded true peak",au["true_peak_dbfs"] is not None and au["true_peak_dbfs"]<=-1.0,au["true_peak_dbfs"],"≤ -1.0 dBFS")
    check("loudness range",au["lra_lu"] is not None and 2.0<=au["lra_lu"]<=14.0,au["lra_lu"],"2–14 LU")
    if KIND=="wf01":
        check("paper-world luma",145<=pic["mean_luma"]<=235,round(pic["mean_luma"],2),"145–235")
        check("controlled dark share",pic["dark_share"]<=.28,round(pic["dark_share"],3),"≤ 0.28")
    else:
        check("noir-world luma",8<=pic["mean_luma"]<=42,round(pic["mean_luma"],2),"8–42")
        check("controlled darkness",pic["dark_share"]>=.50,round(pic["dark_share"],3),"≥ 0.50")
    check("highlight headroom",pic["p99_luma"]>=90,round(pic["p99_luma"],2),"≥ 90")
    check("no perfectly still sampled pairs",pic["near_identical_pairs"]==0,pic["near_identical_pairs"],0)
    check("living-motion floor",pic["motion_min"]>.02,round(pic["motion_min"],4),"> 0.02 mean RGB delta at 6 fps")
    check("no stray empty samples",pic["empty_samples"]==0,pic["empty_samples"],0)
    check("voice not time-stretched",am.get("voice_time_stretched") is False,am.get("voice_time_stretched"),False)
    check("V2 audio event build",am.get("events",0)>=dna["targets"]["audio_events_min"],am.get("events"),f"≥ {dna['targets']['audio_events_min']} (3× V1)")
    check("moving stereo objects",am.get("spatial_moving_events",0)>=dna["targets"]["spatial_moving_events_min"],am.get("spatial_moving_events"),f"≥ {dna['targets']['spatial_moving_events_min']}")
    check("five-act score",am.get("score_sections",0)>=5,am.get("score_sections"),"≥ 5")
    check("stereo field coherence",.20<=am.get("lr_correlation",1)<=.995,am.get("lr_correlation"),"0.20–0.995")
    check("V2 audio identity",am.get("version")=="V2_MONARCH_CINEMA_TABAHI",am.get("version"),"V2_MONARCH_CINEMA_TABAHI")
    check("audio finite samples",aq.get("nan_or_inf")==0,aq.get("nan_or_inf"),0)
    check("audio exact pre-master lock",aq.get("sample_rate")==48000 and aq.get("channels")==2 and abs(aq.get("duration_s",0)-74)<1e-6,f"{aq.get('sample_rate')} Hz / {aq.get('channels')} ch / {aq.get('duration_s')} s","48000 Hz / 2 ch / 74.0 s")
    check("no 100 ms digital silence",aq.get("silent_100ms_blocks")==0,aq.get("silent_100ms_blocks"),0)
    check("shot count",dna.get("shots",0)>=32,dna.get("shots"),"≥ 32")
    gaps=[b["t1"]-b["t0"] for b in tl["beats"]]
    check("voice-led beat cadence",len(tl["beats"])==34 and max(gaps)<=4.71,f"{len(gaps)} beats; max {max(gaps):.2f}s","34; max ≤ 4.71 s")
    bg=(PROJECT/"artifacts"/"BRAIN_GATE.txt").read_text()
    check("editor-brain freshness","PASS (30/30)" in bg,bg.splitlines()[0],"PASS 30/30")
    check("V2 look sheet",(PROJECT/"artifacts"/("LOOK_SHEET_WF01_V2.jpg" if KIND=="wf01" else "LOOK_SHEET_WF03_V2.jpg")).exists(),"present","present")
    check("all transition boundaries smoke-tested",smoke.get("all_pass") is True and smoke.get("boundaries_tested")==33,f"{smoke.get('boundaries_tested')} boundaries; all_pass={smoke.get('all_pass')}","33; all_pass=True")
    check("V2 package identity",dna.get("version")=="V2" and dna.get("task_id")=="EMS-20261011-003",f"{dna.get('version')} / {dna.get('task_id')}","V2 / EMS-20261011-003")
    check("three depth planes",len(dna.get("depth_planes",[]))>=3,len(dna.get("depth_planes",[])),"≥ 3")
    check("six camera controls",len(dna.get("camera_controls",[]))>=6,len(dna.get("camera_controls",[])),"≥ 6")
    check("twelve transition families",len(set(dna.get("transitions",[])))>=12,len(set(dna.get("transitions",[]))),"≥ 12")
    check("five authored WTF suites",len(dna.get("wtf_setpieces",[]))==5,len(dna.get("wtf_setpieces",[])),5)
    complete_rows=sum(bool(r.get("primary_motion") and r.get("depth_motion") and r.get("micro_motion")) for r in visual_rows)
    check("34-beat triple-motion ledger",len(visual_rows)==34 and complete_rows==34,f"{complete_rows}/{len(visual_rows)} complete","34/34")
    check("visual motion delta",pic["motion_median"]>dna["targets"]["motion_median_must_exceed_parent"],round(pic["motion_median"],4),f"> V1 {dna['targets']['motion_median_must_exceed_parent']:.4f}")
    check("timeline byte lock",file_sha(PROJECT/"MASTER_TIMELINE.json")==dna["targets"]["timeline_sha256"],file_sha(PROJECT/"MASTER_TIMELINE.json"),dna["targets"]["timeline_sha256"])
    check("voice byte lock",file_sha(PROJECT/"audio"/"voice00_master.mp3")==dna["targets"]["voice_sha256"],file_sha(PROJECT/"audio"/"voice00_master.mp3"),dna["targets"]["voice_sha256"])
    measured_parent_tree=tree_sha(parent)
    check("immutable V1 parent",measured_parent_tree==dna["parent_v1"]["immutable_tree_sha256"],measured_parent_tree,dna["parent_v1"]["immutable_tree_sha256"])
    renderer=(PROJECT/"src"/"render.py").read_text();audio_src=(PROJECT/"src"/"audio.py").read_text()
    check("V2 source implementation","V2 CINEMA TABAHI LAYER" in renderer and "V2 CINEMA TABAHI SOUND LAYER" in audio_src,"picture + sound V2 markers","both present")
    prov_hashes=provenance.get("critical_file_sha256",{})
    prov_ok=all((PROJECT/q).exists() and file_sha(PROJECT/q)==h for q,h in prov_hashes.items())
    check("critical provenance hashes",prov_ok,f"{sum((PROJECT/q).exists() and file_sha(PROJECT/q)==h for q,h in prov_hashes.items())}/{len(prov_hashes)}","all match")
    check("procedural no-stock provenance",provenance.get("picture",{}).get("stock_footage") is False and provenance.get("audio",{}).get("stock_music") is False and provenance.get("audio",{}).get("stock_samples") is False,"picture/audio stock flags false","all false")
    check("embedded licensed typography",all((PROJECT/q).exists() for q in ("assets/fonts/Montserrat-VF.ttf","assets/fonts/Montserrat-OFL.txt","assets/fonts/PermanentMarker.ttf","assets/fonts/PermanentMarker-APACHE-2.0.txt")),"font binaries + licenses","all present")
    check("delta evidence status",delta["v2"].get("audio_events")==am.get("events") and delta["v2"].get("beat_motion_rows")==34,f"events {delta['v2'].get('audio_events')}; rows {delta['v2'].get('beat_motion_rows')}","matches build; 34 rows")
    check("delivery size",path.stat().st_size<120*1024*1024,f"{path.stat().st_size/1024/1024:.2f} MiB","< 120 MiB")
    sha=hashlib.sha256(path.read_bytes()).hexdigest();md5=hashlib.md5(path.read_bytes()).hexdigest()
    passed=sum(c["pass"] for c in checks);report={"style":KIND,"file":str(path),"sha256":sha,"md5":md5,"probe":pr|au,"picture":pic,"checks":checks,"summary":{"passed":passed,"total":len(checks),"failed":len(checks)-passed}}
    art=PROJECT/"artifacts";art.mkdir(exist_ok=True);(art/"DELIVERY_GATES.json").write_text(json.dumps(report,indent=2)+"\n")
    lines=[f"# DELIVERY GATES — {KIND.upper()} — {passed}/{len(checks)} {'PASS' if passed==len(checks) else 'FAIL'}","",f"- File: `{path.name}`",f"- SHA-256: `{sha}`",f"- MD5: `{md5}`","","| # | Gate | Result | Measured | Target |","|---:|---|---|---|---|"]
    for i,c in enumerate(checks,1):lines.append(f"| {i} | {c['name']} | {'PASS' if c['pass'] else 'FAIL'} | {c['measured']} | {c['target']} |")
    (art/"DELIVERY_GATES.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines))
    raise SystemExit(0 if passed==len(checks) else 1)

if __name__=="__main__":main()
