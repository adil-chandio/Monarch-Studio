#!/usr/bin/env python3
"""WF-01 picture renderer — TUMHARI RESERVED SEAT.

Deterministic 1920x1080 / 30 fps / 74 s paper-ink-SHADE film. The selected
voice is never altered here; picture is cut to MASTER_TIMELINE.json. Output is
mute by design and is muxed with the independently generated WF-01 mix.
"""
from __future__ import annotations

import argparse
import bisect
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
STYLE = PROJECT.parents[1]
REPO = STYLE.parents[1]
sys.path.insert(0, str(STYLE / "src"))
import toon as T  # noqa: E402
import shade as SH  # noqa: E402

W, H, FPS = 1920, 1080, 30
TIMELINE = json.loads((PROJECT / "MASTER_TIMELINE.json").read_text())
DUR = float(TIMELINE["picture_duration_s"])
NF = int(round(DUR * FPS))
BEATS = TIMELINE["beats"]
STARTS = [float(b["t0"]) for b in BEATS]

PAPER = (244, 238, 225)
PAPER_D = (231, 222, 204)
INK = (27, 25, 29)
SOFT = (103, 94, 84)
RED = (190, 42, 43)
GOLD = (184, 120, 8)
CYAN = (9, 112, 126)
MINT = (28, 128, 76)
INDIGO = (50, 61, 122)
ACCENTS = [RED, GOLD, CYAN, INDIGO, MINT]
FONT_DIR = STYLE / "fonts"
_FONTS: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def clamp(x: float, a: float = 0.0, b: float = 1.0) -> float:
    return max(a, min(b, x))


def ease(x: float) -> float:
    x = clamp(x)
    return x * x * (3 - 2 * x)


def out(x: float, p: float = 3.0) -> float:
    return 1 - (1 - clamp(x)) ** p


