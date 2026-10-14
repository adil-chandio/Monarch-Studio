"""Assemble existing single-view art; never invent motion or alter a face.

Outputs are explicitly labelled character/shot-design stills. Native generated
images remain separately available. Layout scaling is uniform and for the
printed sheet only, not a claim of a rig, scan or animated performance.
"""
from __future__ import annotations
import argparse
import io
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.utils import ImageReader

W,H=4000,2400
PAPER='#f1f1ed';INK='#20272b';MUTED='#697277';GOLD='#c2a26a';NIGHT='#151c21'
FONT_ROOT=Path('/usr/share/fonts/truetype/dejavu')


def font(size,bold=False,serif=False):
    name=('DejaVuSerif' if serif else 'DejaVuSans')+('-Bold' if bold else '')+'.ttf'
    return ImageFont.truetype(str(FONT_ROOT/name),size)


def tracked(d,xy,text,size=26,fill=INK,gap=4,bold=False):
    x,y=xy;f=font(size,bold)
    for c in text:
        d.text((x,y),c,font=f,fill=fill)
        x+=d.textlength(c,font=f)+gap
    return x


def crown(d,x,y,w,color=GOLD):
    points=[(0,.15),(.19,.40),(.30,0),(.5,.31),(.70,0),(.81,.40),(1,.15),(.89,.79),(.11,.79)]
    p=[(x+a*w,y+b*w*.57) for a,b in points]
    d.polygon(p,fill=color)
    d.rounded_rectangle((x+w*.105,y+w*.49,x+w*.895,y+w*.56),radius=w*.025,fill=color)


def base(title,subtitle,tag):
    im=Image.new('RGB',(W,H),PAPER);d=ImageDraw.Draw(im)
    d.rectangle((0,0,W,350),fill=NIGHT)
    crown(d,105,57,68)
    tracked(d,(200,61),'MONARCH STUDIO',31,fill='#f1eee7',gap=5,bold=True)
    tracked(d,(2980,66),'DESIGN SERIES / 01',23,fill=GOLD,gap=2)
    d.text((101,126),title,font=font(98,True),fill='#f7f5ee')
    d.text((106,264),subtitle,font=font(30),fill='#b7c0c3')
    tracked(d,(3020,279),tag,20,fill='#a9b2b5',gap=1)
    return im,d


