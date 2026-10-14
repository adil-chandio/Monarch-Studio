"""Shot-aware removal of baked-in English titles and social UI.

Input is the USER-SUPPLIED reference animation, not generated stills. This
module retains its actual changing frames. It never accepts the Instagram
end card as a usable shot. Attribution/provenance is retained in README and
PROVENANCE.json, rather than as a visible social tag requested to be removed.
"""
from pathlib import Path
import cv2
import numpy as np

W, H = 720, 1280
ICON=cv2.imread(str(Path(__file__).with_name('icon-template.png')),cv2.IMREAD_GRAYSCALE)
# Input source time, not output narration time. Ref is 720 x 1282 (1px crop).
CUTS = [0, 4.23, 6.22, 9.65, 13.72, 14.97, 21.03, 23.80,
        27.13, 30.63, 32.20, 36.23, 39.70, 46.30, 51.64]
NAMES = ['einstein','equations','clock','violin','watch','flow','car',
         'runner','engine','brain','shortcut','talent','sandbags','art']

def rect(mask, r):
    x0,y0,x1,y1 = [int(z) for z in r]
    mask[max(0,y0):min(H,y1),max(0,x0):min(W,x1)] = 255

def cleanup(frame, t, shot=None, debug=False):
    """Remove glyphs, not whole footage panels. Inpaint only known title ROIs."""
    if frame.shape[0] == 1282:
        frame = frame[1:-1].copy()
    if frame.shape[:2] != (H,W):
        frame = cv2.resize(frame,(W,H))
    k = max(0,min(13,int(np.searchsorted(CUTS,t,side='right')-1))) if shot is None else shot
    regions=[]
    if k==0:
        # Year is moving upwards during the source's opening camera move.
        # Find the first dense row run of the dark numeric glyphs, above hand.
        bw = (frame[:,:,0].astype(int) + frame[:,:,1].astype(int) + frame[:,:,2].astype(int)) / 3 < 88
        prof = bw[110:495,145:350].sum(axis=1)
        candidates = np.where(prof>24)[0]
        if len(candidates):
            groups=np.split(candidates,np.where(np.diff(candidates)>9)[0]+1)
            groups=[g for g in groups if len(g)>12]
            if groups:
                g=groups[0]; top=int(g[0]+110); bottom=int(g[-1]+111)
                regions += [(140,top-4,352,bottom+6),(105,top-84,190,top-5)]
        if t<1.35:
            regions += [(92,200,378,498)]
        if t>=1.35:
            regions += [(125,727,683,1100)]
    elif k==1:
        regions += [(70,746,670,1110)]
    elif k==2:
        regions += [(76,160,352,404),(73,797,684,1120)]
    elif k==3:
        regions += [(120,90,650,445),(140,909,688,1140)]
    elif k==4:
        regions += [(140,842,688,1110)]
    elif k==5:
        regions += [(90,90,658,430),(69,811,689,1140)]
    elif k==6:
        regions += [(160,180,576,409),(70,776,679,1120)]
    elif k==7:
        header_bottom = float(np.interp(t,[23.8,25.5,26.45,27.13],[565,490,367,367]))
        regions += [(75,105,697,header_bottom)]
        # Do not erase the runner's early low-positioned shoes before the
        # lower title actually enters. The small connector is left of him.
        regions += [(146,805,235,974)]
        if t>=25.70:
            # The original runner rises sharply before SPRINT enters; keep
            # early low shoes, then remove the complete title, including
            # the first stroke rows missed by the V5 ramped region.
            regions += [(125,794,704,1190)]
    elif k==8:
        regions += [(90,115,671,473),(125,860,701,1190)]
    elif k==9:
        regions += [(159,791,673,1140)]
    elif k==10:
        regions += [(125,95,612,470),(285,848,664,905),(164,895,698,994)]
    elif k==11:
        regions += [(80,295,460,470),(343,710,690,1020)]
    elif k==12:
        bottom = float(np.interp(t,[39.7,40.5,42.5,44,46.3],[555,540,492,405,385]))
        regions += [(60,90,696,bottom)]
        if t>=42.6:
            regions += [(88,825,706,1230)]
    elif k==13:
        regions += [(101,139,705,407),(122,890,695,1170)]

    roi=np.zeros((H,W),np.uint8)
    for r in regions:rect(roi,r)
    # Purple / charcoal reference typography. Dilation includes antialiasing.
    hsv=cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
    darkness=(hsv[:,:,1]>45)&(hsv[:,:,2]<197)&(frame[:,:,0].astype(int)>frame[:,:,2].astype(int)+14)
    if k==8: darkness &= hsv[:,:,1]>85
    letters=(darkness & (roi>0)).astype(np.uint8)*255
    if k==12:
        # Protect the large connected sandbag, whose ink-purple colour can
        # otherwise be mistaken for a moving heading. Letters are separate
        # small components; the connected bag/body cluster is much larger.
        n,lab,stats,_=cv2.connectedComponentsWithStats(letters,8)
        for i in range(1,n):
            x,y,w,h,area=stats[i]
            if area>2400 and y>340 and x<530 and x+w>190:
                protected=cv2.dilate((lab==i).astype(np.uint8),np.ones((11,11),np.uint8))
                letters[protected>0]=0
    letters=cv2.dilate(letters,np.ones((7,7),np.uint8))
    # Social tag rectangles, which alternate between these two positions.
    # At early intro the name lies over decorative moons; remove that small
    # decoration rather than claim a perfect restoration of occluded pixels.
    tags=np.zeros_like(roi)
    # Detect the actual active corner. Never paint the other corner: at
    # the talent shot the brain's stone occupies the old lower-left tag area.
    for icon_box,name_box in [((615,298,685,361),(507,368,688,411)),
                              ((76,839,147,905),(76,909,250,955))]:
        x0,y0,x1,y1=icon_box
        gray=cv2.cvtColor(frame[y0:y1,x0:x1],cv2.COLOR_BGR2GRAY)
        score=float(np.max(np.abs(cv2.matchTemplate(gray,ICON,cv2.TM_CCOEFF_NORMED))))
        if score>.58:
            rect(tags,icon_box);rect(tags,name_box)
    if k==0 and t>1.0:
        rect(tags,(477,341,586,477))
    mask=cv2.bitwise_or(letters,tags)
    clean=cv2.inpaint(frame,mask,5,cv2.INPAINT_NS)
    if debug:return clean,mask
    return clean

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--media',default='.runtime/flow-repair')
    a=p.parse_args();root=Path(a.media);cap=cv2.VideoCapture(str(root/'reference.mp4'))
    from PIL import Image,ImageDraw,ImageFont
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
    times=[.4,.9,1.5,2.6,3.8,4.9,5.8,7.4,9.1,10.7,12.8,14.9,16.6,20.8,
           22.9,25.9,29.7,31.4,33.6,35.8,36.8,37.8,39.1,40.4,42.4,45.7,47.8,51.5]
    for j in range(0,len(times),8):
        page=Image.new('RGB',(960,912),(26,24,36));d=ImageDraw.Draw(page)
        for i,t in enumerate(times[j:j+8]):
            cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=cap.read()
            if not ok:continue
            out=cleanup(f,t);cv2.imwrite(str(root/f'clean-{t:.1f}.jpg'),out)
            im=Image.fromarray(cv2.cvtColor(out,cv2.COLOR_BGR2RGB));im.thumbnail((236,421))
            x=(i%4)*240;y=(i//4)*456;page.paste(im,(x,y+28))
            d.text((x+4,y+3),f'{t:.1f}s {NAMES[max(0,min(13,int(np.searchsorted(CUTS,t)-1)))]}',font=font,fill='white')
        page.save(root/f'clean-sheet-{j//8+1}.jpg',quality=94)
    print('Wrote source cleanup review sheets (not a deliverable).')