def back(x: float, s: float = 1.12) -> float:
    x = clamp(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def font(size: int, display: bool = False) -> ImageFont.FreeTypeFont:
    name = "PermanentMarker.ttf" if display else "Montserrat-VF.ttf"
    key = (name, int(size))
    if key not in _FONTS:
        _FONTS[key] = ImageFont.truetype(str(FONT_DIR / name), int(size))
    return _FONTS[key]


def fit_font(text: str, max_width: float, start: int, minimum: int = 28, display: bool = False):
    size = start
    while size > minimum:
        f = font(size, display)
        if f.getlength(text) <= max_width:
            return f
        size -= 2
    return font(minimum, display)


def make_paper() -> Image.Image:
    rng = np.random.default_rng(20261011)
    small = np.zeros((H // 3, W // 3, 3), np.float32)
    small[:] = PAPER
    noise = rng.normal(0, 4.0, (H // 3, W // 3, 1))
    small += noise
    im = Image.fromarray(np.clip(small, 0, 255).astype(np.uint8)).resize((W, H), Image.Resampling.BICUBIC)
    d = ImageDraw.Draw(im, "RGBA")
    for _ in range(1500):
        x = int(rng.integers(0, W)); y = int(rng.integers(0, H))
        r = int(rng.integers(1, 4)); a = int(rng.integers(2, 10))
        d.ellipse([x-r, y-r, x+r, y+r], fill=(75, 63, 50, a))
    d.rectangle([0, 824, W, H], fill=PAPER_D + (255,))
    d.line([(0, 824), (W, 824)], fill=(194, 180, 157, 180), width=3)
    return im.convert("RGBA")


def make_vignette() -> Image.Image:
    yy, xx = np.mgrid[0:H, 0:W]
    dx = (xx - W/2)/(W/2); dy = (yy - H/2)/(H/2)
    a = np.clip((dx*dx + dy*dy - .28) * 23, 0, 22).astype(np.uint8)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., 3] = a
    return Image.fromarray(arr, "RGBA")


PAPER_BG = make_paper()
VIGNETTE = make_vignette()


def accent_for(bid: int):
    if bid <= 2: return RED
    if bid <= 7: return INDIGO
    if bid <= 15: return CYAN
    if bid <= 21: return GOLD
    if bid <= 27: return RED
    return MINT if bid < 33 else GOLD


def text_extruded(layer: Image.Image, xy, text: str, size: int, col=INK, anchor="mm",
                  max_width=1650, display=False, depth=7, glow=None, alpha=255):
    d = ImageDraw.Draw(layer, "RGBA")
    f = fit_font(text, max_width, size, display=display)
    x, y = xy
    if glow:
        tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        td = ImageDraw.Draw(tmp)
        td.text((x, y), text, font=f, fill=glow + (120,), anchor=anchor, stroke_width=2)
        tmp = tmp.filter(ImageFilter.GaussianBlur(16))
        layer.alpha_composite(tmp)
    side = tuple(int(c * .45) for c in col)
    for k in range(depth, 0, -1):
        d.text((x + k*.85, y + k*1.1), text, font=f, fill=side + (int(alpha*.9),), anchor=anchor)
    d.text((x, y), text, font=f, fill=col + (alpha,), anchor=anchor,
           stroke_width=max(1, size//55), stroke_fill=(246, 241, 231, min(alpha, 210)))


def label(layer, xy, text, size=28, col=SOFT, anchor="mm", box=False):
    d = ImageDraw.Draw(layer, "RGBA")
    f = fit_font(text, 800, size, minimum=18)
    if box:
        b = d.textbbox(xy, text, font=f, anchor=anchor, stroke_width=0)
        d.rounded_rectangle([b[0]-18, b[1]-9, b[2]+18, b[3]+9], 18,
                            fill=(247, 242, 232, 225), outline=col+(160,), width=3)
    d.text(xy, text, font=f, fill=col+(255,), anchor=anchor)


def rounded_line(d, pts, col, width):
    d.line(pts, fill=col, width=width, joint="curve")
    r = width/2
    for x, y in (pts[0], pts[-1]):
        d.ellipse([x-r, y-r, x+r, y+r], fill=col)


def draw_seat(layer, x, y, s, col=INK, glow=0.0, occupied=False):
    d = ImageDraw.Draw(layer, "RGBA")
    if glow:
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        gd.ellipse([x-s*.8, y-s*1.8, x+s*.8, y+s*.22], fill=GOLD+(int(80*glow),))
        g = g.filter(ImageFilter.GaussianBlur(int(s*.34)))
        layer.alpha_composite(g)
    w = max(3, int(s*.045))
    d.rounded_rectangle([x-s*.42, y-s*1.22, x+s*.42, y-s*.46], int(s*.10),
                        fill=(235, 225, 207, 255), outline=col+(255,), width=w)
    d.rounded_rectangle([x-s*.5, y-s*.52, x+s*.5, y-s*.28], int(s*.10),
                        fill=(222, 210, 190, 255), outline=col+(255,), width=w)
    rounded_line(d, [(x-s*.38, y-s*.28), (x-s*.45, y+s*.05)], col+(255,), w)
    rounded_line(d, [(x+s*.38, y-s*.28), (x+s*.45, y+s*.05)], col+(255,), w)
    if occupied:
        d.ellipse([x-s*.16, y-s*1.12, x+s*.16, y-s*.80], fill=INK+(210,))
        d.rounded_rectangle([x-s*.24, y-s*.82, x+s*.24, y-s*.37], int(s*.12), fill=INK+(210,))


def draw_phone(layer, x, y, s, face_up=True, progress=1.0, scroll=0.0):
    d = ImageDraw.Draw(layer, "RGBA")
    w, h = s*.54, s
    if not face_up:
        h *= max(.10, 1-progress*.86)
    d.rounded_rectangle([x-w/2, y-h/2, x+w/2, y+h/2], int(max(6, s*.08)),
                        fill=(25, 26, 31, 255), outline=(76, 78, 86, 255), width=max(3, int(s*.03)))
    if face_up and h > s*.4:
        d.rounded_rectangle([x-w*.39, y-h*.42, x+w*.39, y+h*.42], int(s*.05), fill=(32, 55, 69, 255))
        for i in range(4):
            yy = y-h*.30 + ((i*.20 + scroll) % .82)*h
            c = [CYAN, RED, GOLD, MINT][i]
            d.rounded_rectangle([x-w*.30, yy-h*.07, x+w*.30, yy+h*.07], int(s*.025), fill=c+(210,))
        d.ellipse([x-s*.015, y-h*.47, x+s*.015, y-h*.44], fill=(180, 185, 190, 230))


def draw_timer(layer, x, y, r, value, p, col=CYAN):
    d = ImageDraw.Draw(layer, "RGBA")
    d.ellipse([x-r, y-r, x+r, y+r], fill=(250, 247, 240, 235), outline=(184, 174, 159, 220), width=14)
    start = -90; end = start + 359*clamp(p)
    d.arc([x-r+16, y-r+16, x+r-16, y+r-16], start, end, fill=col+(255,), width=22)
    text_extruded(layer, (x, y-4), value, int(r*.45), col, depth=4, max_width=r*1.4)
    d.ellipse([x-7, y-r+27, x+7, y-r+41], fill=col+(255,))


def draw_clock(layer, x, y, s, txt="11:47 PM", col=INDIGO, t=0.0):
    d = ImageDraw.Draw(layer, "RGBA")
    d.rounded_rectangle([x-s*.85, y-s*.32, x+s*.85, y+s*.32], int(s*.08),
                        fill=(34, 34, 41, 255), outline=col+(255,), width=max(4, int(s*.028)))
    f = fit_font(txt, s*1.5, int(s*.26), minimum=28)
    d.text((x, y), txt, font=f, fill=(239, 242, 247, 255), anchor="mm")
    if int(t*2)%2 == 0:
        d.ellipse([x+s*.70, y-s*.06, x+s*.74, y-s*.02], fill=RED+(255,))


def draw_ticket(layer, x, y, w, h, holes=0, col=GOLD, alpha=255, rotate=0):
    ticket = Image.new("RGBA", (int(w*1.4), int(h*1.8)), (0,0,0,0))
    d = ImageDraw.Draw(ticket, "RGBA")
    ox, oy = ticket.width/2, ticket.height/2
    d.rounded_rectangle([ox-w/2, oy-h/2, ox+w/2, oy+h/2], int(h*.12),
                        fill=(249, 242, 222, alpha), outline=col+(alpha,), width=max(3,int(h*.045)))
    d.line([(ox-w*.18, oy-h/2), (ox-w*.18, oy+h/2)], fill=col+(int(alpha*.5),), width=3)
    d.text((ox-w*.33, oy), "20", font=fit_font("20", w*.22, int(h*.38)), fill=INK+(alpha,), anchor="mm")
    d.text((ox+w*.14, oy-h*.12), "RESERVED", font=fit_font("RESERVED", w*.44, int(h*.17)), fill=INK+(alpha,), anchor="mm")
    d.text((ox+w*.14, oy+h*.15), "SEAT · 90 DAYS", font=fit_font("SEAT · 90 DAYS", w*.46, int(h*.11)), fill=SOFT+(alpha,), anchor="mm")
    for i in range(holes):
        a = i/30*math.tau
        hx = ox+w*.15+math.cos(a)*w*.27
        hy = oy+math.sin(a)*h*.28
        rr = max(2, int(h*.024))
        d.ellipse([hx-rr,hy-rr,hx+rr,hy+rr], fill=(35,31,30,alpha))
    if rotate:
        ticket = ticket.rotate(rotate, Image.Resampling.BICUBIC, expand=False)
    layer.alpha_composite(ticket, (int(x-ticket.width/2), int(y-ticket.height/2)))


def draw_train(layer, x, y, w, h, light=1.0):
    d = ImageDraw.Draw(layer, "RGBA")
    d.rounded_rectangle([x, y-h, x+w, y], int(h*.15), fill=(53, 57, 65, 255), outline=INK+(255,), width=8)
    d.rounded_rectangle([x+w*.82, y-h*.92, x+w*.98, y-h*.10], int(h*.08), fill=(37, 41, 48, 255))
    n = 8
    for i in range(n):
        wx = x+w*.05+i*w*.095
        col = tuple(int(PAPER[j]*(1-light)+GOLD[j]*light) for j in range(3))
        d.rounded_rectangle([wx, y-h*.72, wx+w*.065, y-h*.36], int(h*.025), fill=col+(235,), outline=(20,20,22,255), width=3)
    for xx in (x+w*.20, x+w*.75):
        d.ellipse([xx-h*.12,y-h*.10,xx+h*.12,y+h*.14], fill=INK+(255,))
        d.ellipse([xx-h*.06,y-h*.04,xx+h*.06,y+h*.08], fill=(121,119,116,255))


def draw_shade(layer: Image.Image, x, y, s, pose, expr="neutral", p=1.0, look=(0,0), alpha=1.0, flip=False):
    char = Image.new("RGBA", (W, H), (0,0,0,0))
    d = ImageDraw.Draw(char, "RGBA")
    SH.shade(d, x, y, s, pose, expr=expr, p=p, look=look, blink=0.0, flip=flip)
    if alpha < 1:
        a = char.getchannel("A").point(lambda q: int(q*alpha))
        char.putalpha(a)
    layer.alpha_composite(char)


def pose(kind: str, t: float):
    if kind == "sad": return T.p_sad(t)
    if kind == "think": return T.p_think(t)
    if kind == "point": return T.p_point(t, up=False, right=True)
    if kind == "present": return T.p_present(t)
    if kind == "type": return T.p_type(t)
    if kind == "cheer": return T.p_cheer(t)
    if kind == "walk": return T.p_walk(t*1.15)
    if kind == "hold": return T.p_hold(t)
    return T.p_idle(t)


def base_world(t: float, bid: int, acc) -> Image.Image:
    # Six background updates per second are enough for drifting paper light;
    # character/type/camera motion still updates on every output frame.
    return _base_world_q(int(t * 6), bid, tuple(acc)).copy()


@lru_cache(maxsize=20)
def _base_world_q(tick: int, bid: int, acc) -> Image.Image:
    t = tick / 6.0
    im = PAPER_BG.copy()
    d = ImageDraw.Draw(im, "RGBA")
    # moving blueprint grid and sparse paper geometry
    off = int((t*14) % 96)
    for x in range(-off, W, 96):
        d.line([(x, 145), (x, 824)], fill=acc+(10,), width=1)
    for y in range(160+off//2, 824, 96):
        d.line([(0, y), (W, y)], fill=acc+(8,), width=1)
    for k in range(18):
        x = (k*337 + int(t*(7+k%3))) % (W+160)-80
        y = 170 + ((k*149 + int(t*(3+k%2))) % 610)
        r = 2 + k%3
        d.ellipse([x-r,y-r,x+r,y+r], fill=acc+(25+k%4*5,))
    # one broad drifting wash
    wash = Image.new("RGBA", (W//4, H//4), (0,0,0,0)); wd=ImageDraw.Draw(wash)
    cx=(W*(.18+.64*((math.sin(t*.12+bid)+1)/2)))/4; cy=(H*(.28+.20*math.sin(t*.09)))/4
    wd.ellipse([cx-210,cy-160,cx+210,cy+160], fill=acc+(16,))
    wash=wash.filter(ImageFilter.GaussianBlur(60)).resize((W,H),Image.Resampling.BICUBIC)
    im.alpha_composite(wash)
    return im


def draw_caption_and_chrome(layer, beat, t, acc):
    d = ImageDraw.Draw(layer, "RGBA")
    bid=beat["id"]
    d.rounded_rectangle([84,68,W-84,74],3,fill=(206,196,178,200))
    xp=84+(W-168)*clamp(t/DUR)
    d.rounded_rectangle([84,67,xp,75],4,fill=acc+(255,))
    d.ellipse([xp-7,64,xp+7,78],fill=acc+(255,))
    d.text((84,112),f"WF-01 · {bid:02d}/34",font=font(22),fill=acc+(255,),anchor="lm")
    d.text((W-84,112),"TUMHARI RESERVED SEAT",font=font(21),fill=SOFT+(240,),anchor="rm")
    # headline with local entry movement
    lp=clamp((t-beat["t0"])/max(.01,beat["t1"]-beat["t0"]))
    yy=190+(1-out(lp*3))*28
    text_extruded(layer,(W/2,yy),beat["caption"],76,acc,depth=5,max_width=1600,glow=acc if bid in (1,7,19,21,25,33,34) else None)
    # subtitle story label; small and quiet
    d.text((W/2,1003),beat["story"].upper(),font=fit_font(beat["story"].upper(),1450,24,18),fill=SOFT+(225,),anchor="mm")


def scene(layer: Image.Image, beat, t: float, p: float, acc):
    bid=beat["id"]
    d=ImageDraw.Draw(layer,"RGBA")
    gy=824
    pulse=.5+.5*math.sin(t*math.tau*1.15)

    if bid in (1,2):
        draw_seat(layer,1300,gy,330,col=INK,glow=out(p)*(.45+.55*pulse))
        draw_shade(layer,520,gy,520,pose("think" if bid==1 else "point",t),"worried" if bid==1 else "determined",p=out(p*2.5))
        if bid==1:
            text_extruded(layer,(1300,555),"?",220,RED,depth=10,glow=RED,max_width=350)
        else:
            draw_ticket(layer,1300,590,470,190,holes=int(6*p),col=RED,rotate=-4+2*math.sin(t))
            label(layer,(1300,740),"NOT HELD FOREVER",28,RED,box=True)

    elif bid in (3,4,5):
        draw_shade(layer,500,gy,500,pose("idle",t),"worried",p=out(p*3))
        if bid==3:
            for k in range(5):
                r=90+k*62+18*math.sin(t*2+k)
                d.arc([1220-r,560-r,1220+r,560+r],-75,210,fill=RED+(170-k*20,),width=8)
            text_extruded(layer,(1220,560),"NOW",150,RED,depth=8,glow=RED,max_width=600)
        elif bid==4:
            draw_shade(layer,1400,gy,500,pose("idle",t+.18),"focus",p=out(p*2),alpha=.78,flip=True)
            rounded_line(d,[(960,340),(960,800)],INDIGO+(150,),5)
            label(layer,(500,720),"YOU",34,INDIGO,box=True); label(layer,(1400,720),"SAME AGE",34,INDIGO,box=True)
        else:
            chips=[("GHAR KA PRESSURE",(1120,410)),("BILLS",(1430,560)),("CONFUSION",(1080,700)),("TALENT?",(1510,760))]
            for i,(txt,xy) in enumerate(chips):
                q=clamp((p*1.5-i*.12))
                if q>0: label(layer,(xy[0],xy[1]+(1-out(q))*30),txt,30,RED if i<3 else SOFT,box=True)
            for i in range(6):
                a=i/6*math.tau+t*.2
                d.line([(520,510),(520+math.cos(a)*250,510+math.sin(a)*210)],fill=RED+(45,),width=3)

    elif bid in (6,7):
        draw_shade(layer,460,gy,510,pose("think" if bid==6 else "point",t),"think" if bid==6 else "determined",p=out(p*2.5))
        if bid==6:
            d.ellipse([1180,360,1500,680],outline=INDIGO+(220,),width=14)
            for a in np.linspace(0,math.tau,12,endpoint=False):
                d.line([(1340+math.cos(a)*180,520+math.sin(a)*180),(1340+math.cos(a)*225,520+math.sin(a)*225)],fill=INDIGO+(160,),width=7)
            d.line([(1210,390),(1470,650)],fill=RED+(255,),width=22)
            d.line([(1470,390),(1210,650)],fill=RED+(255,),width=22)
        else:
            draw_timer(layer,1330,550,245,"+20:00",p,INDIGO)
            d.arrow if False else None
            label(layer,(1330,790),"NOT GENIUS · JUST AHEAD",28,INDIGO,box=True)

    elif bid in (8,9,10):
        if bid==8:
            draw_shade(layer,570,gy,470,pose("idle",t),"neutral",p=out(p*3))
            draw_shade(layer,1360,gy,470,pose("idle",t+.2),"neutral",p=out(p*3),flip=True)
            rounded_line(d,[(960,320),(960,824)],RED+(170,),7)
            label(layer,(570,720),"SAME NIGHT",26,SOFT,box=True); label(layer,(1360,720),"SAME CHOICE",26,SOFT,box=True)
        elif bid==9:
            draw_clock(layer,960,545,390,"11:47 PM",INDIGO,t)
            draw_shade(layer,340,gy,390,pose("think",t),"tired" if "tired" in SH.EXPR else "sad",p=out(p*2))
            draw_shade(layer,1580,gy,390,pose("think",t+.2),"focus",p=out(p*2),flip=True)
        else:
            draw_phone(layer,620,565,380,True,scroll=t*.12)
            draw_phone(layer,1300,565,380,True,scroll=t*.12)
            rounded_line(d,[(960,350),(960,790)],INDIGO+(120,),4)

    elif bid in (11,12,13):
        if bid==11:
            draw_phone(layer,960,560,500,True,scroll=t*.38)
            for k in range(3):
                text_extruded(layer,(1320+k*30,490+k*48),"1",90,RED,depth=4,max_width=150,alpha=max(50,220-k*55))
        elif bid==12:
            # tunnel of feed cards rushing toward lens
            for k in range(11,0,-1):
                u=(k/11 + t*.45)%1
                ww=160+u*980; hh=90+u*520
                a=int(40+u*150)
                d.rounded_rectangle([960-ww/2,540-hh/2,960+ww/2,540+hh/2],int(20+u*45),outline=ACCENTS[k%5]+(a,),width=max(2,int(3+u*9)))
            draw_shade(layer,960,gy,350,pose("sad",t),"worried",p=1)
        else:
            draw_shade(layer,520,gy,480,pose("present",t),"determined",p=out(p*2))
            draw_phone(layer,1270,650,430,face_up=False,progress=out(p),scroll=0)
            d.line([(1110,790),(1450,790)],fill=INK+(100,),width=5)
            label(layer,(1270,720),"FLIP THE CHOICE",26,CYAN,box=True)

    elif bid in (14,15):
        draw_timer(layer,1260,545,255,"20:00" if bid==14 else "19:59",p if bid==14 else 1,CYAN)
        draw_shade(layer,520,gy,520,pose("point" if bid==14 else "type",t),"focus",p=out(p*2.3))
        if bid==15:
            d.rounded_rectangle([1010,730,1510,792],31,fill=MINT+(220,),outline=INK+(255,),width=5)
            d.rectangle([1024,744,1024+460*out(p),778],fill=(246,244,235,230))
            label(layer,(1260,761),"WORK SESSION STARTED",24,INK)

    elif bid in (16,17,18,19):
        day={16:1,17:10,18:30,19:90}[bid]
        col={16:SOFT,17:CYAN,18:INDIGO,19:GOLD}[bid]
        # stairs + calendar stack
        for k in range(6):
            x=340+k*210; h=70+k*60
            d.rounded_rectangle([x,gy-h,x+170,gy],16,fill=tuple(int(PAPER_D[j]*(1-k/8)+col[j]*(k/8)) for j in range(3))+(240,),outline=INK+(180,),width=4)
            if k<=int(p*6): label(layer,(x+85,gy-h/2),str(min(day,max(1,int(day*k/5)))),24,col)
        x=350+out(p)*1050; y=gy-(80+out(p)*300)
        draw_shade(layer,x,y+80,300,pose("walk",t),"focus",p=1)
        text_extruded(layer,(1500,540),f"DAY {day}",145,col,depth=9,glow=col if bid==19 else None,max_width=600)
        sub={16:"NO VISIBLE GAP",17:"CONFIDENCE",18:"REAL SKILL",19:"THE GAP IS REAL"}[bid]
        label(layer,(1500,690),sub,30,col,box=True)

    elif bid in (20,21):
        draw_ticket(layer,430,590,430,180,holes=int(30*p),col=GOLD,rotate=-7)
        if bid==20:
            text_extruded(layer,(1180,510),"20 × 90",190,GOLD,depth=12,glow=GOLD,max_width=950)
            label(layer,(1180,690),"1,800 MINUTES",36,SOFT,box=True)
        else:
            text_extruded(layer,(1180,500),"30 HOURS",205,GOLD,depth=13,glow=GOLD,max_width=1050)
            # graph made of ticket punches
            for k in range(30):
                q=clamp(p*2-k/30)
                if q<=0: continue
                x=720+k*31; yy=760-(k/29)**1.35*185
                d.ellipse([x-6,yy-6,x+6,yy+6],fill=GOLD+(int(255*q),))

    elif bid in (22,23,24):
        draw_shade(layer,520,gy,500,pose("present" if bid<24 else "think",t),"proud" if bid<24 else "worried",p=out(p*2))
        d.rounded_rectangle([950,350,1590,770],28,fill=(251,247,239,245),outline=INK+(255,),width=7)
        d.rectangle([990,390,1550,520],fill=(30,35,43,255))
        if bid in (22,23):
            xs=[1030,1120,1210,1300,1390,1480]; vals=[50,90,120,170,240,315]
            d.line(list(zip(xs,[720-v for v in vals])),fill=MINT+(255,),width=12,joint="curve")
            for x,v in zip(xs,vals): d.ellipse([x-10,710-v,x+10,730-v],fill=MINT+(255,))
            label(layer,(1270,585),"RESULT POSTED",34,MINT,box=True)
            label(layer,(1270,675),"EARNED, NOT MAGIC",25,SOFT)
        else:
            d.rounded_rectangle([1020,560,1520,685],35,fill=(238,232,220,255),outline=RED+(255,),width=5)
            text_extruded(layer,(1270,623),'“LUCKY THA.”',64,RED,depth=4,max_width=430)
            for i in range(3):
                d.ellipse([1030+i*36,720,1050+i*36,740],fill=SOFT+(120+i*30,))

    elif bid==25:
        d.rectangle([0,145,W,824],fill=(19,18,23,245))
        for k in range(8):
            r=70+k*70+20*math.sin(t*2+k)
            d.arc([960-r,535-r,960+r,535+r],-40,220,fill=RED+(120-k*10,),width=6)
        text_extruded(layer,(960,545),"LEKIN SACH?",150,(245,239,227),depth=10,glow=RED,max_width=1500)

    elif bid==26:
        # two versions; the missed one tears out of the paper
        draw_shade(layer,570,gy,520,pose("sad",t),"worried",p=1)
        draw_shade(layer,1370,gy,520,pose("cheer",t),"proud",p=out(p*1.6),alpha=.62,flip=True)
        for k in range(13):
            yy=325+k*38
            x=960+math.sin(k*2.3)*26
            d.line([(x-10,yy),(x+14,yy+25)],fill=RED+(180,),width=5)
        label(layer,(570,760),"YOU TODAY",26,SOFT,box=True)
        label(layer,(1370,760),"THE VERSION YOU MISSED",26,RED,box=True)

    elif bid==27:
        draw_seat(layer,1320,gy,330,col=INK,glow=.25+.25*pulse)
        draw_shade(layer,520,gy,520,pose("point",t),"think",p=out(p*2))
        draw_ticket(layer,1280,560,470,190,holes=int(30*p),col=RED,rotate=5*out(p))
        # reservation ribbon peels away
        xx=1050+out(p)*650
        d.polygon([(xx,390),(xx+310,420),(xx+280,495),(xx-30,465)],fill=RED+(235,))
        label(layer,(xx+140,444),"RESERVED",31,(248,241,225))

    elif bid in (28,29,30,31):
        draw_shade(layer,480,gy,500,pose("point" if bid==28 else "type",t),"determined",p=out(p*2))
        if bid==28:
            draw_timer(layer,1280,545,250,"20:00",p,MINT)
        elif bid==29:
            draw_phone(layer,1280,640,440,face_up=False,progress=1,scroll=0)
            d.line([(1070,790),(1490,790)],fill=INK+(130,),width=6)
            label(layer,(1280,725),"DISTRACTION OFF",27,MINT,box=True)
        elif bid==30:
            d.rounded_rectangle([1000,370,1580,760],30,fill=(251,248,240,245),outline=INK+(255,),width=7)
            label(layer,(1290,420),"TODAY'S ONE JOB",28,SOFT)
            for i,txt in enumerate(["OPEN THE FILE","DO 20 MINUTES","LEAVE PROOF"]):
                y=505+i*90
                d.rounded_rectangle([1050,y-32,1108,y+26],14,outline=MINT+(255,),width=5)
                if i<int(p*4):
                    rounded_line(d,[(1064,y-2),(1077,y+13),(1100,y-18)],MINT+(255,),6)
                label(layer,(1150,y),txt,29,INK,anchor="lm")
        else:
            d.rounded_rectangle([1030,445,1530,670],42,fill=MINT+(240,),outline=INK+(255,),width=8)
            text_extruded(layer,(1280,558),"START",125,(246,242,230),depth=7,glow=MINT,max_width=430)
            for k in range(10):
                a=k/10*math.tau+t*.2
                d.line([(1280+math.cos(a)*160,558+math.sin(a)*90),(1280+math.cos(a)*230,558+math.sin(a)*145)],fill=MINT+(120,),width=7)

    elif bid==32:
        d.polygon([(0,320),(960,280),(960,824),(0,824)],fill=MINT+(34,))
        d.polygon([(960,280),(W,320),(W,824),(960,824)],fill=RED+(32,))
        draw_shade(layer,520,gy,500,pose("cheer",t),"proud",p=1)
        draw_shade(layer,1400,gy,500,pose("sad",t),"worried",p=1,flip=True)
        text_extruded(layer,(500,500),"PROOF",120,MINT,depth=9,glow=MINT,max_width=650)
        text_extruded(layer,(1410,500),"LUCKY?",120,RED,depth=9,glow=RED,max_width=650)
        rounded_line(d,[(960,300),(960,824)],INK+(180,),8)

    elif bid==33:
        draw_seat(layer,1320,gy,360,col=INK,glow=.8+.2*pulse)
        x=360+out(p)*430
        draw_shade(layer,x,gy,500,pose("walk",t),"determined",p=1)
        draw_ticket(layer,1320,585,470,190,holes=30,col=GOLD,rotate=-3)
        label(layer,(1320,748),"OWNER: YOU",29,GOLD,box=True)

    elif bid==34:
        # paper ground folds upward into tracks; train waits in gold light
        for k in range(5):
            y=790+k*45
            d.line([(0,y),(W,y-40*k)],fill=(99,92,84,170),width=4)
        tx=730+min(0,p-.15)*0
        draw_train(layer,tx,775,1050,330,light=out(p*1.4))
        draw_shade(layer,520+out(p)*270,gy,500,pose("walk",t),"proud",p=1)
        draw_ticket(layer,350,570,380,160,holes=30,col=GOLD,rotate=-8)
        # overhead light cone
        cone=Image.new("RGBA",(W,H),(0,0,0,0)); cd=ImageDraw.Draw(cone)
        cd.polygon([(1330,160),(1010,820),(1740,820)],fill=GOLD+(42,))
        cone=cone.filter(ImageFilter.GaussianBlur(32)); layer.alpha_composite(cone)
        label(layer,(1440,690),"BOARDING NOW",28,GOLD,box=True)


def transition(layer: Image.Image, beat, t: float, acc):
    lp=t-beat["t0"]
    if beat["id"]==1 or lp>.24: return
    q=out(lp/.24)
    d=ImageDraw.Draw(layer,"RGBA")
    kind=beat["id"]%5
    if kind==0:
        x=W*q
        d.polygon([(x,130),(W,130),(W,850),(x+180,850)],fill=acc+(int(150*(1-q)),))
    elif kind==1:
        for k in range(7):
            x=k*W/7
            hh=H*(1-clamp(q-k*.035))
            d.rectangle([x,0,x+W/7+2,hh],fill=INK+(int(120*(1-q)),))
    elif kind==2:
        r=q*1250
        d.ellipse([W/2-r,H/2-r,W/2+r,H/2+r],outline=acc+(int(180*(1-q)),),width=max(2,int(80*(1-q))))
    elif kind==3:
        for k in range(9):
            y=130+k*80
            x=min(W,W*(1-q)+(k%2)*120)
            d.rectangle([x,y,W,y+26],fill=acc+(int(130*(1-q)),))
    else:
        x=W*(1-q)
        d.polygon([(0,0),(x,0),(x-300,H),(0,H)],fill=INK+(int(130*(1-q)),))


def render_frame(i: int) -> Image.Image:
    t=i/FPS
    idx=min(len(BEATS)-1,max(0,bisect.bisect_right(STARTS,t)-1))
    beat=BEATS[idx]
    dur=max(.001,beat["t1"]-beat["t0"])
    p=clamp((t-beat["t0"])/dur)
    acc=accent_for(beat["id"])
    im=base_world(t,beat["id"],acc)
    scene(im,beat,t,p,acc)
    draw_caption_and_chrome(im,beat,t,acc)
    transition(im,beat,t,acc)
    # tiny time-code/tactile proof in the corner
    d=ImageDraw.Draw(im,"RGBA")
    d.text((W-84,H-43),f"{t:05.2f}s",font=font(18),fill=SOFT+(150,),anchor="rm")
    im.alpha_composite(VIGNETTE)
    return im.convert("RGB")


def ffmpeg_exe() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def render_video(path: Path, start: int=0, end: int|None=None):
    end=NF if end is None else min(end,NF)
    path.parent.mkdir(parents=True,exist_ok=True)
    cmd=[ffmpeg_exe(),"-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
         "-an","-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p","-movflags","+faststart",str(path)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
    began=time.time()
    try:
        for i in range(start,end):
            proc.stdin.write(render_frame(i).tobytes())
            if (i-start)%60==0:
                elapsed=time.time()-began
                rate=(i-start+1)/max(.001,elapsed)
                eta=(end-i-1)/max(.001,rate)
                print(f"WF01 frame {i+1}/{end} · {rate:.1f} fps · ETA {eta/60:.1f} min",flush=True)
    finally:
        if proc.stdin: proc.stdin.close()
    rc=proc.wait()
    if rc: raise SystemExit(f"ffmpeg failed: {rc}")


def contact_sheet(path: Path):
    times=[.7,3.3,7.7,14.9,19.5,23.5,29.4,37.4,41.2,49.7,60.8,72.7]
    cellw,cellh=480,270
    sheet=Image.new("RGB",(cellw*4,cellh*3+72),(22,21,23))
    sd=ImageDraw.Draw(sheet)
    for k,t in enumerate(times):
        fr=render_frame(int(t*FPS)).resize((cellw,cellh),Image.Resampling.LANCZOS)
        x=(k%4)*cellw; y=(k//4)*cellh
        sheet.paste(fr,(x,y))
        sd.rectangle([x,y,x+94,y+29],fill=(18,18,20))
        sd.text((x+8,y+15),f"{t:04.1f}s",font=font(18),fill=(245,240,230),anchor="lm")
    sd.text((30,cellh*3+39),"WF-01 · TUMHARI RESERVED SEAT · 12-FRAME LOOK/CADENCE SHEET",font=font(27),fill=(240,234,221),anchor="lm")
    path.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(path,quality=92,subsampling=0)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path)
    ap.add_argument("--still",type=float)
    ap.add_argument("--still-output",type=Path)
    ap.add_argument("--sheet",action="store_true")
    ap.add_argument("--sheet-output",type=Path,default=PROJECT/"artifacts"/"LOOK_SHEET_WF01.jpg")
    ap.add_argument("--start-frame",type=int,default=0)
    ap.add_argument("--end-frame",type=int)
    args=ap.parse_args()
    if args.still is not None:
        outp=args.still_output or PROJECT/"artifacts"/f"still_{args.still:.2f}.png"
        outp.parent.mkdir(parents=True,exist_ok=True)
        render_frame(int(clamp(args.still,0,DUR-.001)*FPS)).save(outp)
        print(outp)
        return
    if args.sheet:
        contact_sheet(args.sheet_output); print(args.sheet_output); return
    output=args.output or REPO/"build"/"tumhari-seat-wf01-mute.mp4"
    render_video(output,args.start_frame,args.end_frame)
    print(output)

if __name__=="__main__":
    main()
