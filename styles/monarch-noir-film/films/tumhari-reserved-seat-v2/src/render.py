#!/usr/bin/env python3
"""WF-03 V2 picture renderer — TUMHARI RESERVED SEAT · MONARCH NOIR IMAX TABAHI.

A deterministic 1920x1080 / 24 fps / 74 s multi-plane noir railway-platform upgrade. It does
not reuse THE SHADOW's lantern/cast-shadow device or THE WINDOW's apartment
facade. The physical spine is one self-punching reserved ticket.
"""
from __future__ import annotations

import argparse
import bisect
import json
import math
from pathlib import Path
import subprocess
import sys
import time
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops, ImageEnhance

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
STYLE = PROJECT.parents[1]
REPO = STYLE.parents[1]
WF01 = REPO / "styles" / "monarch-stickman-animation"
sys.path.insert(0, str(WF01 / "src"))
sys.path.insert(0, str(STYLE / "src"))
sys.path.insert(0, str(PROJECT / "src"))
import human as HM  # noqa: E402

W, H, FPS = 1920, 1080, 24
TIMELINE = json.loads((PROJECT / "MASTER_TIMELINE.json").read_text())
DUR = float(TIMELINE["picture_duration_s"])
NF = int(round(DUR * FPS))
BEATS = TIMELINE["beats"]
STARTS = [float(b["t0"]) for b in BEATS]
FONT_DIR = PROJECT / "assets" / "fonts"
_FONTS = {}

BLACK = (5, 6, 9)
WALL = (13, 16, 21)
FLOOR = (16, 19, 24)
BONE = (232, 230, 220)
SLATE = (110, 120, 132)
CYAN = (91, 160, 184)
BLUE = (64, 98, 142)
RED = (188, 43, 42)
AMBER = (224, 164, 80)
GREEN = (78, 142, 106)


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x=clamp(x); return x*x*(3-2*x)
def out(x,p=3): return 1-(1-clamp(x))**p


def font(size, marker=False):
    name="PermanentMarker.ttf" if marker else "Montserrat-VF.ttf"
    key=(name,int(size))
    if key not in _FONTS:
        _FONTS[key]=ImageFont.truetype(str(FONT_DIR/name),int(size))
    return _FONTS[key]


def fit(text,maxw,start,minimum=22,marker=False):
    s=start
    while s>minimum:
        f=font(s,marker)
        if f.getlength(text)<=maxw:return f
        s-=2
    return font(minimum,marker)


def base_gradient():
    yy=np.linspace(0,1,H,dtype=np.float32)[:,None,None]
    top=np.array([7,9,14],np.float32)[None,None,:]
    bot=np.array([17,20,25],np.float32)[None,None,:]
    arr=top*(1-yy)+bot*yy
    arr=np.repeat(arr,W,axis=1)
    rng=np.random.default_rng(3301)
    arr += rng.normal(0,1.5,(H,W,1)).astype(np.float32)
    return Image.fromarray(np.clip(arr,0,255).astype(np.uint8),"RGB").convert("RGBA")

BASE=base_gradient()


def glow(layer,xy,r,col,power=.25):
    g=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(g)
    x,y=xy
    d.ellipse([x-r,y-r,x+r,y+r],fill=col+(int(255*power),))
    g=g.filter(ImageFilter.GaussianBlur(max(2,int(r*.42))))
    layer.alpha_composite(g)


def station(t,bid,amber=0.0):
    # Platform rain/light plates update at 6 Hz; performance, titles and props
    # remain full-frame-rate. This preserves living holds without wasting CPU.
    return _station_q(int(t*6),bid,int(clamp(amber)*100)).copy()


@lru_cache(maxsize=4)
def _station_q(tick,bid,amber_q):
    t=tick/6.0;amber=amber_q/100.0
    im=BASE.copy(); d=ImageDraw.Draw(im,"RGBA")
    vp=(1040,430)
    # ceiling and platform architecture
    d.polygon([(0,0),(W,0),(W,300),(vp[0]+330,vp[1]),(vp[0]-500,vp[1]),(0,350)],fill=(8,10,14,255))
    d.polygon([(0,430),(W,430),(W,H),(0,H)],fill=FLOOR+(255,))
    for x in (-400,0,360,690,1000,1280,1530,1780,2050):
        d.line([(vp[0],vp[1]),(x,H)],fill=(45,50,57,100),width=2)
    for y in (520,620,720,820,930,1030):
        d.line([(0,y),(W,y)],fill=(43,48,55,70),width=2)
    # tracks and warning edge
    d.polygon([(0,790),(W,740),(W,835),(0,900)],fill=(10,12,15,255))
    d.line([(0,785),(W,735)],fill=(150,115,52,170),width=8)
    d.line([(0,930),(W,840)],fill=(112,116,120,180),width=13)
    d.line([(0,1025),(W,900)],fill=(88,92,98,180),width=12)
    # rail joints move subtly to imply waiting train energy
    off=int((t*28)%110)
    for x in range(-off,W+120,110):
        d.line([(x,901),(x+70,935)],fill=(74,76,81,150),width=4)
    # columns
    for x in (170,1740):
        d.rectangle([x-46,260,x+46,825],fill=(19,22,28,255),outline=(50,55,64,180),width=4)
        d.rectangle([x-66,250,x+66,278],fill=(29,33,40,255))
    # fluorescent practicals; occasional brief flicker, never full-frame strobe
    flick=1.0-(0.42 if (int(t*17)+bid*3)%113==0 else 0.0)
    for x in (420,920,1420):
        c=tuple(int(CYAN[i]*(1-amber)+AMBER[i]*amber) for i in range(3))
        d.rounded_rectangle([x-160,125,x+160,145],10,fill=c+(int(210*flick),))
        glow(im,(x,170),155,c,.10*flick)
    # bench
    d.rounded_rectangle([285,650,725,697],12,fill=(38,39,43,255),outline=(76,76,76,200),width=4)
    for x in (330,675): d.line([(x,697),(x-12,810)],fill=(74,74,76,210),width=13)
    # station sign
    d.rounded_rectangle([1450,315,1810,395],9,fill=(18,21,26,245),outline=(65,72,82,230),width=4)
    d.text((1630,355),"PLATFORM 20",font=font(28),fill=BONE+(230,),anchor="mm")
    # rain in open track world
    rng=np.random.default_rng(int(t*12)+bid*1009)
    for _ in range(95):
        x=float(rng.uniform(0,W)); y=float(rng.uniform(250,900)); ln=float(rng.uniform(12,36))
        d.line([(x,y),(x-4,y+ln)],fill=CYAN+(int(rng.uniform(18,55)),),width=1)
    # dust/breath particles in practical pools
    for k in range(42):
        x=(k*211+int(t*(9+k%4)))%W; y=190+(k*97+int(t*5))%520
        a=20+15*(k%3)
        d.ellipse([x-1,y-1,x+1,y+1],fill=BONE+(a,))
    return im


