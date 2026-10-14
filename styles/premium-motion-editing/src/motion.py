"""WF-05 reusable multi-plane image-space motion and short directional depth cuts.

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
# New projects provide their own normalized complete-subject plateau.

def smooth(x):
    x=np.clip(x,0,1);return x*x*(3-2*x)

@functools.lru_cache(maxsize=14)
def depth(rect):
    x0,y0,x1,y1=rect
    x0*=W;x1*=W;y0*=H;y1*=H
    dx=np.maximum(np.maximum(x0-X,X-x1),0)
    dy=np.maximum(np.maximum(y0-Y,Y-y1),0)
    d=1-smooth(np.maximum(dx/75,dy/85))
    return d.astype(np.float32)


def camera(frame,p,rect=(.06,.20,.94,.80),z_strength=.045,direction=1,vertical_drift=-7,roll_degrees=.65):
    p=float(np.clip(p,0,1));d=depth(tuple(rect))
    direction=1 if direction>=0 else -1
    drift=math.sin(p*math.pi)
    # Dolly settles instead of an endless same-speed Ken Burns zoom.
    z=1.004+z_strength*(.15+.85*math.sin(math.pi*p*.82))
    tx=direction*(15*drift-5*p)
    ty=vertical_drift*drift
    roll=direction*roll_degrees*math.sin(2.2*p)
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


def cut(cur,prev,local,mode='depth_push',direction=1):
    mode={'depth_push':0,'diagonal_whip':1,'feathered_cut':2}[mode]
    duration=.25 if mode!=2 else .22
    if prev is None or local>=duration:return cur
    e=float(smooth(local/duration));sign=1 if direction>=0 else -1
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