def panel(im,path,box,bg='#d7d9d9'):
    x,y,w,h=box
    pic=Image.open(path).convert('RGB')
    scale=min(w/pic.width,h/pic.height)
    result=pic.resize((round(pic.width*scale),round(pic.height*scale)),Image.Resampling.LANCZOS)
    cell=Image.new('RGB',(w,h),bg)
    cell.paste(result,((w-result.width)//2,(h-result.height)//2))
    im.paste(cell,(x,y))


def save_page(im,path):
    im.save(path,dpi=(250,250),optimize=True)
    preview=ImageOps.contain(im,(2000,1200))
    preview.save(path.with_name(path.stem+'_preview.jpg'),quality=92)


def character(root,out):
    im,d=base('CHARACTER / THE MONARCH',
        'Video identity references → one new master → matching generated views',
        '15 OCT 2026')
    positions=[(100,875,'01 / FRONT','FRONT_MASTER.png'),
               (1005,875,'02 / RIGHT-FACING PROFILE','PROFILE.png'),
               (1910,875,'03 / REAR','BACK.png'),
               (2815,1085,'04 / FACE DETAIL','FACE_DETAIL.png')]
    for x,width,label,name in positions:
        tracked(d,(x,392),label,24,gap=2,bold=True)
        d.line((x,437,x+width,437),fill='#a6aeaf',width=2)
        panel(im,root/'character'/name,(x,466,width,1350))
    d.line((100,1882,3900,1882),fill='#abb1b1',width=2)
    tracked(d,(100,1934),'WARDROBE CONTINUITY',27,gap=3,bold=True)
    d.text((100,1988),'Charcoal wool blazer · black open-collar shirt · slim black trousers · leather lace-up boots',font=font(30),fill=INK)
    materials=[('CHARCOAL / WOOL','#454649'),('BLACK / COTTON','#161919'),('BLACK / LEATHER','#24262a'),('WARM / LINING','#242326')]
    for i,(label,color) in enumerate(materials):
        x=100+i*635
        d.rounded_rectangle((x,2070,x+95,2140),radius=8,fill=color)
        tracked(d,(x+118,2094),label,20,gap=1,fill=MUTED)
    tracked(d,(2815,1934),'IDENTITY DIRECTION',27,gap=2,bold=True)
    lines=['Keep the same face, hair and outfit in every shot.',
           'Original video supplies identity reference only.',
           'No footage cut-outs. No face/body warping.']
    for j,line in enumerate(lines):d.text((2815,1994+j*46),line,font=font(25),fill=INK)
    d.line((100,2217,3900,2217),fill='#bec3c1',width=2)
    d.text((100,2276),'AI-generated visual-development stills. Reference-based likeness; not a 3D scan, rig or animation.',font=font(25),fill=MUTED)
    tracked(d,(3510,2279),'SHEET / 01',22,fill=MUTED,gap=2)
    p=out/'MONARCH_CHARACTER_SHEET.png';save_page(im,p)
    return p


SHOTS=[
 ('01_THRESHOLD.png','01 / THE THRESHOLD','Slow entry. Grounded heel-to-toe step.'),
 ('02_FOCUS.png','02 / FOCUS','Small head turn and controlled cuff gesture.'),
 ('03_BREAK.png','03 / THE BREAK','Body pivot and sidestep; debris reacts separately.'),
 ('04_RESOLVE.png','04 / RESOLVE','Settle. Small head turn; hold eye contact.'),
]


def story(root,out):
    if not all((root/'shots'/name).exists() for name,_,_ in SHOTS):return None
    im,d=base('SEQUENCE / AFTER HOURS',
        'Original shot designs from the character master · industrial noir · warm / cool separation',
        'STILLS — NOT VIDEO')
    for i,(name,label,action) in enumerate(SHOTS):
        x=100+i*960
        tracked(d,(x,392),label,24,gap=2,bold=True)
        d.line((x,437,x+920,437),fill='#a6aeaf',width=2)
        panel(im,root/'shots'/name,(x,466,920,1570),bg=NIGHT)
        # A second line rather than tiny squeezed type.
        text=action.split('; ')
        if len(text)==1:
            words=action.split();line='';text=[]
            for word in words:
                candidate=(line+' '+word).strip()
                if d.textlength(candidate,font=font(27))>920:text.append(line);line=word
                else:line=candidate
            if line:text.append(line)
        for j,line in enumerate(text):d.text((x,2086+j*39),line,font=font(27),fill=INK)
    d.line((100,2220,3900,2220),fill='#bec3c1',width=2)
    d.text((100,2276),'These are newly generated cinematic keyframe concepts. Natural body animation has not been rendered.',font=font(25),fill=MUTED)
    tracked(d,(3510,2279),'SHEET / 02',22,fill=MUTED,gap=2)
    p=out/'MONARCH_SHOT_DESIGNS.png';save_page(im,p)
    return p


def ending(root,out):
    image=root/'brand'/'MONARCH_CROWN_END.png'
    if not image.exists():return None
    im,d=base('ENDING / THE STUDIO MARK',
        'Original crown-and-type artwork · the crown remains above the studio name',
        'END-FRAME DESIGN')
    panel(im,image,(240,430,990,1760),bg=NIGHT)
    tracked(d,(1520,530),'THE FINAL HOLD',58,gap=4,bold=True)
    d.line((1520,638,3770,638),fill='#acb1af',width=2)
    lines=[('01','Crown above MONARCH STUDIO.'),
           ('02','Clean typography. No borrowed creator watermark.'),
           ('03','Planned final hold: 3.6 seconds.'),
           ('04','Native ending artwork: 1080 × 1920 pixels.')]
    for i,(n,text) in enumerate(lines):
        y=748+i*153
        tracked(d,(1520,y),n,27,fill='#9b7b44',gap=2,bold=True)
        d.text((1630,y-1),text,font=font(37),fill=INK)
    tracked(d,(1520,1510),'EDIT DIRECTION',26,gap=3,bold=True)
    for i,line in enumerate(['Let the final body action finish before the brand cut.',
                             'Land a restrained metallic accent; let the end mark breathe.',
                             'Fade to black only after the name has had time to read.']):
        d.text((1520,1570+i*60),line,font=font(30),fill=INK)
    d.line((100,2220,3900,2220),fill='#bec3c1',width=2)
    d.text((100,2276),'This page specifies a static end-frame design and proposed edit timing. No final video has been rendered.',font=font(25),fill=MUTED)
    tracked(d,(3510,2279),'SHEET / 03',22,fill=MUTED,gap=2)
    path=out/'MONARCH_ENDING_DESIGN.png';save_page(im,path)
    return path


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    pages=[character(a.root,a.output)];s=story(a.root,a.output)
    if s:pages.append(s)
    e=ending(a.root,a.output)
    if e:pages.append(e)
    pdf=a.output/'MONARCH_CHARACTER_AND_SHOT_BIBLE.pdf'
    c=pdfcanvas.Canvas(str(pdf),pagesize=(1200,720))
    c.setTitle('Monarch Studio — Character and Shot Design')
    c.setAuthor('Monarch Studio')
    c.setSubject('Generated character reference and original shot-design stills; not animation')
    for path in pages:
        # A compact review PDF; lossless PNG boards and native art remain separate.
        buf=io.BytesIO();Image.open(path).convert('RGB').save(buf,format='JPEG',quality=95,subsampling=0)
        buf.seek(0);c.drawImage(ImageReader(buf),0,0,width=1200,height=720);c.showPage()
    c.save()
    report={'pages':[p.name for p in pages],'pdf':pdf.name,'canvas':[W,H],
            'source_native_sizes':{p.name:list(Image.open(p).size) for p in (a.root/'character').glob('*.png')},
            'layout_only_uniform_scaling':True,'face_warps':False,'actual_animation':False}
    (a.output/'ASSEMBLY.json').write_text(json.dumps(report,indent=2)+'\n')
    print('ASSEMBLED',len(pages),'pages:',*[str(p) for p in pages],str(pdf))


if __name__=='__main__':main()
