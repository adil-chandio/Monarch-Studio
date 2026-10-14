"""Preserve moving reference objects on a freshly reconstructed paper stage.

Robust polynomial background keying avoids the cloudy rectangular patches
produced by large-area inpainting. Original source objects/motion stay in
place. Typography and social UI are explicitly excluded, not blurred over.
"""
import cv2
import numpy as np
from clean import W,H,CUTS

# Fixed deterministic paper texture, never random-per-frame flicker.
rng=np.random.default_rng(41014)
yy,xx=np.mgrid[:H,:W].astype(np.float32)
u=(xx-W/2)/(W/2);v=(yy-H/2)/(H/2)
TERMS=[(i,j) for i in range(5) for j in range(5-i)]
small_y,small_x=np.mgrid[:80,:45].astype(np.float32)
su=(small_x-22)/22;sv=(small_y-39.5)/39.5
B=np.stack([su**i*sv**j for i,j in TERMS],-1).reshape(-1,len(TERMS))
Y,X=np.mgrid[:320,:180].astype(np.float32)
U=(X-89.5)/89.5;V=(Y-159.5)/159.5
BP=np.stack([U**i*V**j for i,j in TERMS],-1).reshape(-1,len(TERMS))
noise=rng.normal(0,.5,(H,W)).astype(np.float32)
linen=.35*np.sin(xx*2.5+np.sin(yy*.05)) + .28*np.sin(yy*2.4)
TEXTURE=(noise+linen)[...,None]


def background(frame):
    sm=cv2.resize(frame,(45,80),interpolation=cv2.INTER_AREA).reshape(-1,3).astype(np.float32)
    keep=np.ones(len(sm),bool)
    coef=None
    for step in range(5):
        coef=np.linalg.lstsq(B[keep],sm[keep],rcond=None)[0]
        resid=np.max(np.abs(sm-B@coef),axis=1)
        threshold=max(10.,min(28.,float(np.percentile(resid,65))))
        keep=resid<threshold
        if keep.sum()<400:break
    pred=(BP@coef).reshape(320,180,3)
    pred=cv2.resize(pred,(W,H),interpolation=cv2.INTER_CUBIC)
    return np.clip(pred,0,255).astype(np.float32)


def inrect(mask,box,value=1):
    x0,y0,x1,y1=map(int,box);mask[max(0,y0):min(H,y1),max(0,x0):min(W,x1)]=value