def title(layer,xy,text,size=72,col=BONE,marker=False,glow_col=None,alpha=255,maxw=1600):
    d=ImageDraw.Draw(layer,"RGBA"); f=fit(text,maxw,size,marker=marker)
    if glow_col:
        g=Image.new("RGBA",(W,H),(0,0,0,0)); gd=ImageDraw.Draw(g)
        gd.text(xy,text,font=f,fill=glow_col+(100,),anchor="mm")
        g=g.filter(ImageFilter.GaussianBlur(16)); layer.alpha_composite(g)
    d.text((xy[0]+3,xy[1]+4),text,font=f,fill=(0,0,0,int(alpha*.9)),anchor="mm")
    d.text(xy,text,font=f,fill=col+(alpha,),anchor="mm")


def small(layer,xy,text,size=25,col=SLATE,anchor="mm",box=False):
    d=ImageDraw.Draw(layer,"RGBA"); f=fit(text,800,size,18)
    if box:
        b=d.textbbox(xy,text,font=f,anchor=anchor)
        d.rounded_rectangle([b[0]-16,b[1]-8,b[2]+16,b[3]+8],12,fill=(9,11,15,220),outline=col+(150,),width=2)
    d.text(xy,text,font=f,fill=col+(240,),anchor=anchor)


def draw_ticket(layer,x,y,w,h,holes=0,warning=False,angle=0,alpha=255):
    tw,th=int(w*1.5),int(h*2.0)
    im=Image.new("RGBA",(tw,th),(0,0,0,0)); d=ImageDraw.Draw(im,"RGBA"); ox,oy=tw/2,th/2
    paper=(213,205,184) if not warning else (185,165,148)
    edge=RED if warning else AMBER
    d.rounded_rectangle([ox-w/2,oy-h/2,ox+w/2,oy+h/2],int(h*.08),fill=paper+(alpha,),outline=edge+(alpha,),width=max(3,int(h*.035)))
    d.line([(ox-w*.18,oy-h/2),(ox-w*.18,oy+h/2)],fill=edge+(int(alpha*.55),),width=3)
    d.text((ox-w*.34,oy),"20",font=fit("20",w*.24,int(h*.38)),fill=BLACK+(alpha,),anchor="mm")
    d.text((ox+w*.14,oy-h*.13),"RESERVED SEAT",font=fit("RESERVED SEAT",w*.45,int(h*.14)),fill=BLACK+(alpha,),anchor="mm")
    d.text((ox+w*.14,oy+h*.15),"VALID · 90 DAYS",font=fit("VALID · 90 DAYS",w*.44,int(h*.10)),fill=(64,58,52,alpha),anchor="mm")
    for i in range(min(30,holes)):
        row=i//10; col=i%10
        hx=ox-w*.05+col*w*.047; hy=oy-h*.20+row*h*.20
        rr=max(2,int(h*.018))
        d.ellipse([hx-rr,hy-rr,hx+rr,hy+rr],fill=BLACK+(alpha,))
    if angle: im=im.rotate(angle,Image.Resampling.BICUBIC)
    layer.alpha_composite(im,(int(x-tw/2),int(y-th/2)))


def draw_clock(layer,x,y,r,t,txt="11:47"):
    d=ImageDraw.Draw(layer,"RGBA")
    glow(layer,(x,y),r*1.35,CYAN,.12)
    d.ellipse([x-r,y-r,x+r,y+r],fill=(9,12,17,245),outline=(92,109,122,240),width=8)
    for k in range(12):
        a=k/12*math.tau-math.pi/2
        l=16 if k%3==0 else 9
        d.line([(x+math.cos(a)*(r-24),y+math.sin(a)*(r-24)),(x+math.cos(a)*(r-24-l),y+math.sin(a)*(r-24-l))],fill=BONE+(180,),width=4)
    minute=47+((t*.08)%1); hour=11+minute/60
    a1=minute/60*math.tau-math.pi/2; a2=hour/12*math.tau-math.pi/2
    d.line([(x,y),(x+math.cos(a1)*r*.62,y+math.sin(a1)*r*.62)],fill=CYAN+(255,),width=7)
    d.line([(x,y),(x+math.cos(a2)*r*.43,y+math.sin(a2)*r*.43)],fill=BONE+(255,),width=10)
    d.ellipse([x-9,y-9,x+9,y+9],fill=RED+(255,))
    small(layer,(x,y+r+48),txt+" PM",27,BONE,box=True)


