"""V6 multi-plane image-space motion and short directional depth cuts.

This is explicitly 2.5D compositing of the supplied moving footage, NOT a
claim that photographed subjects have been reconstructed as 3D geometry.
No foreground pixels are keyed out: near/far inverse maps blend only through
wide background margins, preserving pale objects, hands, shoes and strings.
"""
import functools, math
import cv2
import numpy as np

W,H=720,1280
Y,X=np.mgrid[0:H:4,0:W:4].astype(np.float32)
POINTS=np.dstack([X,Y]).reshape(-1,1,2)
# Constant-depth plateaus include each complete subject cluster. Feathered
# boundaries lie in empty paper, not across a face or limb.
BOXES=[(35,235,685,890),(10,350,710,790),(10,365,710,845),
       (110,280,680,950),(65,95,690,875),(15,260,708,860),
       (5,345,715,830),(100,330,645,1020),(30,335,702,930),
       (85,165,685,845),(55,255,705,1160),(25,205,710,1045),
       (110,330,640,1015),(140,350,690,955)]
MAX_Z=[.07,.028,.045,.06,.06,.045,.027,.09,.045,.045,.025,.026,.085,.025]

def smooth(x):
    x=np.clip(x,0,1);return x*x*(3-2*x)

@functools.lru_cache(maxsize=14)
def depth(k):
    x0,y0,x1,y1=BOXES[k]
    dx=np.maximum(np.maximum(x0-X,X-x1),0)
    dy=np.maximum(np.maximum(y0-Y,Y-y1),0)
    d=1-smooth(np.maximum(dx/75,dy/85))
    return d.astype(np.float32)


def camera(frame,p,k):
    p=float(np.clip(p,0,1));d=depth(k)
    direction=1 if k%2==0 else -1
    drift=math.sin(p*math.pi)
    # Dolly settles instead of an endless same-speed Ken Burns zoom.
    z=1.004+MAX_Z[k]*(.15+.85*math.sin(math.pi*p*.82))
    tx=direction*(15*drift-5*p)
    ty=(-7*drift if k not in [9,10,13] else 3*drift)
    roll=direction*.65*math.sin(2.2*p)
    a=cv2.getRotationMatrix2D((360,645),roll,z)
    a[0,2]+=tx;a[1,2]+=ty
    fg=np.vstack([a,[0,0,1]]).astype(np.float32)
    # A small yaw produces a coherent perspective plane; values stay modest
    # so all source edges remain safely inside the portrait canvas.
    fg[2,0]=direction*0.000021*math.sin(math.pi*p)
    fg[2,1]=0.000008*math.sin(p*math.pi)
    bg=cv2.getRotationMatrix2D((360,640),-roll*.14,1.002)
    bg[0,2]-=tx*.18;bg[1,2]-=ty*.12
    bg=np.vstack([bg,[0,0,1]]).astype(np.float32)
    near=cv2.perspectiveTransform(POINTS,np.linalg.inv(fg)).reshape(Y.shape+(2,))
    far=cv2.perspectiveTransform(POINTS,np.linalg.inv(bg)).reshape(Y.shape+(2,))
    coords=near*d[...,None]+far*(1-d[...,None])
    maps=cv2.resize(coords,(W,H),interpolation=cv2.INTER_LINEAR)
    out=cv2.remap(frame,maps[:,:,0],maps[:,:,1],cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT_101)
    # Very gentle focus separation in the far paper plane only.
    soft=cv2.GaussianBlur(out,(5,5),.8)
    alpha=cv2.resize(d,(W,H),interpolation=cv2.INTER_LINEAR)[...,None]
    out=np.clip(out.astype(np.float32)*(.55+.45*alpha)+soft.astype(np.float32)*(.45-.45*alpha),0,255).astype(np.uint8)
    return out


def radial_blur(im,strength):
    if strength<.007:return im
    acc=im.astype(np.float32)*.34
    for z,w in [(1+strength,.33),(1+strength*2,.33)]:
        m=cv2.getRotationMatrix2D((360,640),0,z)
        acc+=cv2.warpAffine(im,m,(W,H),borderMode=cv2.BORDER_REFLECT_101).astype(np.float32)*w
    return np.clip(acc,0,255).astype(np.uint8)


def cut(cur,prev,local,k):
    duration=.25 if k%3!=2 else .22
    if prev is None or local>=duration:return cur
    e=float(smooth(local/duration));sign=1 if k%2 else -1
    mode=k%3
    if mode==0:
        a=cv2.getRotationMatrix2D((360,640),sign*1.7*e,1+.25*e)
        b=cv2.getRotationMatrix2D((360,640),-sign*1.0*(1-e),1.18-.18*e)
        one=cv2.warpAffine(prev,a,(W,H),borderMode=cv2.BORDER_REFLECT_101)
        two=cv2.warpAffine(cur,b,(W,H),borderMode=cv2.BORDER_REFLECT_101)
        mix=cv2.addWeighted(one,1-e,two,e,0)
        return radial_blur(mix,.016*math.sin(math.pi*e))
    if mode==1:
        a=np.float32([[1,0,-sign*280*e],[0,1,45*e]])
        b=np.float32([[1,0,sign*235*(1-e)],[0,1,-45*(1-e)]])
        one=cv2.warpAffine(prev,a,(W,H),borderMode=cv2.BORDER_REFLECT_101)
        two=cv2.warpAffine(cur,b,(W,H),borderMode=cv2.BORDER_REFLECT_101)
        mix=cv2.addWeighted(one,1-e,two,e,0)
        n=int(1+20*math.sin(math.pi*e))//2*2+1
        return cv2.blur(mix,(n,3))
    # A feathered diagonal cut supplies variety without a white flash.
    yy,xx=np.mgrid[:H,:W].astype(np.float32)
    edge=xx/W+.17*(yy/H-.5)
    mask=np.clip((e*1.28-.13-edge)*18+.5,0,1)[...,None]
    mix=prev.astype(np.float32)*(1-mask)+cur.astype(np.float32)*mask
    return np.clip(mix,0,255).astype(np.uint8)


def tilt_title(rgba,progress,direction=1):
    """A brief yaw/tilt of an extruded type plane, flat and readable at rest."""
    p=float(smooth(progress))
    if p>.997:return rgba
    h,w=rgba.shape[:2];a=(1-p)
    src=np.float32([[0,0],[w-1,0],[w-1,h-1],[0,h-1]])
    xpad=w*.07*a;yshift=h*.10*a
    if direction>0:
        dst=np.float32([[xpad,yshift],[w-1-xpad,0],[w-1,h-1],[0,h-1-yshift]])
    else:
        dst=np.float32([[xpad,0],[w-1-xpad,yshift],[w-1,h-1-yshift],[0,h-1]])
    m=cv2.getPerspectiveTransform(src,dst)
    out=cv2.warpPerspective(rgba,m,(w,h),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
    out[:,:,3]=(out[:,:,3].astype(np.float32)*p).astype(np.uint8)
    return out
