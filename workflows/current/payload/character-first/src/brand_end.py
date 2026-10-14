"""Create an original static crown-above-MONARCH-STUDIO ending design.
This is graphic artwork, not an encoded or rendered animation.
"""
import argparse
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter,ImageFont,ImageOps

W,H=1080,1920
FONTS=Path('/usr/share/fonts/truetype/dejavu')


def spaced_text(d,text,y,font,fill,spacing):
    widths=[d.textlength(c,font=font) for c in text]
    x=(W-sum(widths)-spacing*(len(text)-1))/2
    for c,width in zip(text,widths):
        d.text((round(x),y),c,font=font,fill=fill)
        x+=width+spacing


def build(path):
    ramp=Image.linear_gradient('L').resize((W,H))
    im=ImageOps.colorize(ramp,(15,23,29),(5,9,12)).convert('RGBA')
    glow=Image.new('RGBA',(W,H),(0,0,0,0));g=ImageDraw.Draw(glow)
    g.ellipse((10,260,1070,1230),fill=(109,89,58,31))
    im=Image.alpha_composite(im,glow.filter(ImageFilter.GaussianBlur(170)))
    d=ImageDraw.Draw(im)
    # Quiet geometric framing, not an overlaid full-frame special effect.
    d.line((140,443,940,443),fill=(94,84,63,65),width=1)
    d.line((140,1329,940,1329),fill=(94,84,63,65),width=1)
    x,y,cw,ch=360,635,360,194
    pts=[(.08,.92),(0,.12),(.20,.47),(.25,.06),(.405,.43),(.50,0),
         (.595,.43),(.75,.06),(.80,.47),(1,.12),(.92,.92)]
    mask=Image.new('L',(W,H),0);m=ImageDraw.Draw(mask)
    points=[(round(x+a*cw),round(y+b*ch)) for a,b in pts]
    m.polygon(points,fill=255)
    m.rounded_rectangle((x+cw*.077,y+ch*.99,x+cw*.923,y+ch*1.13),radius=7,fill=255)
    gold=Image.new('RGB',(W,H));gd=ImageDraw.Draw(gold)
    for row in range(H):
        u=max(0.,min(1.,(row-y)/(ch*1.14)))
        if u<.36:
            f=u/.36;col=tuple(round(a+(b-a)*f) for a,b in zip((239,214,164),(187,143,72)))
        elif u<.69:
            f=(u-.36)/.33;col=tuple(round(a+(b-a)*f) for a,b in zip((187,143,72),(243,216,163)))
        else:
            f=(u-.69)/.31;col=tuple(round(a+(b-a)*f) for a,b in zip((243,216,163),(142,101,48)))
        gd.line((0,row,W,row),fill=col)
    im.paste(gold,(0,0),mask)
    d=ImageDraw.Draw(im)
    d.line(points+[points[0]],fill=(251,224,170,255),width=2)
    for px,py in [(x,y+ch*.12),(x+cw*.25,y+ch*.06),(x+cw*.50,y),(x+cw*.75,y+ch*.06),(x+cw,y+ch*.12)]:
        d.ellipse((px-4,py-4,px+4,py+4),fill=(241,218,174,255))
    main=ImageFont.truetype(str(FONTS/'DejaVuSerif.ttf'),86)
    small=ImageFont.truetype(str(FONTS/'DejaVuSans.ttf'),37)
    spaced_text(d,'MONARCH',951,main,(229,209,170,255),10)
    spaced_text(d,'STUDIO',1080,small,(208,180,128,255),18)
    d.line((375,1200,705,1200),fill=(160,129,77,255),width=2)
    path.parent.mkdir(parents=True,exist_ok=True)
    im.convert('RGB').save(path,optimize=True,dpi=(240,240))
    print('BRAND_STILL_READY',path)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    build(p.parse_args().output)