def draw_departure(layer,x,y,w,h,main,sub="",col=BONE,flips=0):
    d=ImageDraw.Draw(layer,"RGBA")
    d.rounded_rectangle([x-w/2,y-h/2,x+w/2,y+h/2],12,fill=(8,11,15,245),outline=(55,63,72,255),width=5)
    # split-flap cells
    n=max(8,min(22,len(main)+2)); cw=(w-36)/n
    for i in range(n):
        xx=x-w/2+18+i*cw
        d.rectangle([xx,y-h*.22,xx+cw-3,y+h*.18],fill=(15,18,23,255),outline=(42,47,55,220),width=1)
        d.line([(xx,y-2),(xx+cw-3,y-2)],fill=(2,3,4,180),width=2)
    f=fit(main,w-60,int(h*.33),20)
    d.text((x,y-h*.02),main,font=f,fill=col+(255,),anchor="mm")
    if sub:d.text((x,y+h*.34),sub,font=fit(sub,w-80,int(h*.13),18),fill=SLATE+(240,),anchor="mm")
    # a few flipping slats
    for i in range(min(6,flips)):
        xx=x-w/2+35+i*cw*2.2
        d.rectangle([xx,y-5,xx+cw*1.4,y+4],fill=col+(90,),)


def draw_phone(layer,x,y,s,face=True,scroll=0.0,flat=False):
    d=ImageDraw.Draw(layer,"RGBA")
    h=s if not flat else s*.11; w=s*.52
    d.rounded_rectangle([x-w/2,y-h/2,x+w/2,y+h/2],max(6,int(s*.07)),fill=(16,18,24,255),outline=(82,92,105,255),width=max(3,int(s*.025)))
    if face and not flat:
        d.rounded_rectangle([x-w*.39,y-h*.42,x+w*.39,y+h*.42],int(s*.045),fill=(32,55,76,255))
        for i,c in enumerate((RED,CYAN,AMBER,GREEN)):
            yy=y-h*.28+((i*.21+scroll)% .78)*h
            d.rounded_rectangle([x-w*.29,yy-h*.065,x+w*.29,yy+h*.065],int(s*.02),fill=c+(170,))
        glow(layer,(x,y),s*.7,CYAN,.08)


def human(layer,x,y,s,t,kind="stand",expr="neutral",flip=False,alpha=1.0):
    char=Image.new("RGBA",(W,H),(0,0,0,0))
    if kind=="sit": p=HM.p_sit(t,.55)
    elif kind=="phone": p=HM.p_sit(t,.72)
    else: p=HM.p_stand(t,math.sin(t*.8)*.35)
    if kind=="walk":
        p=HM.p_stand(t,math.sin(t*4)*.55); p.update(yaw=50,az_l=30*math.sin(t*7),az_r=-30*math.sin(t*7),lz_l=28*math.sin(t*7),lz_r=-28*math.sin(t*7))
    HM.draw_human(char,x,y,s,p,(1480,145),expr=expr,look=(.15,.10),blink_v=HM.blink(t,seed=11),flip=flip,string_sway=math.sin(t*1.7)*.5,hood_up=kind=="phone")
    if alpha<1:
        a=char.getchannel("A").point(lambda q:int(q*alpha)); char.putalpha(a)
    layer.alpha_composite(char)


def train(layer,x,y,w,h,t,amber=0.0,windows=10):
    d=ImageDraw.Draw(layer,"RGBA")
    d.rounded_rectangle([x,y-h,x+w,y],int(h*.10),fill=(22,27,34,255),outline=(73,80,91,230),width=7)
    d.polygon([(x+w*.84,y-h),(x+w,y-h*.73),(x+w,y),(x+w*.84,y)],fill=(16,20,26,255))
    for i in range(windows):
        wx=x+w*.045+i*w*.073
        c=tuple(int(CYAN[j]*(1-amber)+AMBER[j]*amber) for j in range(3))
        d.rounded_rectangle([wx,y-h*.72,wx+w*.048,y-h*.34],int(h*.02),fill=c+(220,),outline=BLACK+(255,),width=2)
        glow(layer,(wx+w*.024,y-h*.53),h*.20,c,.035)
    for xx in (x+w*.18,x+w*.69):
        d.ellipse([xx-h*.11,y-h*.08,xx+h*.11,y+h*.14],fill=BLACK+(255,))
        d.ellipse([xx-h*.05,y-h*.02,xx+h*.05,y+h*.08],fill=(108,111,116,255))
    # headlight
    glow(layer,(x+w*.94,y-h*.45),h*.27,AMBER,.22*amber)


def caption_chrome(layer,beat,t,col):
    d=ImageDraw.Draw(layer,"RGBA"); bid=beat["id"]
    d.line([(74,69),(W-74,69)],fill=(52,59,68,200),width=3)
    xp=74+(W-148)*clamp(t/DUR)
    d.line([(74,69),(xp,69)],fill=col+(240,),width=5)
    d.ellipse([xp-6,63,xp+6,75],fill=col+(255,))
    d.text((74,108),f"WF-03 · {bid:02d}/34",font=font(21),fill=col+(240,),anchor="lm")
    d.text((W-74,108),"PLATFORM 20 · 11:47 PM",font=font(20),fill=SLATE+(220,),anchor="rm")
    lp=clamp((t-beat["t0"])/max(.01,beat["t1"]-beat["t0"]))
    title(layer,(960,193+(1-out(lp*3))*22),beat["caption"],68,col,marker=bid in (1,11,24,25),glow_col=col if bid in (1,7,19,21,25,33,34) else None)
    small(layer,(960,1011),beat["story"].upper(),21,SLATE)