def make_layer(frame,t,shot=None,debug=False):
    if frame.shape[0]==1282:frame=frame[1:-1].copy()
    k=max(0,min(13,int(np.searchsorted(CUTS,t,side='right')-1))) if shot is None else shot
    bg=background(frame)
    f=frame.astype(np.float32)
    delta=np.max(np.abs(f-bg),axis=2)
    seed=(delta>17).astype(np.uint8)
    # Ignore bright paper rings/illumination, but retain pale objects by
    # filling small holes enclosed by their contiguous darker silhouette.
    seed[np.min(f,axis=2)>224]=0
    allow=np.zeros((H,W),np.uint8)
    rois={
      0:[(40,253,610,835)],1:[(18,389,699,746)],
      2:[(20,399,705,793)],3:[(169,306,625,910)],
      4:[(107,130,647,840)],5:[(42,305,682,811)],
      6:[(31,400,709,780)],7:[(70,374,625,805)],
      8:[(72,377,683,874)],9:[(116,182,663,795)],
      10:[(118,300,661,861),(80,986,340,1132)],
      11:[(49,243,636,993)],12:[(153,367,602,862)],
      13:[(176,400,666,891)],
    }
    for box in rois[k]:inrect(allow,box)
    # Broad title zones allow for animated letters moving into place.
    textzones=np.zeros((H,W),np.uint8)
    top=[(0,0,720,490),(0,0,720,375),(0,0,720,402),(0,0,720,439),
         None,(0,0,720,419),(0,0,720,416),(0,0,720,394),
         (0,0,720,409),None,(0,0,720,458),None,
         (0,0,720,496),(0,0,720,413)][k]
    if top:inrect(textzones,top)
    bottom_start=[725,746,792,905,836,802,772,794,871,790,847,0,848,885][k]
    if bottom_start:inrect(textzones,(0,bottom_start,720,1200))
    if k==11:
        inrect(textzones,(80,297,465,472));inrect(textzones,(340,700,714,1070))
    hsv=cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
    # Reference lettering is deeply saturated ink, unlike grayscale bodies.
    ink=((hsv[:,:,1]>94)&(hsv[:,:,2]<180)&(frame[:,:,0].astype(int)>frame[:,:,2].astype(int)+12))
    ink &= textzones>0
    ink=cv2.dilate(ink.astype(np.uint8),np.ones((7,7),np.uint8))
    seed[ink>0]=0
    allow[ink>0]=0
    # Completely exclude social UI. The author remains credited off-frame.
    tagboxes=[(615,298,685,361),(507,368,688,411),(76,839,147,905),(76,909,250,955)]
    if k==0 and t>1.:tagboxes += [(492,350,580,490)]
    for box in tagboxes:inrect(allow,box,0)
    seed*=allow
    # Eliminate very small noise islands; keep thin bow/string components.
    n,lab,stats,_=cv2.connectedComponentsWithStats(seed,8)
    good=np.zeros(n,np.uint8)
    for i in range(1,n):
        if stats[i,cv2.CC_STAT_AREA]>=14:good[i]=1
    seed=good[lab]
    seed=cv2.morphologyEx(seed,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
    # Fill modest enclosed holes (hair highlights / reflective metal), not
    # all negative space between e.g. crutches or laptop lid and base.
    inv=1-seed;n,lab,stats,_=cv2.connectedComponentsWithStats(inv,8)
    holes=np.zeros(n,np.uint8)
    for i in range(1,n):
        if stats[i,cv2.CC_STAT_AREA]<3300:holes[i]=1
    seed=np.maximum(seed,holes[lab])*allow
    alpha=cv2.GaussianBlur(seed.astype(np.float32),(3,3),.55)
    return frame,alpha,bg


def clean_stage(frame,t,shot=None,return_layer=False):
    frame,alpha,bg=make_layer(frame,t,shot)
    # A clean new lavender paper stage; its light shifts by only a few levels
    # independently of the foreground to avoid an obvious static-slide feel.
    Y=yy/H;X=(xx-W/2)/(W/2)
    light=np.exp(-((X*.90)**2+((Y-.48)*2.1)**2)*1.35)
    b=187+63*light;r=115+104*light;g=115+101*light
    base=np.stack([b,g,r],-1).astype(np.float32)+TEXTURE
    # Neutral source-background correction keeps translucent boundaries from
    # showing the old paper as a rectangular patch.
    out=frame.astype(np.float32)*alpha[...,None]+base*(1-alpha[...,None])
    out=np.clip(out,0,255).astype(np.uint8)
    if return_layer:return out,alpha,bg
    return out

if __name__=='__main__':
    from pathlib import Path
    from PIL import Image,ImageDraw,ImageFont
    p=Path('.runtime/flow-repair');cap=cv2.VideoCapture(str(p/'reference.mp4'))
    times=[.4,1.5,2.6,5.8,7.4,10.7,12.8,14.9,16.6,20.8,22.9,25.9,29.7,31.4,
           33.6,35.8,36.8,37.8,39.1,40.4,42.4,45.7,47.8,51.5]
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
    for j in range(0,len(times),8):
        page=Image.new('RGB',(960,912),(26,24,36));d=ImageDraw.Draw(page)
        for i,t in enumerate(times[j:j+8]):
            cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,fr=cap.read()
            if not ok:continue
            out,alpha,bg=clean_stage(fr,t,return_layer=True)
            cv2.imwrite(str(p/f'matte-{t:.1f}.jpg'),out)
            im=Image.fromarray(cv2.cvtColor(out,cv2.COLOR_BGR2RGB));im.thumbnail((236,421))
            x=i%4*240;y=i//4*456;page.paste(im,(x,y+28));d.text((x+3,y+3),f'{t:.1f}s',font=font,fill='white')
        page.save(p/f'matte-sheet-{j//8+1}.jpg',quality=94)
