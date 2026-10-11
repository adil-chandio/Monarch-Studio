#!/usr/bin/env python3
"""V2 procedural score, spatial SFX/ASMR and shared-VO mix for TUMHARI RESERVED SEAT.

The same source is retained by both style packages. It infers WF-01/WF-03 from
its path and builds a completely different original soundtrack for each.
No stock music, samples or loops are used. V2 adds authored micro-foley, moving stereo objects, sectional score automation and five synchronized cinema set-piece suites.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import subprocess

import numpy as np
from scipy.io import wavfile
from scipy import signal, ndimage

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parent
STYLE=PROJECT.parents[1]
REPO=STYLE.parents[1]
KIND="wf01" if "stickman" in STYLE.name else "wf03"
SR=48000
DUR=74.0
N=int(SR*DUR)
RNG=np.random.default_rng(12011 if KIND=="wf01" else 32011)
LEDGER=[]


def ffmpeg_exe():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def pan_gains(pan):
    a=(pan+1)*math.pi/4
    return math.cos(a),math.sin(a)


def env(n,attack=.01,release=.08):
    e=np.ones(n,np.float32)
    a=min(n,max(1,int(attack*SR))); r=min(n,max(1,int(release*SR)))
    e[:a]=np.linspace(0,1,a,dtype=np.float32)
    e[-r:]=np.linspace(1,0,r,dtype=np.float32)
    return e


def add_sig(bed,start,sig,gain=1.0,pan=0.0,kind="event"):
    i0=max(0,int(start*SR)); i1=min(N,i0+len(sig))
    if i1<=i0:return
    sig=np.asarray(sig[:i1-i0],np.float32)*gain
    l,r=pan_gains(pan)
    bed[i0:i1,0]+=sig*l;bed[i0:i1,1]+=sig*r
    LEDGER.append(dict(time=round(start,3),kind=kind,pan=round(pan,3),gain=round(gain,4),duration=round(len(sig)/SR,3)))


def tone(freq,dur,wave="sine",attack=.01,release=.10,detune=0.0):
    n=max(1,int(dur*SR)); t=np.arange(n,dtype=np.float32)/SR
    ph=2*np.pi*freq*t
    if wave=="triangle": y=2/np.pi*np.arcsin(np.sin(ph))
    elif wave=="softsquare": y=np.tanh(np.sin(ph)*2.2)
    else:y=np.sin(ph)
    if detune:
        y=.5*y+.5*np.sin(2*np.pi*freq*(1+detune)*t+.7)
    return (y*env(n,attack,release)).astype(np.float32)


def filtered_noise(dur,low=None,high=None):
    n=max(1,int(dur*SR)); x=RNG.normal(0,1,n).astype(np.float32)
    if low is not None or high is not None:
        if low is not None and high is not None:sos=signal.butter(3,[low,high],btype="bandpass",fs=SR,output="sos")
        elif low is not None:sos=signal.butter(3,low,btype="highpass",fs=SR,output="sos")
        else:sos=signal.butter(3,high,btype="lowpass",fs=SR,output="sos")
        x=signal.sosfilt(sos,x).astype(np.float32)
    x/=max(1e-6,float(np.max(np.abs(x))))
    return x


def click(dur=.055,freq=1600):
    n=int(dur*SR); t=np.arange(n)/SR
    x=np.sin(2*np.pi*(freq+freq*1.8*t/dur)*t)*np.exp(-t*55)
    x+=filtered_noise(dur,high=7000)*np.exp(-t*80)*.35
    return x.astype(np.float32)


def thump(dur=.35,f0=74):
    n=int(dur*SR);t=np.arange(n)/SR
    ph=2*np.pi*(f0*t-0.55*f0*t*t/dur)
    return (np.sin(ph)*np.exp(-t*11)).astype(np.float32)


def whoosh(dur=.42,bright=True):
    x=filtered_noise(dur,low=500 if bright else 120,high=9000 if bright else 2500)
    n=len(x);u=np.linspace(0,1,n,dtype=np.float32)
    e=np.maximum(0.0,np.sin(np.pi*u))**1.8
    return x*e


def bell(freq=880,dur=1.5):
    n=int(dur*SR);t=np.arange(n)/SR
    y=np.zeros(n,np.float32)
    for k,g,dec in ((1,1,2.8),(2.01,.42,3.7),(3.98,.18,5.4),(6.1,.08,7.5)):
        y+=(np.sin(2*np.pi*freq*k*t)*np.exp(-t*dec)*g).astype(np.float32)
    return y*env(n,.005,.35)


def add_pad(bed,start,dur,notes,gain,pan_spread=.5):
    for j,f in enumerate(notes):
        y=tone(f,dur,"sine",.9,1.3,detune=.0025*(1 if j%2 else -1))
        y+=.18*tone(f*2,dur,"sine",.9,1.3,detune=.001)
        add_sig(bed,start,y,gain/(1+j*.10),(-pan_spread if j%2==0 else pan_spread),"pad")


def build_wf01(bed):
    bpm=94; beat=60/bpm
    prog=[(146.83,174.61,220.00),(116.54,146.83,174.61),(130.81,164.81,196.00),(130.81,164.81,220.00)]
    bar=beat*4
    k=0;st=0.0
    while st<DUR:
        add_pad(bed,st,min(bar+1.0,DUR-st),prog[k%4],.0105,.68)
        k+=1;st+=bar
    # tactile pulse / pencil bed
    nbeat=int(DUR/beat)+1
    for i in range(nbeat):
        t=i*beat
        root=prog[(i//4)%4][0]
        add_sig(bed,t,tone(root*2,.26,"triangle",.004,.20),.060,(-.22 if i%2 else .22),"pencil_pluck")
        if i%2==0:add_sig(bed,t,thump(.28,62),.075,0,"soft_kick")
        if i%4 in (1,3):add_sig(bed,t,filtered_noise(.10,low=4200)*env(int(.10*SR),.003,.07),.018,(.65 if i%4==1 else -.65),"paper_brush")
    # ASMR events tied to picture beats; no consecutive repeat
    events=[(0.0,"ticket_tear"),(1.75,"seat_lock"),(5.3,"paper_rub"),(8.98,"card_snap"),(12.6,"marker_squeak"),(14.44,"timer_click"),(16.38,"split_seam"),(18.43,"clock_tick"),(20.98,"phone_glass"),(22.43,"reel_swipe"),(24.43,"doppler_scroll"),(25.88,"phone_thump"),(28.45,"timer_click"),(32.65,"calendar_flip"),(33.53,"calendar_flip_hi"),(34.52,"paper_step"),(36.59,"counter_clack"),(39.03,"pencil_tick"),(40.36,"gold_bell"),(42.22,"card_snap"),(45.04,"comment_pop"),(48.57,"truth_braam"),(51.99,"paper_tear"),(55.36,"seat_warning"),(59.75,"timer_click"),(62.55,"phone_thump"),(63.59,"page_open"),(64.59,"start_click"),(65.86,"fork_hit"),(70.56,"seat_lock"),(71.81,"train_chime")]
    for j,(t,knd) in enumerate(events):
        pan=(-.72+(j%7)*.24)
        if "thump" in knd or "hit" in knd or "braam" in knd:add_sig(bed,t,thump(.45,52 if "braam" in knd else 74),.14,pan,knd)
        elif "bell" in knd or "chime" in knd:add_sig(bed,t,bell(740 if "gold" in knd else 660,1.6),.085,pan,knd)
        elif "swipe" in knd or "scroll" in knd or "tear" in knd or "rub" in knd:add_sig(bed,t,whoosh(.36,True),.032,pan,knd)
        elif "flip" in knd or "clack" in knd:add_sig(bed,t,click(.09,1100+j*23),.070,pan,knd)
        else:add_sig(bed,t,click(.055,1550+j*17),.062,pan,knd)
    # pattern-interrupt hush and final rail rise
    i0=int(48.35*SR);i1=int(49.15*SR);bed[i0:i1]*=np.linspace(1,.08,i1-i0)[:,None]
    add_sig(bed,70.3,whoosh(2.9,False),.055,-.25,"train_air_arrival")
    add_sig(bed,71.6,bell(523.25,2.2),.10,.35,"final_train_chime")


def build_wf03(bed):
    # true-stereo platform rain and fluorescent/rail ambience
    rainL=filtered_noise(DUR,low=1800,high=11000); rainR=filtered_noise(DUR,low=1900,high=10500)
    bed[:,0]+=rainL*.011;bed[:,1]+=rainR*.011
    LEDGER.append(dict(time=0.0,kind="platform_rain_LR",pan=0,gain=.011,duration=DUR))
    t=np.arange(N,dtype=np.float32)/SR
    hum=(np.sin(2*np.pi*100*t)+.45*np.sin(2*np.pi*200*t+.3))*.0034
    rail=(np.sin(2*np.pi*36.7*t)+.45*np.sin(2*np.pi*73.4*t+.6))*.0065
    bed[:,0]+=hum+rail;bed[:,1]+=hum*.92+np.roll(rail,701)*.95
    LEDGER.extend([dict(time=0.0,kind="fluorescent_hum",pan=0,gain=.0034,duration=DUR),dict(time=0.0,kind="distant_rail",pan=0,gain=.0065,duration=DUR)])
    bpm=72;beat=60/bpm
    # sparse D-minor felt tones; first F-sharp only after the action turn
    for i in range(int(DUR/(beat*2))+1):
        st=i*beat*2
        major=st>=64.59
        notes=(146.83,185.00 if major else 174.61,220.00)
        f=notes[i%3]
        add_sig(bed,st,bell(f*2,2.4),.026,(-.55 if i%2 else .55),"felt_bell_major" if major else "felt_bell_minor")
        if i%2==0:add_sig(bed,st,thump(.65,43),.055,0,"sub_train_pulse")
    events=[(0.0,"ticket_printer"),(1.75,"seat_relay"),(5.3,"departure_flap"),(8.98,"pressure_flaps"),(12.6,"red_cancel"),(14.44,"ticket_punch"),(16.38,"bench_creak"),(18.43,"station_clock"),(20.98,"phone_glass"),(22.43,"reel_tap"),(24.43,"train_occlusion"),(25.88,"phone_down"),(28.45,"ticket_punch"),(32.65,"day_flap1"),(33.53,"day_flap10"),(34.52,"day_flap30"),(36.59,"train_brake"),(39.03,"ticket_punch_run"),(40.36,"thirty_hours"),(42.22,"proof_relay"),(45.04,"lucky_red"),(48.57,"fluorescent_blackout"),(51.99,"ticket_reveal"),(55.36,"reservation_burn"),(59.75,"ticket_punch"),(62.55,"phone_down"),(63.59,"paper_open"),(64.59,"amber_relay"),(65.86,"track_switch"),(70.56,"door_chime"),(71.81,"train_arrival")]
    for j,(st,knd) in enumerate(events):
        pan=(-.8+(j%9)*.2)
        if "flap" in knd:add_sig(bed,st,click(.12,720+j*19),.065,pan,knd)
        elif "brake" in knd or "arrival" in knd:
            y=whoosh(1.8,False)+tone(440,1.8,"sine",.05,1.2)*.14
            add_sig(bed,st,y,.075,pan,knd)
        elif "blackout" in knd or "hours" in knd or "switch" in knd:add_sig(bed,st,thump(.65,42),.12,pan,knd)
        elif "chime" in knd or "relay" in knd:add_sig(bed,st,bell(523 if st>64 else 392,1.8),.060,pan,knd)
        elif "creak" in knd or "burn" in knd or "reveal" in knd:add_sig(bed,st,whoosh(.55,False),.035,pan,knd)
        else:add_sig(bed,st,click(.075,900+j*13),.055,pan,knd)
    # clock ticks around the story time and proof fork
    for st0,st1 in ((18.43,21.0),(65.86,70.56)):
        st=st0
        while st<st1:
            add_sig(bed,st,click(.035,1900),.032,-.45,"clock_tick")
            st+=.5
    # dramatic hole for truth, amber Picardy rise, quiet tail
    bed[int(48.35*SR):int(49.20*SR)]*=.07
    add_pad(bed,64.59,8.5,(146.83,185.00,220.00),.018,.72)
    bed[int(73.15*SR):]*=np.linspace(1,0,N-int(73.15*SR))[:,None]



# ---------------------------------------------------------------------------
# V2 CINEMA TABAHI SOUND LAYER
# These additions are intentionally different in each workflow. They do not
# replace or time-stretch the locked voice; they enrich the score/foley buses
# beneath it and are later side-chained by the original narration envelope.
V2_WTF_TIMES=(0.0,24.43,40.36,48.57,71.81)


def add_sweep(bed,start,sig,gain=.03,pan0=-.8,pan1=.8,kind="moving_object"):
    i0=max(0,int(start*SR));i1=min(N,i0+len(sig))
    if i1<=i0:return
    x=np.asarray(sig[:i1-i0],np.float32)*gain
    u=np.linspace(0,1,len(x),dtype=np.float32)
    pan=pan0+(pan1-pan0)*(u*u*(3-2*u))
    ang=(pan+1)*np.pi/4
    bed[i0:i1,0]+=x*np.cos(ang);bed[i0:i1,1]+=x*np.sin(ang)
    LEDGER.append(dict(time=round(start,3),kind=kind,pan=f"{pan0:.2f}>{pan1:.2f}",gain=round(gain,4),duration=round(len(sig)/SR,3)))


def reverse_riser(dur=.48,bright=True):
    x=whoosh(dur,bright)[::-1].copy();u=np.linspace(0,1,len(x),dtype=np.float32)
    return x*(u**1.4)


def paper_tic(pitch=2100,dur=.038):
    n=max(1,int(dur*SR));t=np.arange(n,dtype=np.float32)/SR
    nse=filtered_noise(dur,low=1800,high=11000)
    y=.65*nse+.35*np.sin(2*np.pi*pitch*t)
    return (y*np.exp(-t*95)).astype(np.float32)


def rail_clack(dur=.10,pitch=520):
    n=max(1,int(dur*SR));t=np.arange(n,dtype=np.float32)/SR
    y=np.sin(2*np.pi*(pitch*(1-0.42*t/dur))*t)*np.exp(-t*43)
    y+=filtered_noise(dur,low=700,high=6500)*np.exp(-t*62)*.55
    return y.astype(np.float32)


def sub_drop(dur=.9,f0=68,f1=31):
    n=int(dur*SR);t=np.arange(n,dtype=np.float32)/SR
    k=(f1-f0)/dur;ph=2*np.pi*(f0*t+.5*k*t*t)
    return (np.sin(ph)*np.exp(-t*3.1)*env(n,.008,.25)).astype(np.float32)


def beat_boundaries():
    data=json.loads((PROJECT/"MASTER_TIMELINE.json").read_text())
    return [(float(b["t0"]),int(b["id"])) for b in data["beats"]]


def build_wf01_v2(bed):
    # Paper-percussion orchestra: 1/8-note foreground plucks, quieter 1/16
    # pencil ghosts and section-aware harmony. Every note is synthesized.
    bpm=94;quarter=60/bpm;eighth=quarter/2
    scale=(146.83,164.81,196.0,220.0,246.94,293.66,329.63)
    st=0.0;i=0
    while st<DUR:
        sec=0 if st<16.38 else 1 if st<32.65 else 2 if st<48.57 else 3 if st<64.59 else 4
        f=scale[(i*3+sec*2)%len(scale)]*(2 if i%4 else 1)
        vel=(.018,.026,.021,.032)[i%4]*(1.18 if sec in (2,4) else 1.0)
        add_sig(bed,st,tone(f,.115,"triangle",.002,.095,detune=.0015),vel,(-.62+(i%7)*.205),"v2_paper_arp")
        if i%2:
            add_sig(bed,st+.055,paper_tic(1850+(i%9)*93,.032),.012,(.78 if i%4==1 else -.78),"v2_pencil_ghost")
        st+=eighth;i+=1
    # Handled-paper micro-foley moves through the headphones without crossing
    # narration centre. Dynamics stay low; density is perceptual, not loud.
    st=.22;j=0
    while st<73.0:
        sig=paper_tic(2400+(j%13)*137,.028+(j%3)*.006)
        add_sweep(bed,st,sig,.010+(j%5)*.0015,-.88 if j%2==0 else .88,.55 if j%2==0 else -.55,"v2_paper_micro_ASMR")
        st+=.287+(j%4)*.021;j+=1
    # Every story cut has a quiet pre-lap and a tactile landing, making picture
    # transitions feel authored even under speech.
    for j,(st,bid) in enumerate(beat_boundaries()):
        if st>.16:add_sweep(bed,st-.16,reverse_riser(.16,True),.011,(-.8 if j%2 else .8),(.25 if j%2 else -.25),f"v2_cut_prelap_{bid:02d}")
        add_sig(bed,st,paper_tic(1300+(bid%8)*120,.045),.018,(-.5+(bid%5)*.25),f"v2_cut_land_{bid:02d}")
    # Five authored WTF suites: low impact, reverse intake, stereo debris,
    # resonant ticket ring and a long tail. The combinations never repeat.
    for n,st in enumerate(V2_WTF_TIMES):
        if st>.55:add_sweep(bed,st-.52,reverse_riser(.52,n%2==0),.048,(-.95 if n%2 else .95),(.2 if n%2 else -.2),f"v2_wtf{n+1}_intake")
        add_sig(bed,st,sub_drop(.95,70-n*3,30+n),.105,0,f"v2_wtf{n+1}_sub")
        add_sig(bed,st+.018,bell(392*(1+n*.11),1.75),.040,(-.58+n*.29),f"v2_wtf{n+1}_ticket_ring")
        for k in range(7):
            add_sig(bed,st+.045+k*.038,paper_tic(2200+k*230,.055),.018,(k-3)/3.4,f"v2_wtf{n+1}_paper_debris")
    # Positive action lift: bright train ostinato and widening final resolve.
    st=64.59;j=0
    while st<73.35:
        f=(293.66,329.63,392.0,440.0)[j%4]
        add_sweep(bed,st,tone(f,.19,"triangle",.003,.16),.030,(-.7 if j%2 else .7),(.35 if j%2 else -.35),"v2_action_lift")
        st+=quarter/2;j+=1


def build_wf03_v2(bed):
    # Railway rhythm is physical rather than "beat music": sleeper clacks,
    # transformer breaths and sparse harmonic pressure at 72 BPM.
    bpm=72;half=60/bpm/2
    st=.10;i=0
    while st<73.3:
        gain=.017 if i%4 else .027
        add_sig(bed,st,rail_clack(.092,430+(i%5)*44),gain,(-.72 if i%2 else .72),"v2_rail_sleeper_clack")
        if i%4==3:add_sweep(bed,st-.13,reverse_riser(.20,False),.009,(-.65 if i%8==3 else .65),(.1 if i%8==3 else -.1),"v2_rail_suction")
        st+=half;i+=1
    # Near/mid/far rain transients: irregular intervals and alternating depth.
    st=.37;j=0
    while st<73.0:
        dur=.022+(j%4)*.009
        sig=paper_tic(3100+(j%11)*170,dur)
        gain=(.006,.010,.014)[j%3]
        pan=(-.92+(j%13)/12*1.84)
        add_sig(bed,st,sig,gain,pan,f"v2_rain_depth_{j%3+1}")
        st+=.49+(j%7)*.041;j+=1
    # Mechanical cut grammar: flap pre-laps and relay landings.
    for j,(st,bid) in enumerate(beat_boundaries()):
        if st>.24:add_sweep(bed,st-.23,reverse_riser(.23,False),.012,(-.9 if j%2 else .9),(.22 if j%2 else -.22),f"v2_shutter_prelap_{bid:02d}")
        add_sig(bed,st,rail_clack(.12,520+(bid%6)*53),.022,(-.62+(bid%6)*.24),f"v2_relay_land_{bid:02d}")
    # Five noir set pieces, each spatially distinct and lower-pitched than WF-01.
    for n,st in enumerate(V2_WTF_TIMES):
        if st>.72:add_sweep(bed,st-.68,reverse_riser(.68,False),.052,(.95 if n%2 else -.95),(-.15 if n%2 else .15),f"v2_wtf{n+1}_tunnel_intake")
        add_sig(bed,st,sub_drop(1.25,59-n*2,24+n),.118,0,f"v2_wtf{n+1}_rail_sub")
        add_sig(bed,st+.025,bell(261.63*(1+n*.08),2.35),.031,(.55-n*.27),f"v2_wtf{n+1}_platform_resonance")
        for k in range(5):
            add_sig(bed,st+.07+k*.082,rail_clack(.16,360+k*61),.021,(k-2)/2.25,f"v2_wtf{n+1}_metal_debris")
    # Post-decision Picardy lift: warm relay pulse, still recognisably noir.
    st=64.59;j=0
    while st<73.15:
        f=(146.83,185.0,220.0,293.66)[j%4]
        add_sweep(bed,st,tone(f,.46,"sine",.018,.35,detune=.001),.023,(-.6 if j%2 else .6),(.22 if j%2 else -.22),"v2_amber_resolve")
        st+=half;j+=1


def v2_bus_automation(bed):
    # Gentle 5-act energy contour and M/S widening. This is applied before
    # narration side-chain, so every added layer still yields to the words.
    points=((0,.78),(8.98,.92),(16.38,.80),(24.43,1.04),(32.65,.88),(40.36,1.10),(48.57,.58),(55.36,.84),(64.59,1.05),(71.81,1.20),(74,.58))
    x=np.arange(N,dtype=np.float32)/SR
    e=np.interp(x,[a for a,_ in points],[b for _,b in points]).astype(np.float32)
    bed*=e[:,None]
    mid=(bed[:,0]+bed[:,1])*.5;side=(bed[:,0]-bed[:,1])*.5
    width=1.18 if KIND=="wf01" else 1.28
    bed[:,0]=mid+side*width;bed[:,1]=mid-side*width

def decode_voice(path):
    cmd=[ffmpeg_exe(),"-v","error","-i",str(path),"-f","f32le","-acodec","pcm_f32le","-ac","1","-ar",str(SR),"-"]
    raw=subprocess.check_output(cmd)
    v=np.frombuffer(raw,dtype=np.float32)
    out=np.zeros(N,np.float32);out[:min(N,len(v))]=v[:N]
    return out


def build(output,mux_video=None,final=None):
    bed=np.zeros((N,2),np.float32)
    if KIND=="wf01":
        build_wf01(bed);build_wf01_v2(bed)
    else:
        build_wf03(bed);build_wf03_v2(bed)
    v2_bus_automation(bed)
    voice=decode_voice(PROJECT/"audio"/"voice00_master.mp3")
    # transparent compression keeps words close without radio harshness
    vc=np.tanh(voice*2.15)/np.tanh(2.15)
    venv=ndimage.uniform_filter1d(np.abs(vc),size=int(.065*SR),mode="nearest")
    duck=1-(.58 if KIND=="wf01" else .52)*np.clip(venv/.12,0,1)
    bed*=duck[:,None]
    bed*=1.18 if KIND=="wf01" else 1.12
    voice_gain=.72 if KIND=="wf01" else .66
    mix=bed+vc[:,None]*voice_gain
    # Short, filtered, asymmetric room taps keep the narrator firmly centred
    # while giving headphones a real space instead of fake bus widening.
    sos=signal.butter(2,[180,6200],btype="bandpass",fs=SR,output="sos")
    wet=signal.sosfilt(sos,vc).astype(np.float32)
    taps_l=((.019,.085),(.057,.050),(.109,.028))
    taps_r=((.031,.085),(.073,.050),(.127,.028))
    for delay,gain in taps_l:
        n=int(delay*SR);mix[n:,0]+=wet[:-n]*gain
    for delay,gain in taps_r:
        n=int(delay*SR);mix[n:,1]+=wet[:-n]*gain
    # quiet half-second tail and codec headroom
    mix[-int(.45*SR):]*=np.linspace(1,0,int(.45*SR))[:,None]
    pk=float(np.max(np.abs(mix)))
    if pk>.84:mix*=.84/pk
    output.parent.mkdir(parents=True,exist_ok=True)
    wavfile.write(output,SR,mix.astype(np.float32))
    corr=float(np.corrcoef(mix[:,0],mix[:,1])[0,1])
    metrics={"style":KIND,"sample_rate":SR,"duration_s":DUR,"pre_master_peak_dbfs":round(20*math.log10(max(1e-9,float(np.max(np.abs(mix))))),3),"lr_correlation":round(corr,4),"voice_source":"voice00_master.mp3","voice_time_stretched":False,"events":len(LEDGER),"version":"V2_MONARCH_CINEMA_TABAHI","spatial_moving_events":sum(1 for e in LEDGER if isinstance(e.get("pan"),str)),"wtf_setpiece_suites":5,"score_sections":5,"audio_bus_width":1.18 if KIND=="wf01" else 1.28}
    (PROJECT/"artifacts").mkdir(exist_ok=True)
    (PROJECT/"artifacts"/"AUDIO_BUILD_METRICS.json").write_text(json.dumps(metrics,indent=2)+"\n")
    with (PROJECT/"artifacts"/"AUDIO_EVENT_LEDGER.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["time","kind","pan","gain","duration"]);w.writeheader();w.writerows(LEDGER)
    print(json.dumps(metrics,indent=2))
    if mux_video and final:
        target="-13" if KIND=="wf01" else "-16"
        lra="7" if KIND=="wf01" else "9"
        final.parent.mkdir(parents=True,exist_ok=True)
        cmd=[ffmpeg_exe(),"-y","-i",str(mux_video),"-i",str(output),"-filter:a",f"loudnorm=I={target}:LRA={lra}:TP=-1.2,aresample=48000","-c:v","copy","-c:a","aac","-ar","48000","-b:a","256k","-t",str(DUR),"-movflags","+faststart",str(final)]
        subprocess.run(cmd,check=True)
        print(final)


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",type=Path,required=True);ap.add_argument("--mux-video",type=Path);ap.add_argument("--final",type=Path)
    a=ap.parse_args();build(a.output,a.mux_video,a.final)

if __name__=="__main__":main()