def scene(layer,beat,t,p,col):
    bid=beat["id"]; d=ImageDraw.Draw(layer,"RGBA"); gy=824
    if bid in (1,2):
        if bid==1:
            draw_ticket(layer,960,560,900,300,holes=int(p*3),warning=True,angle=-1)
            draw_departure(layer,960,780,820,120,"EK BURI KHABAR","RESERVATION STATUS",RED,flips=int(p*7))
        else:
            # empty reserved seat under isolated practical
            d.rounded_rectangle([1180,570,1530,720],25,fill=(31,34,39,255),outline=(80,84,90,220),width=5)
            d.rounded_rectangle([1160,706,1550,760],20,fill=(38,40,44,255),outline=(80,84,90,220),width=5)
            d.line([(1200,760),(1180,830)],fill=(75,76,80,220),width=11); d.line([(1510,760),(1530,830)],fill=(75,76,80,220),width=11)
            glow(layer,(1355,550),330,CYAN,.16)
            human(layer,520,824,500,t,"stand","doubt")
            draw_ticket(layer,1355,445,450,155,holes=int(p*5),warning=True,angle=3)

    elif bid in (3,4,5):
        human(layer,520,824,500,t,"stand","tired" if bid!=4 else "neutral")
        if bid==3:
            draw_departure(layer,1300,525,670,240,"BOARDING NOW","NO PAUSE",RED,flips=int(p*6))
        elif bid==4:
            human(layer,1420,824,500,t+.2,"stand","focus" if "focus" in HM.EXPR else "resolve",flip=True,alpha=.72)
            d.line([(960,330),(960,835)],fill=CYAN+(90,),width=3)
            small(layer,(520,760),"YOU",24,CYAN,box=True); small(layer,(1420,760),"SAME AGE",24,CYAN,box=True)
        else:
            for i,(txt,xy) in enumerate([("GHAR",(1120,420)),("BILLS",(1450,520)),("CONFUSION",(1140,660)),("TALENT?",(1500,720))]):
                q=clamp(p*1.6-i*.14)
                if q>0: draw_departure(layer,xy[0],xy[1],330,86,txt,"",RED if i<3 else SLATE,flips=int(q*4))

    elif bid in (6,7):
        human(layer,510,824,500,t,"stand","doubt" if bid==6 else "resolve")
        if bid==6:
            draw_departure(layer,1310,530,650,230,"GENIUS?","NOT REQUIRED",RED,flips=int(p*6))
            d.line([(1100,380),(1520,680)],fill=RED+(230,),width=17); d.line([(1520,380),(1100,680)],fill=RED+(230,),width=17)
        else:
            draw_ticket(layer,1310,545,700,240,holes=int(p*7),warning=False,angle=-2)
            title(layer,(1310,760),"+20 MINUTES",58,CYAN,glow_col=CYAN,maxw=700)

    elif bid in (8,9,10):
        if bid==8:
            human(layer,520,824,470,t,"stand","neutral"); human(layer,1400,824,470,t+.2,"stand","neutral",flip=True)
            d.line([(960,320),(960,825)],fill=(66,73,82,150),width=4)
            small(layer,(520,760),"SAME NIGHT",24,SLATE,box=True); small(layer,(1400,760),"SAME CHOICE",24,SLATE,box=True)
        elif bid==9:
            draw_clock(layer,960,535,245,t,"11:47")
            human(layer,360,824,390,t,"stand","tired"); human(layer,1580,824,390,t+.2,"stand","resolve",flip=True)
        else:
            human(layer,515,824,470,t,"sit","tired"); human(layer,1405,824,470,t+.2,"sit","neutral",flip=True)
            draw_phone(layer,600,580,330,True,t*.14); draw_phone(layer,1320,580,330,True,t*.14)

    elif bid in (11,12,13):
        if bid==11:
            draw_phone(layer,960,555,520,True,t*.42)
            human(layer,370,824,420,t,"stand","envy")
            draw_departure(layer,1470,540,560,180,"ONE MORE","REEL",RED,flips=int(p*7))
        elif bid==12:
            # passing train cards become a dopamine tunnel
            for k in range(9):
                u=((k/9+t*.5)%1); ww=170+u*1050; hh=100+u*460
                d.rounded_rectangle([960-ww/2,535-hh/2,960+ww/2,535+hh/2],int(15+u*38),outline=(RED,CYAN,AMBER,GREEN)[k%4]+(int(35+u*115),),width=max(2,int(2+u*8)))
            human(layer,960,824,380,t,"stand","tired")
        else:
            human(layer,520,824,500,t,"stand","resolve")
            draw_phone(layer,1270,730,440,False,0,flat=True)
            d.line([(1020,792),(1510,792)],fill=(84,84,86,200),width=6)
            draw_ticket(layer,1280,500,480,165,holes=int(p*5),warning=False,angle=3)

    elif bid in (14,15):
        human(layer,520,824,500,t,"stand","resolve")
        draw_departure(layer,1280,525,680,250,"20:00" if bid==14 else "19:59","TIMER / TRACK 1",CYAN,flips=int(p*6))
        draw_ticket(layer,1280,735,530,175,holes=int((p if bid==14 else 1)*8),warning=False,angle=-2)

    elif bid in (16,17,18,19):
        day={16:1,17:10,18:30,19:90}[bid]; c={16:SLATE,17:CYAN,18:BLUE,19:AMBER}[bid]
        draw_departure(layer,1260,480,820,250,f"DAY {day}",{16:"NO VISIBLE GAP",17:"CONFIDENCE",18:"REAL SKILL",19:"ARRIVAL"}[bid],c,flips=int(p*8))
        draw_ticket(layer,500,520,520,180,holes=int(day/3*p) if day<90 else int(30*p),warning=False,angle=-5)
        human(layer,520+out(p)*500,824,440,t,"walk" if bid>16 else "stand","resolve")
        if bid==19:
            train(layer,1120+400*(1-out(p)),790,900,330,t,amber=.35,windows=10)

    elif bid in (20,21):
        draw_ticket(layer,480,540,600,210,holes=int(30*p),warning=False,angle=-5)
        if bid==20:
            draw_departure(layer,1300,520,750,270,"20 × 90","1,800 MINUTES",AMBER,flips=int(p*9))
        else:
            draw_departure(layer,1300,520,780,280,"30 HOURS","THE REAL GAP",AMBER,flips=int(p*10))
            for i in range(30):
                q=clamp(p*2-i/30)
                x=890+i*28; y=760-math.sin(i/29*math.pi)*115
                d.ellipse([x-5,y-5,x+5,y+5],fill=AMBER+(int(240*q),))

    elif bid in (22,23,24):
        human(layer,500,824,480,t,"stand","calm" if bid<24 else "envy")
        d.rounded_rectangle([1020,350,1570,750],24,fill=(13,16,21,245),outline=(73,82,94,240),width=5)
        if bid<24:
            pts=[]
            for i,v in enumerate([20,55,90,145,215,300]): pts.append((1080+i*82,690-v))
            d.line(pts,fill=GREEN+(255,),width=10,joint="curve")
            for x,y in pts:d.ellipse([x-8,y-8,x+8,y+8],fill=GREEN+(255,))
            draw_departure(layer,1295,630,430,92,"RESULT POSTED","PROOF",GREEN,flips=int(p*4))
        else:
            draw_departure(layer,1295,555,440,175,"LUCKY THA.","COMMENT 01",RED,flips=int(p*7))
            d.line([(1070,690),(1520,690)],fill=RED+(80,),width=2)

    elif bid==25:
        d.rectangle([0,145,W,900],fill=(3,3,5,242))
        for k in range(6):
            x=250+k*300
            a=120+80*math.sin(t*7+k)
            d.rectangle([x,160,x+12,860],fill=RED+(int(max(20,a*.25)),))
        title(layer,(960,535),"LEKIN SACH?",150,BONE,marker=True,glow_col=RED,maxw=1550)

    elif bid==26:
        human(layer,520,824,500,t,"stand","doubt")
        # opposite seat carries the viewer's own punched ticket; no shadow-double reuse
        d.rounded_rectangle([1190,575,1520,715],25,fill=(31,34,39,255),outline=(84,88,94,220),width=5)
        d.rounded_rectangle([1170,700,1540,758],18,fill=(39,41,45,255),outline=(84,88,94,220),width=5)
        draw_ticket(layer,1355,510,520,180,holes=30,warning=True,angle=4)
        draw_departure(layer,1355,790,590,105,"YOUR MISSED VERSION","SEAT 20",RED,flips=int(p*6))

    elif bid==27:
        human(layer,520,824,500,t,"stand","doubt")
        draw_ticket(layer,1290,515,650,220,holes=30,warning=True,angle=-3)
        draw_departure(layer,1290,755,700,115,"RESERVATION EXPIRES","DREAMS WAIT · SEATS DON'T",RED,flips=int(p*7))
        # red validity line physically burns away
        d.rectangle([1030,620,1030+520*(1-p),630],fill=RED+(230,))

    elif bid in (28,29,30,31):
        human(layer,500,824,500,t,"stand","resolve")
        if bid==28:
            draw_departure(layer,1300,500,720,260,"20:00","ACTION TICKET",GREEN,flips=int(p*7)); draw_ticket(layer,1300,750,530,175,holes=int(p*8),warning=False,angle=2)
        elif bid==29:
            draw_phone(layer,1300,730,460,False,0,flat=True); d.line([(1050,790),(1550,790)],fill=(85,86,89,220),width=6)
            draw_departure(layer,1300,490,600,150,"PHONE DOWN","STEP 1",GREEN,flips=int(p*5))
        elif bid==30:
            d.rounded_rectangle([1020,365,1580,760],22,fill=(17,20,25,245),outline=(74,82,91,240),width=5)
            draw_departure(layer,1300,430,460,105,"ONE TASK","STEP 2",GREEN,flips=int(p*4))
            for i,txt in enumerate(("OPEN IT","20 MIN","LEAVE PROOF")):
                y=545+i*70; d.rectangle([1080,y-16,1112,y+16],outline=GREEN+(220,),width=3)
                if i<int(p*4): d.line([(1085,y),(1096,y+11),(1110,y-13)],fill=GREEN+(255,),width=4)
                small(layer,(1140,y),txt,25,BONE,anchor="lm")
        else:
            draw_departure(layer,1300,535,720,280,"START","STEP 3",AMBER,flips=int(p*9)); glow(layer,(1300,535),330,AMBER,.18)

    elif bid==32:
        # departure board splits the future; same platform, two destinations
        draw_departure(layer,640,500,620,250,"PROOF","TRACK 1",GREEN,flips=int(p*8))
        draw_departure(layer,1300,500,620,250,"LUCKY?","TRACK 0",RED,flips=int(p*8))
        human(layer,770+out(p)*180,824,470,t,"walk","resolve")
        d.line([(960,300),(960,825)],fill=(81,87,96,130),width=3)
        draw_clock(layer,1640,690,125,t,"11:47")

    elif bid==33:
        train(layer,820,790,1100,360,t,amber=.65,windows=10)
        human(layer,500+out(p)*300,824,500,t,"walk","resolve")
        draw_ticket(layer,440,510,480,165,holes=30,warning=False,angle=-7)
        draw_departure(layer,1390,520,650,160,"SEAT 20","OWNER · YOU",AMBER,flips=int(p*7))

    elif bid==34:
        # first full amber practical in the world; thirty ticket holes become train windows
        train(layer,670,790,1250,380,t,amber=out(p*1.4),windows=10)
        human(layer,600+out(p)*270,824,500,t,"walk","calm")
        draw_ticket(layer,360,520,440,150,holes=30,warning=False,angle=-8)
        draw_departure(layer,1400,480,650,175,"BOARDING NOW","TRAIN STILL HERE",AMBER,flips=int(p*8))
        glow(layer,(1390,630),380,AMBER,.20*out(p))


def transition(layer,beat,t,col):
    lp=t-beat["t0"]
    if beat["id"]==1 or lp>.20:return
    q=out(lp/.20); d=ImageDraw.Draw(layer,"RGBA"); kind=beat["id"]%6
    if kind==0:
        x=W*(1-q); d.rectangle([x,130,W,900],fill=BLACK+(int(190*(1-q)),))
    elif kind==1:
        # train occlusion
        x=-W+q*W*2; d.polygon([(x,100),(x+600,100),(x+390,940),(x-210,940)],fill=(12,15,20,int(210*(1-q))))
    elif kind==2:
        for k in range(8):
            x=180+k*220; hh=(1-clamp(q-k*.025))*720
            d.rectangle([x,140,x+160,140+hh],fill=col+(int(110*(1-q)),))
    elif kind==3:
        d.rectangle([0,130,W,900],fill=BLACK+(int(190*(1-q)),))
        if q>.65:d.rectangle([0,460,W,570],fill=col+(int(90*(1-q)),))
    elif kind==4:
        r=q*1150; d.ellipse([960-r,535-r,960+r,535+r],outline=col+(int(170*(1-q)),),width=max(2,int(60*(1-q))))
    else:
        for k in range(12):
            y=150+k*60; x=min(W,W*(1-q)+(k%2)*160)
            d.rectangle([x,y,W,y+16],fill=col+(int(100*(1-q)),))


def _render_base_frame(i):
    t=i/FPS; idx=min(len(BEATS)-1,max(0,bisect.bisect_right(STARTS,t)-1)); beat=BEATS[idx]
    p=clamp((t-beat["t0"])/max(.001,beat["t1"]-beat["t0"]))
    bid=beat["id"]
    amber=out((t-64.59)/9.2)*.75 if t>64.59 else 0.0
    col=RED if bid in (1,2,5,6,11,24,25,26,27) else (AMBER if bid>=19 and bid not in (22,23,28,29,30) else (GREEN if bid in (22,23,28,29,30,31,32) else CYAN))
    im=station(t,bid,amber)
    scene(im,beat,t,p,col)
    caption_chrome(im,beat,t,col)
    transition(im,beat,t,col)
    d=ImageDraw.Draw(im,"RGBA"); d.text((W-72,H-38),f"{t:05.2f}s",font=font(17),fill=SLATE+(120,),anchor="rm")
    # restrained cinematic vignette
    vg=Image.new("RGBA",(W,H),(0,0,0,0)); vd=ImageDraw.Draw(vg)
    vd.rectangle([0,0,W,H],outline=(0,0,0,90),width=55)
    im.alpha_composite(vg)
    return im.convert("RGB")



# ---------------------------------------------------------------------------
# V2 NOIR IMAX TABAHI LAYER
# Deepens the existing platform into foreground/mid/background planes, adds
# motivated dolly/lens controls, real floor reflection, suspended rain depth,
# anamorphic practicals and five authored visual set pieces. Darkness remains
# controlled; the upgrade is spatial and cinematic rather than merely louder.
V2_WTF_BEATS={1,12,21,25,34}
V2_TRANSITIONS=(
    "printer_macro_depth","train_window_match","rail_occlusion_whip","split_flap_volume",
    "fluorescent_phase_cut","ticket_hole_constellation","reflection_roll","clock_shutter",
    "rain_freeze_orbit","amber_relay_bloom","platform_dolly_pass","carriage_portal",
)


def _beat_at(t):
    idx=min(len(BEATS)-1,max(0,bisect.bisect_right(STARTS,t)-1));b=BEATS[idx]
    return b,clamp((t-b["t0"])/max(.001,b["t1"]-b["t0"])),t-b["t0"]


def _camera_control(im,t,bid,p):
    # Deliberate dolly/tilt map: tension pulls backwards, action moves forward.
    tension=bid in (1,2,5,6,11,24,25,26,27)
    sign=-1 if tension else 1
    push=(ease(p)-.5)*sign
    scale=1.055+.018*math.sin(t*.31+bid*.72)+.032*push
    if bid in V2_WTF_BEATS:scale+=.025*math.sin(math.pi*p)
    scale=max(1.035,min(1.12,scale))
    dx=math.sin(t*.22+bid*1.17)*22+push*34
    dy=math.sin(t*.17+bid*.39)*11-push*7
    roll=.32*math.sin(t*.19+bid*.43)
    if bid in (12,25):roll+=.7*math.sin(math.pi*p)
    # Single affine lens solve: dolly, truck, pedestal and roll share one
    # resampling pass, preserving smoothness and removing needless blur.
    th=math.radians(roll);cs=math.cos(th)/scale;sn=math.sin(th)/scale;cx,cy=W/2,H/2
    matrix=(cs,sn,cx-cs*cx-sn*cy+dx,-sn,cs,cy+sn*cx-cs*cy+dy)
    return im.transform((W,H),Image.Transform.AFFINE,matrix,Image.Resampling.BICUBIC,fillcolor=BLACK)


@lru_cache(maxsize=16)
def _atmos_plate(tick,bid):
    rng=np.random.default_rng(93000+tick+bid*503)
    sm=Image.new("RGBA",(480,270),(0,0,0,0));d=ImageDraw.Draw(sm,"RGBA")
    # Layered fog banks, not a full-frame wash.
    for k in range(7):
        x=int(rng.uniform(-80,560));y=int(rng.uniform(90,250));rx=int(rng.uniform(70,180));ry=int(rng.uniform(10,35))
        d.ellipse([x-rx,y-ry,x+rx,y+ry],fill=CYAN+(int(rng.uniform(5,15)),))
    return sm.filter(ImageFilter.GaussianBlur(18))


def _floor_reflection(layer,t,bid):
    # Reflect the actual performance/prop state into the wet floor.
    strip=layer.crop((0,430,W,805)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    strip=strip.resize((W,250),Image.Resampling.BILINEAR).filter(ImageFilter.GaussianBlur(8))
    a=strip.getchannel("A").point(lambda q:int(q*.19));strip.putalpha(a)
    layer.alpha_composite(strip,(0,780))
    d=ImageDraw.Draw(layer,"RGBA")
    for k in range(9):
        y=805+k*26+6*math.sin(t*.8+k)
        d.line([(120,y),(1800,y-25)],fill=CYAN+(12+k%3*5,),width=2)


def _lens_and_rain(layer,t,bid,p,col):
    d=ImageDraw.Draw(layer,"RGBA")
    # Anamorphic practicals tied to platform lights.
    flick=.55+.45*math.sin(t*1.2+bid)
    for x in (420,920,1420):
        y=150+5*math.sin(t*.4+x)
        d.line([(x-270,y),(x+270,y)],fill=col+(int(13+18*flick),),width=2)
        d.ellipse([x-5,y-5,x+5,y+5],fill=BONE+(55,))
    # Three rain depth planes: far streaks are already in station(); these are
    # mid streaks and near-lens bokeh with opposing parallax.
    for k in range(34):
        x=(k*173+int(t*(120+7*(k%4)))+bid*29)%W
        y=(k*101+int(t*(210+9*(k%3))))%820+130
        ln=28+(k%5)*11
        d.line([(x,y),(x-8,y+ln)],fill=CYAN+(28+(k%4)*9,),width=1+(k%2))
    for k in range(10):
        x=(k*347-int(t*(42+k)))%(W+160)-80;y=250+(k*149)%610
        r=10+(k%4)*8;d.ellipse([x-r,y-r,x+r,y+r],outline=CYAN+(18+(k%3)*10,),width=2)
    # Moving foreground columns create real occlusion and depth.
    for side in (-1,1):
        x=(-105 if side<0 else W+105)+side*math.sin(t*.16+bid)*70
        ww=88+20*math.sin(t*.13+bid)
        d.rectangle([x-ww,210,x+ww,920],fill=BLACK+(115,),outline=SLATE+(24,),width=3)


def _setpiece(layer,t,bid,p,col):
    d=ImageDraw.Draw(layer,"RGBA");pulse=math.sin(math.pi*p)
    if bid==1:
        # Printer macro: ticket travels through a mechanical Z tunnel.
        for k in range(11,0,-1):
            u=k/11;ww=260+u*1000;hh=75+u*300
            d.rounded_rectangle([960-ww/2,535-hh/2,960+ww/2,535+hh/2],int(12+u*32),outline=RED+(int((12+50*(1-u))*pulse),),width=max(2,int(2+u*6)))
        scan=-180+(W+360)*ease(p);d.rectangle([scan-7,260,scan+7,810],fill=RED+(80,))
        glow(layer,(scan,535),90,RED,.10*pulse)
    elif bid==12:
        # Passing carriage windows become the dopamine tunnel.
        for k in range(12):
            u=((k/12+t*.58)%1);z=1/(.18+u)
            ww=95+u*1180;hh=55+u*520
            c=(RED,CYAN,AMBER,GREEN)[k%4]
            d.rounded_rectangle([960-ww/2,535-hh/2,960+ww/2,535+hh/2],int(12+u*34),outline=c+(int(18+u*55),),width=max(2,int(2+u*7)))
        d.line([(0,535),(W,535)],fill=BONE+(35,),width=2)
    elif bid==21:
        # Ticket holes lift into a volumetric constellation then line up as windows.
        pts=[]
        for k in range(30):
            q=clamp(p*1.6-k/38);a=k/30*math.tau+t*.12
            x=960+math.cos(a)*(190+150*q);y=535+math.sin(a)*(80+120*q)-q*120
            z=5+int(11*q);pts.append((x,y))
            # One-pass halo: avoid thirty full-canvas blur allocations per frame.
            d.ellipse([x-22,y-22,x+22,y+22],fill=AMBER+(int(5+18*q),))
            d.ellipse([x-z,y-z,x+z,y+z],fill=AMBER+(int(70+170*q),))
        for a,b in zip(pts,pts[1:]):d.line([a,b],fill=AMBER+(22,),width=2)
    elif bid==25:
        # Rain freezes in midair while the platform camera orbits the truth card.
        for k in range(90):
            a=k/90*math.tau;rr=120+(k%11)*31
            x=960+math.cos(a+t*.05)*rr;y=535+math.sin(a)*rr*.48
            d.ellipse([x-2,y-6,x+2,y+6],fill=CYAN+(55+(k%3)*18,))
        for r in (180,280,390):d.arc([960-r,535-r*.5,960+r,535+r*.5],15+40*p,150+40*p,fill=RED+(65,),width=4)
    elif bid==34:
        # Carriage portal: platform lines and 30 holes converge through the door.
        vp=(1410,540)
        for k in range(14):
            x=k*150;d.line([(x,H),(vp[0]+(k-7)*19,vp[1])],fill=AMBER+(25+int(70*p),),width=3)
        for k in range(30):
            q=clamp(p*1.7-k/40);x=950+(k%10)*76;y=430+(k//10)*62
            rr=3+int(6*q);d.ellipse([x-rr,y-rr,x+rr,y+rr],fill=AMBER+(int(55+185*q),))
        glow(layer,(1410,590),360,AMBER,.18*p)


def _transition_energy(layer,lp,bid,col):
    if bid==1 or lp>.18:return
    q=1-out(lp/.18)
    # Directional frame echo mimics a precision shutter/rail whip, not shake.
    ghost=ImageChops.offset(layer,int((52+bid%3*13)*q*((-1)**bid)),0)
    ghost=ghost.filter(ImageFilter.GaussianBlur(max(1,int(5*q))))
    return Image.blend(layer,ghost,.10*q)


def render_frame(i):
    t=i/FPS;beat,p,lp=_beat_at(t);bid=beat["id"]
    amber=out((t-64.59)/9.2)*.75 if t>64.59 else 0.0
    col=RED if bid in (1,2,5,6,11,24,25,26,27) else (AMBER if bid>=19 and bid not in (22,23,28,29,30) else (GREEN if bid in (22,23,28,29,30,31,32) else CYAN))
    base=_render_base_frame(i).convert("RGBA")
    base=_camera_control(base,t,bid,p)
    _floor_reflection(base,t,bid)
    atmos=_atmos_plate(int(t*4)%16,bid).resize((W,H),Image.Resampling.BICUBIC)
    base=Image.alpha_composite(base,atmos)
    fx=Image.new("RGBA",(W,H),(0,0,0,0))
    _lens_and_rain(fx,t,bid,p,col)
    _setpiece(fx,t,bid,p,col)
    # Motivated volumetric shaft shifts from cyan to amber only after action.
    fd=ImageDraw.Draw(fx,"RGBA");sx=360+(t*.9%1)*1180
    c=AMBER if t>=64.59 else CYAN
    fd.polygon([(sx-80,135),(sx+70,135),(sx+430,900),(sx-310,900)],fill=c+((13 if bid not in V2_WTF_BEATS else 24),))
    outim=Image.alpha_composite(base,fx)
    tr=_transition_energy(outim,lp,bid,col)
    if tr is not None:outim=tr
    # Cinemascope aperture breathes only at truth/finale; output remains 16:9.
    if bid in (25,34):
        bars=int(20+34*math.sin(math.pi*p));dd=ImageDraw.Draw(outim,"RGBA")
        dd.rectangle([0,0,W,bars],fill=BLACK+(245,));dd.rectangle([0,H-bars,W,H],fill=BLACK+(245,))
    # Restrained noir grade: richer blacks, protected practicals.
    rgb=ImageEnhance.Contrast(outim.convert("RGB")).enhance(1.075)
    return ImageEnhance.Color(rgb).enhance(.93 if t<64.59 else 1.04)

def ffmpeg_exe():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def render_video(path,start=0,end=None):
    end=NF if end is None else min(NF,end); path.parent.mkdir(parents=True,exist_ok=True)
    cmd=[ffmpeg_exe(),"-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-an","-c:v","libx264","-preset","medium","-threads","1","-crf","19","-pix_fmt","yuv420p","-movflags","+faststart",str(path)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.DEVNULL); began=time.time()
    try:
        for i in range(start,end):
            proc.stdin.write(render_frame(i).tobytes())
            if (i-start)%48==0:
                el=time.time()-began; rate=(i-start+1)/max(.001,el); eta=(end-i-1)/max(.001,rate)
                print(f"WF03-V2 frame {i+1}/{end} · {rate:.1f} fps · ETA {eta/60:.1f} min",flush=True)
    finally:
        if proc.stdin:proc.stdin.close()
    rc=proc.wait()
    if rc:raise SystemExit(f"ffmpeg failed: {rc}")


def contact_sheet(path):
    times=[.7,3.3,7.7,14.9,19.5,23.5,29.4,37.4,41.2,49.7,60.8,72.7]
    cw,ch=480,270; sheet=Image.new("RGB",(cw*4,ch*3+72),(4,5,8)); d=ImageDraw.Draw(sheet)
    for k,t in enumerate(times):
        fr=render_frame(int(t*FPS)).resize((cw,ch),Image.Resampling.LANCZOS)
        x=(k%4)*cw;y=(k//4)*ch;sheet.paste(fr,(x,y))
        d.rectangle([x,y,x+94,y+29],fill=(4,5,7));d.text((x+8,y+15),f"{t:04.1f}s",font=font(18),fill=BONE,anchor="lm")
    d.text((30,ch*3+39),"WF-03 V2 · TUMHARI RESERVED SEAT · NOIR IMAX TABAHI LOOK SHEET",font=font(27),fill=BONE,anchor="lm")
    path.parent.mkdir(parents=True,exist_ok=True);sheet.save(path,quality=92,subsampling=0)


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",type=Path);ap.add_argument("--still",type=float);ap.add_argument("--still-output",type=Path);ap.add_argument("--sheet",action="store_true");ap.add_argument("--sheet-output",type=Path,default=PROJECT/"artifacts"/"LOOK_SHEET_WF03_V2.jpg");ap.add_argument("--start-frame",type=int,default=0);ap.add_argument("--end-frame",type=int)
    a=ap.parse_args()
    if a.still is not None:
        p=a.still_output or PROJECT/"artifacts"/f"still_{a.still:.2f}.png";p.parent.mkdir(parents=True,exist_ok=True);render_frame(int(clamp(a.still,0,DUR-.001)*FPS)).save(p);print(p);return
    if a.sheet:contact_sheet(a.sheet_output);print(a.sheet_output);return
    render_video(a.output or REPO/"build"/"tumhari-seat-wf03-v2-mute.mp4",a.start_frame,a.end_frame)

if __name__=="__main__":main()
